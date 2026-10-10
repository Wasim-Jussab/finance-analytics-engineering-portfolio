# Pipeline evidence pack

`make evidence-pack` writes `reports/evidence-pack.json` after the pipeline, health policy and dbt documentation have completed. It indexes seven exact local artifacts: the latest run pointer, its archived run, the health decision, policy, dbt manifest, run results and catalogue.

The builder first requires the latest pointer to equal its archived run byte for byte. The health decision must name and fingerprint that run and match the current policy. The dbt results must contain only successful model/hook or passing-test statuses. Each indexed artifact records a repository-relative path, SHA-256 fingerprint and byte size.

The pack also records the pipeline run ID, health decision ID, dbt invocation ID and resource counts. A stable pack ID covers that complete payload. This makes one CI result easier to inspect and explain, but it is still evidence stored alongside the workflow that created it. It is not immutable storage, a digital signature, external attestation or an availability claim.

`make evidence-pack-verify` is a separate read-only step. It rebuilds the expected index in memory from the seven current artifacts and requires an exact match with the saved pack. It neither repairs nor rewrites evidence: a changed artifact or changed saved field fails verification. This checks reproducibility at verification time, not whether files were protected from modification before that point.
