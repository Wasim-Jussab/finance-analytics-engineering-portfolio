# Validation evidence

This page records checks that I have actually run. It is not a list of intended controls.

## Baseline run — 31 August 2026

The pipeline was rebuilt from the deterministic seed-42 dataset using a fresh DuckDB file.

| Check | Result |
|---|---:|
| Generated customers | 25 |
| Generated loans | 25 |
| Generated subscriptions | 20 |
| Generated payment attempts | 99 |
| dbt table models | 3 passed |
| dbt data tests | 31 passed |
| Total dbt resources | 34 passed |
| Python tests | 6 passed |
| Ruff | Passed |

The dbt tests cover keys, relationships, required fields, accepted values, payment chronology and completed-payment reconciliation.

## Controlled failure

A valid payment status was changed to `Unknown` in the temporary mart table. The accepted-values test then returned one offending row and a non-zero dbt exit code.

Expected result:

```text
accepted_values_fct_payment_payment_status__Completed__Failed ... FAIL 1
```

This matters because a suite that only passes on clean generated data does not prove that it can detect a bad value.

The invalid row and temporary DuckDB file are not committed.

## Subscription mart run — 1 September 2026

The same seed-42 pipeline was rebuilt after adding the subscription mart.

| Check | Result |
|---|---:|
| Raw subscription agreements | 20 |
| Mart subscription agreements | 20 |
| Active agreements | 14 |
| Cancelled agreements | 6 |
| dbt table models | 4 passed |
| dbt data tests | 46 passed |
| Total dbt resources | 50 passed |
| Python tests | 9 passed |
| Ruff | Passed |

The subscription-specific checks cover key grain, required fields, customer relationships, accepted values, start-date chronology and raw-to-mart row-count reconciliation.

For a controlled failure, one temporary mart start date was changed to 1 January 2026, after the fixed run date of 31 December 2025. `subscription_start_not_after_as_of_date` returned exactly one row and dbt exited with code 1. Rebuilding `dim_subscription` restored the clean data and all 15 subscription tests passed.

## Known gaps

- Source freshness is not enabled because the raw tables do not yet contain a genuine ingestion timestamp.
- The dbt models currently rebuild as tables rather than incrementally.
- Subscription billing events, cancellation dates and price data are not yet available, so revenue and active-tenure measures are deliberately excluded.
- The current dataset is intentionally small; scale and performance behaviour have not been tested.
