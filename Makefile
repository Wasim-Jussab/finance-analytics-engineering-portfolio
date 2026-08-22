.PHONY: test lint format generate load check

test:
	python -m pytest

lint:
	ruff check .

format:
	ruff format .

generate:
	PYTHONPATH=src python -m finance_portfolio.generate_data

load:
	PYTHONPATH=src python -m finance_portfolio.load_duckdb

check: lint test
