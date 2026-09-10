# Initial architecture notes

## Why I am starting locally

I do not want the first step to be creating cloud resources that I barely use or could accidentally leave running. I can learn the modelling, testing and pipeline structure locally first, then document how the same design would map to S3, Glue and Redshift.

The current local flow is:

~~~mermaid
flowchart TD
    A["Generated CSV source data"] --> B["Python typed load"]
    B --> C["DuckDB raw schema"]
    C --> D["SQL models"]
    D --> E["DuckDB mart schema"]
    E --> F["Reconciliation checks"]
~~~

## What each part is for

| Part | Why it is here |
|---|---|
| Generated source data | Gives me realistic edge cases without using work data |
| Python typed load | Makes the raw table types explicit instead of relying on inference |
| DuckDB raw schema | Separates source-shaped data from reporting logic |
| SQL models | Makes the transformation rules reviewable and closer to a warehouse workflow |
| DuckDB mart schema | Provides stable reporting grains for later BI or dbt work |
| Quality checks | Proves whether the output is complete and explainable |

## Day 4 implementation

The loader replaces the local `raw` tables on each run. That is a full-refresh approach for this small learning dataset, not an incremental production pipeline. It is useful for now because rerunning the generator and loader gives me a clean, repeatable starting point.

The SQL models create:

- `mart.dim_customer`, one row per customer
- `mart.dim_loan`, one row per loan account with completed-payment summaries
- `mart.fct_payment`, one row per payment event, retaining failed payments

The model uses a stored `run_parameters` table for the as-of date. This keeps loan-age calculations stable when the same input is rerun later.

## Day 9 addition

dbt now also creates `mart.dim_subscription` at one row per subscription agreement. It uses the same stored run date to calculate completed months since start. The model does not infer revenue or active tenure because the current source has no price, billing-event or cancellation-date fields.

## Day 10 addition

The synthetic source now includes cancellation dates and a separate subscription billing-event file. The loader keeps those events in `raw.subscription_payments`, and dbt creates `mart.fct_subscription_payment` at one row per billing attempt.

This preserves the boundary between an agreement and its transactions. Joining the two without respecting that one-to-many relationship would multiply agreement rows and make active-subscription counts unreliable. Completed attempts can be summed as synthetic collections, but the model does not claim accounting revenue.

## Day 11 addition

`mart.agg_subscription_monthly` sits downstream of the agreement dimension and billing fact. It joins at subscription key, then aggregates to month, product and billing frequency. This creates a BI-friendly reporting table without changing the transaction-level source of truth.

The model does not generate empty calendar months. That is acceptable for the current event-reporting use case, but a later trend model will need a date spine if zero-activity months must appear.

## Day 12 addition

`mart.dim_date` provides a daily calendar from a configured start date to the fixed reporting date. Subscription billing events use a left join to derive their reporting month, while relationship and required-field tests verify complete coverage.

I chose a left join so a calendar defect cannot silently remove a financial event. A missing calendar match leaves the event in the fact with a NULL reporting month, which causes the build to fail visibly.

## Day 13 addition

The synthetic plan definitions now move through the same source-to-mart path as the transaction data. Python writes `subscription_plans.csv`, the typed loader creates `raw.subscription_plans`, and dbt materialises `mart.dim_subscription_plan`.

Agreements reference plans by key. The monthly aggregate takes product and billing frequency from the plan dimension rather than treating the generator's price lookup as hidden business logic. A payment-to-plan control also confirms that every attempted amount equals the related synthetic contractual amount.

This is a current-state reference table, not a historical pricing model. Effective dating and plan changes remain separate modelling work.

## Day 14 addition

The monthly mart now starts from eligible plan months rather than billing events. It combines the date dimension with agreement start and cancellation dates, retaining a plan month only when at least one agreement overlaps it. Billing metrics are then left joined and missing activity is converted to explicit zeros.

This prevents a quiet gap in a trend chart without inventing rows for plans that have no agreement population. The model also exposes the active-agreement count behind each plan month, so a zero means "agreements existed but no attempt occurred" rather than "the plan may not have existed".

## Day 15 addition

`mart.agg_subscription_movement_monthly` is separate from the billing aggregate. It builds a complete month series for each plan from its first observed agreement, then derives opening, started, cancelled and closing populations from agreement dates.

Keeping movement separate avoids mixing transaction activity with account population. The model can answer a month-end agreement question without changing the "active at any point in the month" definition used to qualify zero-activity billing rows.

## Day 16 addition

The Python load now stamps every raw row, including the run parameters, with one UTC `loaded_at` value for the batch. dbt checks the maximum timestamp on each source before it builds the marts.

This separates two different ideas: business event dates describe when a payment or agreement event happened, while `loaded_at` describes when this pipeline received the record. A production ingestion layer would normally retain upstream extraction and batch identifiers as well; the local project can only prove freshness from the point at which it loads DuckDB.

## Day 17 addition

The loader now gives every raw row one generated `load_id` and writes a seven-row `raw.ingestion_audit` manifest covering the six CSV sources and the run parameters. The audit records the source file, row count, status and shared UTC load time. A dbt reconciliation test compares those recorded counts with the physical raw tables.

The full replacement load runs inside one DuckDB transaction. Raw tables, the retained SQL comparison marts, the run parameters and the audit manifest are committed together only after Python validation succeeds. If a required source file is missing, the transaction rolls back and the previous valid batch remains available. This is still a local full-refresh pattern; it does not provide an upstream extraction guarantee or a multi-run audit history.

## What I already know

I am comfortable with SQL, Redshift views, Power BI modelling, reporting logic, reconciliations and checking results against business expectations. I also have experience with AWS Glue and Python in my current work.

## What I still need to prove to myself

- How to organise dbt models so they remain understandable
- How to test failures without hiding them in the final output
- How to make reruns safe when the source is larger than this example
- Which parts should be handled in SQL and which belong in Python
- How much orchestration is useful for a project of this size

## Future mapping, not current implementation

| Local version | Possible production equivalent |
|---|---|
| Local files | S3 landing area |
| Python load | Glue job or another ingestion task |
| DuckDB raw schema | Redshift raw or staging schema |
| DuckDB mart schema | Redshift reporting schema |
| Local scheduled run | Airflow or another scheduler |
| Local tests | CI checks before a merge |

This mapping is an investigation list. It is not evidence that this repository is running on AWS.
