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
