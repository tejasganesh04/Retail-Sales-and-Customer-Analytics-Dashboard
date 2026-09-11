# Retail Sales and Customer Analytics Dashboard

A tested retail analytics layer and interactive Power BI report built on the curated Parquet output of the [Automated Retail Data Ingestion Pipeline](https://github.com/tejasganesh04/Automated-Retail-Data-Ingestion-Pipeline).

The project uses DuckDB and version-controlled SQL to calculate sales, product, market, cancellation, customer, and data-quality metrics. Python validates the inputs, audits the results, and exports six stable tables for Power BI.

## End-to-end workflow

```text
Curated Parquet in S3 or a local folder
                  |
                  v
       Python schema validation
                  |
                  v
       DuckDB analytical models
                  |
                  v
   Six audited reporting tables
                  |
                  v
       Excel handoff workbook
                  |
                  v
      Interactive Power BI report
```

The analytics repository deliberately starts at curated Parquet. Raw-file ingestion, cleansing, quarantine handling, and idempotency remain in the upstream pipeline rather than being duplicated here.

## What is implemented

- Local-directory and Amazon S3 Parquet loading through one validated `curated_transactions` view
- Strict validation of all ten fields in the upstream curated-data contract
- Shared SQL models for sale, cancellation, and adjustment classification
- Six purpose-specific report tables for KPIs, monthly sales, products, countries, customers, and data quality
- Eleven cross-report reconciliation rules that block publication when totals disagree
- Atomic generation and structural verification of a formatted Excel workbook with six named tables
- A two-page Power BI report covering business performance and data quality
- Fourteen automated tests, including hand-calculated business cases and workbook checks

## Verified dataset

The current workbook and Power BI report were built from the first curated source batch:

- 40,020 curated transaction rows
- 39,017 sale rows, 898 cancellation rows, and 105 adjustment rows
- 1,511 completed orders and 923 known customers
- 3,001 product groups and 24 country groups
- Reporting period: 1–18 December 2009

These figures are evidence for the current report build, not performance claims about a larger system.

## Dashboard pages

### Overview

The overview page presents the headline KPIs and comparison visuals for sales, orders, products, countries, and new-versus-repeat customer activity. Report labels use the exact business terms defined in the analytics contract, including **gross sales**, **net recorded value**, and **cancellation document rate**.

### Data Quality

The data-quality page shows total curated rows, the three-way row classification, and missing-description and missing-customer-ID counts. Its monitoring note explains why cancellation and adjustment rows are retained for reconciliation instead of being silently discarded.

The saved report structure and its verified values are recorded in [dashboard/README.md](dashboard/README.md).

The report is intentionally based on small prepared tables instead of importing every transaction line into Power BI. Version 1 uses a reproducible manual refresh: regenerate the workbook, replace or upload it, and refresh the semantic model. It does not claim automatic refresh from S3.

## Repository layout

```text
sql/                    Reviewed DuckDB models and report queries
src/retail_analytics/   Loader, analytics runner, audit, and exporter
tests/                  Unit, integration, and workbook tests
docs/                   Contracts and implementation guides
outputs/dashboard/      Generated workbook location; contents are ignored
dashboard/              Saved-report structure and verified visual inventory
```

Generated workbooks, downloaded data, credentials, and Power BI project files are excluded from Git.

## Local setup

Python 3.12 is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run all tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

## Inspect curated data

Inspect a local Parquet file or directory:

```bash
PYTHONPATH=src python -m retail_analytics.loader /path/to/curated
```

The same command accepts an S3 prefix when standard AWS credentials are available:

```bash
PYTHONPATH=src python -m retail_analytics.loader \
  s3://your-bucket/curated/
```

Successful output reports the resolved Parquet files, row count, and validated schema. It does not calculate business metrics.

## Run the analytics layer

Execute all six report queries without writing a workbook:

```bash
PYTHONPATH=src python -m retail_analytics.analytics /path/to/curated
```

The command prints each report's row count and the overall KPI summary. Business rules stay in the SQL files rather than being hidden inside Python or visual configuration. [The SQL guide](docs/sql-guide.md) explains each model and report query.

## Export the Power BI workbook

Generate the workbook from a local Parquet file or directory:

```bash
PYTHONPATH=src python -m retail_analytics.export /path/to/curated
```

The default destination is `outputs/dashboard/retail_analytics.xlsx`. A custom destination and an S3 source are also supported:

```bash
PYTHONPATH=src python -m retail_analytics.export \
  s3://your-bucket/curated/ \
  --output /path/to/retail_analytics.xlsx
```

Before publishing, the exporter verifies row counts and monetary totals across the six independent report grains. It then writes a temporary workbook, reopens it to verify the structure, and atomically replaces the destination. [The workbook guide](docs/workbook-guide.md) documents the sheet and table names used by Power BI.

## Metric boundaries

- **Gross sales** include only non-cancelled rows with positive quantity and price.
- **Net recorded value** includes every curated row, including cancellations and adjustments.
- **Completed orders** are distinct invoices containing at least one sale row.
- **Cancellation document rate** compares cancellation documents with completed and cancellation documents; it is not presented as a one-to-one order return rate.
- **New customers** means a customer's first completed order observed within the loaded dataset, not necessarily their lifetime first purchase.

All definitions and refresh guarantees are recorded in [docs/analytics-contract.md](docs/analytics-contract.md).
