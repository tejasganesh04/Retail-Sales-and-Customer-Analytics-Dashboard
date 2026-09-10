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
2. Confirm the command prints the workbook path and six report row counts.
3. Replace or upload the workbook connected to Power BI.
4. Refresh the Power BI semantic model.
5. Compare the dashboard cards with the `KPI Summary` sheet.

The export is deliberately narrow. It does not copy the raw transaction-level
dataset into Excel, and it does not contain formulas that could disagree with
the SQL definitions.

## Why named tables matter

Power BI imports a named table as a stable object. Formatting or adding notes
outside the table will not change its data range, and regenerating the workbook
keeps the same six table names for the next refresh.
