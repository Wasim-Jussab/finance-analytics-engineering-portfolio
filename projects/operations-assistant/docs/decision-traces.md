# Question decision traces

`POST /api/questions` returns a deterministic `decision_trace` for answered requests. Governed refusals return the same structure inside the HTTP 422 detail. Each trace records the outcome, explicit dates and region, one rounded routing decision, model version, selected tool, evidence ID, contract version and a fingerprint of the structured claims.

The trace deliberately stores a SHA-256 fingerprint of the question rather than its raw text. This reduces accidental retention of names or other sensitive wording while allowing repeated local requests to be compared. Dates and region remain visible because they define the metric scope and must be auditable.

The decision ID fingerprints the complete trace payload. `verify_decision_trace` rejects changed fields, and the end-to-end evaluation now verifies all eight answered and blocked traces. The ID is deterministic integrity evidence only: it is not encryption, a digital signature, immutable storage or proof that the classifier is broadly accurate.
