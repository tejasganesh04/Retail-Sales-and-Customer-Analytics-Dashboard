"""Cross-check report totals before they are handed to Power BI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from .analytics import QueryResult


@dataclass(frozen=True)
class AuditCheck:
    """One named reconciliation rule and its verified result."""

    name: str
    actual: object
    expected: object


def _single_row(result: QueryResult, report_name: str) -> dict[str, object]:
    rows = result.as_dicts()
    if len(rows) != 1:
        raise ValueError(
            f"Audit expected one {report_name!r} row, but found {len(rows)}."
        )
    return rows[0]


def _sum(rows: list[dict[str, object]], column: str) -> object:
    values = [row[column] for row in rows]
    if not values:
        return Decimal("0.000")
    return sum(values, start=Decimal("0.000"))


def audit_reports(reports: Mapping[str, QueryResult]) -> tuple[AuditCheck, ...]:
    """Verify row counts and financial totals across independent report grains.

    A failed rule raises ``ValueError`` so the exporter cannot publish a
    workbook whose summary, monthly, country, and quality tables disagree.
    """
    required = {
        "kpi_summary",
        "monthly_sales",
        "product_performance",
        "country_performance",
        "customer_monthly",
        "data_quality_summary",
    }
    missing = sorted(required.difference(reports))
    if missing:
        raise ValueError(f"Audit cannot run; missing reports: {', '.join(missing)}")

    kpis = _single_row(reports["kpi_summary"], "kpi_summary")
    quality = _single_row(
        reports["data_quality_summary"], "data_quality_summary"
    )
    monthly = reports["monthly_sales"].as_dicts()
    countries = reports["country_performance"].as_dicts()
    products = reports["product_performance"].as_dicts()
    customer_monthly = reports["customer_monthly"].as_dicts()

    checks = (
        AuditCheck(
            "quality row classes reconcile to curated rows",
            quality["sale_rows"]
            + quality["cancellation_rows"]
            + quality["adjustment_rows"],
            quality["curated_rows"],
        ),
        AuditCheck(
            "quality values reconcile to net recorded value",
            quality["sale_value"]
            + quality["cancellation_value"]
            + quality["adjustment_value"],
            quality["net_recorded_value"],
        ),
        AuditCheck(
            "KPI row count agrees with quality summary",
            kpis["curated_rows"],
            quality["curated_rows"],
        ),
        AuditCheck(
            "KPI gross sales agrees with quality summary",
            kpis["gross_sales"],
            quality["sale_value"],
        ),
        AuditCheck(
            "KPI net value agrees with quality summary",
            kpis["net_recorded_value"],
            quality["net_recorded_value"],
        ),
        AuditCheck(
            "monthly gross sales reconcile to KPI",
            _sum(monthly, "gross_sales"),
            kpis["gross_sales"],
        ),
        AuditCheck(
            "monthly net value reconciles to KPI",
            _sum(monthly, "net_recorded_value"),
            kpis["net_recorded_value"],
        ),
        AuditCheck(
            "country gross sales reconcile to KPI",
            _sum(countries, "gross_sales"),
            kpis["gross_sales"],
        ),
        AuditCheck(
            "country net value reconciles to KPI",
            _sum(countries, "net_recorded_value"),
            kpis["net_recorded_value"],
        ),
        AuditCheck(
            "product gross sales reconcile to KPI",
            _sum(products, "gross_sales"),
            kpis["gross_sales"],
        ),
        AuditCheck(
            "new and repeat orders reconcile within each month",
            sum(
                row["new_customer_orders"] + row["repeat_customer_orders"]
                for row in customer_monthly
            ),
            sum(row["known_customer_orders"] for row in customer_monthly),
        ),
    )

    failures = [check for check in checks if check.actual != check.expected]
    if failures:
        details = "; ".join(
            f"{check.name}: actual={check.actual!r}, expected={check.expected!r}"
            for check in failures
        )
        raise ValueError(f"Analytics reconciliation failed: {details}")

    return checks
