# Swappable proposal producer and executed classifier baseline

`ProposalAdapter.propose(scope)` returns untrusted JSON text. The new
`plan_with_adapter(scope, adapter, router)` passes that output through existing
scope validation and governed-router agreement before returning a request and
routing evidence. Invalid output, scope changes, wrong tools and policy blocks
remain failures. No tool is executed by the planner.

`ClassifierProposalAdapter` is the implemented local baseline. It runs the existing
classifier/policy, serialises its approved request and then undergoes the same
validation as another producer. In this baseline configuration the classifier is
called twice: once to propose and once to authorise. That is deliberate, measurable
overhead for the separation of responsibilities—not a performance improvement.

Tests execute the real classifier adapter and a synthetic read-only query with
218 due shipments and unchanged database bytes. Recorded adversarial outputs are
explicitly test doubles, not language-model inference or evaluation. A swappable
interface alone is not evidence that another model works.

This helper is not a new public API and does not load a generative model. Production
integration must retain artifact verification, release/readiness and audit checks.
An adapter is trusted local application code: the protocol cannot sandbox arbitrary
Python or prevent an implementation from attempting side effects. Only its returned
tool proposal is treated as untrusted data. Existing classifier inference remains
the only implemented inference; metrics and answers remain deterministic.
