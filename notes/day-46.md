# Day 46 — index one pipeline's evidence

The pipeline now produces several useful artifacts, but a reviewer still had to infer which run report, health decision and dbt files belonged together. I added a small evidence-pack builder that reconciles those relationships before writing one index.

The latest run pointer must exactly equal its archived run. The health decision must name and fingerprint that run and match the current policy. The dbt results must contain only successful model or hook outcomes and passing tests. The pack then fingerprints seven artifacts and records the run, decision and invocation IDs needed to trace them.

I deliberately kept the underlying files separate rather than copying them into a new archive. The pack is a reproducible local index, not immutable storage, a signature or third-party attestation. The next useful control is an independent read-only verifier rather than adding more metadata to the same writer.
