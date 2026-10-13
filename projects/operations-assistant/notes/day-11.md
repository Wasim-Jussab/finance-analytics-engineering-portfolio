# Day 11 — separate model inference from governed routing

The first local classifier worked, but the router constructed and owned the scikit-learn pipeline directly. That made the model difficult to replace and blurred which decisions came from inference versus deterministic policy. I introduced a small adapter contract that returns only a label, confidence and margin.

The router still owns the confidence threshold, domain checks, unsafe-action patterns, parameter validation and approved-tool mapping. I proved that boundary with an injected adapter that confidently labels a mixed write request as supported: the outer write guardrail still blocks it before tool execution. Unknown labels and invalid probabilities also fail closed.

The current adapter still runs the same TF-IDF logistic-regression inference locally. Its version now covers the examples, model settings and scikit-learn version, and each routing result records the adapter and inference location. This is useful separation and provenance, not a new or more capable model. A future adapter would have to pass the existing held-out, adversarial and complete-path release gates before replacing it.
