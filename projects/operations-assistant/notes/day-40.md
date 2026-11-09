# Day 40 — gate the saved-report handoff

9 November 2026

I moved the saved-report replay into the package gate. It now writes the
actual demo's JSON to a temporary file, verifies it through the CLI and
cleans up the file. Either command failing fails the target. I kept
`make proposal-demo` for anyone who wants to see the full evidence.

This closes the loop from a local classifier choosing an approved tool
to an API-matched trace, bound claims and replayable evidence. The replay
checks one fixed weekly comparison. It is not a second model evaluation:
it loads no model and checks calculations over regenerated synthetic data.
The original demo uses the local intent classifier; no generative inference
is implemented.

The local gate passed: 154 tests, API parity, the evaluation and readiness
checks, Ruff and the new generate-then-replay target.
