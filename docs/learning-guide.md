# Learning Guide

This file is the permanent map of the project. It makes the implementation easy
to resume and explain without relying on conversation history.

## Block 0 — Understand the upstream output

**Purpose:** Treat the ingestion pipeline's curated Parquet schema as a stable
interface instead of copying ingestion code into this repository.

**Input:** Typed, validated Parquet files produced by the ingestion pipeline.

**Output:** The accepted schema recorded in `docs/analytics-contract.md`.

**Interview explanation:** "I separated ingestion from analytics. The
analytics project consumes a documented Parquet contract, so either side can
change internally without duplicating responsibilities."

## Block 1 — Create the repository foundation

**Purpose:** Give every future file a clear responsibility before adding code.

**Input:** The upstream schema and the dashboard requirements.

**Output:** Repository layout, ignore rules, project README, and analytics
contract.

**Verification:** Confirm generated data and credentials are ignored, and all
documentation links resolve locally.

**Interview explanation:** "I defined metrics and data boundaries before
writing queries, which prevents different dashboard pages from calculating the
same KPI differently."

## Block 2 — Load and validate Parquet

**Purpose:** Give every later SQL query one trusted input called
`curated_transactions`, regardless of whether the Parquet files came from a
local directory or S3.

**Input:** A local Parquet file/directory or an `s3://bucket/prefix` URI.

**Output:** An in-memory DuckDB connection containing the
`curated_transactions` view.

**Code structure:** The loader resolves files, downloads S3 objects when
needed, validates every Arrow schema, creates the DuckDB view, and cleans up
temporary downloads when closed. It performs no business calculations.

**Verification:** Five focused tests cover local files, nested batches, empty
sources, incompatible schemas, and simulated S3 downloads. An integration
check transformed the upstream pipeline's real `batch_001.csv` and confirmed
that all 40,020 curated rows loaded with the expected ten columns.

**Interview explanation:** "I built a loader that presents multiple Parquet
batches as one DuckDB view. It checks every file against the upstream schema
before analysis, preventing a later batch from silently changing a KPI."

## Block 3 — Create the SQL analytics layer

**Purpose:** Keep business rules in readable, version-controlled SQL instead
of hiding them inside Python or dashboard visuals.

**Input:** The validated `curated_transactions` view from Block 2.

**Output:** Two reusable model views and six report results: overall KPIs,
monthly trends, product performance, country performance, customer behaviour,
and data-quality reconciliation.

**Code structure:** `analytics_transactions` adds dates and the three-way row
classification. `customer_orders` reduces sale lines to one row per customer
order and labels the first order as new. The six report queries aggregate only
from these documented models. Python only coordinates the SQL files and
returns their column names and rows.

**Verification:** Five analytics tests use nine hand-checkable rows across two
months. They verify exact KPI values, row classification, monthly
reconciliation, new/repeat customer logic, and the presence of all six report
tables. The full ten-test suite passes. A real-batch integration run analysed
40,020 curated rows and produced 3,001 product groups and 24 country groups.

**Interview explanation:** "I separated modelling from reporting. Shared SQL
views define row and customer-order logic once, while small report queries
reuse those definitions. I tested the KPIs against manually calculated data
before running them on a real batch."

## Block 4 — Export dashboard-ready tables

**Purpose:** Create a small, stable handoff that Power BI can import without
embedding calculations in the workbook.

**Input:** The six tested report results from Block 3.

**Output:** `outputs/dashboard/retail_analytics.xlsx`, with one worksheet and
one named Excel table for each report.

**Code structure:** Pandas converts each typed query result into a labelled
table. OpenPyXL writes those tables, applies explicit date and numeric formats,
freezes the headers, and hides gridlines. The exporter first writes a temporary
file, reopens it to detect structural problems, and only then replaces the
destination workbook.

**Verification:** Two exporter tests check all sheet/table names, typed KPI
values, formats, frozen headers, and successful reopening. Two additional audit
tests verify eleven cross-report reconciliation rules and prove that a
disagreement blocks publication. A real workbook was generated from 40,020
curated rows and visually inspected across all six sheets. The complete
fourteen-test suite passes.

**Interview explanation:** "I kept Excel as a generated delivery format, not
another calculation layer. Every refresh reruns the reviewed SQL and atomically
replaces six named tables that Power BI can import directly."

## Block 5 — Build the Power BI report

**Purpose:** Turn the reviewed reporting tables into a small, explainable
business report without redefining metrics in the visual layer.

**Input:** The six named tables in `retail_analytics.xlsx`.

**Output:** A saved two-page Power BI report: an Overview page for sales,
orders, products, countries, and customer activity, plus a Data Quality page
for row coverage and reconciliation context.

**Design boundary:** Each visual uses the purpose-specific table that already
contains its required grain. Version 1 deliberately avoids claiming a star
schema or automatic S3 refresh. Labels distinguish gross sales, net recorded
value, and cancellation documents instead of collapsing them into an ambiguous
"revenue" measure.

**Verification:** Headline cards and visual totals were compared with the
generated workbook. The current report covers 40,020 curated rows from 1–18
December 2009 and displays the completed-order count without abbreviated units.

**Interview explanation:** "I kept business definitions in tested SQL and used
Power BI as the interactive presentation layer. The report has a performance
view and a data-quality view, so users can interpret KPIs alongside the health
of the underlying data."

## Block 6 — Final quality and portfolio review

**Purpose:** Make every repository and resume claim traceable to repeatable
evidence.

**Verification:** Run all fourteen tests, regenerate and reopen the workbook,
confirm the eleven reconciliation rules, inspect ignored files and credentials,
and compare the README metrics with the exported KPI and quality tables.

**Portfolio boundary:** Dashboard screenshots may be added for presentation,
but generated workbooks, downloaded source data, credentials, and Power BI
project files remain outside Git.
