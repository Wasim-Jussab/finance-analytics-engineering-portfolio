# Finance analytics engineering practice

I am using this repository to work through the parts of analytics engineering that I want more evidence of publicly.

In my current work I already use SQL, Power BI, Redshift, AWS Glue/Python, reporting models, regulatory reporting and reconciliations. I do not want to upload work data or pretend that a small GitHub project is the same as running a production platform. The plan is to build a small synthetic finance data system, make the decisions visible and keep notes on what I am learning.

## What I am trying to learn

The main gaps I want to practise are:

- Structuring a Python data project properly
- Building transformations in dbt
- Testing data rather than only checking the final report
- Making pipelines repeatable and safe to rerun
- Using GitHub Actions for basic CI
- Designing orchestration and cloud versions of a local pipeline
- Explaining the decisions clearly enough for another analyst or engineer to review

## What the project will cover

The examples will be based on problems I understand, but the data will be generated:

1. Subscription payments and revenue reporting
2. Regulatory-style submission rules and exclusion reasons
3. Loan portfolio snapshots and reconciliation
4. A small governed reporting layer for BI

The order may change when I find something that needs more work. I would rather record that than make the project look more finished than it is.

## Cost and data boundaries

This is a local-first project. I will not create AWS resources, use employer data, add personal identifiers, commit credentials or use paid APIs. The GitHub repository is public so the work can be reviewed, and generated data is excluded from the repository.

## Current state

Day 1 was mainly setup. Day 2 added a standard-library Python generator for customers, loans, subscriptions and payments. Day 3 added a first reporting layer from the raw CSVs. Day 4 added a local DuckDB boundary and moved the reporting SQL into a database-backed run.

Day 5 introduced dbt Core with the DuckDB adapter. The raw DuckDB tables are declared as dbt sources, and the customer, loan and payment models are now materialised into the `mart` schema.

On Day 6 I ran the dbt build against a freshly loaded database, fixed a database-path mismatch, and added descriptions for the sources and models. The local build completed with 3 models and 11 data tests passing. The full notes are in `notes/day-06.md`, and the run sequence is in `docs/dbt-workflow.md`.

The current reporting layer contains:

- `mart.dim_customer`: one row per customer
- `mart.dim_loan`: one row per loan, including completed-payment summaries
- `mart.fct_payment`: one row per payment, including failed payments

## Running it locally

```bash
python -m pip install -e ".[dev]"
make generate
make load
make dbt-debug
make dbt-build
make dbt-docs
```

The generated CSVs, DuckDB file and dbt `target/` directory are ignored by Git. They can be recreated from the commands above. `DBT_DATABASE` can be set when a different local database path is needed.

## Repository structure

~~~text
config/               Local dbt profile with no credentials
docs/                 Notes about the design, data and dbt workflow
notes/                Short learning notes by day
data/                 Local generated data, excluded where appropriate
models/               dbt sources and reporting models
macros/               Small dbt configuration macro
sql/duckdb/            Earlier SQL models run against the local database
src/finance_portfolio/ Reusable Python code
tests/                 Automated checks and dbt singular tests
pyproject.toml         Python project and tooling configuration
Makefile               Short repeatable commands
~~~

## Rough sequence

- Generate deterministic synthetic customers, loans, subscriptions and payments.
- Inspect the output before writing reporting logic.
- Load typed raw tables into a local analytical database.
- Add dbt models and tests once the database boundary is understood.
- Add reconciliation and failure cases rather than only successful examples.
- Add CI and an orchestration design after the local process works.
- Finish with a reporting layer and a review of what I would change in a real system.

This is a learning project and a public record of the work. It is not a claim that every tool listed here has already been used in production.
