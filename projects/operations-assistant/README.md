# Operations Intelligence

A local delivery-performance dashboard and governed analytics-assistant foundation. It highlights missed promises by region, then exposes the shipments behind each total.

## Current behaviour

- Deterministic synthetic data: 448 shipments across four regions and two weeks.
- Two approved read-only tools with validated arguments and weekly comparisons.
- Traceable snapshot/request evidence IDs and one consistent snapshot per tool call.
- Evidence-cited answer templates with executable grounding checks.
- Swappable local intent-model adapter with explicit abstention and validated dates.
- Fingerprinted local model artifact with verify-before-load evaluation.
- Read-only runtime provenance for the active classifier and artifact fingerprint.
- Versioned release policy over held-out and adversarial routing evidence.
- End-to-end evaluation, privacy-conscious traces and a question-path release gate.
- Runtime readiness gate binding both approvals to the exact loaded artifact bytes.
- Optional hash-linked local decision audit without retained raw question text.
- On-time completion, late delivery and overdue-open counts.
- Regional breakdown, daily trend and inspectable exceptions.
- Tested period boundaries, denominator rules, empty results and invalid filters.

The project executes a local TF-IDF logistic model through a tested adapter. It is not an LLM: figures and prose remain deterministic, and dates stay explicit.

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
make model-artifact
make model-artifact-verify
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

`POST /api/questions` adds the [local intent model](docs/local-intent-model.md) through a [local adapter](docs/local-model-adapter.md). Held-out and [adversarial](docs/adversarial-evaluation.md) suites feed the routing [release gate](docs/routing-release-gate.md); the [question-path gate](docs/question-release-gate.md) checks routing, tools, evidence and traces together. The [runtime readiness gate](docs/runtime-readiness.md) requires both approvals to name the exact verified classifier bytes. This is constrained local inference, not broad language accuracy or generative AI.

The [model artifact lifecycle](docs/model-artifact.md) records and verifies the fitted classifier bytes and compatible runtime metadata before loading. The held-out and adversarial reports name the exact artifact fingerprint used by the release gate. It only accepts locally generated trusted serialization; a matching hash does not make an untrusted pickle safe.

`GET /api/model` exposes the active [runtime provenance](docs/model-provenance.md), including the local inference boundary and whether a verified artifact was loaded. It does not expose training examples or model weights.

`OPERATIONS_DECISION_AUDIT=reports/decision-audit.jsonl` enables the optional
[local decision audit](docs/decision-audit.md). It binds answered and blocked
decisions to their model artifact and evidence, but is not immutable storage.

[Days 11–15 local-inference review](docs/local-inference-review.md)
