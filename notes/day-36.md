# Day 36 — make the local pipeline sequence explicit

Until today, `make pipeline` relied on Make target ordering. That was enough while
the workflow was small, but it did not leave one run result showing which stage
failed or which later stages were not attempted.

I added a small Python runner for the four existing operational stages: generate,
load, source freshness and dbt build. Each stage names its dependency, commands run
without a shell, and the runner stops after the first non-zero exit code. It writes
an ignored JSON report with the run ID, UTC timestamps, return codes and blocked
stages. The report is written through a temporary file so a partial write is not
mistaken for a completed run.

The runner deliberately does not add retries or scheduling yet. A retry policy
needs a distinction between transient and deterministic failures, and a backfill
needs an explicit reporting period. Automatically retrying a schema or data-test
failure would only repeat bad input and obscure the cause.

I also chose not to add Airflow. One local process is enough for this dependency
graph, and running a separate service would add installation and operational weight
without proving better control. The useful evidence today is failure propagation,
not the name of the scheduler.

## What I checked

- The runner topologically orders steps rather than trusting their declaration order.
- A failed load prevents downstream freshness and transformation stages from running.
- Missing dependencies and cycles are rejected before execution.
- The database path reaches both the loader and dbt environment.
- The existing `make verify` gate now enters the pipeline through this runner.

The first focused test command did not start because this fresh workspace did not
have the declared development dependencies installed. After the documented
installation command, all four new tests passed.

A later rerun against a reused disposable database hit the known DuckDB WAL replay
conflict during `load`. The run report recorded `generate` as successful, `load` as
failed and both downstream dbt stages as blocked. I kept that as real
failure-propagation evidence and ran the clean gate against a fresh database.

The full local shell also exposed that the GitHub workflow disabled dbt anonymous
usage statistics, while a direct `make verify` did not. The Makefile now exports
the same opt-out for every child process. No telemetry is needed for this project.

The next operational step should distinguish retryable command failures from
non-retryable contract and data-quality failures before adding any retry behaviour.
