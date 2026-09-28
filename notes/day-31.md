# Day 31 — first month-end loan snapshot

Today I moved from subscription reporting to the loan side of the dataset. The aim
was to create a useful month-end grain before adding more financial measures.

## What I built

I added `fct_loan_monthly_snapshot` at one row per account and month end. It starts
in the loan's origination month and continues to the fixed reporting date, including
months where no completed payment occurred.

Each row keeps the month's completed-payment count and amount, the cumulative
values to date, and a calculated remaining balance. The seed-42 build produced 355
rows for 25 loans and reconciled £6,025.00 of completed payments.

## A boundary I kept

The obvious next columns were arrears and days past due, but the current source has
no contractual schedule, instalment amount or due date. Creating those measures now
would make the output look more complete while hiding an invented assumption.

I have therefore called the balance `calculated_remaining_balance`. It is only
original balance less completed payments, floored at zero. It does not include
interest, fees, adjustments or principal allocation and is not a lender statement
balance.

## Checks added

- Every eligible account and month-end appears once.
- Monthly payment movement rolls into the cumulative totals.
- The calculation cannot produce a negative remaining balance.
- Payments above original balance remain visible in a separate field.
- Each account's final snapshot reconciles to `dim_loan`.

## What happened while validating it

The fresh executor did not have the repository dependencies installed, so the first
command stopped before project logic ran. After installing the declared development
dependencies, the build passed 277 of 277 dbt results. Reading the completed file in
a new process also reproduced the known DuckDB recovery-file conflict. The first
full gate then stopped at the same point before the history scenarios ran.

I added a constrained fallback for scenario copies. It applies only when DuckDB
reports the known duplicate-schema WAL replay error and the recovery file exists.
It copies the already checkpointed database, keeps the recovery file for diagnosis
and allows every unrelated catalogue error to fail normally. The final full gate
passed, including 22 Python tests and all controlled scenarios.

## Next step

The next loan increment should add an explicit synthetic repayment schedule. That
will provide the evidence needed to calculate scheduled amount, arrears and days
past due without pretending the existing payment attempts contain those rules.
