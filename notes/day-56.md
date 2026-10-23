# Day 56 — build an explainable delinquency exception queue

I wanted the next step to answer a practical question: which synthetic accounts
would an analyst inspect first, and can that order be defended without pretending
to have a credit model? I therefore reused the tested account-level proxy fact and
included only accounts with positive scheduled-principal shortfall.

I chose a deliberately simple order: the governed proxy band, shortfall amount,
then account ID. I kept both portfolio and product ranks, counts and shortfall
denominators on every row. This makes the queue easy to reconcile and avoids a
composite score whose weights would have no business approval or outcome evidence.

The limitation remains important. The queue uses a synthetic principal-only
schedule and an assumed allocation rule. It is not contractual arrears, a default
list, a customer-treatment decision or an SLA. A useful next increment would add
synthetic ownership and action outcomes while keeping those operational events
separate from the financial source of truth.

The full verification gate passed with 449 dbt data tests and 79 Python tests.
The resulting queue has 25 accounts across all three products, ranks 1 through 25
without gaps and reconciles to £51,687.01 of scheduled-principal shortfall.
