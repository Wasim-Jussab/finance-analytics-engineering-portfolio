# Day 46 — verify comparison prose before returning it

15 November 2026

I extended the template-specific checks to the comparison's baseline/current
windows, due counts, rates and signed percentage-point change. The existing
API grounding gate enforces them on both answer-producing paths.

The regressions alter counts, rates and the direction of the change while
leaving claims and evidence alone. Both API paths must refuse an inverted
rate-change sign. These checks still don't judge arbitrary prose: exception
prose, remaining comparison sentences and causal inference are outside this
new numeric check. No generative model is introduced or evaluated.

The seven focused tests and full package gate passed: 172 Python tests,
6/6 grounding cases, 13/13 question cases, routing/adversarial checks,
readiness, saved-report replay and Ruff. The API returned healthy 200s
and rejected the altered change sign with a generic 500 and no answer.
