# Case monitoring: Days 61–65 review

The [direct-reader probe](reader-readiness.md) provides a separate fail-closed
consumer check. A successful build is not a direct-reader readiness claim.

I separated three questions that are easy to conflate:

| Question | Model | Meaning |
|---|---|---|
| Is any activity recorded? | `rpt_loan_case_activity_summary` | Includes assignment events |
| Is an action observed after current assignment? | `rpt_loan_current_assignment_action` | Any team, through the fixed reporting date |
| What share of assigned cases has such an action? | `agg_loan_assignment_action_coverage` | Assigned accounts only; NULL with no denominator |

The account reports preserve every exception-queue account. Team aggregates use
current ownership, not the historical event actor. They must not rank staff,
establish causation or imply contact success, recovery, a contractual SLA or
regulatory compliance. The source is synthetic and principal-only.

## Reproduce and inspect

Run the root `make verify` gate. The new cross-model Python test executes actual
model SQL in isolated DuckDB fixtures: an old action before reassignment and a
future action do not qualify; a same-timestamp action does; unassigned cases stay
visible. Its downstream group has 50% assigned coverage and a NULL unassigned rate.
Those are controlled fixture results, not production findings.

To inspect a successfully opened build, use:

```sql
select as_of_date, current_assigned_team, assigned_account_count,
       assigned_accounts_with_action, assigned_accounts_without_action,
       assigned_action_coverage_rate
from mart.agg_loan_assignment_action_coverage
order by current_assigned_team nulls last;
```

## What remains limited

The known DuckDB WAL replay conflict can still prevent a direct read of the default
database after documentation generation. The gate's isolated scenario/documentation
copies do not certify that this later direct read will work. I have not deleted a
recovery file or claimed that this milestone fixes the lifecycle issue.

Definitions: [activity and current-team contract](data-contract.md),
[assignment window](current-assignment-action.md),
[assigned denominator](assignment-action-coverage.md). Daily notes record the actual
checks and decisions; exact-head CI evidence is retained in PR #24.
