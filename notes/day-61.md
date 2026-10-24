# Day 61 — summarise activity without inventing an SLA

I started the next milestone by turning the event timeline into one row per
exception account. The model counts action and assignment events separately,
reconciles them to a total, and keeps the first and latest observed activity
timestamps. All 25 queue accounts remain present, including the 17 with no recorded
activity.

For accounts with activity, I calculate whole calendar days from the latest event
date to the fixed reporting date. I deliberately stopped there. There is no approved
response deadline, follow-up cadence or customer-treatment policy in the synthetic
source contract, so an age band or breach flag would look more useful than it really
is.

Two singular tests rebuild the account result from the case-status and event facts
and check the zero/null, count and chronology rules. Generic tests protect grain,
relationships, accepted values and required fields.

## Validation

I could validate file structure locally, but this environment does not contain the
project's dbt and DuckDB dependencies. I published one batched Day 61 commit for
the exact-head GitHub Actions gate and will only report executable validation after
that run completes.
