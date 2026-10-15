# Credit-risk proxy boundary

`mart.fct_loan_delinquency_position` has one row per synthetic loan account at the
fixed reporting date. It groups the existing `days_past_due_proxy` into `Current`,
`1-29 days`, `30-89 days` and `90+ days` so an analyst can segment the portfolio
without repeating CASE logic downstream.

The classification inherits the project’s principal-only schedule and
oldest-due-first payment-allocation assumption. `Current` means that no scheduled
principal is uncovered under that rule; it does not certify that interest, fees or
other contractual amounts are current. The remaining bands count calendar days
from the oldest uncovered synthetic principal instalment to 31 December 2025.

This is deliberately not labelled contractual arrears, default, impairment or
IFRS 9 staging. The source has no contractual interest schedule, grace periods,
forbearance, write-offs, credit-risk events or approved staging policy. Those
would need explicit source fields and governed business rules before a regulatory
classification could be defended.

Validation checks one row per account, complete account coverage, accepted band
values, exact reconciliation to `fct_loan_schedule_position` and consistency
between the band, uncovered principal and oldest uncovered due date.

`mart.agg_loan_delinquency_by_product` is the governed reporting view over that
fact. Its grain is reporting date, product and observed proxy band. The account
share denominator is every loan in the same product on the same reporting date;
the coverage ratio is amount-weighted, using allocated completed payments divided
by scheduled principal due within the band. Missing bands are not zero-filled:
only bands observed in the portfolio are returned. Counts and amounts reconcile
exactly to the account-level fact.
