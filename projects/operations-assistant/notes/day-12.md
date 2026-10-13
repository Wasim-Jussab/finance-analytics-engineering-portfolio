# Day 12 — package the local classifier as a verified artifact

The adapter boundary still fitted a classifier whenever the application started. I added an explicit local artifact lifecycle so the fitted bytes can be exported, fingerprinted, checked and loaded separately from routing policy.

The manifest records the training/model version, approved labels, scikit-learn version and SHA-256 fingerprint. Verification checks those fields and the complete directory before deserializing. I kept the in-memory fit as the default developer path and made the artifact opt-in through the app factory or environment variable.

The important limitation is trust: joblib is pickle-compatible. A matching fingerprint detects a changed known artifact, but it does not make an arbitrary downloaded file safe. I therefore describe and test this as trusted local serialization, not a secure model registry. The resulting inference is still the same narrow local intent classifier; metrics and answer prose remain deterministic.
