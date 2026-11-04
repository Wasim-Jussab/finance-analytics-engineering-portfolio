# Day 69 — distinguish completed-run evidence from permission to delete a lock

1 November 2026

I inspected the retained Day 68 lock and found its exact run ID and start marker
in an immutable report marked succeeded. This is stronger evidence than guessing
from a timestamp or process number, but it still does not prove the owner is dead.
The run report is written before the context releases the lock.

I added a read-only status command with explicit unresolved/completed/unlocked
states and no cleanup operation. It rejects malformed metadata and mismatched
reports, sanitises diagnostics and never labels a lock safe to remove. The old
lock and original database remain untouched. This is diagnosis, not a WAL repair.

## Local validation and actual reproduction result

`make verify` passed in the Day 69 checkout: 613 dbt results, 574 data tests,
113 Python tests, all controlled scenarios, Ruff and docs. The real status CLI
classified both retained checkout locks as `retained_completed_run`, with matched
successful reports and `safe_to_remove: false`. They remain untouched.

I then ran the existing Day 68 lifecycle diagnostic with `--verify` in a separate
clean worktree at ee78aa3, with its own synthetic database and lock. It exited zero:
all 11 post-load stage observations reopened the original database, counted 25 raw
loans and found no WAL. There was no first-unreadable stage. This execution used
the existing diagnostic code, not a replacement lock around either retained database.
Its full gate passed 101 Python tests (the baseline before today's 12 status tests).

The fresh diagnostic unblocks reproduction testing, not cleanup of the old locks.
A lock was also retained after this run. Completed-run provenance is established;
retention cause and the historical intermittent WAL failure are not resolved. I
am not claiming a permanent reliability fix from one successful lifecycle.
