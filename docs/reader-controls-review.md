# Days 66–70: build success and consumer readiness are separate decisions

Day 71 strengthens the [checkpoint/copy policy](checkpoint-copy-policy.md): an
unreadable original recovery state may no longer be bypassed with a file-only copy.

The milestone adds three deliberately different controls:

| Control | Establishes | Does not establish |
|---|---|---|
| Account/date probe | Original file opens, report grain and populations agree | Freshness or correct business rules |
| Lifecycle diagnostic | Raw loans can be read after specific pipeline stages | Case-mart reconciliation or failure causality |
| Lock status | Lock metadata matches completed-run evidence, or remains unresolved | Process death or permission to remove a lock |

## Run locally

After the documented installation, from the repository root:

```bash
make verify
python -m finance_portfolio.reader_readiness
python -m finance_portfolio.lock_status
```

In a separate clean checkout with its own database, run:

```bash
python -m finance_portfolio.reader_lifecycle --verify
```

Do not replace or remove an existing shared lock to make that command succeed.
The [lock status contract](lock-status.md), [lifecycle runbook](reader-lifecycle.md)
and [account/date probe](reader-readiness.md) document their exit codes and limits.

## Executable boundary regressions

The integration tests demonstrate that raw-data readability can pass while two
case reports have equal counts but different account membership. They also show
that a completed run report cannot bypass the actual pipeline lock. Healthy
controls preserve source bytes; blocked execution preserves the lock and creates
no new run report. These are controlled cases, not manufactured operational incidents.

## Actual observations and unresolved issues

Day 67's original-reader check hit the historical WAL replay error. Day 68's live
diagnostic was blocked by a retained lock. Day 69 executed the full lifecycle in
an independent clean checkout: all 11 reads reopened the original file, counted
25 loans and found no WAL. This did not reproduce or repair the earlier failure.

Retained local locks match completed successful run reports. The cause of retention
and the intermittent WAL issue remain unresolved. A matching report is written
before lock release and cannot prove the owning process is dead. No automated
cleanup or recovery-file deletion is included. Passing CI is evidence of tested
controls, not a guarantee of uninterrupted consumer availability.

Day 70's full standard gate passed (613 dbt results and 116 Python tests), but
the subsequent original-file readiness probe again reported `wal_replay_error`:
WAL present, reader not opened, no partial counts. That consumer-readiness check
did not pass. The source, recovery file and retained lock were preserved. This
milestone delivers diagnostic controls; it does not resolve the reliability defect.
