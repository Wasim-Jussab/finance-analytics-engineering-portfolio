# Exception investigation: milestone review

## Demonstration

Run `make verify` in this package, then `make demo`. In `/docs`, call
`POST /api/tools/execute` with:

```json
{"name":"delivery_exceptions","start":"2026-09-21","end":"2026-09-28","outcome":"overdue_open","limit":7,"offset":0}
```

Follow `next_offset` until `has_more` is false. The three pages reconstruct all 21
overdue-open shipments in the fixed fixture. All exceptions total 65, comprising
44 late deliveries and 21 overdue-open shipments. Cancelled shipments are excluded.

The API regression test walks the all-outcome and both filtered populations,
reconciles every row in order and checks unique shipment IDs, stable full counts,
snapshot identity, distinct request evidence and an exhausted offset.

## What inference actually does

The locally fitted TF-IDF/logistic-regression classifier chooses one of three
approved tools or abstains. It does not generate SQL, extract dates or filters,
calculate metrics, generate prose or decide treatment priority. Typed parameters
remain caller-supplied. Grounding tests execute deterministic answers; routing
and end-to-end tests actually execute the classifier through its adapter.

## Limits

This is a small, fixed synthetic snapshot. Offsets are not a production cursor
protocol. If snapshot IDs differ between pages, a caller must restart rather
than combine results. The current application does not enforce that across calls.
Evidence hashes establish identity, not business correctness or immutable storage.
Observed delay is descriptive, not a contractual service breach or causal finding.

The first Day 24 CI run failed lint on one long line, subsequently corrected.
That failure is retained in the PR record; it was not an intentional exercise.
