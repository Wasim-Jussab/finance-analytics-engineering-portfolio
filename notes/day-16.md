# Day 16 — checking source freshness from the load itself

**Date:** 9 September 2026

I had deliberately left freshness out since Day 7 because the raw tables had no ingestion timestamp. Using payment dates or the fixed reporting date would have made the check pass or fail for the wrong reason.

Today I changed the loader so every raw row receives the same UTC `loaded_at` value for that batch. The generated CSVs remain deterministic; only the pipeline metadata records when they were loaded. I then configured dbt to warn when a source is more than one hour old and error after 24 hours.

The normal run checked all seven sources before transformation and they passed. The dbt build passed all 9 models, 125 data tests and the end-of-run checkpoint hook. All 15 Python tests and Ruff passed, and the dbt documentation catalogue generated successfully.

I moved the temporary payments load timestamp back by 25 hours to check the error path. The selected freshness check returned one `ERROR STALE` result and exit code 1. Reloading the raw tables restored the current timestamp and all seven source checks passed again.

My first attempt did not reach that test because the previous dbt build had left a DuckDB recovery file that conflicted with the next connection. I recreated the disposable database rather than treating that unrelated error as freshness evidence. A normal checkpoint did not clear the file reliably, so I changed the DuckDB-only end-of-run hook to force the checkpoint. The clean build then left no recovery file and the following dbt documentation command succeeded.

This timestamp only describes the local ingestion step. It does not prove when an upstream system produced the data, and an empty source would need a separate batch-audit record. I have recorded both as limitations rather than treating one timestamp as full observability.
