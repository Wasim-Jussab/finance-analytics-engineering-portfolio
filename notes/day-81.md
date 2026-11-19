# Day 81 — expose the accounts behind portfolio coverage

15 November 2026

I extracted the account-month calculation from the product aggregate into
a reusable fact. A reviewer can now inspect which accounts make up due,
assumed allocation, shortfall, future principal and excess payments without
reimplementing the aggregate's private CTE.

The formulas and principal-only assumptions are unchanged. I added a
three-account fixture covering partial payment, payment above due and
principal not yet due. Grain and account-month population checks accompany
the amount identities. The existing product reconciliation remains
independent: it still reconstructs amounts from snapshots and schedules.

The full local gate passed: 642 dbt results, 124 Python tests, controlled
scenarios, Ruff, docs and lock cleanup. A read-only query found 355
account-month positions; December totals still reconcile to 57,712.01 due,
6,025.00 allocated and 51,687.01 shortfall.
