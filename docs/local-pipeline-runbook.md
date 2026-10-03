# Local pipeline runbook

## Run and inspect

Use `make pipeline` for generation, load, freshness and dbt build, or `make verify` for all eleven ordered stages. The full gate adds three history scenarios, incremental validation, lint, Python tests and documentation. Each stage streams output and stops the run on a non-zero return code.

Inspect `reports/latest-pipeline-run.json` for run ID, start/end timestamps, database, command, dependencies, stage durations and exit codes. Later stages after a failure are labelled blocked. Completed success and failure reports also remain under `reports/runs/<run-id>.json`; exclusive creation prevents accidental reuse of a run ID. Local reports are ignored by Git.

GitHub Actions uploads these JSON files after the quality gate using `always()`, retaining them for seven days. Open the workflow run's Artifacts section to download evidence. Missing reports produce a warning rather than masking the original error. An artifact is operational evidence, not proof that every possible business rule was checked.

## Failure and recovery

A non-zero quality stage must be investigated before using its outputs. Use its command and log to identify the first failed stage. Rerun the documented full gate after correction; the next run receives a new ID and retains the previous completed report.

An overlapping runner exits before executing a stage or replacing latest evidence. Do not remove a lock while its recorded owner is active. For an abandoned lock, verify the recorded process is no longer running and that no other invocation is operating on the same workspace before manually clearing it. The runner does not automatically steal or expire locks.

## Limits

The lock protects runner invocations in a shared local workspace. Individual manual commands do not acquire it. This is neither Airflow nor distributed orchestration: no scheduling service, retries, remote workers or backfills are demonstrated.

Abrupt termination can leave an unfinished run without a report or a stale lock. Archive failure prevents successful completion. Archives can be changed or deleted by someone with filesystem access; no tamper-proof audit claim is made. Local retention is manual, and CI retention expires. The fixed synthetic dataset is small; no throughput claim is made.

## Milestone evidence

Days 36–40 established ordered execution, fail-fast status, lock ownership, full-gate protection, completed-run history and downloadable CI reports. Controlled overlap, success/failure history and collision tests cover the runner. The broader gate exercises source freshness, dbt data checks, history, incremental corrections/absence/restoration and Python validation.


Day 40 local verification passed all eleven stages: 9 source freshness checks, 361 dbt results including 339 data tests, history/incremental scenarios, 36 Python tests, Ruff and documentation. Artifact upload is validated on the published GitHub run rather than simulated locally.
