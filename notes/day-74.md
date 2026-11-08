# Day 74 — check the destination before handoff

8 November 2026

A source that checkpoints is only half the handoff. I added a read-only
catalogue probe of the destination before the helper gives its path to dbt
or a scenario. The probe closes before the caller gets the path, so it
doesn't hold a read connection while dbt tries to write.

In the regression I substituted an invalid destination for a successful
copy. The helper must raise before the consumer runs and clean up its own
temporary directory. The source remains readable. I kept the probe small:
it is a check that the destination opens, not a full scan, a reconciliation
of every table or a repair of the earlier replay failure.

The six focused copy tests and full local gate passed: 613 dbt results,
controlled scenarios, 120 Python tests, Ruff and dbt docs. I checked that
this run released its lock.
