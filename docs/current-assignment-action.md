# Current assignment and observed action

The [team coverage rollup](assignment-action-coverage.md) keeps assigned and
unassigned populations distinct and documents its denominator explicitly.

`rpt_loan_current_assignment_action` has one row per exception-queue account at the
fixed `as_of_date`. It joins by the current assignment ID, then selects the earliest
recorded action by that account at or after `assigned_at` and on or before the UTC
reporting date. Same-timestamp events qualify; later actions beyond the reporting
date do not. A NULL elapsed duration means no qualifying pair, not zero response.

The states distinguish unassigned, assigned-with-no-observed-action, and
assigned-with-observed-action. An action from another team still qualifies. This
does not assert causation, contact success, regulatory compliance or a service SLA.
Assignment history is synthetic; no employer policy is used.

Run `make verify` to execute model SQL boundary fixtures, exact source
reconciliation, state consistency, grain and required-field tests.
