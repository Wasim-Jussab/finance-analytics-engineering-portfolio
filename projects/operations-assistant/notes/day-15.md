# Day 15 — bind readiness to the exact evaluated model bytes

I found that the routing suites used the persisted classifier artifact, while the
end-to-end question suite fitted an equivalent classifier in memory. The training
specification and model version matched, but that did not prove the question path
ran the same serialized bytes intended for runtime use.

I changed the question evaluation to verify and load the artifact and carry its
fingerprint into the question release decision. The new readiness gate then
requires the runtime manifest, routing approval and question-path approval to agree
on model name, version and SHA-256 fingerprint. A blocked approval or mismatch
stops the gate.

Installing the declared environment exposed a genuine DuckDB runtime dependency
on `pytz`, which had been available implicitly elsewhere. I added it explicitly to
the package contract rather than treating the import error as model evidence.

This closes the five-session artifact milestone. It still proves only local intent
classification over named fixtures. Generative inference, production accuracy,
deployment security and drift monitoring are not implemented.
