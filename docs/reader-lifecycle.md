# Original-reader lifecycle diagnosis

Run from the repository root:

```bash
python -m finance_portfolio.reader_lifecycle --verify
```

This executes the real pipeline under its existing single-writer lock, using the
same stages as `make verify`. After the load stage and each subsequently executed
stage, it opens the original database read-only and counts `raw.loans`. The JSON
report at `reports/reader-lifecycle.json` names the first failed reader observation,
the pipeline run ID, stage return codes, WAL presence and sanitised error classes.
Exit zero requires both pipeline success and successful reader observations.

A later successful observation does not erase an earlier failure. Failed pipeline
stages remain failures and later stages remain blocked. The normal `make verify`
contract is unchanged; this is an opt-in diagnostic invocation, not a new claim
that build success guarantees consumer availability.

It does not delete WAL files, repair a source or substitute a copy. Source absence
before loading is not probed. Reading raw loans is not case-mart readiness; use
the [reader probe](reader-readiness.md) for account/date reconciliation. Association
with a stage is not proof that the stage caused the problem. Observational reads
may change timing, so a successful diagnostic run is not proof of permanent repair.

An existing pipeline lock prevents execution (exit 2) without changing the lock
or writing a new diagnostic report. Resolve ownership through the normal pipeline
runbook; do not remove a lock merely to obtain a successful diagnostic result.
