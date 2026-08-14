
# Data contract — first version

Before generating data, I wrote down the grain I think each entity should have. This is a starting point, not a finished specification. If the data generation exposes a problem, I will change the contract and record why.

## Current entities

| Entity | Intended grain | Key |
|---|---|---|
| Customer | One row per customer | customer_id |
| Loan | One row per loan account | account_id |
| Subscription | One row per subscription agreement | subscription_id |
| Payment | One row per payment transaction | payment_id |
| Portfolio snapshot | One row per account and reporting date | account_id plus snapshot_date |
| Reporting exclusion | One row per account, run and exclusion reason | run_id plus account_id plus exclusion_code |

## Rules I want to keep visible

- Keys should be unique within their own table.
- A foreign key should resolve, unless I deliberately create an exception to test.
- Dates should be stored consistently.
- Money calculations need controlled decimal handling.
- Status values should come from a small documented list.
- NULL should mean something different from an empty string.
- The generator should use a fixed seed so I can reproduce a result.

## Initial fields

Customer: customer_id, date_of_birth, postcode, customer_created_date

Loan: account_id, customer_id, product_code, origination_date, original_balance, status

Subscription: subscription_id, customer_id, product_code, start_date, billing_frequency, status

Payment: payment_id, account_id, payment_date, amount, payment_status, payment_method

Snapshot: account_id, snapshot_date, outstanding_balance, arrears_amount, days_past_due

## Questions for the next few days

- Should payments belong to loans, subscriptions or both?
- Do I need a separate product table?
- Which dates need to be event dates and which are reporting dates?
- How will I represent a refund or reversed payment?
- What should happen when an account has no matching customer?

These questions are intentionally left open. I will answer them when the generated data and first models make the trade-offs clearer.
