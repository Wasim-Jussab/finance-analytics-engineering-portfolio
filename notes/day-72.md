# Day 72 — check the recovery file before copying

6 November 2026

I separated two questions: did checkpoint complete, and is a nonempty recovery
file still visible once its connection closes? A yes to the first doesn't
justify ignoring a yes to the second. The scenario and docs helper now refuses
the file-only copy in that case and leaves both files in place.

I used a controlled test double to make checkpoint return successfully but
leave a WAL behind. This tests the decision boundary; it does not reproduce
or explain the earlier replay failure. The healthy copy test still checks the
catalogue name and table contents. I kept the quiescent-source assumption
explicit: this check can't rule out a writer changing files afterwards.

In a fresh temporary checkout, `make verify` passed: nine freshness checks,
613 dbt results, the controlled scenarios, 118 Python tests, Ruff and dbt
docs. I checked that this run's lock was absent after it finished.
