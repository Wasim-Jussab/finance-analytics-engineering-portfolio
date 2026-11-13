# Day 78 — compare coverage without rounding away the difference

12 November 2026

I added current and prior coverage ratios and their percentage-point change
to the adjacent-month report. I calculate the change from the amount inputs,
not from the four-decimal display ratios. A zero denominator in either month
or a missing prior calendar month leaves the change null.

My isolated fixture includes zero due, missing months, and one-third versus
two-thirds coverage. The latter must change by 33.333333 percentage points,
not the 33.34 obtained by subtracting rounded display rates. These remain
descriptive positions across potentially changing cohorts, not causal
performance or an assertion about cash collections.

The full local gate passed: 630 dbt results, 123 Python tests, controlled
scenarios, Ruff, dbt docs and lock cleanup. A read-only query returned
24 rows with two null changes. December 2025 displayed 10.44% versus
10.96% for November, with an unrounded-input change of -0.523177
percentage points rather than the -0.52 from subtracting display values.
