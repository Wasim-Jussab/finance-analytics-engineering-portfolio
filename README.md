# Finance Analytics Engineering Portfolio

[![quality-checks](https://github.com/Wasim-Jussab/finance-analytics-engineering-portfolio/actions/workflows/quality-checks.yml/badge.svg)](https://github.com/Wasim-Jussab/finance-analytics-engineering-portfolio/actions/workflows/quality-checks.yml)

A local finance data pipeline built with Python, DuckDB and dbt Core. It generates synthetic customer, loan, subscription and payment data, loads typed raw tables, builds reporting models and checks the outputs through data tests and reconciliation controls.

I am building this project to make my move from data analysis into analytics engineering visible without publishing employer data. The business problems are familiar to me; the dbt structure, automated testing and engineering workflow are the areas I am practising publicly.

## Current pipeline

```mermaid
flowchart LR
    A["Synthetic finance data"] --> B["Python generation and validation"]
    B --> C[("DuckDB raw tables")]
    C --> D["dbt transformations"]
    D --> E[("Reporting marts")]
    E --> F["dbt tests and reconciliation"]
    F --> G["GitHub Actions"]
```

Everything runs locally with no cloud account, credentials or paid service.

## What is implemented

| Area | Current implementation |
|---|---|
| Data generation | Deterministic customers, loans, subscriptions, loan payments and subscription billing attempts using a fixed seed |
| Ingestion | Python loader creates typed DuckDB tables in the `raw` schema |
| Transformation | dbt materialises customer, loan, subscription, transaction and monthly aggregate models in the `mart` schema |
| Data quality | Key, relationship, required-field, accepted-value and chronology tests |
| Financial control | Completed loan payments reconcile across raw, fact and account-summary levels; completed subscription collections reconcile from raw to fact |
| Documentation | dbt source/model descriptions, architecture notes, data contract and daily decision log |
| Automation | GitHub Actions reruns the local pipeline, Python tests and linting |

## Reporting models

| Model | Grain | Important logic |
|---|---|---|
| `mart.dim_customer` | One row per customer | Combines customer attributes into a reporting dimension |
| `mart.dim_date` | One row per calendar date | Provides tested calendar, month, quarter and weekend attributes |
| `mart.dim_loan` | One row per loan account | Adds completed-payment count, value and latest completed-payment date |
| `mart.dim_subscription` | One row per subscription agreement | Adds cancellation date, current status and completed active months |
| `mart.fct_payment` | One row per payment attempt | Retains successful and failed attempts and derives a success flag |
| `mart.fct_subscription_payment` | One row per subscription billing attempt | Retains completed and failed attempts and derives a collected flag |
| `mart.agg_subscription_monthly` | One row per month, product and billing frequency | Summarises attempts, failures, collections and attempt-based collection rate |

Failed payments are deliberately retained. Filtering them out during transformation would make the reporting totals look cleaner while removing useful operational evidence.

## Validation evidence

The current seed-42 run produced:

| Check | Result |
|---|---:|
| Customers | 25 |
| Loans | 25 |
| Subscriptions | 20 |
| Loan payment attempts | 99 |
| Subscription billing attempts | 150 |
| Completed subscription collections | 125 / £3,648.00 |
| Monthly aggregate rows | 54 |
| Calendar dates | 731 |
| dbt models | 7 passed |
| dbt data tests | 93 passed |
| Total dbt resources | 100 passed |
| Python tests | 12 passed |
| Ruff | Passed |

Controlled failure checks have detected an invalid loan-payment status, a subscription start date after the reporting date, a non-positive subscription payment amount, a duplicate monthly grain and a missing calendar day. Each targeted test returned exactly one offending result and a non-zero exit code before the clean model was rebuilt.

The full evidence and remaining limitations are recorded in [docs/validation.md](docs/validation.md).

## Run locally

Requirements: Python 3.11 or later.

```bash
git clone https://github.com/Wasim-Jussab/finance-analytics-engineering-portfolio.git
cd finance-analytics-engineering-portfolio
python -m pip install -e ".[dev]"
make pipeline
make check
```

Useful individual commands:

```bash
make generate
make load
make dbt-debug
make dbt-build
make dbt-docs
```

Generated CSVs, DuckDB files, dbt output and logs are excluded from Git.

## Design decisions

- **Synthetic data only:** no employer records, customer identifiers or confidential business rules are used.
- **Explicit grain:** customer, loan and payment models have documented keys and relationship tests.
- **Fixed reporting date:** loan age uses a supplied as-of date rather than the machine clock.
- **Decimal money types:** monetary fields are loaded as controlled decimal values.
- **Raw and mart separation:** source data is kept separate from reporting transformations.
- **Reconciliation before presentation:** completed-payment values are compared at raw, fact and account-summary level.
- **Separate agreement and event grains:** subscription attributes remain in the dimension while billing attempts have their own fact table.
- **Explicit synthetic pricing:** billing amounts come from a small, documented lookup created for this project; they do not represent an employer's pricing.
- **Collections are not revenue:** a completed synthetic billing attempt supports a cash-collected measure, but revenue recognition remains out of scope.
- **Aggregate grain is explicit:** monthly performance is grouped by billing month, product and billing frequency, with a compound-grain test.
- **Collection rate is attempt-based:** completed attempts are divided by all attempts; this is not an amount-weighted recovery rate.
- **Calendar range is controlled:** the date dimension starts from a dbt variable and ends at the fixed reporting date, with bounds and continuity tests.
- **No false freshness claim:** source freshness is deferred because the raw tables do not yet contain a genuine ingestion timestamp.

## Known gaps

This is a working project, not a finished platform.

- The models currently rebuild as tables rather than incrementally.
- Subscription refunds, retries, plan changes and revenue-recognition rules are not modelled.
- The monthly aggregate is not yet zero-filled from the date dimension, so months without billing events remain absent.
- The calendar start date is configuration rather than source-system metadata.
- Source freshness needs real ingestion metadata.
- The dataset is intentionally small and has not been performance-tested.
- The cloud architecture is documented as a possible production mapping, not presented as a deployed AWS system.

## Repository map

```text
config/                 Local dbt profile with no credentials
docs/                   Architecture, data contract, workflow and validation evidence
models/                 dbt sources and reporting models
notes/                  Daily learning and decision log
src/finance_portfolio/  Python generation and loading code
sql/duckdb/             Earlier SQL implementation retained for comparison
tests/                   Python and dbt data tests
.github/workflows/       Automated quality checks
```

## Project notes

The daily notes record what changed, what failed and what remains unresolved. They are intentionally more candid than the main README.

- [Day 1: foundation and initial data contract](notes/day-01.md)
- [Day 2: deterministic synthetic data](notes/day-02.md)
- [Day 3: first reporting layer](notes/day-03.md)
- [Day 4: DuckDB ingestion and SQL marts](notes/day-04.md)
- [Day 5: first dbt models](notes/day-05.md)
- [Day 6: end-to-end dbt run](notes/day-06.md)
- [Day 7: stronger data-quality checks](notes/day-07.md)
- [Day 8: public milestone review](notes/day-08.md)
- [Day 9: subscription modelling without invented revenue](notes/day-09.md)
- [Day 10: subscription billing events and controls](notes/day-10.md)
- [Day 11: monthly subscription performance](notes/day-11.md)
- [Day 12: tested date dimension](notes/day-12.md)

This repository demonstrates how I structure and validate analytics-engineering work. My production experience with Redshift, AWS Glue/Python, Power BI, regulatory reporting and financial reconciliations is described separately in my professional profile.
