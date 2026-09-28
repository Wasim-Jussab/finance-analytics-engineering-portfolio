# Loan reporting milestone review

Days 31–35 turn the synthetic loan data into a small, tested reporting chain:

1. complete month-end account snapshots;
2. an explicit principal-only repayment schedule;
3. oldest-due-first payment allocation;
4. a fixed-date account schedule position; and
5. a monthly product-level portfolio aggregate.

## What the work demonstrates

- Clear fact grains from instalment to account-month and portfolio-month.
- Reconciliation between source payments, schedules, allocation and aggregates.
- Separation of source status from calculated analytical classifications.
- Reproducible reporting dates and deterministic synthetic inputs.
- Controlled failure testing as well as clean-path tests.
- A BI-ready aggregate whose numerator and denominator are documented.

## Evidence from the seed dataset

The monthly portfolio mart contains 65 rows across 24 month ends and three loan
products. At 31 December 2025 it reconciles 25 accounts, £68,350.00 original
principal, £57,712.01 principal due, £6,025.00 assumed allocation and £51,687.01
shortfall. Its portfolio-weighted due-principal coverage ratio is 0.1044.

The uniformly weak schedule position is a property of the deliberately sparse
generated payments. It is useful for exercising controls, but it is not presented
as a representative loan book.

## Limits I would discuss in an interview

- The schedule is invented, principal-only and not a lender contract.
- The allocation order is an explicit project assumption.
- Current source status cannot reconstruct historical active populations.
- There are no interest, fee, grace-period, reversal, hardship or reschedule events.
- The data is too small to prove performance or production-scale operation.
- DuckDB is a local analytical substitute, not a deployed warehouse.

The project therefore demonstrates analytics-engineering structure and control
thinking. It does not claim contractual arrears, accounting balances, credit-risk
models or a production servicing platform.
