# Untrusted tool-proposal boundary

`proposals.validate_proposal(raw_json, question_request)` parses a proposed
`ToolRequest` but never executes it. It accepts one JSON object up to 4096 UTF-8
bytes, rejecting duplicate fields, non-finite constants, prose/code fences,
unknown capabilities and invalid tool arguments.

Only the approved tool name may be proposed. Dates, baseline, region, outcome,
limit, offset and snapshot expectation must match the explicit caller scope.
Missing required scope and unsupported tool/argument combinations fail rather
than being silently filled or corrected. Existing Pydantic contracts remain the
source of truth. Tool arguments are not extracted from natural-language text.

The tests include a real synthetic overdue-open query: 21 matching shipments,
seven returned rows, evidence-bound request and unchanged source bytes.
Negative cases exercise changed scope, arbitrary SQL, ambiguous JSON and size limits.

This is preparation for a future local language-model adapter, not a new model.
No LLM is loaded or evaluated here. The existing intent classifier remains the
only executed inference in the full package gate. This helper is not an alternative
API router: any future integration must retain existing question-policy, release
and readiness checks before executing the validated read-only tool. Structured
validation cannot establish that a tool choice answers the user's question.
