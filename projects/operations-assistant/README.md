# Operations Intelligence

A local delivery-performance dashboard and governed analytics-assistant foundation. It highlights missed promises by region, then exposes the shipments behind each total.

## Current behaviour

- Deterministic synthetic data: 448 shipments across four regions and two weeks.
- Two approved read-only tools with validated arguments and weekly comparisons.
- Traceable snapshot/request evidence IDs and one consistent snapshot per tool call.
- Evidence-cited answer templates with executable grounding checks.
- Local intent-model routing with explicit abstention and validated dates.
- Versioned release policy over held-out and adversarial routing evidence.
- End-to-end evaluation from question routing to grounded answer evidence.
- On-time completion, late delivery and overdue-open counts.
- Regional breakdown, daily trend and inspectable exceptions.
- Tested period boundaries, denominator rules, empty results and invalid filters.

The project now executes a small local TF-IDF logistic model for intent routing. It is not an LLM: figures and prose still come from deterministic metric and template services, and reporting dates remain explicit validated fields.

## Metric definition

On-time completion rate is shipments delivered by their promised timestamp divided by all non-cancelled shipments due in the selected period. Late deliveries and overdue open shipments remain in the denominator. An empty denominator returns null.

Periods use the promised date in UTC: inclusive start, exclusive end. The snapshot is fixed at 28 September 2026 00:00 UTC; it is not live operational data.

## Run locally

Requires Python 3.11+ and Make. From the repository root:

```bash
cd projects/operations-assistant
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make test
make evaluate
make demo
```

Open `http://127.0.0.1:8000`; API documentation is at `/docs`. The application binds to localhost and needs no cloud account, paid API, employer information or credentials.

## Evidence and scope

For 21–27 September, the fixture produces 218 due shipments: 153 on time, 44 late and 21 overdue open. Six cancellations are excluded, producing a 70.18% on-time completion rate.

This is one row per shipment, with one shipment per order assumed. Cancellation reflects current snapshot status; historical cancellation timing, partial shipments, returns and causal explanations are outside this increment.

[Metric contract and validation](docs/metric-contract.md) · [Learning notes](notes/)

## Approved tools

`GET /api/tools` publishes the schema. `POST /api/tools/execute` accepts two approved tools, date boundaries and an optional region. Comparisons require equal, non-overlapping periods. SQL and unrecognised arguments are rejected. Responses identify the snapshot, request, contract and result; evidence IDs are not proof of correctness.

`POST /api/answers` renders a fixed, evidence-cited answer from either approved tool. The [grounding evaluation](docs/answer-grounding.md) executes four cases and records exact-claim and disclosure checks. Passing it does not constitute model evaluation because no model is invoked.

`POST /api/questions` adds the [local intent model](docs/local-intent-model.md). Fifteen held-out cases cover summaries, comparisons and unsupported requests. A separate [adversarial evaluation](docs/adversarial-evaluation.md) tests mixed requests and named risk slices. A [release gate](docs/routing-release-gate.md) reconciles both suites, while the [end-to-end evaluation](docs/end-to-end-question-evaluation.md) checks routing, tool execution and grounded evidence together. This is constrained local inference, not broad language accuracy or generative AI.
