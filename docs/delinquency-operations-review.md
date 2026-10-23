# Days 56–60 technical review — controlled delinquency operations

## What I built

I started from the tested account-level delinquency proxy and added five controlled
operational layers:

1. A deterministic 25-account exception queue with explicit ranks and denominators.
2. Twelve synthetic action events while retaining 17 accounts with no action.
3. Ten synthetic assignment events, including two preserved reassignments.
4. A three-bucket current-workload summary that keeps Unassigned visible.
5. A unified 22-event action-and-assignment timeline with deterministic chronology.

The queue, case status, workload aggregate and event timeline reconcile back to
their account- or event-grain sources. Assignment and action history cannot rewrite
financial shortfall, proxy band or rank.

## What this demonstrates

The useful engineering pattern is separation of concerns. Financial classification
comes from the scheduled-principal proxy. Operational events remain append-only
fixtures. Current status is derived without deleting history, and aggregates carry
their denominators instead of relying on dashboard context.

The controls cover grain, relationships, chronology, complete populations, latest-
event selection and exact count and amount reconciliation. The result is locally
reproducible with synthetic data and free tooling.

## What this does not prove

This is not contractual arrears, default, IFRS 9 staging or a credit decision.
There is no real servicing policy, contact consent, promise-to-pay lifecycle,
response deadline, agent capacity, case complexity, treatment outcome or customer
vulnerability data. For that reason I have not labelled elapsed time as SLA
performance or team distribution as productivity.

The next credible step is movement across reporting dates using genuine dated
snapshots. Adding more ranks or thresholds without a business contract would make
the portfolio look busier without making it more defensible.
