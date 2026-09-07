# Day 14 — making zero-activity months visible

**Date:** 7 September 2026

The monthly model previously started from billing events. That preserved the totals, but a month with active agreements and no attempt simply disappeared. A line chart could then jump across the gap without showing that the activity was actually zero.

I considered crossing every calendar month with all four plans. I did not use that approach because the plan table has no effective dates, so it would imply that every current plan existed throughout the full calendar. Instead, a plan month is eligible only when at least one related agreement overlaps it.

The mart now includes `active_agreement_count`. Billing metrics are left joined to the eligible population, and a month with no attempts receives zero counts, amounts and collection rate. "Zero" therefore has a defined meaning: there was at least one active agreement on the plan, but no billing attempt in that month.

The seed-42 output increased from 54 event-led rows to 82 eligible rows. The additional 28 rows are all annual-plan months with no billing event. The original 150 attempts, £4,680 attempted and £3,648 collected still reconcile exactly.

All 8 models and 109 dbt tests passed, giving 117 successful dbt resources. All 14 Python tests and Ruff also passed.

I deleted the temporary April 2024 SUB-1 annual row to test coverage. The control returned exactly one missing eligible plan month and a non-zero exit code. I rebuilt the aggregate afterwards.

The active agreement measure currently means active for at least one day in the month. A month-end population would answer a different question, so I have left that as a separate measure rather than labelling this one ambiguously.
