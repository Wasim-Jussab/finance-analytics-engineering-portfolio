# Day 39 — replay the saved weekly comparison

8 November 2026

The binding check could reject mismatched claims, but it didn't recalculate
them. I added a replay mode that rebuilds the synthetic data and computes the
same fixed weekly comparison without loading the classifier. It compares the
claims, full evidence and deterministic prose with the saved report. The
report cannot choose a different tool or set of dates.

I tested two edits that still passed the previous binding check: changing the
prose and changing the snapshot ID alone. Replay must reject both. This checks
the report against a reproducible calculation, not who made it or whether
its routing and release records are genuine.

The full local package gate passed with 154 tests, API parity, evaluation
and readiness checks, and Ruff. I saved a fresh CLI report and verified it
with the replay command. The original demo ran local intent inference;
replay did not run inference.
