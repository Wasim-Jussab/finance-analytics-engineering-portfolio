.PHONY: data test model-artifact model-artifact-verify evaluate verify demo

data:
	python -m operations_assistant.generate

test:
	python -m pytest

model-artifact:
	python -m operations_assistant.model_artifact

model-artifact-verify:
	python -m operations_assistant.model_artifact --verify

evaluate: data model-artifact-verify
	python -m operations_assistant.evaluation
	python -m operations_assistant.intent_evaluation --model-artifact artifacts/local-intent-model
	python -m operations_assistant.adversarial_evaluation --model-artifact artifacts/local-intent-model
	python -m operations_assistant.routing_release
	python -m operations_assistant.question_evaluation
	python -m operations_assistant.question_release

verify: test model-artifact evaluate

demo: data
	python -m uvicorn operations_assistant.app:create_app --factory --host 127.0.0.1 --port 8000
