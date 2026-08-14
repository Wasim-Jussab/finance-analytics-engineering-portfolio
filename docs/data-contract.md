
# Initial data contract

This contract defines the synthetic domain before data generation begins. It prevents the project from becoming a collection of unstructured CSV files.

## Planned entities and grain

| Entity | Grain | Candidate business key |
|---|---|---|
| Customer | One row per synthetic customer | customer_id |
| Loan | One row per loan account | account_id |
| Subscription | One row per subscription agreement | subscription_id |
| Payment | One row per payment transaction | payment_id |
| Portfolio snapshot | One row per account per reporting date | account_id, snapshot_date |
| Reporting exclusion | One row per excluded account and reporting run | run_id, account_id, exclusion_code |

## Required contract principles

- Business keys must be unique within their entity.
- Foreign keys must resolve unless an exception is explicitly documented.
- Dates must use ISO YYYY-MM-DD representation at the interface boundary.
- Monetary values must use fixed decimal logic rather than binary floating-point calculations where precision affects reporting.
- Status values must come from documented controlled vocabularies.
- NULL has a defined meaning and must not silently become an empty string.
- Every generated dataset must include a reproducible seed or generation version.

## Initial synthetic fields

### Customer

customer_id, date_of_birth, postcode, customer_created_date

### Loan

account_id, customer_id, product_code, origination_date, original_balance, status

### Subscription

subscription_id, customer_id, product_code, start_date, billing_frequency, status

### Payment

payment_id, account_id, payment_date, amount, payment_status, payment_method

### Portfolio snapshot

account_id, snapshot_date, outstanding_balance, arrears_amount, days_past_due

## Contract changes

Changes to this contract must record:

- What changed
- Why it changed
- Which models are affected
- Which tests were added or amended
- Whether historical outputs are expected to change
