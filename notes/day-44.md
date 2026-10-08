# Day 44 — verify the recorded health decision

The health artifact identified its inputs, but the same command that created it was still the only way I had checked it. I added a separate read-only verifier that rebuilds the complete decision in memory from the archived reports and policy, then requires an exact match with the saved JSON.

I chose exact object equality rather than checking only the decision ID. That catches edits to the operational summary as well as changes to the policy result or fingerprints. The verifier does not rewrite the artifact, and tests cover changed reports, changed policy and an edited summary.

This provides independent reproducibility inside the repository, not immutable audit storage. Someone with permission to replace every input and regenerate the output can still rewrite the evidence set; signed or externally retained evidence would be a separate production control.
