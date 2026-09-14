# Day 20 — enforcing the CSV column contract

**Date:** 13 September 2026

The generator and loader had separate lists of the same CSV columns. They agreed because I had updated both carefully, but there was nothing preventing one list from changing without the other.

I moved the six source definitions into one Python module. The generator uses the names when it writes each file, and the loader uses the same names and DuckDB types when it creates the raw tables.

I also made the loader inspect every header before it starts replacing raw tables. Missing, unexpected or duplicate names now raise a `SourceContractError`. I chose to allow reordered columns because ingestion reads by name, so treating position as part of the contract would reject a change that does not affect the result.

The clean pipeline still passed 8 freshness checks, 9 dbt models, 158 data tests and the checkpoint hook. Ruff and all 20 Python tests passed. I then renamed `postcode` to `email` in a temporary customer file. The load failed, retained the previous 25-customer table and recorded the rejected attempt with the two conflicting column names. A separate test reversed the header order and loaded successfully.

This only makes the structural expectation executable. DuckDB still performs value conversion, and I have not yet added contract versions, nullability rules or a policy for deciding whether a new column is backward compatible.
