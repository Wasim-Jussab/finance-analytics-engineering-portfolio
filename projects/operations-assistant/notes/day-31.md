# Operations Day 31 — validate proposed calls before giving them authority

31 October 2026

I started the next milestone with an untrusted JSON proposal boundary. It allows
an approved tool name but rejects model-proposed changes to explicit caller dates,
filters or pagination. Duplicate JSON keys and non-finite constants are rejected
instead of allowing a parser to silently pick a value.

The executable test uses the actual approved read-only tool and reconciles the
overdue-open population and returned rows. The helper itself performs neither
inference nor execution. It is not wired around existing question-policy or model
release gates. A future language-model adapter must use those controls too.

This increment does not satisfy the goal of generative model inference. I am
keeping that gap explicit rather than describing a JSON parser as AI.

## Local verification

The final package gate passed 135 tests, grounding 6/6, held-out routing 18/18,
adversarial routing 27/27 and end-to-end questions 10/10. Both release gates and
runtime readiness passed; Ruff passed. All 17 targeted proposal cases passed.
The existing TestClient dependency warning remains. The real proposal/tool test
returned 21 overdue-open shipments in the full population and seven detail rows,
with unchanged database bytes. No generative inference was executed.
