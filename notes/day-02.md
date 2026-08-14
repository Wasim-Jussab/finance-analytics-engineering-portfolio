# Day 2 — generating the first dataset

**Date:** 15 August 2026

## What I built

I added a small Python generator for customers, loans, subscriptions and payments. It uses the standard library rather than adding another dependency at this stage.

The default run creates 25 customers, one loan per customer, a smaller set of subscriptions and between two and six payments per loan. The values are not meant to model a real lender exactly. They are just enough to give me keys, dates, relationships and a few different statuses to work with.

## Decisions made today

For now, payments belong to a loan account through account_id. Subscription billing is separate and is linked to the customer. I considered putting both types of payment into one table, but that would make the grain unclear before I have a real reason to combine them.

That may change later. If it does, I want the reason to be visible rather than quietly changing the meaning of the payment table.

## Checks added

The generator validates:

- Duplicate customer, account, subscription and payment keys
- Loan-to-customer relationships
- Subscription-to-customer relationships
- Payment-to-account relationships
- Payments that occur before the loan originated
- Reproducibility when the same seed is used

## What I actually ran

The generator ran successfully for a five-customer sample. I also checked that the same seed produces the same dataset, a different seed changes the data and the generated relationships pass validation. The files are written locally and are not being committed as portfolio data.

The next useful step is to inspect the CSVs and load them into a local analytical database. I do not want to start writing transformations without seeing whether the generated data makes sense.
