.PHONY: data test evaluate verify demo

data:
	python -m operations_assistant.generate

test:
	python -m pytest

evaluate: data
	python -m operations_assistant.evaluation
	python -m operations_assistant.intent_evaluation
	python -m operations_assistant.adversarial_evaluation
	python -m operations_assistant.routing_release

verify: test evaluate

demo: data
	python -m uvicorn operations_assistant.app:create_app --factory --host 127.0.0.1 --port 8000
