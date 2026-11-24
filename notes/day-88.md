# Day 88 — find the first rank covering a review share

22 November 2026

I added a month/direction summary showing the minimum ordinal account
count covering at least 80% of gross movement. This fixed 80% threshold
is a descriptive review choice, not a business treatment policy. Exact
equality qualifies; ties keep account-ID order. Missing directions stay
absent rather than looking like observed zero populations.

The fixture has an increase exactly at 80%, a decrease list needing both
accounts, another month and an unknown-only month. The dbt check verifies
the crossing rank and that its predecessor is below threshold, and
reconciles gross amounts and account counts to source contributions.
The focused fixture and full `make verify` passed: 671 dbt results,
130 Python tests, freshness, history/incremental scenarios, degraded-path
checks, Ruff and documentation generation.
A read-only December query showed 6 of 11 increasing accounts cover at
least 80% of gross increases of 2,754.15. The preceding-rank check proves
five do not cross that threshold. Additional evidence verifiers passed.
