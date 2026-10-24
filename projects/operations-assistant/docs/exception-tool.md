# Governed delivery-exception tool

## Business question

Which synthetic shipments were delivered late or remained open after their promise
within a selected promised-date period?

## Contract

- Grain: one row per shipment ID.
- Population: non-cancelled shipments promised from inclusive start to exclusive end.
- Outcomes: `late_delivered` or `overdue_open`.
- Delay: whole minutes from promise to delivery, or to the fixed snapshot for open rows.
- Ordering: overdue open first, then descending delay, promise and shipment ID.
- Bound: 25 rows by default; callers may request 1 to 100 and an offset from 0 to 10,000.
- Filters: explicit UTC dates, one approved region and one approved outcome (`late_delivered` or `overdue_open`).
- Access: `POST /api/tools/execute`; no SQL or write action is accepted.

The response reports total exception count, returned count and whether the result
was truncated. Its evidence envelope binds the request, result and source snapshot.
That supports traceability but is not a digital signature or correctness guarantee.

## Current inference boundary

The tool is available through direct execution and the evaluated question path. The local classifier selects the tool name only. Dates, region, outcome and limit are explicit typed fields and are never extracted or invented from prose.

Day 23 filters before counting and truncating, so 44 late-delivered plus 21 overdue-open rows reconcile to the 65 second-week exceptions. Grounding and end-to-end checks execute the overdue-open path. Metrics, evidence and prose remain deterministic; there is no generative inference.


## Pagination boundary

Pagination is offset-based because the source is a fixed local snapshot and the
sort has complete tie-breakers. Filtering and sorting happen before slicing.
`exception_count` remains the full filtered count; `returned_count`,
`has_more` and `next_offset` describe the current page.

The request evidence includes the explicit offset. A different offset therefore
produces a different evidence ID. This does not claim snapshot isolation across
future live refreshes or model-based parameter extraction.
