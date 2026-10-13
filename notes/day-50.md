# Day 50 — turn retained evidence into an explicit decision

The evidence milestone could verify individual files, a portable bundle and the complete retained inventory, but it still stopped short of a clear outcome. I added a small versioned policy and a reproducible approved-or-blocked decision over that verified inventory.

The policy requires at least one seven-artifact bundle and accepts only succeeded pipeline runs with healthy policy decisions. The decision fingerprints both its policy and retention index, records every breach and has a separate read-only verifier. Tests cover too few bundles, failed and degraded statuses, and an edited saved decision.

I kept the policy deliberately narrow. A green local result means this repository's stated evidence contract passed; it does not mean an external reviewer approved the work, the storage is immutable or these thresholds suit a regulated production process. That boundary is the main reason to finish this milestone here rather than add more local metadata.
