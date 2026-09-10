# Retail Sales and Customer Analytics Dashboard

An analytics portfolio project built on the curated Parquet output of the
[Automated Retail Data Ingestion Pipeline](https://github.com/tejasganesh04/Automated-Retail-Data-Ingestion-Pipeline).

The project uses DuckDB and SQL to analyse retail sales, products, markets,
cancellations, and customer behaviour. Python prepares stable tables for an
interactive Power BI report that can be built from a Mac in the Power BI web
application.

## Current status

Blocks 1 through 4 are complete: the repository foundation, validated Parquet
loader, SQL analytics layer, and Power BI-ready Excel export are implemented.
The loader accepts local or S3 data and exposes one DuckDB view named
`curated_transactions`. Versioned SQL then classifies each row, builds
customer-order history, and produces six purpose-specific report tables.

Twelve automated tests pass. They include hand-calculated metric tests and an
integration check against 40,020 real curated rows produced by the upstream
pipeline's first source batch. The real-data workbook was reopened, inspected,
and rendered sheet by sheet. Building and verifying the Power BI report is the
remaining dashboard block.

## Planned workflow

```text
Curated Parquet in S3 or a local folder
                  |
                  v
         Python input validation
                  |
                  v
          DuckDB SQL analytics
                  |
                  v
      Dashboard-ready Excel workbook
                  |
                  v
         Power BI web dashboard
```

The first version uses a deliberate manual refresh step: run one command to
regenerate the Excel workbook, then refresh the report in Power BI. It does not
claim that Power BI refreshes automatically when a file arrives in S3.

## Repository layout

```text
data/sample/            Small, non-sensitive test data
dashboard/screenshots/  Images of the completed Power BI report
docs/                   Contracts and learning notes
outputs/dashboard/      Generated Excel output (not committed)
sql/                    Reviewed DuckDB queries
src/retail_analytics/   Python package
tests/                  Automated tests
```

## Local setup

Create an isolated Python environment and install the dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run the complete test suite:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

## Inspect curated data

Inspect a local Parquet file or a directory containing multiple batches:

```bash
PYTHONPATH=src .venv/bin/python -m retail_analytics.loader /path/to/curated
```

The same command accepts an S3 prefix when standard AWS credentials are
available:

```bash
PYTHONPATH=src .venv/bin/python -m retail_analytics.loader \
  s3://your-bucket/curated/
```

Successful output reports the number of Parquet files, total rows, and the ten
validated columns. No business metrics are calculated at this stage.

## Run the analytics layer

Run all six report queries against a local Parquet file or directory:

```bash
PYTHONPATH=src .venv/bin/python -m retail_analytics.analytics \
  /path/to/curated
```

You can pass an `s3://bucket/prefix` URI instead. The command prints the row
count for each report and the overall KPI summary. It does not write an output
file yet.

The SQL is intentionally split into two reusable model views and six report
queries. See [`docs/sql-guide.md`](docs/sql-guide.md) for the role of each
file and the reasoning behind the design.

## Export the Power BI workbook

Generate the six-table Excel workbook from a local curated directory:

```bash
PYTHONPATH=src .venv/bin/python -m retail_analytics.export \
  /path/to/curated
```

The default output is `outputs/dashboard/retail_analytics.xlsx`. To select a
different location:

```bash
PYTHONPATH=src .venv/bin/python -m retail_analytics.export \
  s3://your-bucket/curated/ \
  --output /path/to/retail_analytics.xlsx
```

The workbook is regenerated from the SQL results each time. It contains one
named Excel table per report, so Power BI can import only the prepared results
instead of more than one million transaction lines. See
[`docs/workbook-guide.md`](docs/workbook-guide.md) for the exact table names.

## Learning approach

Development follows the checkpoints in
[`docs/learning-guide.md`](docs/learning-guide.md). Each block explains its
purpose, inputs, outputs, verification, and interview-level summary before the
next block begins.
