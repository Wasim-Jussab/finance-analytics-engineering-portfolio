# Day 35 — monthly loan portfolio reporting

The account position from Day 34 answered one point-in-time question. Today I
used the existing month-end snapshots and repayment schedule to create a reporting
mart that can show how the same measures change over time and by loan product.

## What I built

`agg_loan_portfolio_monthly` has one row per month end and product code. It reports
the number of originated accounts in that population, original balance, completed
payments, principal due, assumed allocation, shortfall and future principal. It
also counts accounts as `Not Yet Due`, `On Schedule` or `Behind Schedule` under
the project assumption.

The model contains 65 rows across 24 month ends and three products. Not every
product appears in every early month because a product is included only after its
first synthetic account has originated. At 31 December 2025 the three product
rows reconcile to 25 accounts, £57,712.01 due, £6,025.00 allocated and £51,687.01
shortfall. The portfolio-weighted due-principal coverage ratio is 0.1044.

That ratio is not the same as the 0.1644 average of the 25 account-level ratios
reported on Day 34. The monthly mart divides total allocation by total principal
due, so accounts with larger due balances have more weight. I kept the calculation
explicit rather than averaging ratios with different denominators.

## Checks added

- The month-end and product compound grain is unique.
- Every row resolves to the date dimension and an accepted product.
- Account position counts add back to the monthly product population.
- Due principal equals assumed allocation plus shortfall.
- Original balance equals due plus future principal.
- Completed payments equal allocated plus unallocated cash.
- The coverage ratio is recalculated from the monetary totals.
- An independent test rebuilds the account-month detail and reconciles every
  aggregate measure.

I changed one December product shortfall by £0.01 in an isolated database. The
monthly reconciliation returned exactly one failing row. The untouched database
then passed the complete project gate: 339 dbt data tests, 25 Python tests, every
controlled history and incremental scenario, Ruff and dbt documentation.

## What this does not prove

The historical population means accounts originated by each month end. I did not
use today's source status to invent a historical active-account population. The
schedule is principal-only and has no interest, fees, grace periods, reversals or
rescheduling, so the shortfall and position counts remain analytical project
measures rather than lender arrears, default or regulatory classifications.

This closes the first loan-reporting milestone. The useful lesson was that a
portfolio ratio needs a clearly stated denominator and cannot safely be inferred
by averaging account-level percentages.
