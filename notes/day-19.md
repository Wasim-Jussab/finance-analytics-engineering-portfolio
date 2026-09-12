# Day 19 — retaining failed ingestion attempts

**Date:** 12 September 2026

Day 18 kept history for successful batches, but a rejected load disappeared after rollback. That protected the data correctly, yet it left no record that the attempt happened.

I added a separate failure-history table and allowed `ingestion_runs` to hold both `Success` and `Failed` statuses. The main load transaction still owns the raw-table replacement. If anything fails, that transaction is rolled back first; only then does a second, small control transaction write the failed run and its error detail. This keeps the previous valid batch current without losing the operational event.

I chose not to create source-history rows for a failed run. Those rows mean a source was accepted as part of a complete batch, which is not true when a required file is missing. Failed runs therefore have zero accepted sources and one related failure-detail row.

The stored message is deliberately limited. A missing-file failure records the exception type and filename, but not the local filesystem path. This is a small example of keeping an audit useful without copying unnecessary environment detail into it.

The clean run passed 8 freshness checks, 9 dbt models, 158 data tests, the checkpoint hook, 18 Python tests and Ruff. I then removed `payments.csv` after a valid load. The command failed, the previous 99 raw payment rows remained available, and the audit showed one successful and one failed attempt. Removing the failure detail produced exactly one result from `ingestion_failure_consistency` and a non-zero dbt exit code.

Running the missing-file scenario immediately after a full dbt build first exposed the existing DuckDB recovery-file conflict. That failure occurred before my new logic, so I did not use it as evidence. I recreated the disposable database and repeated the test against the ingestion step on its own.

The remaining limitation is that this is still one local database. A production failure log should survive loss of the analytical store and would normally include severity, retries, ownership and alert routing.
