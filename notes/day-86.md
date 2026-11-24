# Day 86 — rank changes without dropping the population

20 November 2026

I added an account-level ranked view over the reconciled contribution
report. Increases and decreases are separate monthly lists, ordered by
absolute amount descending and account ID ascending for deterministic
ties. All accounts remain present; zero and unknown changes have no rank.

The focused fixture covers tied increases, two decreases, zero and a
missing comparator. These are ordinal ranks, not peer-tied ranks or a
collections treatment recommendation. The dbt check independently counts
preceding contributions and verifies account grain and source changes.
I documented how to filter a direction to its first N accounts without
suggesting that those rows are the whole portfolio.

The focused fixture passed. The first full run flagged my new YAML's
generic-test argument syntax as deprecated. I nested the arguments to
match the existing project style and reran the full gate before publishing.
The corrected `make verify` passed: 665 dbt results, 128 Python tests,
freshness, history/incremental scenarios, degraded-path checks, Ruff and
documentation generation. The corrected run had no deprecation warning.
