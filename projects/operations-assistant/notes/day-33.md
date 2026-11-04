# Operations Day 33 — separate proposal production from authorisation

2 November 2026

I added a small proposal-adapter protocol and a working classifier-backed baseline.
The planner validates the returned JSON and requires the existing governed router
to agree. Test doubles return malformed or inappropriate proposals; they are not
described as model executions.

The real baseline executes the existing classifier twice, for production and veto.
That cost is explicit rather than being presented as an optimisation. An adapter
is trusted application code, not a sandbox; validation applies to its output.
No new endpoint, generative model, release bypass or tool-execution authority is
introduced. This is a tested integration seam, not generative inference.

## Local verification

The complete package gate passed: 148 tests, grounding 6/6, held-out routing
18/18, adversarial 27/27, end-to-end questions 10/10, both release gates and
runtime readiness. Ruff passed. All seven targeted adapter cases passed separately.
The real adapter/service test reconciled 218 due shipments and preserved source
bytes. The existing TestClient dependency warning remains. No generative model
was loaded or evaluated, and no adapter performance improvement is claimed.
