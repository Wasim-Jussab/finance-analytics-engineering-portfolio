# Day 92 — refuse inconsistent reader populations

26 November 2026

The bounded reader trusted the concentration summary. I added a targeted
preflight against the full ranked direction: summary grain, count and gross
amount must agree, account IDs must be unique, ranks contiguous/distinct,
and signs must match direction. A one-row cap must not hide a broken full
population. All reads now share one read-only transaction.

The mutations alter fresh controlled fixture databases, not the generated
portfolio: count, amount, missing/duplicate summaries, invalid ranks and
duplicate accounts. Refusal must leave the database fingerprint unchanged.
These checks complement dbt rather than proving source authenticity or
replacing every upstream contract. All 16 focused cases and full `make
verify` passed: 673 dbt results, 147 Python tests, freshness, scenarios,
degraded-path checks, Ruff and docs. Additional health/evidence verifiers
and lock cleanup passed. The executed CLI still returned three of eleven
December increasing accounts, 1,354.19 against full gross 2,754.15.
