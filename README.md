
# Finance Analytics Engineering Portfolio

A reproducible, cost-controlled portfolio demonstrating the transition from production Data Analyst / BI delivery into analytics engineering.

The portfolio uses synthetic finance data and locally executable tools. It is deliberately based on realistic problems—subscriptions, regulatory reporting, loan portfolios, reconciliations and governed BI—without using confidential employer data.

## Current status

**Day 1 — repository foundation**

The repository currently contains the project scope, engineering standards, architecture, data-contract principles, 90-day roadmap and a minimal Python test scaffold.

## Portfolio objectives

This portfolio will demonstrate:

- Reliable ingestion and transformation
- SQL data modelling and warehouse design
- dbt project structure, tests and documentation
- Reconciliation and data-quality controls
- Historical modelling and incremental processing
- CI checks and reproducible local execution
- Orchestration design
- Redshift-compatible SQL and AWS-compatible patterns
- Governed BI outputs and clear business definitions

The aim is to make engineering decisions inspectable, not to create disconnected tutorial projects.

## Planned portfolio projects

1. **Subscription revenue pipeline**  
   Synthetic subscription, payment and creditor data transformed into auditable reporting marts.

2. **Regulatory reporting quality framework**  
   Explicit eligibility rules, exclusion reasons, source-to-output reconciliation and validation evidence.

3. **Loan portfolio and ECL-style model**  
   Monthly snapshots, arrears, repayment behaviour, yield assumptions and balance reconciliation.

4. **Governed BI delivery**  
   A semantic model and finance/risk reporting specification built on the curated warehouse outputs.

## High-level architecture

~~~mermaid
flowchart TD
    A["Synthetic source data"] --> B["Python ingestion"]
    B --> C["Local raw storage"]
    C --> D["SQL and dbt transformation"]
    D --> E["Quality and reconciliation checks"]
    E --> F["Curated reporting marts"]
    F --> G["BI-ready outputs"]
~~~

The local implementation comes first. AWS Glue, S3 and Redshift-compatible versions will be represented through portable code and documented deployment patterns without creating billable cloud resources.

## Cost and privacy controls

- Synthetic or public data only
- No employer data, personal identifiers or production credentials
- No AWS resources created
- No paid APIs or services
- Local execution using free/open-source tooling
- Public GitHub repository with standard CI only
- No secrets committed to the repository

## Repository structure

~~~text
.
├── docs/                  # Architecture, contracts, roadmap and decisions
├── data/
│   ├── raw/               # Generated or public inputs; no sensitive data
│   └── processed/         # Generated outputs; excluded from Git
├── src/
│   └── finance_portfolio/ # Reusable Python package code
├── tests/                 # Automated validation
├── .github/workflows/     # CI added during the roadmap
├── AGENTS.md              # Engineering rules for future changes
├── Makefile               # Repeatable local commands
└── pyproject.toml         # Project metadata and tooling configuration
~~~

## 90-day delivery model

The portfolio is built through consistent focused sessions rather than 90 unrelated projects:

- Days 1–15: engineering foundations
- Days 16–30: dbt and subscription analytics
- Days 31–45: testing, quality and CI
- Days 46–60: orchestration and cloud-compatible design
- Days 61–75: loan risk, reconciliation and BI
- Days 76–90: documentation, review and interview readiness

## Validation standard

Every material transformation should eventually have:

- Defined grain
- Explicit key and relationship assumptions
- Duplicate and NULL checks
- Reconciliation controls
- Repeatable tests
- Documented business definitions
- Clear failure behaviour

This repository is a learning and evidence project. It must not be presented as production employment experience.
