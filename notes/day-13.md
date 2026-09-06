# Day 13 — making subscription pricing visible

**Date:** 6 September 2026

The billing amounts added on Day 10 were documented, but they still lived inside a Python lookup. That made the generated events repeatable without making the pricing assumption part of the data model. Today I moved the four synthetic product and billing-frequency combinations into their own source table and dbt dimension.

Each agreement now has a `subscription_plan_id`. Billing attempts take their amount from that plan, and the monthly aggregate gets product and frequency through the same relationship. I kept product and frequency on the agreement because they are already useful descriptive fields, but added a test so the duplicated values cannot quietly disagree with the plan.

The clean run produced four plans, 20 agreements with valid plan references and 150 billing attempts matching their plan amount. All 8 models and 107 dbt tests passed, giving 115 successful dbt resources. All 14 Python tests, Ruff and dbt documentation generation also passed.

I changed one temporary billing attempt by £0.01 to prove the contract. The targeted test returned exactly one mismatch and a non-zero exit code. I rebuilt the fact afterwards and reran the clean suite.

The first documentation run also exposed a local DuckDB WAL replay conflict after the successful build. Rebuilding and checkpointing the disposable database allowed the catalogue to generate. I added `*.wal` to `.gitignore` so that recovery state cannot leak into a commit.

The four prices are arbitrary project values. They are not copied from an employer and are not intended to represent market pricing. The plan dimension is also only a current-state catalogue: it cannot yet answer which price applied before a change because it has no effective dates. I would add effective-from and effective-to dates when the project introduces plan changes rather than pretending that history already exists.
