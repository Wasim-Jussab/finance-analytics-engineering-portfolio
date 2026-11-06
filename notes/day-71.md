# Day 71 — stop trusting a database copy whose recovery state is unknown

3–5 November 2026

I found that the isolated-copy helper caught the known WAL replay error and then
copied only the database file. A readable copy does not prove that unreplayed
source changes were included. I removed that fallback: checkpoint/recovery failure
must stop scenarios and documentation, while preserving the database and WAL.

The regression injects the real error class and verifies no copy begins and no
source bytes change. A separate healthy path checks catalogue identity and data.
My first healthy fixture used an invalid SQL alias; I corrected its table setup
without changing the policy to make it pass. This is stricter fail-closed behaviour,
not a claim that the underlying WAL failure has been repaired.

## Validation and resumed investigation

On 3 November all 117 Python tests passed, but the full stricter gate failed
after 613 passing dbt results when the first scenario reopened the original WAL.
Removing the forced-checkpoint hook did not resolve that boundary. The original
and candidate databases and recovery files remain preserved.

On 4 November I inspected installed dbt-duckdb 1.11.1 source. Its local environment
uses `credentials.keep_open` (default true), and closes its connection after the
last handle when false. This motivated an isolated `keep_open: false` experiment,
not a claim of root cause. The full run instead produced missing seed/snapshot
table errors: 259 passing dbt results, 67 errors and 287 skipped. That configuration
was reverted; its failed database was preserved. I have not substituted this
different failure for the original WAL issue.

After reverting the profile experiment, all 117 Python tests passed again and
Ruff passed. I left Day 71 unpublished at that point because the full stricter
gate had not passed. I did not change main or touch earlier failed databases/WALs.

On 5 November I ran the strict gate from a fresh worktree with DuckDB 1.5.5
instead of 1.5.6, keeping dbt-core 1.12.6 and dbt-duckdb 1.11.1. Freshness,
all 613 build results and the plan-history scenario passed. The agreement-history
scenario then hit the same duplicate `history` schema during replay when opening
the source database. A patch rollback is not a demonstrated fix: the failure
moved one step later. I left this database and WAL in place and did not pin
the older version or publish the change.
I ran the checks the gate skipped separately: Ruff and 117 Python tests passed.

A separate run of the unchanged finance gate completed, but a later local
shell saw the completed run's lock with its original modification time and a
newer file birth time. The failed 1.5.5 run's WAL also had a file birth time
later than its last recorded write. Those are clues about file visibility, not
proof of the replay error's cause. I tested the strict change again in a fresh
temporary checkout with 1.5.6, leaving the retained locks and WALs untouched.

That fresh checkout passed all of `make verify`: nine freshness checks, 613 dbt
build results (574 data tests), all controlled scenarios, 117 Python tests, Ruff
and dbt docs. The same shell confirmed that the run's own lock was absent. That
run's pipeline health and seven-artifact evidence bundle also verified. This
is enough to review the fail-closed policy on a draft branch, but not to claim
that WAL replay is fixed in every workspace. I made no dependency pin, retry,
or recovery-file cleanup part of the change.
