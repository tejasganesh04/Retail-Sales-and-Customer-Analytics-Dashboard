# Dashboard Workbook Guide

`retail_analytics.xlsx` is the boundary between the analytics code and Power
BI. It is generated output and should not be edited manually.

## Sheets and Excel tables

| Worksheet | Excel table | Intended dashboard use |
|---|---|---|
| `KPI Summary` | `tblKpiSummary` | Headline cards and reporting period |
| `Monthly Sales` | `tblMonthlySales` | Sales and cancellation trends |
| `Products` | `tblProductPerformance` | Product ranking and comparison |
| `Countries` | `tblCountryPerformance` | Geographic performance |
| `Customers Monthly` | `tblCustomerMonthly` | New and repeat customer behaviour |
| `Data Quality` | `tblDataQualitySummary` | Row coverage and value reconciliation |

## Refresh process

1. Run `python -m retail_analytics.export` with the curated Parquet source.
2. Confirm the command completes all cross-report audits and prints the workbook
   path and six report row counts.
3. Replace or upload the workbook connected to Power BI.
4. Refresh the Power BI semantic model.
5. Compare the dashboard cards with the `KPI Summary` sheet.

The export is deliberately narrow. It does not copy the raw transaction-level
dataset into Excel, and it does not contain formulas that could disagree with
the SQL definitions.

## Publication safeguards

The exporter will not publish a workbook unless all of these groups agree:

- Sale, cancellation, and adjustment rows reconcile to curated rows.
- Sale, cancellation, and adjustment values reconcile to net recorded value.
- KPI row and monetary totals agree with the data-quality summary.
- Monthly and country totals agree with the overall KPIs.
- Product gross sales agree with overall gross sales.
- New and repeat customer-order counts agree with known customer orders.

After the audit, the exporter writes a temporary file, reopens it to verify the
workbook structure, and atomically replaces the destination. A failed run cannot
partially overwrite the last valid workbook.

## Power BI report structure

- **Overview:** headline KPIs plus product, country, period sales, and
  new-versus-repeat customer visuals.
- **Data Quality:** curated and classified row counts, missing-value indicators,
  and a monitoring note explaining the reconciliation treatment of
  cancellations and adjustments.

The current version imports the six tables independently. It does not claim a
shared star schema or automatic cross-table filtering.

## Why named tables matter

Power BI imports a named table as a stable object. Formatting or adding notes
outside the table will not change its data range, and regenerating the workbook
keeps the same six table names for the next refresh.
