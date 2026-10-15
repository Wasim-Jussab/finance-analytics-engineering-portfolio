# Day 13 — evaluate the artifact that the application can load

The held-out and adversarial suites previously fitted a fresh in-memory classifier. That tested the model definition, but not the exact serialized bytes introduced on Day 12. I changed the executable evaluation path to verify and load the local artifact before running all 39 routing cases.

Both reports now record the artifact's SHA-256 fingerprint, and the release gate rejects reports that name different artifacts. A focused test exports one artifact, reloads it and executes both suites against that same adapter. The in-memory path remains available for unit tests, while the documented `make verify` path uses the persisted artifact.

This closes a traceability gap rather than improving measured accuracy: the same fixed cases still pass 15/15 and 24/24. It proves which trusted local classifier bytes were evaluated. It does not estimate performance on unseen real-world language, and no generative model is involved.

The final API check exposed one genuine wording problem: nested metric evidence still said model inference was not implemented even when the question endpoint had just used the classifier. I changed that field to describe deterministic metric computation and kept the top-level response responsible for stating whether local intent inference ran.
