
.PHONY: test lint format check

test:
	python -m pytest

lint:
	ruff check .

format:
	ruff format .

check: lint test
