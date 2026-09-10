# Analytics Contract

## 1. Project boundary

This repository does not ingest or clean raw CSV files. Those responsibilities
belong to the upstream ingestion pipeline. This project begins with validated,
typed Parquet files and turns them into analytical tables and visualisations.

The first release supports two equivalent input locations:

- A local file or directory containing curated Parquet files.
- An Amazon S3 URI containing the same curated Parquet files.

## 2. Required curated schema

The loader will require these exact columns:

| Column | Logical type | Meaning |
|---|---|---|
| `invoice` | string | Invoice or transaction document identifier |
| `stock_code` | string | Product or adjustment code |
| `description` | nullable string | Product description |
| `quantity` | 32-bit integer | Units recorded on the line |
| `invoice_timestamp` | timestamp | Transaction date and time |
| `unit_price` | decimal(18,3) | Price per unit |
| `customer_id` | nullable string | Customer identifier |
| `country` | string | Customer market |
| `is_cancelled` | boolean | Whether the invoice starts with `C` |
| `line_amount` | decimal(18,3) | `quantity * unit_price` |

Decimal monetary values must remain decimals through the analytics layer. They
must not be converted to binary floating-point values before aggregation.

## 3. Row classification

The dashboard separates three business cases instead of assuming every valid
row is a completed sale:

- **Sale:** not cancelled, `quantity > 0`, and `unit_price > 0`.
- **Cancellation:** `is_cancelled = true`.
- **Other adjustment:** every remaining valid row, including zero-value and
  unusual non-cancelled records.

This classification does not delete unusual records. It makes their treatment
visible and prevents them from silently inflating completed-sales metrics.

## 4. KPI definitions

| KPI | Definition |
|---|---|
| Gross sales | Sum of `line_amount` for sale rows |
| Net recorded value | Sum of `line_amount` across every curated row |
| Completed orders | Distinct invoices containing at least one sale row |
| Average order value | Gross sales divided by completed orders |
| Cancellation documents | Distinct invoices classified as cancellations |
| Cancellation document rate | Cancellation documents divided by completed orders plus cancellation documents |
| Known customers | Distinct non-null customers associated with sale rows |

`Cancellation document rate` is deliberately named precisely. The source
contains cancellation documents, not a guaranteed one-to-one status history
for every original order.

## 5. Customer classification

Customer analysis excludes null `customer_id` values. A customer's first
chronological completed order observed within the loaded dataset is classified
as **new**. Later completed orders are classified as **repeat**. All lines
belonging to the same invoice receive the same classification. This is a
dataset-relative cohort label; it does not claim to know whether the customer
purchased before the available history began.

## 6. Implemented dashboard tables

The Excel export contains small, purpose-specific tables rather than trying
to place more than one million transaction lines into a worksheet:

- `kpi_summary`
- `monthly_sales`
- `product_performance`
- `country_performance`
- `customer_monthly`
- `data_quality_summary`

Each table is generated from version-controlled SQL. The Power BI report
visualises these results; it does not introduce undocumented business rules.

Before workbook generation, eleven reconciliation rules compare totals across
the KPI, monthly, product, country, customer, and data-quality grains. Any
disagreement raises an error and prevents publication.

## 7. Refresh promise

Version 1 provides a reproducible manual refresh:

1. Run the export command.
2. Replace or synchronise the generated workbook used by Power BI.
3. Refresh the Power BI semantic model.

Automatic S3-to-Power-BI refresh is outside version 1 and must not be claimed
until it is implemented and tested.

## 8. Dashboard model boundary

The six exported tables have different grains and are intentionally imported as
separate reporting tables. Version 1 does not claim a shared dimensional model
or cross-table global filtering. Each visual is bound to the report table that
already contains the grain and metric it needs.
