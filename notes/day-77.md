# Day 77 — compare adjacent month-end positions

11 November 2026

I added differences in account count, principal due, assumed allocation and
shortfall from the prior calendar month end. I used an explicit date join:
if the previous calendar month is missing, a previous observed row is not
silently substituted. Missing comparators return null changes, not zeros.

The report keeps the current amounts and comparator date alongside the
differences. Due change must equal allocation change plus shortfall change.
These are position comparisons across potentially changing account cohorts;
they are not cash receipts, delinquency migrations or causal explanations.

I also ran the model SQL against an isolated fixture with January, February
and April positions. It must compare February to January but not April to
February. This tests the gap rule separately from the complete monthly
synthetic dataset, substituting only the dbt reference for the fixture table.

The full local gate passed: 630 dbt results (589 data tests), 122 Python
tests, controlled scenarios, Ruff and docs, with lock cleanup confirmed.
The report has 24 rows and one missing comparator at the start. December
2025 has 2,754.15 more due and shortfall than November, with no change
in assumed allocation or account count. I have not labelled that change
as a collections flow.
