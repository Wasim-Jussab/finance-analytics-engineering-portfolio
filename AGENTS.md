
# Project instructions

## Scope

This repository is a public portfolio project for analytics engineering. Use synthetic or clearly licensed public data only.

## Non-negotiable controls

- Never add Payment Assist, Amazon or any other employer's confidential data.
- Never add personal identifiers, credentials, tokens or connection strings.
- Never create or invoke billable cloud resources.
- Do not claim a local simulation is production cloud experience.
- Preserve source grain and document every intentional grain change.
- Prefer source-of-truth fields over re-calculating existing business logic without evidence.

## Engineering standards

- Use Redshift-compatible SQL where warehouse SQL is required.
- Make joins, filters, NULL handling, date logic and status logic explicit.
- Add tests for duplicates, missing keys, invalid dates and reconciliation variances.
- Keep transformations deterministic and rerunnable.
- Keep business rules documented beside the implementation.
- Update the README or relevant documentation when architecture changes.

## Validation before a milestone is published

1. Run the available tests.
2. Run linting or formatting checks.
3. Review the diff for secrets and generated data.
4. Confirm the README reflects the current state.
5. Confirm the change is small enough to explain in an interview.
