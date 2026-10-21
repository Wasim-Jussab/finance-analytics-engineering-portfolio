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
- Bound: 25 rows by default; callers may request 1 to 100.
- Filters: explicit UTC dates and one approved region only.
- Access: `POST /api/tools/execute`; no SQL or write action is accepted.

The response reports total exception count, returned count and whether the result
was truncated. Its evidence envelope binds the request, result and source snapshot.
That supports traceability but is not a digital signature or correctness guarantee.

## Deliberate boundary

Day 21 does not add this tool to the local intent classifier or answer renderer.
Direct deterministic execution is tested first. Natural-language routing and
grounded prose require their own training examples, held-out cases and release
evidence before being described as supported AI behaviour.
