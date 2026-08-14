
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
