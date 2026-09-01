# Day 9 — modelling subscriptions without inventing revenue

**Date:** 1 September 2026

The subscriptions file was already generated and loaded into DuckDB, but it stopped at the raw layer. I added the first dbt subscription model at one row per agreement.

The tempting next step was monthly recurring revenue. I did not do that because the source does not contain price, invoice or subscription-payment fields. Billing frequency alone cannot prove that a charge was raised or collected. Adding a revenue number now would hide an unsupported assumption inside a polished metric.

The model therefore stays narrow. It exposes the agreement, customer, product, start date, billing frequency and status. It also calculates completed months since start using the fixed run date already used elsewhere in the project.

I called that field `months_since_start`, not tenure. A cancelled agreement has no cancellation date in the current source, so I cannot calculate its active duration accurately.

I added tests for the agreement grain, required fields, customer relationship, accepted product/frequency/status values, start dates after the run date and raw-to-mart row-count reconciliation.

The full run produced 20 mart agreements from 20 raw agreements: 14 active and 6 cancelled. All 4 models and 46 dbt tests passed, giving 50 successful dbt resources. The 9 Python tests and Ruff also passed.

I then changed one temporary mart start date to 1 January 2026, after the fixed run date of 31 December 2025. The chronology test failed with exactly one row and exit code 1. I rebuilt the model afterwards and all 15 subscription tests passed again.

The next modelling decision is whether to add synthetic subscription billing events. That needs a separate transaction grain and explicit price rules; it should not be inferred from the agreement row.
