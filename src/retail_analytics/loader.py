"""Load the ingestion pipeline's curated Parquet output into DuckDB.

This module has one responsibility: turn a local path or an S3 URI into a
validated DuckDB view named ``curated_transactions``. Business calculations
belong in the SQL layer and are deliberately kept out of this loader.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Final, Self
from urllib.parse import urlparse

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

VIEW_NAME: Final[str] = "curated_transactions"

# This is copied from the public interface documented by the upstream pipeline,
# not from its implementation. Keeping the contract here lets this repository
# validate inputs without importing or duplicating the ingestion code.
EXPECTED_ARROW_SCHEMA: Final[pa.Schema] = pa.schema(
    [
        pa.field("invoice", pa.string(), nullable=False),
        pa.field("stock_code", pa.string(), nullable=False),
        pa.field("description", pa.string(), nullable=True),
        pa.field("quantity", pa.int32(), nullable=False),
        pa.field("invoice_timestamp", pa.timestamp("us"), nullable=False),
        pa.field("unit_price", pa.decimal128(18, 3), nullable=False),
        pa.field("customer_id", pa.string(), nullable=True),
        pa.field("country", pa.string(), nullable=False),
        pa.field("is_cancelled", pa.bool_(), nullable=False),
        pa.field("line_amount", pa.decimal128(18, 3), nullable=False),
    ]
)


class DataSourceError(ValueError):
    """The requested local or S3 source cannot provide Parquet files."""


class SchemaMismatchError(ValueError):
    """A Parquet file does not satisfy the curated-data contract."""


@dataclass
class LoadedDataset:
    """A DuckDB connection and the resources that keep its view available."""

    connection: duckdb.DuckDBPyConnection
    source_files: tuple[Path, ...]
    _temporary_directory: TemporaryDirectory[str] | None = None

    def close(self) -> None:
        """Close DuckDB and remove any temporary S3 downloads."""
        self.connection.close()
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _local_parquet_files(source: Path) -> tuple[Path, ...]:
    """Resolve one local Parquet file or every Parquet file below a directory."""
    resolved = source.expanduser().resolve()

    if not resolved.exists():
        raise DataSourceError(f"Local source does not exist: {resolved}")

    if resolved.is_file():
        if resolved.suffix.lower() != ".parquet":
            raise DataSourceError(f"Expected a .parquet file: {resolved}")
        return (resolved,)

    files = tuple(
        sorted(
            path.resolve()
            for path in resolved.rglob("*")
            if path.is_file() and path.suffix.lower() == ".parquet"
        )
    )
    if not files:
        raise DataSourceError(f"No Parquet files found below: {resolved}")
    return files


def _parse_s3_uri(source: str) -> tuple[str, str]:
    parsed = urlparse(source)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise DataSourceError(f"Invalid S3 URI: {source}")
    return parsed.netloc, parsed.path.lstrip("/")


def _s3_parquet_files(
    source: str,
    s3_client: Any | None,
) -> tuple[tuple[Path, ...], TemporaryDirectory[str]]:
    """Download Parquet objects under an S3 URI into an isolated directory."""
    bucket, prefix = _parse_s3_uri(source)

    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")

    keys: list[str] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(
            item["Key"]
            for item in page.get("Contents", [])
            if item["Key"].lower().endswith(".parquet")
        )

    keys.sort()
    if not keys:
        raise DataSourceError(f"No Parquet objects found below: {source}")

    temporary_directory = TemporaryDirectory(prefix="retail-analytics-")
    temporary_root = Path(temporary_directory.name)
    files: list[Path] = []

    try:
        for index, key in enumerate(keys):
            destination = temporary_root / f"part-{index:05d}.parquet"
            s3_client.download_file(bucket, key, str(destination))
            files.append(destination)
    except Exception:
        temporary_directory.cleanup()
        raise

    return tuple(files), temporary_directory


def _validate_parquet_schemas(files: tuple[Path, ...]) -> None:
    """Check every file, preventing a later batch from silently changing schema."""
    for path in files:
        actual_schema = pq.read_schema(path)
        if not actual_schema.equals(EXPECTED_ARROW_SCHEMA, check_metadata=False):
            raise SchemaMismatchError(
                "Curated schema mismatch in "
                f"{path}.\nExpected:\n{EXPECTED_ARROW_SCHEMA}\nActual:\n{actual_schema}"
            )


def _sql_string(value: str) -> str:
    """Return one safely quoted DuckDB string literal."""
    return "'" + value.replace("'", "''") + "'"


def _create_view(
    files: tuple[Path, ...],
    database: str,
) -> duckdb.DuckDBPyConnection:
    file_list = ", ".join(_sql_string(str(path)) for path in files)
    connection = duckdb.connect(database=database)
    try:
        connection.execute(
            f"CREATE VIEW {VIEW_NAME} AS "
            f"SELECT * FROM read_parquet([{file_list}], union_by_name = false)"
        )
    except Exception:
        connection.close()
        raise
    return connection


def load_curated_dataset(
    source: str | Path,
    *,
    database: str = ":memory:",
    s3_client: Any | None = None,
) -> LoadedDataset:
    """Validate curated Parquet and expose it as ``curated_transactions``."""
    temporary_directory: TemporaryDirectory[str] | None = None

    if isinstance(source, str) and source.startswith("s3://"):
        files, temporary_directory = _s3_parquet_files(source, s3_client)
    else:
        files = _local_parquet_files(Path(source))

    try:
        _validate_parquet_schemas(files)
        connection = _create_view(files, database)
    except Exception:
        if temporary_directory is not None:
            temporary_directory.cleanup()
        raise

    return LoadedDataset(connection, files, temporary_directory)


def _summary(dataset: LoadedDataset) -> dict[str, object]:
    row_count = dataset.connection.execute(
        f"SELECT COUNT(*) FROM {VIEW_NAME}"
    ).fetchone()[0]
    columns = [field.name for field in EXPECTED_ARROW_SCHEMA]
    return {
        "view": VIEW_NAME,
        "files": len(dataset.source_files),
        "rows": row_count,
        "columns": columns,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate curated retail Parquet and inspect its DuckDB view."
    )
    parser.add_argument("source", help="Local Parquet file/directory or S3 URI")
    arguments = parser.parse_args()

    with load_curated_dataset(arguments.source) as dataset:
        print(json.dumps(_summary(dataset), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
