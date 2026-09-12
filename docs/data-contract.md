# Data contract — first version

Before generating data, I wrote down the grain I think each entity should have. This is a starting point, not a finished specification. If the data generation exposes a problem, I will change the contract and record why.

## Current entities

| Entity | Intended grain | Key |
|---|---|---|
| Customer | One row per customer | customer_id |
| Date | One row per calendar date | calendar_date |
| Loan | One row per loan account | account_id |
| Subscription plan | One row per product and billing-frequency combination | subscription_plan_id |
| Subscription | One row per subscription agreement | subscription_id |
| Subscription payment | One row per scheduled subscription billing attempt | subscription_payment_id |
| Payment | One row per payment transaction against a loan account | payment_id |
| Portfolio snapshot | One row per account and reporting date | account_id plus snapshot_date |
| Reporting exclusion | One row per account, run and exclusion reason | run_id plus account_id plus exclusion_code |
| Current ingestion audit | One row per expected source in the current load | source_name |
| Ingestion run history | One row per successful or failed load attempt | load_id |
| Ingestion source history | One row per source in each successful load | load_id plus source_name |
| Ingestion failure history | One row per failed load attempt | load_id |

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

Subscription plan: subscription_plan_id, product_code, billing_frequency, billing_amount

Subscription: subscription_id, customer_id, product_code, subscription_plan_id, start_date, cancellation_date, billing_frequency, status

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

## Day 11 monthly performance mart

The billing fact now feeds a reporting aggregate with an explicit compound grain:

| Output | Grain | Purpose |
|---|---|---|
| agg_subscription_monthly | One row per billing month, product code and billing frequency | Monthly attempt, failure and collection reporting |

`billing_month` is stored as the first day of the month rather than a display string. That keeps it usable for sorting, date filtering and later calendar joins.

The model exposes attempt, completed and failed counts alongside attempted and collected amounts. `collection_rate` is completed attempts divided by all attempts in the group. It is deliberately named and documented as an attempt-based rate; it is not a revenue measure or an amount-weighted recovery percentage.

The additional controls confirm that:

- The month, product and frequency combination is unique.
- Completed and failed counts add back to all attempts.
- Collected amount cannot exceed attempted amount.
- Collection rate remains between zero and one.
- Counts and monetary totals reconcile from the aggregate back to the billing fact.

The aggregate currently contains only months with billing events. A date spine would be needed before missing months could be represented explicitly with zero values.

## Day 12 date dimension

The reporting calendar has its own tested grain:

| Output | Grain | Purpose |
|---|---|---|
| dim_date | One row per calendar day from 1 January 2024 to the fixed run date | Shared date, month, quarter, month-end and weekend attributes |

The start date is the `calendar_start_date` dbt variable and the end date comes from `raw.run_parameters`. This makes the calendar repeatable and prevents it from changing with the machine clock.

Subscription billing dates are left joined to the calendar. The left join retains an event even if calendar coverage is wrong; the required `billing_month` field and date relationship test then expose the gap rather than silently dropping the transaction.

The additional controls confirm that:

- Calendar date and integer date key are unique and required.
- Month and quarter values remain within valid ranges.
- The first date, last date and expected row count agree with the configured bounds.
- There are no missing dates inside the range.
- Every billing date and aggregate billing month resolves to the calendar.

The date dimension is now available, but the monthly aggregate is still event-led. Zero-filling every product and frequency combination would require a separate definition of which plans are valid in each month.

## Day 13 subscription plan catalogue

The price lookup used by the generator is now a source entity and a reporting dimension:

| Output | Grain | Purpose |
|---|---|---|
| dim_subscription_plan | One row per product code and billing frequency | Visible synthetic plan definitions and contractual billing amounts |

Each agreement references a `subscription_plan_id`. The denormalised product code and billing frequency remain on the agreement for now, but a consistency test verifies that they agree with the referenced plan. This avoids silently accepting conflicting descriptions.

The four billing amounts are invented project values. They are not employer pricing or market benchmarks. Every billing attempt must equal the amount on its agreement's plan; a separate control returns any mismatch.

The additional checks confirm that:

- Plan identifiers are unique and required.
- Product and frequency combinations occur exactly once.
- Plan amounts are positive.
- Agreement plan references resolve and descriptive fields agree.
- Plan rows reconcile from raw source to mart.
- Every billing attempt agrees with its plan amount.

The catalogue is deliberately current-state only. It has no effective-from or effective-to dates, so it cannot yet represent a historical price change or a mid-agreement plan change.

## Day 14 zero-activity reporting

The monthly mart keeps the same month, product and billing-frequency grain, but it is no longer limited to months containing a billing event. A row is eligible when at least one agreement on that plan overlaps the calendar month.

`active_agreement_count` counts agreements active for at least one day in the month. If an eligible plan month has no billing attempt, attempt and collection counts, amounts and the attempt-based collection rate are set to zero.

This population rule avoids two misleading alternatives:

- An event-only aggregate hides months with no activity.
- A full date-by-plan cross join implies that every current plan existed in every historical month.

The additional controls confirm that:

- Every eligible plan month appears exactly once.
- Active agreement counts match the agreement-date overlap rule.
- Zero-attempt rows contain zero counts, amounts and rate.
- Non-zero rows retain the expected rate calculation.
- All event counts and monetary totals still reconcile to the billing fact.

## Day 15 monthly agreement movement

A second monthly aggregate keeps agreement population movement separate from billing performance:

| Output | Grain | Purpose |
|---|---|---|
| agg_subscription_movement_monthly | One row per reporting month, product code and billing frequency | Opening agreements, starts, cancellations, net movement and closing agreements |

The reporting series begins with the first observed agreement for each plan and continues to the fixed reporting date. It does not create historical rows before a plan has any observed agreement.

The movement equation is:

`closing agreements = opening agreements + starts - cancellations`

The cancellation date is treated as the event date on which the agreement leaves the closing population. An agreement cancelled on the first day of a month is therefore in that month's opening count and cancellation count, but not its closing count.

The additional controls confirm that:

- Month and plan remain unique.
- Every expected month exists from the plan's first observed agreement onward.
- Starts and cancellations reconcile to the agreement dimension.
- Counts are non-negative and the movement equation balances.
- A month's closing population equals the next month's opening population.

## Day 16 ingestion metadata

Every raw table now adds one pipeline-managed field that is not present in the generated CSV files:

| Field | Type | Meaning |
|---|---|---|
| `loaded_at` | Timestamp with time zone | UTC timestamp at which the current batch was loaded into DuckDB |

The loader creates one timestamp per run and applies it to every raw row and the run-parameters record. Event dates remain business fields and are not used as a substitute for arrival time.

dbt treats the seven raw sources as fresh when their latest `loaded_at` value is no more than one hour old, warns after one hour and errors after 24 hours. This threshold is deliberately short for a pipeline that is rebuilt on demand. It is not presented as a production service-level agreement.

The Day 16 implementation could show that individual tables were recent, but it could not identify which tables belonged to the same load or prove that the replacement was complete.

## Day 17 ingestion batch contract

Every raw table now contains these pipeline-managed fields:

| Field | Type | Meaning |
|---|---|---|
| `load_id` | String UUID | Identifier shared by every table in the current load |
| `loaded_at` | Timestamp with time zone | UTC timestamp at which the batch was loaded into DuckDB |

`raw.ingestion_audit` has one row for each of the six CSV sources and one for `run_parameters`:

| Field | Meaning |
|---|---|
| `load_id` | Batch identifier shared with the loaded rows |
| `source_name` | Expected raw table name |
| `source_file` | CSV filename, or NULL for generated run parameters |
| `source_row_count` | Number of rows loaded for that source |
| `load_status` | `Loaded` for the current accepted batch |
| `loaded_at` | Shared UTC batch timestamp |

The current contract requires all seven expected source records exactly once, a positive row count and a matching physical-table count. The full-refresh transaction is committed only after those checks and the existing mart reconciliations pass. An empty source is therefore rejected rather than assumed to be a valid zero-row extract.

This current manifest is still replaced by each full refresh. Day 18 adds separate history tables so successful prior runs are not lost.

## Day 18 ingestion history contract

`audit.ingestion_runs` has one row per load attempt. A committed batch records `Success`, seven expected sources and their total rows. A rejected batch records `Failed` with zero accepted sources and zero accepted rows.

`audit.ingestion_sources` has one row per source within each successful batch. It retains the current-manifest fields plus two file controls:

| Field | Meaning |
|---|---|
| `source_file_size_bytes` | Size of the input CSV in bytes |
| `source_file_sha256` | Lowercase 64-character SHA-256 digest of the input file |

Both fields are NULL for `run_parameters` because that record is created by the loader rather than read from a file. The six CSV sources require a positive size and valid digest. History controls confirm seven sources per run, one shared timestamp, run-level totals equal to source-level totals, and the current manifest agrees with its matching history rows.

## Day 19 failure-history contract

`audit.ingestion_failures` has one row for each failed run. It records the `load_id`, failure time, exception type and sanitised error message. Its run ID must resolve to a `Failed` row in `audit.ingestion_runs`; a successful run must not have failure detail.

Failed runs have no rows in `audit.ingestion_sources`. Those records describe accepted sources, so creating them for an incomplete batch would make the history ambiguous. The current raw manifest also stays on the last valid load ID after a failure.

The failure record is committed only after the source transaction has rolled back. Missing-file messages contain the filename but not the machine-specific path. The history is stored in the same DuckDB file and is not presented as an immutable operational ledger. A production contract would also define upstream extraction IDs, retention, access controls, severity, retry policy and alert routing.

## Questions for the next few days

- When should a plan become effective-dated rather than current-state only?
- Which dates need to be event dates and which are reporting dates?
- How will I represent a refund or reversed payment?
- Should a failed attempt followed by a retry be linked through a billing-cycle identifier?
- Would a future status-event source require pause and reactivation movements as separate categories?
- What should happen when an account has no matching customer?
- Which sources, if any, should be allowed to complete with zero rows?

These questions are intentionally left open. I will answer them when the generated data and models make the trade-offs clearer.
