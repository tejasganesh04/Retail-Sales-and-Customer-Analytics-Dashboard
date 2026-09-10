# Power BI Report

The saved report is named **Retail Sales and Customer Analytics Dashboard** and
was last refreshed from `outputs/dashboard/retail_analytics.xlsx` on
10 September 2026. It contains two pages.

## Overview

Headline cards:

- Gross Sales (£)
- Completed Orders
- Average Order Value (£)
- Known Customers
- Cancellation Document Rate (%)

Comparison visuals:

- Monthly Gross Sales
- Sales by Country
- Top Products by Gross Sales
- New vs Repeat Customer Sales

## Data Quality

The page is titled **Data Quality & Pipeline Monitoring**. It summarizes counts
for curated, sale, cancellation, adjustment, missing-customer-ID, and
missing-description rows; Power BI abbreviates the three largest card values at
the current canvas size. The exact verified values are recorded below. A
monitoring note explains that cancellations and adjustments remain in the
dataset for reconciliation rather than being silently discarded.

## Verified values

| Metric | Value |
| --- | ---: |
| Curated rows | 40,020 |
| Sale rows | 39,017 |
| Cancellation rows | 898 |
| Adjustment rows | 105 |
| Missing customer IDs | 10,486 |
| Missing descriptions | 82 |
| Gross sales | £739,789.770 |
| Net recorded value | £716,559.160 |
| Completed orders | 1,511 |
| Average order value | £489.603 |
| Cancellation documents | 357 |
| Cancellation document rate | 19.11% |
| Known customers | 923 |
| Reporting period | 1–18 December 2009 |

These values come from the generated KPI and data-quality tables. The report is
kept in the authenticated Power BI workspace; generated workbooks and local
Power BI project files are intentionally excluded from Git.
