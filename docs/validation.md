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

## Known gaps

- Source freshness is not enabled because the raw tables do not yet contain a genuine ingestion timestamp.
- The dbt models currently rebuild as tables rather than incrementally.
- Subscription data is generated and loaded but is not yet represented in the mart layer.
- The current dataset is intentionally small; scale and performance behaviour have not been tested.
