# Day 57 — keep action events separate from financial exceptions

The queue showed which accounts an analyst might inspect, but it could not answer
whether any operational action had been recorded. I added 12 synthetic action
events across eight accounts and kept them at one row per event.

The reporting view starts from the complete exception queue and left joins action
summaries. That choice matters: an untouched account stays visible with a zero
count instead of disappearing through an inner join. The latest event uses its
timestamp and action ID as a deterministic tie-breaker.

I did not use action outcomes to change the financial band, shortfall or queue
rank. I also did not label a zero-action account as overdue, because the project
has no approved contact strategy or SLA. The events are entirely synthetic and
demonstrate grain, history and reconciliation rather than customer treatment.

## Validation

`make verify` passed with 9/9 source freshness checks, 514/514 dbt results,
483 data tests, all controlled history and incremental scenarios, 79 Python
tests, Ruff and dbt documentation. A read-only evidence query returned 25 queue
accounts: eight with 12 recorded actions and 17 with zero recorded actions.
