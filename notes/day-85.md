# Day 85 — reconcile directions before closing the milestone

19 November 2026

I added a separate account-filtered reconciliation for each sign bucket.
A partition check alone cannot catch swapped increasing and unchanged
counts: the total still agrees. The focused regression proves that a
four-account population with deliberately swapped buckets is rejected.
This is controlled test input, not an error found in the generated data.

I wrote a short read-only review with the December result and linked it
from the root overview, keeping the README below 500 words. It separates
observed membership from business events and position change from flows.
The account facts, contribution union, gross/net changes and direction
counts now form the completed Days 81–85 milestone.

Dependency setup encountered a proxy timeout; retrying completed setup.
Full `make verify` passed: 659 dbt results, 127 Python tests, freshness,
history/incremental scenarios, degraded-path checks, Ruff and docs.
