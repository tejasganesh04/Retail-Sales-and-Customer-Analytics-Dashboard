"""Build and run the project's version-controlled DuckDB analytics queries."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import duckdb

from .loader import load_curated_dataset

SQL_DIRECTORY: Final[Path] = Path(__file__).resolve().parents[2] / "sql"

MODEL_FILES: Final[tuple[str, ...]] = (
    "00_analytics_transactions.sql",
    "01_customer_orders.sql",
)

REPORT_FILES: Final[dict[str, str]] = {
    "kpi_summary": "kpi_summary.sql",
    "monthly_sales": "monthly_sales.sql",
    "product_performance": "product_performance.sql",
    "country_performance": "country_performance.sql",
    "customer_monthly": "customer_monthly.sql",
    "data_quality_summary": "data_quality_summary.sql",
}


@dataclass(frozen=True)
class QueryResult:
    """Column names and exact values returned by one report query."""

    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]

    def as_dicts(self) -> list[dict[str, object]]:
        """Return rows in a convenient form for tests and later exports."""
        return [dict(zip(self.columns, row, strict=True)) for row in self.rows]


def _read_sql(filename: str) -> str:
    path = SQL_DIRECTORY / filename
    if not path.is_file():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def build_analytics_models(connection: duckdb.DuckDBPyConnection) -> None:
    """Create the shared classification and customer-order views."""
    for filename in MODEL_FILES:
        connection.execute(_read_sql(filename))


def run_report_query(
    connection: duckdb.DuckDBPyConnection,
    report_name: str,
) -> QueryResult:
    """Execute one named report query without changing its value types."""
    try:
        filename = REPORT_FILES[report_name]
    except KeyError as error:
        available = ", ".join(REPORT_FILES)
        raise KeyError(
            f"Unknown report query {report_name!r}. Available: {available}"
        ) from error

    cursor = connection.execute(_read_sql(filename))
    columns = tuple(item[0] for item in cursor.description)
    rows = tuple(cursor.fetchall())
    return QueryResult(columns=columns, rows=rows)


def run_all_reports(
    connection: duckdb.DuckDBPyConnection,
) -> dict[str, QueryResult]:
    """Build shared views and execute every dashboard output query."""
    build_analytics_models(connection)
    return {
        report_name: run_report_query(connection, report_name)
        for report_name in REPORT_FILES
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the retail analytics SQL layer against curated Parquet."
    )
    parser.add_argument("source", help="Local Parquet file/directory or S3 URI")
    arguments = parser.parse_args()

    with load_curated_dataset(arguments.source) as dataset:
        reports = run_all_reports(dataset.connection)

    summary = {
        "reports": {name: len(result.rows) for name, result in reports.items()},
        "kpis": reports["kpi_summary"].as_dicts()[0],
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
