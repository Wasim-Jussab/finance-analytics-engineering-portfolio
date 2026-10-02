# Operations Intelligence

A local delivery-performance dashboard with a read-only metric API. This is the reporting foundation for a later governed analytics assistant.

I wanted a second project that shows someone using data to investigate a problem. The first view highlights missed delivery promises by region, then exposes the shipments behind the totals.

## Current behaviour

- Deterministic synthetic data: 448 shipments across four regions and two weeks.
- Date and region filters shared by the dashboard and API.
- Two approved read-only tools with validated arguments and weekly comparisons.
- On-time completion, late delivery and overdue-open counts.
- Regional breakdown, daily trend and inspectable exception records.
- Validation before atomic snapshot replacement.
- Tested period boundaries, denominator rules, empty results and invalid filters.

**There is no language model in this increment.** The figures come from the metric service. The approved metric tools are now available; adding and evaluating local model answers is the next stage.

## Metric definition

On-time completion rate is shipments delivered by their promised timestamp divided by all non-cancelled shipments due in the selected period. Late deliveries and overdue open shipments remain in the denominator. An empty denominator returns null.

Periods use the promised date in UTC: inclusive start, exclusive end. The snapshot is fixed at 28 September 2026 00:00 UTC; it is not live operational data.

## Run locally

Requires Python 3.11+ and Make. From the repository root, using a POSIX shell:

```bash
cd projects/operations-assistant
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make test
make demo
```

Open `http://127.0.0.1:8000`. Interactive API documentation is at `/docs`.

The application binds to localhost. It requires no cloud account, paid API, employer information or credentials.

## Evidence and scope

For 21–27 September, the fixture produces 218 due shipments: 153 on time, 44 late and 21 overdue open. Six cancellations are excluded, producing a 70.18% on-time completion rate.

This is one row per shipment, with one shipment per order assumed. Cancellation reflects current snapshot status; historical cancellation timing, partial shipments, returns and causal explanations are outside this increment.

[Metric contract and validation](docs/metric-contract.md) · [First learning note](notes/day-01.md)


## Approved tools

`GET /api/tools` publishes the request schema. `POST /api/tools/execute` accepts `delivery_summary` or `compare_delivery_periods`, date boundaries and an optional region. Comparisons require equal-duration, non-overlapping periods and report rate changes in percentage points. SQL and unrecognised arguments are rejected. Try the endpoints in `/docs`. These tools still use deterministic calculations.
