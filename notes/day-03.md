# Day 3 — building the first reporting layer

**Date:** 17 August 2026

## What I built

I added a plain-Python transformation that reads the raw customer, loan and payment CSVs and writes three reporting outputs:

- `dim_customer`, one row per customer
- `dim_loan`, one row per loan account
- `fct_payment`, one row per payment event

The payment fact keeps both completed and failed payments. The loan table contains a summary of completed payment count, completed payment amount and the last completed payment date.

## Decisions made today

I nearly filtered failed payments out at the start because most of the first reporting questions will use successful payments. I kept them instead. A failed payment is still an event, and removing it would make payment attempts impossible to analyse later.

I also made the loan age calculation use an explicit as-of date. Using today's date inside the transformation would make a rerun produce different results without any source data changing.

The transformation uses `Decimal` for money and formats dates and amounts consistently. It does not use the system clock or an external database.

## Checks added

The reporting validation checks:

- Duplicate keys at each output grain
- Loan-to-customer foreign keys
- Payment-to-loan foreign keys
- Completed-payment totals against the raw payment file
- Completed-payment summaries against the payment fact

## What I actually ran

I compiled the new module and ran it against a small controlled raw dataset containing one completed payment and one failed payment. The output produced one customer, one loan and two payment rows. The assertions confirmed that the failed row stayed in `fct_payment`, while the loan summary contained only the completed £50.00.

I could not run the repository's full pytest suite in the workspace because pytest is not installed there. The new test file follows the existing pytest setup and the standard-library checks above passed.

## What I have not solved

The current transformation still reads CSV files directly and has no incremental loading, database materialisation or schema-version handling. Those are real gaps. The next step should be adding a local database boundary and testing the model against a deliberately bad input rather than assuming every file is clean.
