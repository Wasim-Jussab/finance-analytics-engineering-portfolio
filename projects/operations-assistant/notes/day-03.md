# Day 3 — bind the tool result to its evidence

The comparison tool previously opened the database independently for its two periods. A snapshot replacement between those calls could mix populations. I moved both cohorts onto the same held read-only connection, including the source fingerprint query.

Each result now carries a content-based snapshot ID, the validated request, a contract version and an evidence ID derived from the exact returned result. The IDs support traceability; they do not prove that an answer is correct.

I tested repeatability, filter changes and replacement data. A controlled replacement after the first cohort query confirmed the second cohort still used the original snapshot. Ten tests pass; the existing TestClient deprecation warning is still visible.

No model inference is present. These structured results are the evidence an eventual answer layer will cite.

