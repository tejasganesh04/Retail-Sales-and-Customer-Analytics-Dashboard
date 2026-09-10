# SQL Analytics Guide

The SQL layer answers one question at a time. Python is responsible for loading
validated Parquet and executing the files; the business definitions remain in
SQL so they can be reviewed independently.

## Reusable models

### `00_analytics_transactions.sql`

This is the transaction-level model. It keeps every curated column, adds daily
and monthly date fields, and assigns exactly one `row_class`:

- `sale` for a non-cancelled row with positive quantity and price;
- `cancellation` when the upstream cancellation flag is true;
- `other_adjustment` for every remaining valid row.

Keeping all three groups allows gross sales and net recorded value to tell
different, clearly named stories.

### `01_customer_orders.sql`

This model selects completed-sale rows with a known customer and reduces their
line items to one row per invoice. A window function numbers each customer's
orders chronologically. Order number one is labelled `new`; later orders are
labelled `repeat`.

## Report queries

| File | Question answered |
|---|---|
| `kpi_summary.sql` | What are the headline totals and date range? |
| `monthly_sales.sql` | How do sales, cancellations, and adjustments change by month? |
| `product_performance.sql` | Which stock codes drive units, orders, and gross sales? |
| `country_performance.sql` | Which markets drive customers, orders, and value? |
| `customer_monthly.sql` | How many new and repeat customer orders occur each month? |
| `data_quality_summary.sql` | Can every curated row and its value be reconciled to one class? |

## Why there is no single giant query

The output tables have different grains. A KPI summary has one row, monthly
sales has one row per month, and product performance has one row per stock
code. Keeping separate queries prevents accidental duplication when unrelated
grains are joined and gives Power BI small, direct tables for each visual.

## Reconciliation rule

The three row-class counts in `data_quality_summary` must add up to
`curated_rows`. Their three value totals must add up to `net_recorded_value`.
This makes unusual but structurally valid records visible rather than silently
discarding them.
