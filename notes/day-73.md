# Day 73 — prove a committed WAL row survives the copy

7 November 2026

I wanted a positive check to go with the tests that refuse an unsafe copy.
I committed an extra row in a disposable DuckDB child process and exited it
without a normal connection close. I checked for a nonempty WAL and compared
the main file's bytes with its pre-commit state so the test wouldn't quietly
pass on a row that had already been checkpointed.

The checkpoint-and-copy helper must produce a database that opens read-only
without a companion WAL and contains both rows. This tests a recoverable WAL,
not the earlier duplicate-schema replay failure. I used only test-owned files.

The five focused copy tests and the full local gate passed: 613 dbt results,
119 Python tests, controlled scenarios, Ruff and dbt docs. The run released
its lock.
