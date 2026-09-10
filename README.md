# Retail Sales and Customer Analytics Dashboard

An analytics portfolio project built on the curated Parquet output of the
[Automated Retail Data Ingestion Pipeline](https://github.com/tejasganesh04/Automated-Retail-Data-Ingestion-Pipeline).

The project uses DuckDB and SQL to analyse retail sales, products, markets,
cancellations, and customer behaviour. Python prepares stable tables for an
interactive Power BI report that can be built from a Mac in the Power BI web
application.

## Current status

Blocks 1 and 2 are complete: the repository foundation is defined and the
Parquet loader is implemented. The loader accepts local or S3 data, validates
every file against the upstream schema, and exposes one DuckDB view named
`curated_transactions`.

The loader passed its focused test suite and an integration check against
40,020 real curated rows produced by the upstream pipeline's first source
batch. SQL models, dashboard export, and the Power BI report will be added and
tested in later blocks.

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

## Learning approach

Development follows the checkpoints in
[`docs/learning-guide.md`](docs/learning-guide.md). Each block explains its
purpose, inputs, outputs, verification, and interview-level summary before the
next block begins.
