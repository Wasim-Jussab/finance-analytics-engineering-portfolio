# Day 11 — monthly subscription performance

**Date:** 4 September 2026

The billing fact from Day 10 is useful for transaction checks, but it is too detailed for a simple monthly performance view. I added an aggregate at one row per billing month, product and billing frequency.

The model reports attempt, completed and failed counts, plus attempted and collected amounts. It also calculates an attempt-based collection rate. I kept the denominator explicit because “collection rate” could otherwise mean value collected divided by value attempted. That is a different measure and should not be implied by the column name or documentation.

I changed `billing_month` in the fact from a `YYYY-MM` string to the first day of the month as a proper date. A display string looks convenient, but it is less useful for date filtering, ordering and joining to a future calendar model.

The aggregate has three controls beyond required fields and accepted values. One tests the compound grain, one checks that counts and amounts are internally possible, and one reconciles all counts and amounts back to the billing fact.

The clean output contains 54 month/product/frequency combinations from March 2024 to December 2025. Its 150 attempts, 125 completions, 25 failures, £4,680.00 attempted and £3,648.00 collected all reconcile to the fact table. All 6 models and 75 dbt tests passed, giving 81 successful dbt resources. All 12 Python tests and Ruff also passed.

I duplicated one temporary aggregate row to test the grain control. The test returned one duplicate group and a non-zero exit code. I rebuilt the aggregate afterwards and reran the clean suite.

This still is not a complete time-series mart. Months with no billing events are absent, and the small generated dataset makes some monthly rates volatile. A calendar spine and a clear decision about zero-activity periods would be needed before treating it as a polished trend model.
