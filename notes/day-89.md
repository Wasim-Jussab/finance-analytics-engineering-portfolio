# Day 89 — keep the crossing evidence visible

23 November 2026

I added the actual covered gross amount and share at the review threshold,
plus the preceding rank's share. Reaching 80% does not mean covering exactly
80%; rounding the result down would hide the overshoot. A null predecessor
means the first account qualifies, not an observed zero prior movement.

The fixture checks exact equality at 80%, overshoot to 100%, a predecessor
at 75%, a single-account direction and absent/unknown directions. The dbt
check ties the displayed evidence back to the ranked account report.
The threshold is still a descriptive review choice, not treatment policy.
The focused fixture and full `make verify` passed: 673 dbt results,
130 Python tests, freshness, history/incremental scenarios, degraded-path
checks, Ruff and documentation generation. Additional health/evidence
checks passed and the pipeline lock was removed.
A read-only December query showed the crossing six accounts cover 2,218.06,
or 80.54% when displayed to two decimals; the preceding five cover 70.95%.
The stored fractions remain unrounded rather than being set to 80%.
