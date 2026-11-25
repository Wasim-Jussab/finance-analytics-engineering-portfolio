# Day 91 — offer a bounded read-only consumer

25 November 2026

I added a CLI over the reconciled ranked report so a reviewer can request
one snapshot, direction and row cap without editing SQL. Queries use bound
parameters and a read-only connection. The full gross direction denominator
stays visible even when only one or three accounts are returned.

Amounts are decimal strings and shares are unrounded fractions. An absent
direction has null population/amount fields rather than invented zeros;
unavailable snapshots or comparison months are refused. The consumer trusts
the dbt contract, so the setup explicitly requires verification first.

The first lint check caught a long limitation string and import ordering;
I corrected both before running the tests. All 10 focused cases passed,
including database-byte fingerprint stability, both directions, missing
comparators and invalid limits. This is deterministic reporting, not AI.
Full `make verify` passed: 673 dbt results, 141 Python tests, freshness,
history/incremental scenarios, degraded-path checks, Ruff and docs.
Additional health/evidence verifiers and lock cleanup passed. The real
CLI returned three of eleven December increasing accounts with 1,354.19
selected against the full 2,754.15 denominator. The absent decrease stayed
null, and limit zero exited 2 without JSON. These were executed checks,
not changes to the synthetic data.
