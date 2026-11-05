# Day 36 — a weekly comparison I can reproduce from the proposal path

5 November 2026

I wanted one answer I could trace from business question to source, rather than
another report that stopped at the tool name. I chose two fixed, equal-length
promised-date cohorts and a fresh temporary synthetic snapshot. That makes the
comparison repeatable and keeps the CLI from accepting a database path, SQL or
model-inferred dates. It is a demo, not a new public execution path.

The saved routing and question decisions must approve the exact classifier.
I check its identity again after loading it for routing. The existing router
checks the proposal before the read-only comparison runs. The same classifier
backs both stages, so that second check is policy enforcement, not corroboration
from another model. The output links its answer to the request and snapshot.

My run showed 176 on-time out of 213 due in the baseline, and 153 out of 218
in the current cohort: down 12.45 percentage points. Current due shipments
reconcile to 153 on time + 44 late + 21 overdue open; six cancellations were
excluded. Both cohorts use the same snapshot. The template can report where
on-time counts fell; it cannot explain why they fell.

The three focused tests passed: grounded counts and evidence, a blocked release,
and a different classifier identity. The package gate now runs the demo with the
release files it just built. This uses an existing routing question, not a new
holdout. Local classifier inference ran; no generative model ran.

I also called the unchanged questions API with the same artifact and scope.
It returned the same claims and evidence as the CLI (HTTP 200) and refused a
request to delete shipments (HTTP 422).

The final local package gate passed: 154 Python tests, grounding 6/6,
routing 18/18, adversarial 27/27, end-to-end questions 10/10, both release
checks, readiness, proposal planning 18/18 and the live synthetic CLI demo.
Ruff passed; the existing TestClient deprecation warning remained.
