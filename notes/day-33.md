# Day 33 — explicit payment-to-schedule allocation

Yesterday I stopped before calculating arrears because I had a schedule and payment
attempts but no rule connecting them. Today I made that missing assumption visible
instead of burying it inside an account-level measure.

## What I built

`fct_loan_schedule_allocation` keeps one row per scheduled instalment. Completed
payments on or before the fixed reporting date are applied to due principal from
the oldest instalment forward. Failed attempts do not enter the allocation pool.

The model caps each allocation at the scheduled amount. Future instalments remain
untouched, and any payment above total principal due remains unallocated rather
than being treated as an early settlement of future dues.

On the seed-42 data, 236 instalments and £57,712.01 of principal were due at 31
December 2025. The rule allocated £6,025.00 of completed payments and left
£51,687.01 uncovered. Another 58 instalments remained future.

## Checks added

- Every schedule row appears exactly once in the allocation fact.
- Schedule IDs and account relationships resolve.
- Running due principal and row allocations follow the oldest-first formula.
- Allocation cannot be negative or exceed the scheduled principal.
- Future rows cannot receive an allocation or an uncovered amount.
- Account-level allocated value equals the lower of completed payments and due
  principal.

I changed one allocated amount by £0.01 in a disposable database. The account-level
reconciliation returned exactly one failure. I then used a second disposable
database to make one account's completed payments much larger than its due
principal. The model allocated only the £1,566.60 due, left £98,433.40 unallocated
and assigned nothing to future rows; all 19 selected tests passed.

The complete local gate reached documentation generation after every model, test
and controlled scenario had passed, then hit the known DuckDB recovery-file replay
conflict when dbt reopened the database. I routed documentation generation through
the same narrowly checked, checkpointed copy used by the scenario tests. I did not
delete or ignore the recovery file, and unrelated catalogue errors still fail.

## Boundary and next step

This is not a lender's allocation engine. It ignores interest, fees, grace periods,
reversals, rescheduling and contractual payment order. The status on each row only
describes coverage under my stated project assumption.

The next step is to aggregate this tested detail to account and reporting-date
grain. I can then introduce an arrears-style measure without confusing the project
calculation with a source-system balance or lender-defined delinquency status.
