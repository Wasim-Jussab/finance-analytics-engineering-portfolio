# Day 75 — keep failed scenario writes out of the source

9 November 2026

I closed this milestone by testing what happens after a successful handoff.
I committed an extra row in a disposable copy and deliberately raised a
scenario exception. The test checks that the exception still reaches the
caller, the temporary directory disappears and the source still has its
original row and post-checkpoint bytes.

I measured bytes after checkpoint because checkpoint can legitimately change
the source file. This covers Python exception unwinding, not abrupt process
termination. Across the five sessions I checked failed recovery, a retained
WAL, real committed-row replay, destination readability and write isolation.
None of these establishes the cause of the earlier duplicate-schema WAL failure.

The seven focused copy tests and the full local gate passed: 613 dbt results,
121 Python tests, controlled scenarios, Ruff and dbt docs. The run released
its lock.
