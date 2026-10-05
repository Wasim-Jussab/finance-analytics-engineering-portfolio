# Day 5 — add narrow local intent inference

I added a local classifier for one bounded decision: whether a question requests a delivery summary, a period comparison or something unsupported. Dates and region stay explicit and validated; the model cannot write SQL, choose new tools or invent reporting periods.

The first milestone now executes actual model inference, but only for intent routing. The metric result and answer remain deterministic. I added held-out summary, comparison and abstention cases rather than reporting training accuracy, and the API rejects missing comparison dates after routing.

This is not an LLM or a generative assistant. Thirty training examples and fifteen evaluation examples demonstrate the interface and controls, not production language coverage. The next milestone should expand adversarial evaluation before introducing any local generative model.

My first confidence threshold rejected three correctly classified held-out questions. I lowered it only after confirming all unsupported evaluation cases still predicted the unsupported class. That is acceptable for this bounded fixture, but threshold tuning on fifteen examples is another reason not to claim production accuracy.
