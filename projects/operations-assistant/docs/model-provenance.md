# Runtime model provenance

`GET /api/model` is a read-only description of the classifier active in the
running process. It reports the adapter, model version, approved labels,
confidence threshold, inference location and whether network access is required.
It also distinguishes a verified persisted artifact from the development-only
in-memory fit and publishes the loaded artifact's SHA-256 when available.

The endpoint states two separate facts: local classification inference is
implemented, while generative inference is not. Dates, tool arguments, metrics
and answer wording remain governed outside the classifier. This avoids presenting
the deterministic reporting service as an LLM application.

The response does not expose training examples, fitted weights or arbitrary file
paths. A fingerprint establishes which trusted local bytes were loaded; it does
not make untrusted serialized Python safe and it does not prove broad language
performance. Those boundaries remain covered by the artifact checks and the
held-out, adversarial and end-to-end evaluations.
