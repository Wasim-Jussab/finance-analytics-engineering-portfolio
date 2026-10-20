# Day 20 — make audit verification operable without the API

The integrity endpoint was useful, but it made an operator start the web service
to inspect a local ledger. I added a standalone read-only command that uses the
same verifier and optional external head/count expectations.

The command prints small JSON status objects and returns a non-zero exit code for
changed evidence or expectation mismatches. It does not print the configured path,
ledger rows, decision traces or raw questions. Tests exercise both a genuine pass
and a genuine mismatch.

This closes the five-session decision-evidence milestone. The review is explicit
that hash links, external anchors and a single-host writer lock improve local
evidence without providing immutable storage, authentication, digital signatures
or external attestation. The local classifier remains the only model inference;
metric execution and answer wording remain deterministic.

## Validation

The package quality gate passed 72 tests, model-artifact verification, 4/4
grounding cases, 15/15 intent-routing cases, 24/24 adversarial cases and 8/8
end-to-end questions. The question release check approved the suite with zero
blocked tool executions, runtime readiness passed, and Ruff reported no issues.
The only warning was Starlette's existing `TestClient` deprecation warning.
