# Day 32 — explicit loan repayment schedule

Day 31 left arrears out because the source only had payment attempts. Today I added
the contractual side of that comparison instead of treating any payment date as a
due date.

## What I built

Each synthetic loan now has a 6-, 12- or 18-month term and a principal-only monthly
schedule. The first due date is one calendar month after origination. Principal is
split in whole pence, with any rounding remainder placed in the final instalment.

The seed-42 dataset produced 294 scheduled instalments across 25 loans. Their
£68,350.00 scheduled principal equals the total original balance exactly.

I loaded the schedule through the same shared CSV contract and atomic ingestion
path as the other sources, then added `fct_loan_repayment_schedule` in dbt.

## Checks added

- Stable schedule IDs and one account-and-instalment row.
- A complete sequence from instalment one to the loan term.
- Due dates at the expected calendar-month interval.
- Positive principal amounts.
- Account relationships and exact reconciliation to original balance.

## What happened while validating it

The first full dbt build found one real integration gap: the ingestion audit test
listed each source explicitly and I had not added the schedule to that list. The
new source was loaded and audited correctly, but the test reported the audit row as
unexpected. I updated the control and rebuilt from a fresh database; all 294 dbt
results passed.

I also changed one scheduled amount by £0.01 in an isolated database. The principal
reconciliation test returned exactly one failing account. The clean database was
not changed.

## Boundary and next step

This schedule is deliberately simple and synthetic. It has no interest, fees,
grace period, repayment holidays or rescheduling. I have not calculated arrears
yet because I still need to define how completed payments are allocated to due
instalments. The next step is to make that allocation assumption explicit and test
it before adding account-level arrears measures.
