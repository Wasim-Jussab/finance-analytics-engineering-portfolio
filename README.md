# Finance Analytics Engineering Portfolio

[![quality-checks](https://github.com/Wasim-Jussab/finance-analytics-engineering-portfolio/actions/workflows/quality-checks.yml/badge.svg?branch=main)](https://github.com/Wasim-Jussab/finance-analytics-engineering-portfolio/actions/workflows/quality-checks.yml)

A reproducible finance reporting pipeline using **Python, DuckDB and dbt Core**, with synthetic data and automated reconciliation.

I work with financial reporting, SQL and data quality. This project brings those problems into a local warehouse: tracking subscription collections and agreement movements, then explaining loan payments against an explicit principal schedule.

Second project: [Operations Intelligence](projects/operations-assistant/README.md), combining governed read-only metrics with a narrow local intent model. It is not a generative assistant or LLM.

## Questions the models answer

- How many billing attempts completed, and how much was collected each month?
- How do agreement starts and cancellations explain the closing population?
- How do completed loan payments compare with scheduled principal?
- What changed between loads, and can the current reporting totals reconcile to source?

## Engineering behind the reports

Python generates fixed-seed CSVs, validates their column contracts and loads typed DuckDB tables in one transaction. dbt builds dimensions, facts and monthly reporting marts; GitHub Actions runs the same `make verify` gate used locally.

The implementation includes:

- Successful and failed ingestion history, batch IDs and file fingerprints.
- SCD Type 2 snapshots, distinguishing observed status changes from source disappearance.
- Keyed incremental payment merges handling late arrivals, corrections, absence and restoration.
- Grain, relationship, chronology, freshness and financial reconciliation checks.
- Isolated scenarios that exercise failure handling and changes across consecutive runs.
- A fail-fast local runner with locking and independently verified [health decisions](docs/pipeline-health.md).

## Example output

The fixed seed produces 25 loan accounts and 20 subscription agreements. At the reporting date of **31 December 2025**:

| Reporting output | Reconciled result |
|---|---:|
| Completed subscription collections | £3,648 from 150 billing attempts |
| Closing subscription agreements | 14 |
| Loan month-end snapshots | 355 account-month rows |
| Completed loan payments | £6,025 |

The [validation record](docs/validation.md) contains the full results and controlled scenarios.

## Run locally

Requires Python 3.11+, Git and Make. The commands below use a POSIX shell; on Windows, use WSL.

```bash
git clone https://github.com/Wasim-Jussab/finance-analytics-engineering-portfolio.git
cd finance-analytics-engineering-portfolio
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make verify
```

Verification generates the data, loads the database, checks source freshness, builds and tests dbt resources, exercises historical and incremental scenarios, runs Python checks and generates dbt documentation. No cloud account or paid service is needed.

## Assumptions and limits

Collections are cash received, not recognised revenue. Loan schedules are synthetic and principal-only; oldest-due-first allocation is an explicit assumption, not contractual arrears evidence. The dataset is deliberately small, and the full-source incremental merge does not demonstrate a performance improvement at scale.

## Read further

- [Operations project](projects/operations-assistant/README.md)
- [Local pipeline runbook](docs/local-pipeline-runbook.md)
- [Pipeline health summary](docs/pipeline-health.md)
- [Implementation guide and model catalogue](docs/implementation-guide.md)
- [Architecture](docs/architecture.md) · [Data contract](docs/data-contract.md) · [dbt workflow](docs/dbt-workflow.md)
- [Loan reporting review](docs/loan-reporting-review.md) · [Thirty-day technical review](docs/30-day-review.md)
- [Learning notes](notes/) · [Working plan](docs/roadmap.md)
