# Day 5 — introducing dbt

**Date:** 23 August 2026

Today I moved the mart layer into dbt rather than adding another separate reporting implementation.

The dbt project reads the raw DuckDB tables created on Day 4 and materialises the customer, loan and payment models into the `mart` schema. I also added source relationships, uniqueness/not-null tests and a singular reconciliation test for completed payments.

I added a small schema-name macro because dbt normally prefixes custom schemas with the target schema. For this local project I want the output to be visibly called `mart`, matching the architecture notes.

I have not described this as production dbt experience. It is a local implementation showing that I understand sources, models, refs, tests and materialisation. The next useful check is to run dbt against a freshly generated DuckDB database and inspect the compiled SQL and test results.
