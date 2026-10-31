# Operations Intelligence

A local delivery-performance dashboard and governed analytics-assistant foundation.
It answers a practical question: which shipments missed their promised delivery,
and can the figures and underlying exceptions be traced to one source snapshot?

The only model is a local **TF-IDF/logistic intent classifier** selecting an
approved tool. This is not an LLM or generative assistant. Dates, regions, outcomes
and pagination are explicit typed inputs; metrics and answer prose are deterministic.

## Demonstrable behaviour

- Three approved read-only tools: delivery summary, period comparison and exceptions.
- Evidence-cited answers, bounded exception pages and optional snapshot-ID guards.
- Complete pinned investigations with row caps and offline report verification.
- Canonical report digests with optional independently retained expectations.
- Fingerprinted local model artifacts, held-out/adversarial evaluations and
  release gates bound to the exact active classifier bytes.
- Optional local decision ledger with standalone integrity checks.

The [investigation handoff review](docs/investigation-handoff-review.md) includes
runnable collection/verification commands, expected results and the trust boundary.
Hashes check integrity, not authenticity, immutable storage or business correctness.

## Metrics and example

Grain: one row per shipment, assuming one shipment per order. On-time completion
rate is shipments delivered by their promised timestamp divided by all non-cancelled
shipments due in the period. Late deliveries and overdue-open shipments remain in
the denominator; an empty denominator returns null.

Periods use promised date in UTC: inclusive start, exclusive end. The fixed synthetic
snapshot is **28 September 2026 00:00 UTC**, not live operational data. For
21–27 September it contains 218 due shipments: 153 on time, 44 late and 21 overdue
open. Six cancellations are excluded; on-time completion is 70.18%.

Historical cancellation timing, partial shipments, returns, causal explanations
and production-scale performance are outside scope.

## Run locally

Requires Python 3.11+ and Make. From the repository root:

```bash
cd projects/operations-assistant
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make verify
make demo
```

Open `http://127.0.0.1:8000`; API documentation is at `/docs`.
`make verify` runs tests, creates/verifies the local classifier artifact, executes
grounding and classifier evaluations, then checks release/runtime readiness.
No cloud account, paid API, employer information or credentials are required.

## Inspect the contracts

- [Untrusted tool proposals](docs/tool-proposals.md): a validation boundary, not LLM inference.
- [Metric definitions](docs/metric-contract.md) and [exception API review](docs/exception-investigation-review.md)
- [Snapshot guard](docs/snapshot-guard.md), [collector](docs/pinned-investigation.md),
  [offline verifier](docs/offline-investigation-verification.md) and [digest anchor](docs/report-digest-anchor.md)
- [Local model adapter](docs/local-model-adapter.md), [artifact lifecycle](docs/model-artifact.md)
  and [runtime provenance](docs/model-provenance.md)
- [Routing gate](docs/routing-release-gate.md), [question gate](docs/question-release-gate.md)
  and [runtime readiness](docs/runtime-readiness.md)
- [Decision audit](docs/decision-audit.md), [inference review](docs/local-inference-review.md),
  [decision-evidence review](docs/decision-evidence-review.md) and [learning notes](notes/)

The package remains independently installable inside the finance repository.
