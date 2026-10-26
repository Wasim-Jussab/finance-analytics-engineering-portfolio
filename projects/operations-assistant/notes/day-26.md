# Operations Day 26 — pin an investigation to a snapshot

26 October 2026

I added an optional `expected_snapshot_id` to typed tool and question requests.
It must be a lowercase SHA-256 identity from an earlier response. The service
computes the current identity on its read-only connection and rejects a mismatch
before metric execution. The expected identity is also bound into request evidence.

This closes the optional-client guard gap from the previous milestone without
claiming to implement cursors or retain old snapshots. Existing unpinned requests
remain compatible. A mismatch uses the existing 422 validation-error contract and
asks the caller to restart; no partial page or calculated answer is returned.

The regression test executes tool, answer and actual classifier-backed question
endpoints against a matching snapshot, replaces it with a second synthetic seed,
then verifies that the old identity is rejected before metrics execute. The field
is never inferred from prose. No generative model or new intent label was added.

## Local verification

The package `make verify` gate passed: 82 tests, grounding 6/6, held-out routing
18/18, adversarial routing 27/27 and end-to-end questions 10/10. Both release gates
approved and runtime readiness passed. Ruff and the three new API regression cases
also passed. The existing TestClient dependency deprecation warning remains.
