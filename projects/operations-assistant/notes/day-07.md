# Day 7 — gate the routing model release

The classifier had two passing evaluation reports, but nothing reconciled them into one explicit release decision. I added a versioned policy that requires every held-out and adversarial case to pass, all six risk slices to be present and zero unsafe acceptances.

The gate validates case-level evidence instead of trusting headline totals. It also requires both reports to identify the same model version and fingerprints the exact reports and policy behind a stable release ID. A deliberately altered unsafe case is blocked in the tests alongside inconsistent totals and a mismatched model version.

This is a governance control over executed local TF-IDF/logistic-regression inference. It does not turn the deterministic answer templates into AI, and approval of these hand-authored fixtures is regression evidence rather than a production accuracy or safety claim.

My first full evaluation did not reach the new gate because the shared virtual environment still pointed at the older operations package in the finance worktree. I reinstalled this worktree's package in editable mode and reran the unchanged code; the complete evaluation then passed. That was an environment-isolation failure, not model evidence.
