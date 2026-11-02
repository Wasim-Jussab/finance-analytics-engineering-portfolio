# Day 66 — distinguish build success from reader availability

29 October 2026

I added a direct-reader readiness probe instead of continuing to describe the WAL
limitation only in prose. It opens the original database read-only, compares four
case-monitoring population counts and refuses to return partial results on error.
It does not create a missing database, remove a recovery file or fall back to a copy.

Tests cover healthy reads, count mismatches, missing files, incomplete schemas,
sanitised WAL failure and command-line exit codes. The WAL unit case is explicit
fault injection, not a claim that I reproduced or repaired the underlying bug.

The standard gate and downstream readiness are different decisions. Empty matching
counts establish readability, not completeness, business correctness or freshness.
The existing build gate is unchanged; the separate probe will report its actual
result against the generated default database before this increment is published.

## Local results

`make verify` passed: 613 dbt resources, 34 models, 574 data tests, 89 Python
tests, all controlled scenarios, Ruff and docs. All seven readiness tests passed
separately, including sanitised filesystem denial.

The real post-documentation probe exited zero: the original database opened
read-only, no WAL was present and all four population counts were 25. This is a
successful observation for this run, not evidence that I repaired or permanently
eliminated the previously observed WAL replay issue.
