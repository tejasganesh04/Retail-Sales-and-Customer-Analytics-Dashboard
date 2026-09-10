from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from retail_analytics.loader import (
    EXPECTED_ARROW_SCHEMA,
    DataSourceError,
    SchemaMismatchError,
    load_curated_dataset,
)

VALID_ROWS = [
    {
        "invoice": "500001",
        "stock_code": "SKU-1",
        "description": "Test product",
        "quantity": 2,
        "invoice_timestamp": datetime(2011, 1, 10, 9, 30),
        "unit_price": Decimal("4.500"),
        "customer_id": "12345",
        "country": "United Kingdom",
        "is_cancelled": False,
        "line_amount": Decimal("9.000"),
    },
    {
        "invoice": "C500001",
        "stock_code": "SKU-1",
        "description": "Test product",
        "quantity": -1,
        "invoice_timestamp": datetime(2011, 1, 12, 10, 0),
        "unit_price": Decimal("4.500"),
        "customer_id": "12345",
        "country": "United Kingdom",
        "is_cancelled": True,
        "line_amount": Decimal("-4.500"),
    },
]


def write_valid_parquet(path: Path, rows: list[dict[str, object]] = VALID_ROWS) -> None:
    table = pa.Table.from_pylist(rows, schema=EXPECTED_ARROW_SCHEMA)
    pq.write_table(table, path)


class FakePaginator:
    def __init__(self, keys: list[str]) -> None:
        self.keys = keys

    def paginate(self, *, Bucket: str, Prefix: str) -> list[dict[str, object]]:
        del Bucket
        return [
            {
                "Contents": [
                    {"Key": key} for key in self.keys if key.startswith(Prefix)
                ]
            }
        ]


class FakeS3Client:
    def __init__(self, objects: dict[str, Path]) -> None:
        self.objects = objects

    def get_paginator(self, operation: str) -> FakePaginator:
        if operation != "list_objects_v2":
            raise AssertionError(f"Unexpected operation: {operation}")
        return FakePaginator(list(self.objects))

    def download_file(self, bucket: str, key: str, destination: str) -> None:
        if bucket != "test-bucket":
            raise AssertionError(f"Unexpected bucket: {bucket}")
        shutil.copyfile(self.objects[key], destination)


class LoaderTests(unittest.TestCase):
    def test_loads_one_local_file_into_the_named_view(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.parquet"
            write_valid_parquet(path)

            with load_curated_dataset(path) as dataset:
                result = dataset.connection.execute(
                    "SELECT invoice, line_amount "
                    "FROM curated_transactions ORDER BY invoice"
                ).fetchall()

            self.assertEqual(
                result,
                [("500001", Decimal("9.000")), ("C500001", Decimal("-4.500"))],
            )

    def test_loads_every_nested_parquet_file_in_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "batch-1").mkdir()
            (root / "batch-2").mkdir()
            write_valid_parquet(root / "batch-1" / "data.parquet", VALID_ROWS[:1])
            write_valid_parquet(root / "batch-2" / "data.parquet", VALID_ROWS[1:])

            with load_curated_dataset(root) as dataset:
                row_count = dataset.connection.execute(
                    "SELECT COUNT(*) FROM curated_transactions"
                ).fetchone()[0]

            self.assertEqual(row_count, 2)

    def test_rejects_an_empty_local_directory(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(DataSourceError, "No Parquet files"),
        ):
            load_curated_dataset(directory)

    def test_rejects_a_schema_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong.parquet"
            wrong_schema = EXPECTED_ARROW_SCHEMA.remove(
                EXPECTED_ARROW_SCHEMA.get_field_index("country")
            )
            table = pa.Table.from_pylist(
                [
                    {
                        key: value
                        for key, value in VALID_ROWS[0].items()
                        if key != "country"
                    }
                ],
                schema=wrong_schema,
            )
            pq.write_table(table, path)

            with self.assertRaisesRegex(SchemaMismatchError, "country"):
                load_curated_dataset(path)

    def test_downloads_only_parquet_objects_from_s3(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.parquet"
            ignored = Path(directory) / "notes.txt"
            write_valid_parquet(source)
            ignored.write_text("not parquet", encoding="utf-8")
            client = FakeS3Client(
                {
                    "curated/batch-1/data.parquet": source,
                    "curated/batch-1/notes.txt": ignored,
                }
            )

            with load_curated_dataset(
                "s3://test-bucket/curated/", s3_client=client
            ) as dataset:
                row_count = dataset.connection.execute(
                    "SELECT COUNT(*) FROM curated_transactions"
                ).fetchone()[0]
                downloaded_files = dataset.source_files

            self.assertEqual(row_count, 2)
            self.assertEqual(len(downloaded_files), 1)
            self.assertFalse(downloaded_files[0].exists())


if __name__ == "__main__":
    unittest.main()
