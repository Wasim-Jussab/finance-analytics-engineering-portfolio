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

## Date dimension run — 5 September 2026

The calendar was generated from the configured start date to the fixed reporting date.

| Check | Result |
|---|---:|
| First / last date | 1 January 2024 / 31 December 2025 |
| Calendar rows | 731 |
| Month-end dates | 24 |
| Weekend dates | 208 |
| Subscription billing dates matched | 150 / 150 |
| dbt table models | 7 passed |
| dbt data tests | 93 passed |
| Total dbt resources | 100 passed |
| Python tests | 12 passed |
| Ruff | Passed |

For a controlled continuity failure, I removed 15 July 2024 from the temporary date dimension. `date_dimension_continuity` returned exactly one gap and dbt exited with code 1. Rebuilding the calendar restored all 731 dates and the complete suite passed.

## Subscription plan run — 6 September 2026

The hidden generator price lookup was exposed as a typed source and governed plan dimension.

| Check | Result |
|---|---:|
| Raw / mart subscription plans | 4 / 4 |
| Agreements with a valid plan | 20 / 20 |
| Billing attempts matching plan amount | 150 / 150 |
| Reconciled attempted amount | £4,680.00 |
| Reconciled collected amount | £3,648.00 |
| dbt table models | 8 passed |
| dbt data tests | 107 passed |
| Total dbt resources | 115 passed |
| Python tests | 14 passed |
| Ruff | Passed |
| dbt documentation generation | Passed |

For a controlled contract failure, I increased one temporary billing attempt by £0.01. `subscription_payment_matches_plan_amount` returned exactly one mismatch and dbt exited with code 1. Rebuilding the fact restored all 150 matching attempts and the complete suite passed.

The first documentation run hit a local DuckDB write-ahead-log replay conflict after the build. The database itself had passed all 115 resources. I rebuilt the disposable database, checkpointed it cleanly and generated the dbt catalogue successfully. `*.wal` is now explicitly excluded from Git so a local recovery file cannot be committed accidentally.

## Zero-activity monthly run — 7 September 2026

The monthly mart was rebuilt from agreement-calendar overlap before billing metrics were left joined.

| Check | Result |
|---|---:|
| Eligible monthly plan rows | 82 |
| Rows with billing attempts | 54 |
| Explicit zero-activity rows | 28 |
| Zero-activity rows on annual plans | 28 |
| Reconciled billing attempts | 150 |
| Reconciled completed / failed attempts | 125 / 25 |
| Reconciled attempted amount | £4,680.00 |
| Reconciled collected amount | £3,648.00 |
| dbt table models | 8 passed |
| dbt data tests | 109 passed |
| Total dbt resources | 117 passed |
| Python tests | 14 passed |
| Ruff | Passed |

For a controlled coverage failure, I deleted the temporary April 2024 row for the SUB-1 annual plan. That plan had an active agreement but no billing attempt in the month. `subscription_monthly_active_plan_coverage` returned exactly one missing row and dbt exited with code 1. Rebuilding the aggregate restored all 82 eligible rows and the complete suite passed.

## Agreement movement run — 8 September 2026

The agreement population was modelled separately from billing activity.

| Check | Result |
|---|---:|
| Monthly plan rows | 83 |
| Reporting range | March 2024 to December 2025 |
| Reconciled agreement starts | 20 |
| Reconciled cancellations | 6 |
| December closing agreements | 14 |
| dbt table models | 9 passed |
| dbt data tests | 125 passed |
| Total dbt resources | 134 passed |
| Python tests | 14 passed |
| Ruff | Passed |

For a controlled movement failure, I increased one temporary December closing count by one. `subscription_movement_metric_consistency` returned exactly one unbalanced row and dbt exited with code 1. Rebuilding the model restored the closing population of 14 and the complete suite passed.

## Source freshness run — 9 September 2026

The loader now records a single UTC ingestion timestamp across every raw table in a run. The pipeline checks that timestamp before building reporting models.

| Check | Result |
|---|---:|
| Raw sources checked | 7 |
| Fresh sources | 7 |
| dbt table models | 9 passed |
| dbt data tests | 125 passed |
| dbt model and data-test resources | 134 passed |
| DuckDB checkpoint hook | Passed |
| Python tests | 15 passed |
| Ruff | Passed |
| dbt documentation generation | Passed |

For a controlled freshness failure, I moved the temporary `raw.payments.loaded_at` value back by 25 hours. The selected source returned one `ERROR STALE` result and dbt exited with code 1. Reloading the raw tables restored the current batch timestamp and all seven source checks passed.

My first attempt to change the post-build database hit the DuckDB write-ahead-log replay conflict previously seen during documentation generation. That run did not reach the freshness query, so I did not count it as a successful failure test. I recreated the disposable database, moved the timestamp before transformation and obtained the expected single stale-source error. I also changed the DuckDB-only end-of-run hook to force a checkpoint. The clean build left no recovery file, and the following documentation command completed successfully.

## Atomic ingestion run — 10 September 2026

The full-refresh loader now assigns one batch identifier to all raw tables and validates a source-level audit manifest before committing.

| Check | Result |
|---|---:|
| Expected source audit rows | 7 / 7 |
| Distinct load identifiers | 1 |
| Audited source counts matching raw tables | 7 / 7 |
| Fresh raw sources | 8 / 8 |
| dbt table models | 9 passed |
| dbt data tests | 133 passed |
| dbt model and data-test resources | 142 passed |
| DuckDB checkpoint hook | Passed |
| Python tests | 16 passed |
| Ruff | Passed |
| dbt documentation generation | Passed |

For a controlled reconciliation failure, I increased the recorded payment row count by one without changing `raw.payments`. `reconcile_ingestion_audit` returned exactly one mismatch and dbt exited with code 1. I then recreated the database and reran the clean pipeline.

The rollback test starts with a valid five-customer batch, then attempts a seven-customer replacement after removing its required `payments.csv` file. The second load raises `FileNotFoundError`; the original batch identifier and five customer rows remain in the database. This proves that the replacement does not leave a mixture of old and new source tables.

My first attempt to modify the database after a complete dbt build again encountered the local DuckDB recovery-file conflict before the audit query ran. I excluded that attempt from the failure evidence and ran the controlled mismatch against a freshly loaded and checkpointed database. The issue remains a limitation of this local multi-process workflow despite the existing dbt end hook.

## Ingestion history run — 11 September 2026

Successful load and source metadata now persists separately from the current full-refresh manifest. All six CSV inputs receive a byte size and SHA-256 fingerprint.

| Check | Result |
|---|---:|
| Current source audit rows | 7 / 7 |
| Successful run history rows | 1 |
| Source history rows | 7 |
| CSV files with valid fingerprints | 6 / 6 |
| Fresh raw sources | 8 / 8 |
| Declared dbt sources | 10 |
| dbt table models | 9 passed |
| dbt data tests | 151 passed |
| dbt model and data-test resources | 160 passed |
| DuckDB checkpoint hook | Passed |
| Python tests | 17 passed |
| Ruff | Passed |

A two-run Python test produced two distinct batch IDs and fourteen source-history rows. Because the input files were unchanged, the customer source retained one distinct SHA-256 digest. The existing missing-file test also confirmed that a failed replacement did not add a second success record.

For a controlled history failure, I replaced the persisted payment digest with a different valid 64-character value while leaving the current manifest unchanged. `current_ingestion_matches_history` returned exactly one row and dbt exited with code 1. I then recreated the database and reran the clean pipeline.

## Failed-attempt history run — 12 September 2026

The loader now preserves a rejected attempt after rolling back the transaction that replaces the raw data.

| Check | Result |
|---|---:|
| Successful / failed run history rows | 1 / 1 |
| Accepted source-history rows | 7 |
| Failure-detail rows | 1 |
| Raw payment rows retained after failure | 99 |
| Fresh raw sources on clean run | 8 / 8 |
| Declared dbt sources | 11 |
| dbt table models | 9 passed |
| dbt data tests | 158 passed |
| dbt model and data-test resources | 167 passed |
| DuckDB checkpoint hook | Passed |
| Python tests | 18 passed |
| Ruff | Passed |

I removed `payments.csv` after a valid load and reran ingestion. The second command exited with code 1. The database retained the previous 99 payment rows and seven accepted source records, while the control history added one `Failed` run and one `FileNotFoundError` detail. The stored message was `Required source file not found: payments.csv`, without the local path. All three ingestion-history reconciliation tests passed against this mixed success/failure history.

For a controlled audit failure, I removed the temporary failure-detail row but left its `Failed` run header. `ingestion_failure_consistency` returned exactly one result and dbt exited with code 1. I then recreated the generated files and database before the final clean run.

An earlier attempt to run this scenario immediately after the full dbt build encountered the documented DuckDB write-ahead-log replay conflict before the loader reached the missing file. I did not count that as failure-history evidence. Repeating the scenario on a freshly loaded database isolated the loader behaviour and produced the expected result.

## Known gaps

- The freshness timestamp begins at the local DuckDB load; it cannot prove when an upstream system extracted or published the data.
- The history has no upstream extraction identifier and is stored in the same local database rather than an immutable control store.
- Failed attempts retain run-level error detail but no source-level history, retries or alerts.
- Empty raw sources are currently rejected; there is no source-specific policy for a legitimate zero-row extract.
- The dbt models currently rebuild as tables rather than incrementally.
- Subscription refunds, retries, plan changes and revenue-recognition rules are not yet represented.
- The subscription plan catalogue has no effective dates, so price history is not yet represented.
- Agreement history has no pause, reactivation or status-event records, so the movement model is limited to starts and cancellations.
- The calendar start date is a project variable rather than source-system metadata.
- The current dataset is intentionally small; scale and performance behaviour have not been tested.
