# Retail Sales and Customer Analytics Dashboard

An analytics portfolio project built on the curated Parquet output of the
[Automated Retail Data Ingestion Pipeline](https://github.com/tejasganesh04/Automated-Retail-Data-Ingestion-Pipeline).

The project uses DuckDB and SQL to analyse retail sales, products, markets,
cancellations, and customer behaviour. Python prepares stable tables for an
interactive Power BI report that can be built from a Mac in the Power BI web
application.

## Current status

Block 1 is complete: the repository layout and analytics contract are defined.
The data loader, SQL models, dashboard export, and Power BI report will be added
and tested in separate, understandable blocks.

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

## Learning approach

Development follows the checkpoints in
[`docs/learning-guide.md`](docs/learning-guide.md). Each block explains its
purpose, inputs, outputs, verification, and interview-level summary before the
next block begins.
