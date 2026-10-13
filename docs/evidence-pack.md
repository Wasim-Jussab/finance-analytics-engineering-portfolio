# Pipeline evidence pack

`make evidence-pack` writes `reports/evidence-pack.json` after the pipeline, health policy and dbt documentation have completed. It indexes seven exact local artifacts: the latest run pointer, its archived run, the health decision, policy, dbt manifest, run results and catalogue.

The builder first requires the latest pointer to equal its archived run byte for byte. The health decision must name and fingerprint that run and match the current policy. The dbt results must contain only successful model/hook or passing-test statuses. Each indexed artifact records a repository-relative path, SHA-256 fingerprint and byte size.

The pack also records the pipeline run ID, health decision ID, dbt invocation ID and resource counts. A stable pack ID covers that complete payload. This makes one CI result easier to inspect and explain, but it is still evidence stored alongside the workflow that created it. It is not immutable storage, a digital signature, external attestation or an availability claim.

`make evidence-pack-verify` is a separate read-only step. It rebuilds the expected index in memory from the seven current artifacts and requires an exact match with the saved pack. It neither repairs nor rewrites evidence: a changed artifact or changed saved field fails verification. This checks reproducibility at verification time, not whether files were protected from modification before that point.

`make evidence-bundle` then copies the exact seven indexed files and the recorded pack into `reports/evidence-bundles/<evidence_pack_id>/`. The content-addressed directory includes a manifest that records each source path, bundled path, byte size and SHA-256 fingerprint. Creation is atomic and an identical rerun verifies the existing directory instead of replacing it.

`make evidence-bundle-verify` checks the pack ID, manifest, complete file inventory and every copied byte without reading the original working files. This makes the evidence portable as one inspectable local directory and lets a reviewer detect a changed, missing or additional file. It still does not make the directory immutable, prove who created it or replace externally controlled retention.

`make evidence-retention` verifies every bundle below `reports/evidence-bundles/` before writing one deterministic inventory. Each row records the pack, pipeline run, health decision and dbt invocation identities plus artifact counts and bytes. Reusing any of those execution identities across different retained packs fails rather than silently presenting duplicated evidence as separate runs. `make evidence-retention-verify` rebuilds that inventory read-only and requires an exact match.

This is retention visibility, not retention enforcement. It does not apply expiry rules, prevent deletion or move evidence to independently controlled storage.

`make evidence-release` applies the versioned local policy in `config/evidence-release-policy.json` to that independently verified inventory. It requires at least one retained seven-artifact bundle and allows only succeeded pipeline runs with healthy policy decisions. The output records every breach and fingerprints both the policy and retention index; `make evidence-release-verify` rebuilds it without rewriting it.

This is an executable acceptance decision for the portfolio's local evidence contract. It is not external approval, immutable retention, authorship proof or evidence that the chosen thresholds are suitable for another organisation.
