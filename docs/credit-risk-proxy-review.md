# Days 51–55 credit-risk proxy review

This milestone adds a governed reporting layer over the existing principal-only
loan schedule. It does not create a credit-risk model.

| Output | Grain | Decision supported |
|---|---|---|
| `fct_loan_delinquency_position` | Account and reporting date | Inspect the schedule-derived proxy position |
| `agg_loan_delinquency_by_product` | Product, reporting date and observed band | Reconcile the observed portfolio mix |
| `agg_loan_delinquency_product_risk` | Product and reporting date | Compare size, severe-proxy incidence and shortfall |
| `agg_loan_delinquency_portfolio_concentration` | Reporting date | Compare account and shortfall concentration |
| `agg_loan_delinquency_band_matrix` | Product, reporting date and every governed band | Feed BI with explicit zero combinations |

The fixed fixture has 25 accounts, of which 24 fall into the project's `90+ days`
proxy band. Scheduled principal due is £57,712.01, assumed allocated completed
payments are £6,025.00 and proxy shortfall is £51,687.01. Account concentration
HHI is 0.4400 and shortfall concentration HHI is 0.3543.

The complete matrix has twelve rows: three products multiplied by four governed
bands. Four rows are observed and eight are explicit presentation zeros.
`is_observed_band` prevents a consumer from confusing those generated rows with
source observations.

The remaining gaps are material. There is no contractual interest or fee schedule,
grace-period policy, forbearance, write-off history, default definition, ECL model
or approved IFRS 9 staging logic. No output should be described as contractual
arrears, probability of default, expected loss or regulatory stage.
