# Day 12 — adding a tested date dimension

**Date:** 5 September 2026

Day 11 exposed that the monthly model was deriving dates without a shared calendar. I added `dim_date` at one row per day from 1 January 2024 to the fixed reporting date of 31 December 2025.

The start date is a dbt variable and the end date comes from the existing run-parameters table. I did not use the machine date because the same synthetic input should produce the same reporting calendar whenever the project is rerun.

The date dimension includes an integer date key, calendar year and quarter, month attributes, month boundaries, month-end flag and weekend flag. Bounds, row-count and continuity tests sit alongside the standard key and accepted-value checks.

I changed the subscription billing fact to derive `billing_month` through a left join to `dim_date`. An inner join would make a missing calendar date disappear from the fact. The left join preserves the payment attempt, while the required-field and relationship tests make the calendar gap fail visibly.

The clean calendar contains 731 dates from 1 January 2024 to 31 December 2025, including the 2024 leap day, 24 month ends and 208 weekend dates. All 150 billing attempts matched a date. All 7 models and 93 dbt tests passed, giving 100 successful dbt resources. All 12 Python tests and Ruff also passed.

I removed 15 July 2024 from the temporary dimension to test continuity. The test returned one gap and a non-zero exit code. I rebuilt the calendar afterwards and reran the full clean suite.

The date dimension does not automatically solve zero-activity reporting. The monthly aggregate is still event-led. To create zero rows safely, I first need a defined set of valid product and billing-frequency combinations for each month rather than blindly cross joining every possible value.
