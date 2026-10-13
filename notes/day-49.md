# Day 49 — inventory retained evidence bundles

One portable bundle was independently verifiable, but there was no control showing which bundles were retained together. I added a deterministic inventory that verifies every bundle first, then records its pack, pipeline run, health decision and dbt invocation identities with artifact totals.

I reject the same execution identity appearing in two different packs. That is stricter than simply listing directories and prevents a changed pack for one run being presented as a second run. The current repository produces one bundle per verification run, so the clean gate has one row; the tests exercise multiple valid bundles and a duplicate run.

The inventory still lives beside the evidence it describes. It improves completeness checks and retention visibility, but it does not enforce an expiry policy, prevent deletion, prove authorship or provide independently controlled storage.
