
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
