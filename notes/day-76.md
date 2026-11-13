# Day 76 — answer portfolio coverage at month-end grain

10 November 2026

I wanted one answer to “what share of scheduled principal due was covered
across all products at this month end?” I rolled the tested product positions
up to one row per observed month end and divided the total assumed allocated
principal by total principal due. Averaging product percentages would give
small and large denominators the same weight. I kept coverage null when
nothing is due and left both inputs and the shortfall visible.

The reconciliation checks distinct accounts from the account-month snapshot,
ties the amounts to product rows and requires due to equal allocated plus
shortfall. These are point-in-time synthetic positions; summing them across
dates double-counts positions. This isn't contractual arrears or cash flow.

The full local gate passed: 621 dbt results, including 581 data tests,
121 Python tests, controlled scenarios, Ruff and dbt docs. A read-only
query returned 24 month ends, one with zero due and null coverage. At
31 December 2025 the 25 accounts had 57,712.01 due, 6,025.00 allocated
and 51,687.01 shortfall, giving 10.44% coverage.
