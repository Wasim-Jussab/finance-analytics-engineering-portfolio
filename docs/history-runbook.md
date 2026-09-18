# Historical modelling runbook

This runbook covers the local dbt snapshots and the reporting models that consume
them. All examples use synthetic data and a local DuckDB database.

## Normal run

```bash
make pipeline
make check
```

The pipeline loads the current raw batch, checks freshness, runs both snapshots,
builds the marts and executes the data tests. A successful clean run should contain
four current plan versions, twenty current agreement versions and no history events.

## Interpreting the models

- `history.subscription_plan_history` retains observed plan definitions.
- `history.subscription_agreement_history` retains observed agreement states.
- `mart.fct_subscription_status_change` contains business status transitions.
- `mart.fct_subscription_source_removal` contains keys absent from the latest source.
- `mart.fct_subscription_history_event` provides one feed over both event types.

Snapshot validity timestamps mean “first observed by this pipeline”. They are not
contractual effective dates. A Source Removal is an operational observation and must
not be relabelled as Cancelled without upstream evidence.

## Controlled checks

```bash
make snapshot-history-check
make subscription-history-check
make subscription-removal-check
```

Each command checkpoints the clean database, copies it to a temporary location,
applies one controlled change and discards the copy afterwards.

## Failure response

1. Identify whether the failure is in raw freshness, snapshot history, a component
   fact or the unified event feed.
2. Keep the failing database or dbt test output long enough to inspect the affected
   key; do not immediately rebuild over the evidence.
3. Compare the current raw row, all snapshot versions and the relevant component
   fact.
4. Confirm whether the source supplied an event date or deletion reason before
   assigning business meaning.
5. Rebuild from deterministic seed data and rerun the complete suite after the cause
   is understood.

## Known operational limits

The local snapshot store and marts share one DuckDB file. There is no upstream change
sequence, immutable deletion log, contractual effective-date source, retry policy or
alert route. The project proves modelling and control behaviour, not a deployed
production history service.
