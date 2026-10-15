# Day 14 — make the active model boundary inspectable

The application could execute a verified local classifier, but a reviewer had to
infer its runtime configuration from code and response fragments. I added a
read-only model-provenance endpoint that states which adapter and model version
are active, the approved labels and threshold, whether the model needs a network,
and whether the process loaded a fingerprinted artifact or fitted in memory.

I explicitly report classification inference as implemented and generative
inference as absent. That distinction matters because the dates, tool parameters,
metrics and answer prose are still deterministic. The endpoint deliberately omits
training rows and fitted weights; operational transparency does not require
publishing internals that are irrelevant to a business reviewer.

Tests cover both execution modes and require the persisted response to match the
artifact manifest exactly. This improves deployability evidence, not model
quality, and it does not change any evaluation score.
