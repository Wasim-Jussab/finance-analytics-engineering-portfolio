# Day 25 — one event feed, without flattening the meaning

Today I closed the historical-modelling milestone by adding one reporting feed over
the two event types built this week.

`fct_subscription_history_event` unions observed status changes and source removals.
It gives a downstream report one grain and one event timestamp, but it preserves the
important distinction between them. A Status Change can carry a new business status
and event date. A Source Removal keeps the last observed status and has no invented
business event date.

I prefix the component version ID with the event type to form `event_id`. The same
agreement version could first represent a status change and later be the final
version before removal, so using the dbt SCD ID alone would not guarantee uniqueness
across both event types.

The clean feed is empty because the deterministic build has only initial states. The
controlled status scenario should produce one Status Change event, while the removal
scenario should produce one Source Removal event. Both scenarios check the unified
row as well as their component fact.

The first integrated CI run caught an ordering issue in the controlled scenario.
Selecting the component with `dbt build` also selected a downstream reconciliation
test before the unified event model had been refreshed. I changed the scenario to
run the component first, then build and test the unified consumer. The failed run is
kept in the pull-request history because it reflects a real dependency lesson.

I also added a short runbook covering normal execution, interpretation, controlled
checks and failure response. The most important operating rule is to preserve failing
evidence long enough to understand it instead of immediately rebuilding a green
database.

This milestone now demonstrates snapshot design, change detection, hard-delete
handling, downstream event modelling and reconciliation. It does not claim that
observation timestamps are contractual effective dates or that a local DuckDB file
is a production history service.

## Verified result

The corrected workflow passed the full clean build with 12 models, two snapshots and 221 data tests—236 results including the checkpoint hook. The cancellation and removal scenarios each passed the 14-result selected build for the unified event feed. Python finished with 20 passing tests and Ruff found no issues.

The clean feed contains zero events, the cancellation scenario contains one `Status Change`, and the removal scenario contains one `Source Removal`. That is the behaviour I intended to prove.

