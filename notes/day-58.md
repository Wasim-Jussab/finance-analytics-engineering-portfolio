# Day 58 — preserve assignment history instead of overwriting ownership

I wanted the queue to show who currently owns a synthetic case without losing how
that ownership changed. I added 10 assignment events across eight accounts,
including two reassignments, and kept the source at one row per event.

The case-status view derives the latest observed assignment using the assignment
timestamp and assignment ID as a stable tie-breaker. It still starts from the full
25-account queue, so 17 unassigned accounts remain visible rather than disappearing.

I kept assignments separate from both financial priority and action history. A team
assignment does not change shortfall, proxy band or rank, and I have not invented a
capacity target, contact strategy or SLA. These records are synthetic workflow
evidence only.

## Validation

Local execution was unavailable in this run. The branch is published for exact-head
GitHub Actions validation; I will only report executable checks as passed after that
workflow completes.
