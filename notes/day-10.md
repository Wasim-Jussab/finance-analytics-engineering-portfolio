# Day 10 — adding subscription billing events

**Date:** 3 September 2026

Day 9 stopped short of subscription revenue because an agreement row did not prove that money had been billed or collected. Today I added a separate billing-attempt dataset and fact model instead of putting transaction fields onto the subscription dimension.

The new fact is one row per scheduled attempt. It keeps failed attempts, links back to the agreement and marks completed attempts as collected. The generator uses a small price lookup for each synthetic product and billing frequency. Those prices are arbitrary values for this project and are not based on employer data.

I used calendar-month increments for billing dates. Adding 30 days repeatedly would slowly move a monthly billing date across the calendar. The helper instead keeps the original day where possible and uses the last valid day for shorter months.

Cancelled agreements now have a cancellation date, so I can calculate completed active months and stop generating billing attempts after cancellation. Active agreements keep a NULL cancellation date and use the fixed reporting date as their current endpoint.

My first implementation changed the order in which the shared random generator was called. Even though the same seed was still present, that reduced the published seed-42 baseline from 20 to 16 subscriptions and changed loan payment attempts from 99 to 98. I restored the original draw order and used a separate seeded random stream for billing statuses. The existing counts returned to 20 subscriptions and 99 loan payment attempts, and I added a regression test for the published baseline.

The clean run produced 150 subscription billing attempts across 20 agreements: 125 completed and 25 failed. Completed synthetic collections totalled £3,648.00 and reconciled exactly between the raw table and the fact model. All 5 models and 61 dbt tests passed, giving 66 successful dbt resources. All 12 Python tests and Ruff also passed.

I changed one temporary fact amount to `-1.00` and ran the positive-amount test. It returned exactly one row and a non-zero exit code. I rebuilt the fact afterwards and reran the clean suite.

I am still not calling this revenue. The project has no invoice, service-period, refund or accounting-recognition rules. The next useful modelling step is deciding whether a product dimension or a monthly subscription-performance mart would add more value without hiding those gaps.
