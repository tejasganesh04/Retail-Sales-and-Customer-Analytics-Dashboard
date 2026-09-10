from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from retail_analytics.analytics import build_analytics_models, run_all_reports
from retail_analytics.loader import EXPECTED_ARROW_SCHEMA, load_curated_dataset


def row(
    invoice: str,
    stock_code: str,
    quantity: int,
    timestamp: datetime,
    unit_price: str,
    customer_id: str | None,
    country: str,
    *,
    cancelled: bool = False,
    description: str | None = None,
) -> dict[str, object]:
    price = Decimal(unit_price)
    return {
        "invoice": invoice,
        "stock_code": stock_code,
        "description": description or f"Product {stock_code}",
        "quantity": quantity,
        "invoice_timestamp": timestamp,
        "unit_price": price,
        "customer_id": customer_id,
        "country": country,
        "is_cancelled": cancelled,
        "line_amount": (price * quantity).quantize(Decimal("0.001")),
    }


TEST_ROWS = [
    row("1001", "A", 2, datetime(2011, 1, 5, 9), "10.000", "C1", "UK"),
    row("1001", "B", 1, datetime(2011, 1, 5, 9), "5.000", "C1", "UK"),
    row("1002", "A", 1, datetime(2011, 1, 6, 10), "10.000", "C2", "France"),
    row(
        "C1001",
        "A",
        -1,
        datetime(2011, 1, 7, 11),
        "10.000",
        "C1",
        "UK",
        cancelled=True,
    ),
    row(
        "ADJ1",
        "ADJ",
        0,
        datetime(2011, 1, 8, 12),
        "0.000",
        None,
        "UK",
        description="Adjustment",
    ),
    row("1003", "A", 1, datetime(2011, 2, 1, 9), "10.000", "C1", "UK"),
    row("1004", "B", 3, datetime(2011, 2, 2, 10), "5.000", "C3", "France"),
    row("1005", "C", 2, datetime(2011, 2, 2, 11), "7.500", None, "Germany"),
    row(
        "ADJ2",
        "C",
        -1,
        datetime(2011, 2, 3, 12),
        "7.500",
        None,
        "Germany",
        description="Product C",
    ),
]


class AnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        parquet_path = Path(self.temporary_directory.name) / "curated.parquet"
        table = pa.Table.from_pylist(TEST_ROWS, schema=EXPECTED_ARROW_SCHEMA)
        pq.write_table(table, parquet_path)
        self.dataset = load_curated_dataset(parquet_path)

    def tearDown(self) -> None:
        self.dataset.close()
        self.temporary_directory.cleanup()

    def test_classifies_rows_without_discarding_adjustments(self) -> None:
        build_analytics_models(self.dataset.connection)
        result = self.dataset.connection.execute(
            "SELECT row_class, COUNT(*) "
            "FROM analytics_transactions GROUP BY row_class ORDER BY row_class"
        ).fetchall()

        self.assertEqual(
            result,
            [("cancellation", 1), ("other_adjustment", 2), ("sale", 6)],
        )

    def test_calculates_exact_overall_kpis(self) -> None:
        kpis = run_all_reports(self.dataset.connection)["kpi_summary"].as_dicts()[0]

        self.assertEqual(kpis["curated_rows"], 9)
        self.assertEqual(kpis["gross_sales"], Decimal("75.000"))
        self.assertEqual(kpis["net_recorded_value"], Decimal("57.500"))
        self.assertEqual(kpis["completed_orders"], 5)
        self.assertEqual(kpis["average_order_value"], 15.0)
        self.assertEqual(kpis["cancellation_documents"], 1)
        self.assertEqual(kpis["cancellation_document_rate_pct"], 16.67)
        self.assertEqual(kpis["known_customers"], 3)
        self.assertEqual(kpis["first_transaction_date"], date(2011, 1, 5))
        self.assertEqual(kpis["last_transaction_date"], date(2011, 2, 3))

    def test_calculates_monthly_sales_and_adjusted_net_value(self) -> None:
        monthly = run_all_reports(self.dataset.connection)[
            "monthly_sales"
        ].as_dicts()

        self.assertEqual(len(monthly), 2)
        self.assertEqual(monthly[0]["transaction_month"], date(2011, 1, 1))
        self.assertEqual(monthly[0]["gross_sales"], Decimal("35.000"))
        self.assertEqual(monthly[0]["cancellation_value"], Decimal("10.000"))
        self.assertEqual(monthly[0]["net_recorded_value"], Decimal("25.000"))
        self.assertEqual(monthly[1]["gross_sales"], Decimal("40.000"))
        self.assertEqual(monthly[1]["net_recorded_value"], Decimal("32.500"))

    def test_separates_new_and_repeat_customer_orders(self) -> None:
        customer_monthly = run_all_reports(self.dataset.connection)[
            "customer_monthly"
        ].as_dicts()

        self.assertEqual(customer_monthly[0]["new_customer_orders"], 2)
        self.assertEqual(customer_monthly[0]["repeat_customer_orders"], 0)
        self.assertEqual(
            customer_monthly[0]["new_customer_sales"], Decimal("35.000")
        )
        self.assertEqual(customer_monthly[1]["new_customer_orders"], 1)
        self.assertEqual(customer_monthly[1]["repeat_customer_orders"], 1)
        self.assertEqual(
            customer_monthly[1]["new_customer_sales"], Decimal("15.000")
        )
        self.assertEqual(
            customer_monthly[1]["repeat_customer_sales"], Decimal("10.000")
        )

    def test_returns_all_six_documented_report_tables(self) -> None:
        reports = run_all_reports(self.dataset.connection)

        self.assertEqual(
            tuple(reports),
            (
                "kpi_summary",
                "monthly_sales",
                "product_performance",
                "country_performance",
                "customer_monthly",
                "data_quality_summary",
            ),
        )
        self.assertEqual(len(reports["product_performance"].rows), 3)
        self.assertEqual(len(reports["country_performance"].rows), 3)
        quality = reports["data_quality_summary"].as_dicts()[0]
        self.assertEqual(quality["sale_rows"], 6)
        self.assertEqual(quality["cancellation_rows"], 1)
        self.assertEqual(quality["adjustment_rows"], 2)
        self.assertEqual(quality["sale_value"], Decimal("75.000"))
        self.assertEqual(quality["cancellation_value"], Decimal("-10.000"))
        self.assertEqual(quality["adjustment_value"], Decimal("-7.500"))
        self.assertEqual(quality["net_recorded_value"], Decimal("57.500"))


if __name__ == "__main__":
    unittest.main()
