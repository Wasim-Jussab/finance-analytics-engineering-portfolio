# Day 34 — account-level schedule position

Day 33 left the payment assumption at scheduled-instalment grain. Today I rolled
that detail up to one row per loan so the result can be used in portfolio reporting
without hiding how it was calculated.

## What I built

`fct_loan_schedule_position` summarises principal due, assumed allocation,
uncovered due principal and future principal at the fixed reporting date. It also
retains completed payments that could not be allocated because they exceed the
principal currently due.

The model exposes the earliest uncovered due date and the number of calendar days
from that date to the reporting date. I called this `days_past_due_proxy` rather
than `days_past_due`: it is derived from my synthetic principal-only schedule and
does not come from a lender's servicing system.

On the seed-42 data, all 25 loans are behind this assumed schedule. Together they
have £57,712.01 principal due, £6,025.00 allocated and £51,687.01 uncovered. The
result is useful evidence that the generated payments are sparse; it is not a
realistic claim about a loan book's credit performance.

## Checks added

- Every loan has exactly one position row and no extra accounts appear.
- Due and future instalment counts add back to the full schedule.
- Due principal equals allocated plus uncovered principal.
- Due plus future principal equals original balance.
- Completed payments equal allocated plus unallocated cash.
- Coverage ratio, oldest uncovered date, days proxy and status agree with the
  underlying amounts.
- The account summary reconciles independently to the instalment allocation fact
  and completed payment fact.

I changed one account's shortfall by £0.01 in a disposable database. The account
reconciliation returned exactly one failure. I also increased one account's
completed payment in a separate disposable database and rebuilt the allocation and
position models. The account moved to `On Schedule`, its shortfall and proxy became
zero, and £96,075.00 excess cash remained unallocated against £4,000.00 due.

The fresh workspace did not initially contain the declared Python packages, so the
first load stopped before data modelling began. After installing the documented
development dependencies, the focused model checks passed. A narrow dbt selection
also tried to run two shared tests whose unrelated parent models had not been
built, so I used the complete project gate for final evidence. My first
covered-account scenario selection also refreshed a producer without every existing
consumer used by its reconciliation tests. I separated the four-model refresh from
the 28 position-focused tests; the repeated disposable scenario then passed.

## Boundary and next step

`Behind Schedule` is a project classification, not a source status, default flag or
regulatory arrears state. Interest, fees, grace periods, reversals, rescheduling
and contractual payment order remain outside the data contract.

The next step is a monthly portfolio-performance aggregate that uses this governed
account position without presenting the proxy as lender-grade arrears.
