# Day 4 — adding a local database boundary

**Date:** 22 August 2026

## What I built

I added DuckDB as the first local analytical database in the project. The loader reads the generated CSVs, creates typed `raw` tables and runs the reporting SQL in `sql/duckdb/marts.sql`.

The output is split into two schemas:

- `raw`, which is close to the generated source files
- `mart`, which contains the reporting tables from Day 3

The DuckDB file is local and ignored by Git. It can be rebuilt from the generated data, so there is no need to commit a database binary to the repository.

## Decisions made today

I used explicit column types when creating the raw tables. Automatic CSV inference would be convenient, but it could make a date or money field change type depending on the sample. I want those choices visible while the dataset is still small.

I kept the load as a full refresh. That is not meant to be an incremental strategy; it is a simple choice for a small generated dataset where starting from a clean database makes reruns easier to understand.

I moved the reporting SQL into its own file instead of keeping the business logic in Python. The Python code still handles file loading and validation, while the SQL owns the customer, loan and payment model definitions.

The as-of date is stored in `raw.run_parameters`. This keeps the loan-age calculation reproducible and avoids quietly changing the output based on the day the command happens to run.

## Checks I ran

- Generated a ten-customer dataset.
- Loaded 10 customers, 10 loans, 7 subscriptions and 35 payments into DuckDB.
- Built 10 customer rows, 10 loan rows and 35 payment rows in the mart schema.
- Confirmed failed payments remain in `mart.fct_payment`.
- Reconciled completed payment totals between the raw payments, payment fact and loan summary.
- Ran the focused DuckDB test file: 2 tests passed.
- Compiled the new Python modules successfully.

## What I have not solved

This is still a full-refresh local database and not a production ingestion pattern. I have not added incremental loads, dbt or schema-version handling yet. Those gaps are useful next steps rather than things to hide behind a polished README.
