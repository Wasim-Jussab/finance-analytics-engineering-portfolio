# Operations Intelligence

[Verify saved investigation evidence offline](docs/offline-investigation-verification.md)
without opening DuckDB; integrity is not authenticity.

[Run a complete pinned exception investigation](docs/pinned-investigation.md)
using the local collector, with row caps and page-level evidence.

[Snapshot-pinned investigation requests](docs/snapshot-guard.md) prevent a caller
from silently combining pages from different snapshots when an expected ID is supplied.

A local delivery-performance dashboard and governed analytics-assistant foundation. It highlights missed promises by region, then exposes the shipments behind each total.

## Current behaviour

- Deterministic synthetic data: 448 shipments across four regions and two weeks.
- Three approved read-only tools with validated arguments, weekly comparisons and bounded exception detail.
- Traceable snapshot/request evidence IDs and one consistent snapshot per tool call.
- Evidence-cited answer templates with executable grounding checks.
- Swappable local intent-model adapter with explicit abstention and validated dates.
- Fingerprinted local model artifact with verify-before-load evaluation.
- Read-only runtime provenance for the active classifier and artifact fingerprint.
- Versioned release policy over held-out and adversarial routing evidence.
- End-to-end evaluation, privacy-conscious traces and a question-path release gate.
- Runtime readiness gate binding both approvals to the exact loaded artifact bytes.
- Optional hash-linked local decision audit with single-writer protection and no retained raw question text.
- Read-only audit integrity status without exposing ledger records or local paths.
- Standalone read-only ledger verification for operational checks without the API.
- Optional external head and count expectations to detect valid whole-file replacement.
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

`GET /api/tools` publishes the schema. `POST /api/tools/execute` accepts three approved tools, date boundaries and an optional region. Comparisons require equal, non-overlapping periods. SQL and unrecognised arguments are rejected. Responses identify the snapshot, request, contract and result; evidence IDs are not proof of correctness.

`POST /api/answers` renders a fixed, evidence-cited answer from each approved tool. The grounding evaluation executes six cases and records exact-claim and disclosure checks. Passing it alone does not constitute model evaluation because no model is invoked.

`POST /api/questions` adds the [local intent model](docs/local-intent-model.md) through a [local adapter](docs/local-model-adapter.md). Held-out and [adversarial](docs/adversarial-evaluation.md) suites feed the routing [release gate](docs/routing-release-gate.md); the [question-path gate](docs/question-release-gate.md) checks routing, tools, evidence and traces together. The [runtime readiness gate](docs/runtime-readiness.md) requires both approvals to name the exact verified classifier bytes. This is constrained local inference, not broad language accuracy or generative AI.

The [model artifact lifecycle](docs/model-artifact.md) records and verifies the fitted classifier bytes and compatible runtime metadata before loading. The held-out and adversarial reports name the exact artifact fingerprint used by the release gate. It only accepts locally generated trusted serialization; a matching hash does not make an untrusted pickle safe.

`GET /api/model` exposes the active [runtime provenance](docs/model-provenance.md), including the local inference boundary and whether a verified artifact was loaded. It does not expose training examples or model weights.

`OPERATIONS_DECISION_AUDIT=reports/decision-audit.jsonl` enables the optional
[local decision audit](docs/decision-audit.md). It binds answered and blocked
decisions to their model artifact and evidence, but is not immutable storage.
`GET /api/audit/status` verifies that ledger and returns only integrity metadata.
The same verification can run without the web service:

```bash
python -m operations_assistant.audit_cli \
  --path reports/decision-audit.jsonl \
  --expected-head-sha256 <trusted-head> \
  --expected-record-count <trusted-count>
```
An operator can supply an independently retained expected head and record count to
detect replacement by a shorter, internally valid ledger.

[Days 11–15 local-inference review](docs/local-inference-review.md)

[Days 16–20 decision-evidence review](docs/decision-evidence-review.md)

## Day 21 exception-detail boundary

`delivery_exceptions` is a direct approved tool for shipment-grain investigation.
It returns non-cancelled late-delivered and overdue-open rows from an explicit
promised-date period, with optional governed region and outcome filters and a limit from 1 to 100. Overdue
open rows sort first, followed by greatest observed delay and stable tie-breakers.

The tool is read-only, parameterised and evidence-bound to one snapshot. It is
available through natural-language routing and deterministic answer templates,
with explicit caller-supplied dates and filters.


## Day 22 evaluated exception questions

The local classifier now has an approved `delivery_exceptions` label for explicit
row-level requests. A question must still provide governed dates and an optional
region and limit; the model does not extract or invent those parameters. The
deterministic answer reports the full exception count, bounded returned rows,
truncation state and evidence ID.

The updated artifact, held-out, adversarial, grounding and end-to-end suites must
all pass before runtime readiness is described as ready. This remains narrow local
intent classification, not generative answering or broad language understanding.


## Day 23 explicit outcome filter

Callers can now select `late_delivered` or `overdue_open` as a typed field on the direct tool and question endpoint. Filtering happens before counts, truncation and evidence are produced. The fixed second-week fixture reconciles to 44 late-delivered plus 21 overdue-open exceptions.

The model still selects only the approved tool. It does not infer outcome, dates, region or limit from prose. Grounding and end-to-end suites execute the overdue-open path; this adds governed retrieval, not a new AI capability.


## Day 24 stable exception pagination

`delivery_exceptions` now accepts an explicit offset from 0 to 10,000 after the
existing deterministic sort and before the row limit. Responses return the full
filtered exception count, current offset, returned count, `has_more` and
`next_offset`. The offset is part of the evidence-bound request.

Grounding and end-to-end evaluation execute the second page of overdue-open
exceptions. The model still selects only the approved tool; offset, limit, dates,
region and outcome remain typed caller inputs rather than inferred parameters.

## Completed exception-investigation milestone

The [review and runnable API example](docs/exception-investigation-review.md)
explain the three tools, pagination reconciliation and actual inference boundary.
The full-pagination API test reconstructs all exceptions and both outcome subsets
without gaps or duplicates, including exact-boundary and exhausted-offset cases.
