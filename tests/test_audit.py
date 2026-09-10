from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from retail_analytics.analytics import QueryResult, run_all_reports
from retail_analytics.audit import audit_reports
from retail_analytics.loader import EXPECTED_ARROW_SCHEMA, load_curated_dataset
from tests.test_analytics import TEST_ROWS


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        parquet_path = Path(self.temporary_directory.name) / "curated.parquet"
        table = pa.Table.from_pylist(TEST_ROWS, schema=EXPECTED_ARROW_SCHEMA)
        pq.write_table(table, parquet_path)
        self.dataset = load_curated_dataset(parquet_path)

    def tearDown(self) -> None:
        self.dataset.close()
        self.temporary_directory.cleanup()

    def test_all_cross_report_reconciliation_rules_pass(self) -> None:
        reports = run_all_reports(self.dataset.connection)

        checks = audit_reports(reports)

        self.assertEqual(len(checks), 11)
        self.assertTrue(all(check.actual == check.expected for check in checks))

    def test_rejects_a_disagreement_between_report_tables(self) -> None:
        reports = run_all_reports(self.dataset.connection)
        original = reports["monthly_sales"]
        rows = [list(row) for row in original.rows]
        gross_sales_index = original.columns.index("gross_sales")
        rows[0][gross_sales_index] += 1
        reports["monthly_sales"] = QueryResult(
            columns=original.columns,
            rows=tuple(tuple(row) for row in rows),
        )

        with self.assertRaisesRegex(
            ValueError,
            "monthly gross sales reconcile to KPI",
        ):
            audit_reports(reports)


if __name__ == "__main__":
    unittest.main()
