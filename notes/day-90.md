# Day 90 — make the concentration review reproducible

24 November 2026

I added a short read-only review joining the concentration summary to
the exact account prefix behind it, and linked it from the root overview.
The new tied-account fixture uses 40, 40 and 20: account-ID order is stable,
rank two covers exactly 80%, and its predecessor covers 40%.

The review retains the synthetic principal-only limits, separate gross
direction denominators, null comparators and sparse direction behaviour.
This closes the ranked-movement/concentration scope of Days 86–90, not
a collections prioritisation or causal model.

My first validation command ran before dependency installation finished,
so Ruff was not yet available. I waited for setup before retrying.
Both focused fixtures and full `make verify` passed: 673 dbt results,
131 Python tests, freshness, history/incremental scenarios, degraded-path
checks, Ruff and docs. The documented read-only review and additional
health/evidence verifiers passed; the pipeline lock was removed.
