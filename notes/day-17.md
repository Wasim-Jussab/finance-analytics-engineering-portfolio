# Day 17 — making the raw load atomic and auditable

**Date:** 10 September 2026

Yesterday's timestamp could tell me that each source was recent, but it could not prove that the tables came from the same complete load. Two tables loaded at similar times are not necessarily one controlled batch.

I added one generated `load_id` across every raw table and a seven-row ingestion audit covering the six CSV files and the run parameters. The audit records the expected source, filename, loaded row count, status and UTC timestamp. Python compares the manifest with the physical table counts before commit, and dbt repeats the reconciliation independently.

The more important change is transactional. The loader now replaces the raw tables, builds the retained SQL comparison models and validates the audit inside one DuckDB transaction. I tested this by loading a valid five-customer batch, then attempting a seven-customer batch with `payments.csv` removed. The second attempt failed, and the original batch identifier and five rows remained. Without the transaction, the database could have contained a mixture of two runs.

The clean run produced seven audit records with one batch identifier. All eight source freshness checks passed, followed by 9 dbt models, 133 data tests, the checkpoint hook, 16 Python tests and Ruff. I changed the audited payment count by one as a controlled failure; the new dbt reconciliation returned exactly one row and exit code 1.

The first controlled-failure attempt did not reach the test because opening the database after a complete dbt build hit the existing DuckDB recovery-file conflict again. I rebuilt a disposable database, checkpointed it before the change and then obtained the intended audit failure. I have kept this in the validation record because the current end hook has reduced but not eliminated that local multi-process issue.

This is still a small full-refresh implementation. The audit table keeps only the current batch, rejects empty sources and cannot prove when an upstream system extracted a file. A production version would need persistent run history, upstream identifiers, checksums and a source-specific policy for valid empty extracts.
