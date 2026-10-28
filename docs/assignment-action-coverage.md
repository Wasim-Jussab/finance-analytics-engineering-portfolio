# Assignment-action coverage

`agg_loan_assignment_action_coverage` has reporting-date/current-assigned-team grain.
It retains the NULL-team group. Queue accounts reconcile to assigned plus unassigned;
assigned accounts reconcile to with-action plus without-action.

The numerator is assigned accounts with a first observed action at or after the
current assignment, through the reporting date. The denominator is assigned accounts,
not all queue accounts or all event rows. With no assigned accounts the rate is NULL.
No action-to-assignment timestamp is reinterpreted as a service standard.

This rollup inherits the [account contract](current-assignment-action.md): actions
may be recorded by another team and do not prove contact success or causal response.
Use counts and the denominator alongside the rate; do not turn this into a staff KPI.
