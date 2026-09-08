# Day 15 — separating agreement movement from billing activity

**Date:** 8 September 2026

Day 14 defined an active agreement as one that overlapped any part of a month. That definition is useful for explaining whether a plan had a population when billing activity was zero, but it is not the same as a month-end balance.

I added a separate monthly agreement-movement mart instead of putting more columns into the billing aggregate. It reports opening agreements, starts, cancellations, net movement and closing agreements by month and plan.

The movement equation is opening plus starts less cancellations equals closing. Closing then becomes the next month's opening balance. I treated the cancellation date as the event date on which an agreement leaves the closing population. This makes a first-of-month cancellation part of opening and cancellations, but not closing.

The seed-42 model contains 83 plan-month rows from March 2024 to December 2025. All 20 starts and 6 cancellations reconcile to the agreement dimension, and the final closing population is 14, matching the current active agreements.

All 9 models and 125 dbt tests passed, giving 134 successful dbt resources. All 14 Python tests and Ruff also passed.

I increased one temporary December closing balance by one. The movement-consistency test returned exactly one unbalanced row and a non-zero exit code. I rebuilt the model afterwards.

This is not a full status history. The source has only agreement start and cancellation dates, so pauses, reactivations and other lifecycle events would need a proper event source before they could be modelled honestly.
