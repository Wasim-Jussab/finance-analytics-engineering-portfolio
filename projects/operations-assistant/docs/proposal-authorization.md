# Require governed routing agreement for a proposed call

`authorize_proposal(raw, scope, router)` first runs the existing `LocalIntentModel`
classifier and policy. Abstained/blocked questions are rejected even if the proposed
JSON describes a valid tool. Then Day 31's validator checks explicit argument scope,
and the complete proposed request must match the governed router's approved request.

This addresses a separate failure from invalid JSON: a proposal can be perfectly
well formed but select the wrong tool. The regression shows an exception-list
proposal passing structural validation for a summary question but failing router
agreement. Other cases cover write requests, out-of-domain questions, forecasts
and changed date boundaries. The positive path executes the actual local classifier,
then reads the synthetic service: 218 due shipments and unchanged database bytes.

The helper returns a validated request and routing evidence; it does not execute
the tool. It is not a new public API and does not replace the application's existing
artifact, release, readiness or audit controls. Production wiring must retain those
checks. Agreement with this baseline does not prove broad semantic accuracy, and
using it as a veto can preserve the baseline classifier's mistakes and limitations.

No generative model or language-model evaluation is added. This is executed local
intent classification with deterministic policy and validation. A future proposer
must be compared against this baseline rather than silently granted extra authority.
