# Operations Day 34 — execute and record the adapter path

3 November 2026

I added an executable proposal-planning evaluation to the package gate. It uses the
existing 18 routing fixtures through the actual classifier-backed adapter, scope
validation and governed veto. I reused that fixture set deliberately and do not
describe the result as a new holdout or broader accuracy evidence.

The report identifies artifact bytes and case-level outcomes without retaining
question text. A wrong producer test must produce a failing report. Typed dates
remain explicit inputs; the model does not extract them. The harness executes no
tools and is not another release approval. Generative inference is still absent.

## Local verification

The complete package gate passed: 150 tests, grounding 6/6, held-out routing
18/18, adversarial 27/27, end-to-end questions 10/10, both release gates and
runtime readiness. The new persisted-artifact proposal evaluation executed and
passed all 18 reused cases. Its report binds the model artifact hash and explicitly
states no generative inference and no tool execution. Both targeted harness tests
passed, including the intentionally wrong producer's failing report. Ruff passed;
the existing TestClient dependency warning remains.
