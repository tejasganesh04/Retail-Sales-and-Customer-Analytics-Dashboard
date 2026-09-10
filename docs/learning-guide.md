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

Build one loader supporting both a local path and an S3 URI. It will reject a
dataset whose required columns are missing or incompatible.

## Block 3 — Create the SQL analytics layer

Write small DuckDB SQL files for overall KPIs, monthly trends, product
performance, geographic markets, and customer behaviour. Test every important
metric against a tiny hand-checkable fixture.

## Block 4 — Export dashboard-ready tables

Use Python to run the reviewed SQL and write a documented Excel workbook. The
workbook is generated output, not a second source of truth.

## Block 5 — Build the Power BI report

Upload the workbook in Power BI's browser application and create a small number
of focused report pages. Verify every visual against the SQL output.

## Block 6 — Final quality and portfolio review

Run the complete test suite, document reproducible commands, capture dashboard
screenshots, validate the public link if available, and compare each resume
claim with evidence in the repository.
