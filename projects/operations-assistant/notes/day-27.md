# Operations Day 27 — complete the investigation or reject it

27 October 2026

I added a small collector over the existing approved exception tool. It follows
page offsets, sends the first snapshot identity on every subsequent call and
returns one complete set of rows with page-level evidence. It rejects a changed
snapshot, duplicate shipments, count/offset inconsistencies or a non-advancing
page. A bounded row cap rejects oversized populations instead of hiding truncation.

Tests compare all outcomes and both filtered subsets against a full independent
tool call, verify the database bytes are unchanged, replace the snapshot between
pages and check empty/capped/malformed results. A command-line example makes the
business question demonstrable without an API subscription or credentials.

This is deterministic orchestration and invokes no model. The existing intent
classifier is still genuinely executed by the separate package evaluation gate;
I have not added generative inference, model planning or an autonomous agent.

## Local verification

The package gate passed: 93 tests, grounding 6/6, held-out routing 18/18,
adversarial routing 27/27 and end-to-end questions 10/10. Both release gates
approved and runtime readiness passed. Ruff also passed. The documented CLI
actually returned 21 overdue-open rows across three seven-row pages, with every
later page pinned to the first snapshot. The TestClient deprecation warning remains.
