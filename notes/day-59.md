# Day 59 — reconcile current workload without inventing capacity

I wanted a reviewer to see the distribution behind the latest synthetic ownership
state without scanning 25 account rows. I added one row per current team and an
explicit Unassigned bucket, then carried case counts, action coverage and scheduled-
principal shortfall with portfolio denominators.

The model starts from the queue-complete case-status view, so assigned and unassigned
counts reconcile to all cases. Actioned and no-action counts are a separate complete
split; I did not treat assignment as evidence that contact occurred. A singular test
rebuilds every measure from account grain and checks the reported shares.

I deliberately stopped at observed distribution. The data has no staffing hours,
capacity target, case complexity, response deadline or approved treatment policy,
so calling this productivity, utilisation or SLA performance would be false.

## Validation

Local package execution was unavailable in this environment. I published one
batched commit for exact-head GitHub Actions and will only treat those executable
checks as passed after the workflow completes.
