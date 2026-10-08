# Day 43 — fingerprint the health decision

The policy gate could explain a result, but the JSON did not identify the exact policy and run reports behind that decision. I added SHA-256 fingerprints, an evaluator version and a stable decision ID derived from the complete input set and outcome.

I chose exact file fingerprints rather than normalising the JSON because audit evidence should reveal even a one-byte change. The decision ID is independent of local directory names, so copying identical inputs produces the same result. Tests prove that report and policy changes both create a new ID.

This is reproducible local evidence, not tamper-proof storage or a cryptographic signature. Anyone who can replace both the source files and the output can still rewrite the history; external immutable storage would be a separate production control.
