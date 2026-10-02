# Delivery metric contract

## Grain and cohort

The source has one row per shipment ID. The fixture assumes one shipment per order.
No real customers, addresses, employer rules or courier data are used.

The period is selected by promised timestamp in UTC, not delivery timestamp.
Start is inclusive; end is exclusive. Only complete days within the fixed snapshot
are accepted. Shipment dispatch must precede the promise and the snapshot.

## Population and outcome

- Current Cancelled rows are excluded and counted separately.
- Non-cancelled rows delivered at or before promise are on time.
- Non-cancelled rows delivered after promise are late delivered.
- Non-cancelled rows with no delivery timestamp are overdue open.

The selected promised-date population is already due by the snapshot.
Due = on time + late delivered + overdue open.
Observed rows = due + cancelled.
On-time rate = on time / due, or null when due is zero.

A delivery exactly at the promise counts as on time. A promise exactly at the
exclusive end is excluded. Unknown regions and malformed dates are rejected.
Region and period inputs are bound parameters; no endpoint accepts SQL.

## Snapshot checks

IDs must be unique; statuses and regions belong to declared sets. Timestamps must
be timezone-aware. Delivered status requires a delivery timestamp, and other
statuses cannot contain one. Deliveries cannot precede dispatch or occur after the
snapshot. An invalid replacement leaves the existing valid snapshot intact.

The source is accepted only through the generator/validator in this increment.
The service is read-only; the database is not an authenticated production platform.

## Seed-42 evidence

| Period, end exclusive | Due | On time | Late delivered | Overdue open | Cancelled | Rate |
|---|---:|---:|---:|---:|---:|---:|
| 14–21 September 2026 | 213 | 176 | 27 | 10 | 11 | 82.63% |
| 21–28 September 2026 | 218 | 153 | 44 | 21 | 6 | 70.18% |

Each region and day sums back to the period counts. The overall rate uses total
counts, not the average of regional or daily rates.

The generator intentionally increases late delivery probability in Midlands in
the second week. That is a synthetic scenario, not evidence about a real operation.
The dashboard identifies observed performance; it cannot infer a business cause.

## Validation

Five tests cover deadline equality, exclusive boundaries, late/open denominator
retention, cancellation exclusion, empty populations, region filtering,
reproducibility, breakdown reconciliation, duplicate/chronology rejection,
replacement preservation, HTTP filter validation, missing data and dashboard delivery.

## Next increments

1. Add an explicit period-comparison tool with evidence.
2. Define permitted assistant questions and abstention cases.
3. Add a local model adapter with a deterministic fallback visibly labelled.
4. Evaluate numerical accuracy and evidence against a held-out question set.
5. Measure latency and document failure behaviour.

Model inference and evaluation scores will only be reported after actual execution.



## Period comparison tools

Tools share the dashboard service. Compare equally long, non-overlapping promised-date cohorts using the same region and fixed observation timestamp. Recompute each rate from its own counts; subtract rates and multiply by 100 for percentage-point change. Do not sum regional rate changes or interpret count differences as causal effects. Empty-period rate changes are null. Historical point-in-time performance cannot be reconstructed from this single snapshot. Requests reject unsupported tool names, extra keys and arbitrary SQL.
