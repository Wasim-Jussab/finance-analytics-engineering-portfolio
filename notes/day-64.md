# Day 64 — use the assigned population as the denominator

27 October 2026

I added a team/reporting-date rollup of the current-assignment action observation.
This deliberately differs from general activity coverage: an assignment event is
not itself a subsequent action. Assigned accounts split into with/without action;
unassigned accounts remain visible but do not dilute the assigned-action rate.

A group with no assigned accounts returns a NULL rate, not zero performance.
The isolated SQL fixture checks a half-covered assigned group and an unassigned
group. The dbt reconciliation independently derives the numerator from the account
state labels, while consistency checks reconcile both population splits and grain.

An action can be recorded by any team, so this must not rank staff or imply a
contact success, contractual SLA, recovery or causal effect of assignment.
I have not changed or claimed to fix the separately documented DuckDB WAL issue.

## Local verification

`make verify` passed: 613 dbt resources, 34 models, 574 data tests, 81 Python
tests, all controlled historical/incremental scenarios, Ruff and dbt documentation.
The denominator fixture also passed separately. Its 50% and NULL results are
controlled fixture evidence, not claimed output from a post-documentation query
against the default database.
