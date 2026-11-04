# Read-only pipeline lock provenance

```bash
python -m finance_portfolio.lock_status
```

The command reads `reports/pipeline.lock` and its named immutable run report in
`reports/runs/`. It never removes, rewrites or refreshes either file. Missing lock
returns `unlocked` and exit zero. Present locks return exit one, with either
`retained_completed_run` or `unresolved`. Matching completion requires run ID,
start marker, finished marker and a succeeded/failed status. This is a minimal
provenance comparison, not full evidence-pack verification or authentication.

`safe_to_remove` is always false. A completed report is written before the owning
context releases its lock. The process could still be unwinding; PIDs can also
be reused or refer to another namespace. Neither age, PID existence nor a completed
report is sufficient authorisation for automated cleanup. No liveness claim is made.

The original retained Day 68 lock was inspected without alteration. Its run ID
and start marker match a successful completed run report. That narrows the issue
to lock retention/cleanup timing but does not establish the cause. Ownership still
needs to be resolved through the normal runbook before deleting that lock.

Use [reader lifecycle diagnosis](reader-lifecycle.md) in a clean independent checkout
for reproduction, not by selecting a different lock around an active shared database.
