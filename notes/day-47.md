# Day 47 — verify the evidence pack without rewriting it

Yesterday's pack made related evidence easier to navigate, but generation alone did not prove the saved index still matched its artifacts when someone inspected it later. I added a separate read-only command that rebuilds the expected pack in memory and requires an exact match.

The check fails if an indexed file changes, if a recorded count is edited or if any existing run, health or dbt reconciliation no longer holds. It deliberately does not repair the pack. Tests also confirm that successful verification leaves the saved bytes unchanged.

The verifier shares the deterministic pack contract with the writer. That avoids maintaining two subtly different definitions, but it is not an independent implementation or evidence that files were immutable before verification. It is a reproducibility check at one point in time, which is the claim I can defend with local files and free tooling.
