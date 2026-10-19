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

`mart.agg_loan_delinquency_product_risk` reduces that band detail to one row per
product and reporting date for portfolio prioritisation. It repeats the portfolio
account and shortfall denominators, so both product size and shortfall
concentration can be reconstructed. The severe account measure is explicitly the
project's `90+ days` proxy band. It is not a default flag, probability of default
or regulatory stage. Ratios are calculated from additive counts and amounts, not
averaged from band-level percentages.


`mart.agg_loan_delinquency_portfolio_concentration` summarises account and
scheduled-principal-shortfall concentration using HHI and reciprocal effective
product counts. These are descriptive distribution measures, not risk limits.

`mart.agg_loan_delinquency_band_matrix` provides all four governed bands for each
observed product and reporting date. Generated zero rows are marked with
`is_observed_band = false`; they support stable BI axes without rewriting the
sparse observed-band source.

`mart.rpt_loan_delinquency_exception_queue` includes only accounts with positive
scheduled-principal shortfall. Its order is the existing proxy band first,
shortfall second and account ID as a stable tie-breaker. Portfolio and product
denominators make each shortfall share reproducible. This is an analyst work queue,
not a probability of default, customer treatment decision or regulatory score.
