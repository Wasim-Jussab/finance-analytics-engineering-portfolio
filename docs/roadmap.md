
# Working plan

This is the order I currently expect to follow. It is not meant to imply that I already know every tool in advance.

## First 15 days — get a trustworthy local dataset

- Generate synthetic data with a fixed seed
- Inspect row counts, keys, dates and relationships
- Add deliberately bad records so the checks have something to find
- Load the data locally
- Record the first changes to the data contract

## Days 16–30 — build the first reporting use case

- Create staging and reporting models
- Learn the basic dbt project structure
- Build subscription and payment outputs
- Test grain, duplicates and important business rules
- Explain one result from source record to final metric

## Days 31–45 — make it less fragile

- Add Python tests and data-quality checks
- Add reconciliation outputs
- Test reruns and partial failures
- Add GitHub Actions once the local commands are stable

## Days 46–60 — investigate orchestration and cloud patterns

- Create a small orchestration example
- Add retry and backfill thinking
- Map the local process to Glue, S3 and Redshift
- Document what I would monitor in production

## Days 61–75 — loan and reporting work

- Add portfolio snapshots
- Add arrears and repayment behaviour
- Build an ECL-style example with clearly stated assumptions
- Produce a reporting layer that could feed BI

## Days 76–90 — review the work properly

- Revisit joins, grain, NULLs, dates and status logic
- Try to break the pipeline
- Improve the documentation based on what actually happened
- Write a short explanation of the trade-offs and remaining gaps

The plan will change if the data exposes a better question. That change is part of the project rather than something to hide.

## Thirty-day checkpoint

The first month moved faster than this initial outline in some areas. I completed
the local dataset, ingestion controls, subscription reporting, dbt history,
incremental payment handling and CI within Days 1–30. I did not deploy cloud
infrastructure or claim production-scale performance.

The next phase will move to the loan side of the dataset: dated portfolio snapshots,
arrears and repayment behaviour, controlled financial assumptions and a reporting
layer suitable for BI. Orchestration will be added only when there are enough
independent tasks to make scheduling, retries and backfills meaningful.

Day 31 added the first dated loan-portfolio model: complete month-end rows with
monthly and cumulative completed-payment movement. Arrears remains pending because
the source contract does not yet contain a repayment schedule or due amounts.

Day 32 added that missing schedule contract. Every synthetic loan now has an
explicit term and principal-only monthly due rows that reconcile to original
balance. Arrears remains a separate next step because payment allocation, grace
periods, interest and fees still need an honest modelling decision.

Day 33 made the first of those decisions explicit. Completed payments are allocated
to due principal oldest first, with future instalments and any excess payment kept
outside the allocation. The next loan-reporting step can summarise this tested fact
at account and reporting-date grain, while continuing to avoid claims about lender
accounting balances or contractual days past due.

Day 34 added that account-level summary. It reconciles due, allocated, uncovered
and future principal and exposes the oldest uncovered due date. A days-past-due
proxy is clearly separated from source loan status because the project still lacks
the contractual rules needed for a production arrears measure. The next step is to
aggregate the governed account positions for monthly portfolio reporting.

Day 35 completed that step with a monthly product aggregate. It retains complete
originated-account coverage, reconciles to account-month detail and calculates its
coverage ratio from portfolio totals rather than averaging account percentages.
The loan milestone is reviewed in `docs/loan-reporting-review.md`; contractual
arrears and historical active populations remain explicit gaps.

Day 36 starts the operational phase now that generation, ingestion, freshness and
transformation are genuinely separate stages. A small Python runner makes their
dependencies and stop-on-failure behaviour explicit and writes a local run report.
It does not yet retry or backfill work, and it does not introduce a scheduler
service solely for appearance.

Day 37 adds single-run concurrency control around that entry point. The lock is
created atomically before generation, released only by its owner and tested across
success and failure paths. Stale-lock recovery remains manual because deleting a
lock based only on age could allow a second writer into a slow but valid run.

Day 46 begins a pipeline-evidence milestone. A reconciled index ties the latest
run pointer to its archived run, health decision, policy and dbt artifacts using
exact fingerprints. It improves audit navigation without claiming immutable
storage or external attestation; independent pack verification remains next.
