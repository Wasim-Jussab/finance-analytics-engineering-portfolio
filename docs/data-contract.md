# Data contract — first version

Before generating data, I wrote down the grain I think each entity should have. This is a starting point, not a finished specification. If the data generation exposes a problem, I will change the contract and record why.

## Current entities

| Entity | Intended grain | Key |
|---|---|---|
| Customer | One row per customer | customer_id |
| Loan | One row per loan account | account_id |
| Subscription | One row per subscription agreement | subscription_id |
| Subscription payment | One row per scheduled subscription billing attempt | subscription_payment_id |
| Payment | One row per payment transaction against a loan account | payment_id |
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

Subscription: subscription_id, customer_id, product_code, start_date, cancellation_date, billing_frequency, status

Subscription payment: subscription_payment_id, subscription_id, billing_date, amount, payment_status

Payment: payment_id, account_id, payment_date, amount, payment_status, payment_method

Snapshot: account_id, snapshot_date, outstanding_balance, arrears_amount, days_past_due

## Day 2 decision

For the first version, payments belong to loan accounts through account_id. Subscriptions are linked to customers but do not share the payment table yet.

This is intentional. Combining loan and subscription transactions now would create a mixed-grain table before there is a clear business requirement. Subscription billing can be added as a separate transaction type later if the reporting use case needs it.

## Day 3 reporting layer

The first reporting outputs have these grains:

| Output | Grain | Purpose |
|---|---|---|
| dim_customer | One row per customer | Descriptive customer attributes |
| dim_loan | One row per loan account | Loan attributes plus completed-payment summary |
| fct_payment | One row per payment transaction | Payment-level reporting, retaining failed payments |

A failed payment remains a payment event. It is not removed from the fact table. It is excluded from completed-payment counts and amounts using an explicit `is_successful` flag. This avoids a common reporting problem where filtering failed transactions out too early makes the number of attempts look like the number of successful payments.

The validation checks:

- Keys are unique at each output grain.
- Loan customer references resolve.
- Payment account references resolve.
- Completed payment amount reconciles to the raw payment file.
- The completed-payment summary on `dim_loan` reconciles to the same total.

The `as_of_date` used for loan age is supplied to the transformation rather than taken from the machine clock. That keeps the output reproducible.

## Day 9 subscription mart

The first subscription output keeps the agreement grain unchanged:

| Output | Grain | Purpose |
|---|---|---|
| dim_subscription | One row per subscription agreement | Agreement attributes, current status and completed months since start |

The source has a start date and current status but no cancellation date, status history, price or billing transactions. I therefore did not calculate revenue, lifetime value or historical active counts. Those measures would look useful but would rely on invented assumptions.

The model adds `months_since_start` using the same fixed run date as the loan model. For a cancelled agreement this means elapsed months since the agreement began, not active tenure. The model also keeps billing frequency as a descriptive field rather than treating it as proof that a payment occurred.

The additional checks confirm that:

- Subscription keys are unique and required fields are populated.
- Customer references resolve to the customer dimension.
- Product, frequency and status values remain within the documented sets.
- Start dates do not fall after the fixed run date.
- The mart retains the same number of agreements as the raw source.

## Day 10 subscription billing events

Subscription payments now have their own event grain rather than being added to the agreement row or mixed with loan payments:

| Output | Grain | Purpose |
|---|---|---|
| fct_subscription_payment | One row per scheduled subscription billing attempt | Billing-level reporting that retains both completed and failed attempts |

The generator uses an explicit synthetic price lookup for each product and billing frequency. These values are arbitrary project assumptions, not copied from an employer or presented as market pricing. Billing dates advance by calendar month or year from the agreement start date, rather than by a fixed number of days.

| Product | Monthly attempt | Annual attempt |
|---|---:|---:|
| SUB-1 | £15.00 | £150.00 |
| SUB-2 | £24.00 | £240.00 |

Cancelled agreements now carry a cancellation date. This allows `active_months` to end at cancellation and prevents billing attempts after that date. Active agreements keep a NULL cancellation date and use the fixed reporting date as their current endpoint.

A completed attempt is labelled as collected cash in the fact model. It is not treated as recognised revenue because this project has no service-period, invoice, refund or accounting-recognition logic.

The additional checks confirm that:

- Billing-attempt keys are unique and subscription references resolve.
- Amounts are positive and statuses use the documented values.
- Billing dates fall within the related agreement's active dates.
- Cancellation dates agree with current agreement status.
- Completed collection totals reconcile exactly from raw events to the fact table.

## Questions for the next few days

- Do I need a separate product table?
- Which dates need to be event dates and which are reporting dates?
- How will I represent a refund or reversed payment?
- Should a failed attempt followed by a retry be linked through a billing-cycle identifier?
- What should happen when an account has no matching customer?

These questions are intentionally left open. I will answer them when the generated data and first models make the trade-offs clearer.
