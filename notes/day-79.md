# Day 79 — separate the arithmetic effects behind coverage

13 November 2026

I added a two-part bridge for the coverage-rate change. First I change
allocation while holding the prior denominator fixed; then I change the
denominator while holding current allocation fixed. I named the sequence
in both fields because reversing the order changes the components.

The isolated fixture moves allocation from 40 to 100 while due rises from
100 to 300: the two effects are +60 and -66.666667 percentage points,
reconciling to -6.666667. I check their sum within rounding tolerance and
keep both null for zero or missing denominators. This explains the algebra
only. It doesn't say what caused the portfolio to change.

The full local gate passed: 630 dbt results, 123 Python tests, controlled
scenarios, Ruff, docs and lock cleanup. A read-only query showed December
2025's -0.523177 percentage-point change split into 0 allocation-first
and -0.523177 due-second effects under the documented sequence.
