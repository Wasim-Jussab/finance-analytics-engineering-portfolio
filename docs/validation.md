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

## Subscription billing run — 3 September 2026

The seed-42 pipeline was rebuilt after adding cancellation dates and subscription billing attempts. The existing published row counts remained stable.

| Check | Result |
|---|---:|
| Raw subscription agreements | 20 |
| Active / cancelled agreements | 14 / 6 |
| Raw subscription billing attempts | 150 |
| Completed / failed attempts | 125 / 25 |
| Completed synthetic collections | £3,648.00 |
| dbt table models | 5 passed |
| dbt data tests | 61 passed |
| Total dbt resources | 66 passed |
| Python tests | 12 passed |
| Ruff | Passed |

The first generator run exposed a regression: inserting new random choices in the subscription function changed the established seed-42 outputs from 20 to 16 agreements and from 99 to 98 loan-payment attempts. I restored the original random-draw order and gave billing status generation a separate seeded random stream. A unit test now protects the published row-count baseline.

For a controlled failure, one temporary fact amount was changed from a positive value to `-1.00`. `subscription_payment_amount_positive` returned exactly one row and dbt exited with code 1. Rebuilding the fact restored the clean data and all 61 tests passed again.

## Monthly subscription run — 4 September 2026

The subscription billing fact was aggregated by billing month, product and billing frequency.

| Check | Result |
|---|---:|
| Aggregate rows | 54 |
| Billing range | March 2024 to December 2025 |
| Reconciled billing attempts | 150 |
| Reconciled completed / failed attempts | 125 / 25 |
| Reconciled attempted amount | £4,680.00 |
| Reconciled collected amount | £3,648.00 |
| dbt table models | 6 passed |
| dbt data tests | 75 passed |
| Total dbt resources | 81 passed |
| Python tests | 12 passed |
| Ruff | Passed |

For a controlled grain failure, I duplicated one temporary aggregate row for March 2024, SUB-1 and annual billing. `subscription_monthly_unique_grain` returned exactly one duplicate group and dbt exited with code 1. Rebuilding the aggregate restored 54 rows and the complete suite passed.

## Known gaps

- Source freshness is not enabled because the raw tables do not yet contain a genuine ingestion timestamp.
- The dbt models currently rebuild as tables rather than incrementally.
- Subscription refunds, retries, plan changes and revenue-recognition rules are not yet represented.
- The monthly aggregate has no date spine, so months without billing events do not appear as zero rows.
- The current dataset is intentionally small; scale and performance behaviour have not been tested.
