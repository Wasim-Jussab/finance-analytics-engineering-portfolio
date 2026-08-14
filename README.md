
# Finance analytics engineering practice

I am using this repository to work through the parts of analytics engineering that I want more evidence of publicly.

In my current work I already use SQL, Power BI, Redshift, AWS Glue/Python, reporting models, regulatory reporting and reconciliations. I do not want to upload work data or pretend that a small GitHub project is the same as running a production platform. The plan is to build a small synthetic finance data system, make the decisions visible and keep notes on what I am learning.

## What I am trying to learn

The main gaps I want to practise are:

- Structuring a Python data project properly
- Building transformations in dbt
- Testing data rather than only checking the final report
- Making pipelines repeatable and safe to rerun
- Using GitHub Actions for basic CI
- Designing orchestration and cloud versions of a local pipeline
- Explaining the decisions clearly enough for another analyst or engineer to review

## What the project will cover

The examples will be based on problems I understand, but the data will be generated:

1. Subscription payments and revenue reporting
2. Regulatory-style submission rules and exclusion reasons
3. Loan portfolio snapshots and reconciliation
4. A small governed reporting layer for BI

The order may change when I find something that needs more work. I would rather record that than make the project look more finished than it is.

## Cost and data boundaries

This is a local-first project. I will not create AWS resources, use employer data, add personal identifiers, commit credentials or use paid APIs. The GitHub repository is public so the work can be reviewed, and generated data will stay out of the repository where it is not needed.

## Current state

Day 1 is mainly setup. I have written down the first version of the data grain, the rough architecture and the things I want to investigate. There is a very small Python package and smoke test, but there is no useful dataset or business output yet.

## Repository structure

~~~text
docs/                  Notes about the design and data
notes/                 Short learning notes by day
data/                  Local generated data, excluded where appropriate
src/finance_portfolio/ Reusable Python code
tests/                 Automated checks
pyproject.toml         Python project and tooling configuration
Makefile               Short repeatable commands
~~~

## Rough sequence

- First, generate deterministic synthetic customers, loans, subscriptions and payments.
- Then, load and inspect the data before writing reporting logic.
- Add dbt models and tests once the grain is understood.
- Add reconciliation and failure cases rather than only successful examples.
- Add CI and an orchestration design after the local process works.
- Finish with a reporting layer and a review of what I would change in a real system.

This is a learning project and a public record of the work. It is not a claim that every tool listed here has already been used in production.
