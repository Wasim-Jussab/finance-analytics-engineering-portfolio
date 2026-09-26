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

## Day 18 addition

The current-batch manifest still lives in `raw.ingestion_audit`, but each successful commit now also appends to `audit.ingestion_runs` and `audit.ingestion_sources`. The first table has one row per accepted run; the second keeps the seven source records for each run. This separates current operational state from historical evidence without changing the reporting marts.

Before replacing any raw table, Python calculates the byte size and SHA-256 digest of all six required CSV files. Those fingerprints are stored in both the current manifest and source history. They identify whether two runs used identical file content; they do not prove who produced a file or when an upstream extraction occurred.

Only successful runs are retained in the source-level history. A failed replacement is rolled back without adding a false success record.

## Day 19 addition

Failed attempts now have a separate path. The loader first rolls back the transaction that was replacing raw data. It then opens a small control transaction that writes a `Failed` run header and a related row in `audit.ingestion_failures`. This ordering matters: writing the failure before the rollback would undo the evidence, while committing it inside the replacement transaction could also commit part of a bad batch.

The failure detail contains the exception type, failure time and a sanitised message. For a missing file, the message keeps the filename but removes the local path. No source-level history is written for a rejected batch because the sources were not accepted as a complete load.

This is useful local operational evidence, not an independent audit ledger. Both data and controls still live in one DuckDB file, and the loader has no retry or alerting mechanism.

## Day 20 addition

The generator and loader now import the same executable source definition. It lists the expected columns for each of the six CSV files and the DuckDB type used at ingestion. This removes the two separate column lists that had existed in generation and loading code.

Before changing the raw schema, Python reads and checks every CSV header. Missing, unexpected or duplicate names raise a `SourceContractError`; the normal rollback and failure-history path then records the rejected attempt. Column order is allowed to change because the loader maps values by name rather than position.

This is intentionally a narrow first contract. DuckDB still performs the value-to-type conversion, and the definition has no version identifier, nullable-field rules or compatibility policy for adding a column.

## Day 21 addition

The current subscription-plan source is now snapshotted into
`history.subscription_plan_history`. dbt uses the stable plan ID and checks only the
definition fields: product code, billing frequency and synthetic amount. A changed
definition closes the old row and creates a new current row.

The snapshot records system observation time. It does not invent a contractual
effective date. Existing marts continue to use the current plan dimension, so this
addition preserves their published totals while adding an auditable change path.

A repeatable scenario copies the built DuckDB database to a temporary location,
changes one synthetic amount by £0.01, runs the snapshot and verifies four current
versions plus one closed version. The normal database is not altered.

## Day 22 addition

A second snapshot now stores observed versions of subscription agreements in
`history.subscription_agreement_history`. It checks the agreement's customer,
plan, start date, cancellation date, billing frequency and status while ignoring
routine ingestion metadata.

The source's `cancellation_date` and dbt's validity timestamps answer different
questions. The former is the synthetic business event date; the latter records when
this pipeline observed a source version. Keeping both avoids presenting load time as
if it were an operational event.

The plan and agreement failure checks now share one helper for checkpointing and
copying the clean database, running dbt and disposing of the temporary scenario.
The agreement scenario chooses an active record from the generated data rather than
depending on a hard-coded agreement key.

## Day 23 addition

`mart.fct_subscription_status_change` is the first reporting model built from the
agreement snapshot. It orders versions per agreement, compares each status with the
previous status and emits a row only when the two differ.

The clean first snapshot produces no rows because it contains states but no
transitions. The controlled cancellation scenario updates one temporary source row,
reruns the snapshots, then rebuilds and tests the fact. This creates one
Active-to-Cancelled transition without adding invented history to the committed
dataset.

The fact stores the source cancellation date, snapshot observation timestamp and
their day difference. It does not assume that ingestion time is the business event
time.

## Day 24 addition

`mart.fct_subscription_source_removal` identifies historical agreement keys whose
latest snapshot version has closed without a replacement. It is separate from the
status-change fact because source absence is not evidence of a business cancellation.

The current-version control now requires exactly one current history row for every
agreement still present in the source, while a second control prevents any historical
key from having more than one current row. This makes the tests consistent with the
snapshot's hard-delete invalidation setting.

The removal scenario deletes one active agreement only from a temporary database,
reruns snapshots and builds the removal fact. It intentionally has no relationship
test to the current subscription dimension because a removed key is expected to be
absent there.

## Day 25 addition

`mart.fct_subscription_history_event` is the reporting boundary over the two historical event facts. It uses one row per observed event and assigns an explicit `event_type` of `Status Change` or `Source Removal`.

The union does not turn removal into a business status. Status changes can carry a new status and business event date; source removals retain the last observed status and leave the business event date empty. Prefixing the component version ID with the event type keeps the event key unique even if the same snapshot version later supports both observations.

The controlled scenarios now rebuild their component fact first, then build and test the unified consumer. This order matters because a downstream reconciliation test should not run against a stale consumer table.

## Day 26 addition

`mart.fct_subscription_payment` is now an incremental dbt model using a keyed
DuckDB merge. `subscription_payment_id` is the unique key: a new key is inserted,
while a changed source row with an existing key updates the current fact row. The
fact also retains `source_loaded_at` so the accepted source batch remains visible.

The raw CSV load is still a full replacement and the incremental model deliberately
has no date watermark. It therefore processes the complete small payment source on
each run. This is a correctness step—safe inserts, corrections and repeatable
reruns—not a claim that the local pipeline now scans less data.

The controlled check uses a temporary database, reruns unchanged input, corrects
one failed attempt, adds one late retry and reruns twice. It selects the incremental
fact and its descendants together so the monthly aggregate and its reconciliation
test cannot observe different versions of the data.

## Day 27 addition

The incremental payment fact now distinguishes physical retention from current
source presence. If a previously observed key is absent from the latest complete raw
snapshot, the merge keeps one fact row, sets `is_source_present` to false and records
the first observation in `source_missing_since`.

Current monthly metrics filter to source-present rows. This avoids continuing to
report stale collections while preserving evidence that the key existed in an
earlier accepted snapshot. If the key reappears, the next merge sets it present and
clears the absence timestamp.

This is not a claim that the source confirmed a deletion. The local raw table is a
complete snapshot with no deletion event or reason code, so the model records
observed absence only.

## Day 28 addition

`audit.audit_subscription_payment_run` sits downstream of the incremental payment
fact. It appends one row for each dbt invocation that selects it, using dbt's
invocation ID as the run key. The row compares the current raw snapshot with both
the physical fact population and the source-present reporting population. It also
records absent-row, duplicate-key, presence-metadata and collection controls.

The model is append-only so an unchanged rerun leaves evidence rather than replacing
the previous result. The controlled scenario now creates six records: baseline,
insert-and-correction, unchanged rerun, source absence, restoration and final
unchanged rerun. Every state must reconcile before the scenario passes.

This audit is deliberately described as local operational evidence. It shares the
DuckDB file with the data, is created only when selected and records aggregate run
outcomes rather than row-level changes. It is not an immutable external monitoring
service.

## Day 29 addition

`audit.subscription_payment_run_delta` is a view over the append-only payment-run
audit. It orders runs by observation timestamp and invocation ID, then subtracts
the preceding run's raw, physical, current, absent and collected populations and
collection amount. The first recorded run has null differences, not a fabricated
zero baseline. Unchanged reruns produce zero net differences.

The controlled scenario verifies exact differences for a late payment and
correction, one source-absent payment, its restoration and unchanged reruns. The
view shows net movement, not the individual rows responsible for it. Persisted
DuckDB views refer to their source database catalogue, so the scenario copy now
preserves the original database filename when running under a custom local path.

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

## Day 31 addition

`mart.fct_loan_monthly_snapshot` starts the loan-reporting phase. It combines the
tested calendar, loan dimension and payment fact at one row per account and month
end. A loan first appears at the end of its origination month and continues through
the fixed reporting date, including months with no successful payment.

The model separates monthly completed-payment movement from cumulative payment
state. Its remaining balance is intentionally named as a calculation from original
balance, not a source-system balance. Building arrears at this point would require
inventing payment schedules and due dates, so those measures remain out of scope
until the synthetic source represents them explicitly.

## Day 32 addition

The generator now creates `loan_repayment_schedule.csv` alongside the loan source.
The shared contract and atomic loader treat it as the seventh fingerprinted CSV,
so a missing or structurally changed schedule rejects the whole replacement batch.

dbt materialises `mart.fct_loan_repayment_schedule` at one row per account and
instalment. It does not join the rows to payments yet. Keeping contractual dues and
payment attempts separate avoids silently assuming which payment settled which
instalment. Grain, sequence, due-date and full-principal reconciliation tests prove
the schedule before arrears logic is added.

## Day 33 addition

`mart.fct_loan_schedule_allocation` keeps the schedule grain and introduces one
declared modelling rule: completed payments dated on or before the fixed reporting
date are applied to due principal from the oldest instalment forward. Allocation
is capped at each due row and at total due principal. Future instalments remain at
zero even when a controlled scenario supplies more completed cash than is due.

This model deliberately sits between payment attempts and a later account-level
arrears view. It makes the allocation step inspectable and testable without
presenting the resulting uncovered principal as a lender balance. Failed payment
attempts remain in `fct_payment` but do not contribute to allocation.
