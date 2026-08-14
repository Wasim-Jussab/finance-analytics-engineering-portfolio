
# Architecture

## Day 1 target architecture

The portfolio is designed as a local-first analytical platform. It will produce the same logical layers that would be used in a cloud warehouse while avoiding billable infrastructure.

~~~mermaid
flowchart TD
    A["Synthetic source files"] --> B["Python ingestion and validation"]
    B --> C["Raw local layer"]
    C --> D["dbt staging models"]
    D --> E["Intermediate business logic"]
    E --> F["Reporting marts"]
    F --> G["Quality and reconciliation checks"]
    G --> H["BI-ready extracts"]
~~~

## Logical layers

| Layer | Purpose | Expected controls |
|---|---|---|
| Source | Synthetic loans, customers, payments and subscriptions | Schema and licensing checks |
| Raw | Preserve source-shaped records | Load timestamp, source identifier, row count |
| Staging | Standardise names, types and dates | Type checks, required-field checks |
| Intermediate | Apply reusable business logic | Grain and join validation |
| Marts | Produce reporting-ready entities | Uniqueness, relationships, metric tests |
| Quality | Prove output is complete and reconcilable | Counts, balances, exclusions and variance thresholds |
| BI output | Serve governed metrics | Definitions, filter behaviour and security design |

## Cloud-compatible mapping

The local implementation will later be documented against the following target pattern:

| Local concept | AWS-compatible pattern |
|---|---|
| Local files | S3 landing zone |
| Python ingestion | AWS Glue Python/Spark job |
| DuckDB analytical store | Redshift warehouse |
| dbt transformations | dbt models targeting Redshift |
| Local scheduled execution | Airflow or managed orchestration |
| Local tests | GitHub Actions CI and deployment gates |

No AWS resources will be created for this portfolio unless the scope is explicitly changed and costs are confirmed first.

## Design principles

1. **Grain before code** — every table and model must state its grain.
2. **Source of truth before calculation** — use authoritative fields where available.
3. **Auditability before convenience** — retain reason codes and reconciliation outputs.
4. **Idempotency** — rerunning a load must not duplicate records.
5. **Fail loudly** — invalid data should produce a useful failure, not a misleading report.
6. **Portable execution** — the core pipeline must run without a cloud account.
