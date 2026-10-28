# Day 62 — current-team activity coverage

25 October 2026

I aggregated the account summary by reporting date and current assigned team.
Unassigned accounts stay in a NULL-team group instead of disappearing in a join.
The denominator is all queue accounts in the group, not only accounts with events.

I retained shortfall amounts alongside counts so an untouched account population
can be inspected without pretending the count describes financial exposure alone.
Assignment itself counts as activity: this is not a contact, recovery or team
productivity metric. Historical events are attributed to current ownership, not
the team that performed them, so this output must not be used to rank staff.

An exact multiset reconciliation protects every output field, while a separate
test checks grain, counts, coverage and amount bounds. I will record the actual
local gate outcome before publishing this increment.

## Local validation

`make verify` passed: 596 dbt resources, 32 models, 559 data tests, 79 Python
tests, all historical/incremental scenarios, Ruff and dbt documentation.
The output retained 25 accounts: four under Team A, four under Team B and 17
unassigned. All 17 unassigned accounts had no recorded activity; their synthetic
scheduled-principal shortfall reconciled to 32,895.43. That is a fixture result,
not a production recovery claim or a team-performance comparison.
