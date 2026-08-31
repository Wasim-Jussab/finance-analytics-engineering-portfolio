.PHONY: test lint format generate load dbt-debug dbt-build dbt-docs pipeline check

DBT_DATABASE ?= data/finance.duckdb
DBT_FLAGS = --project-dir . --profiles-dir config --target local

test:
	python -m pytest

lint:
	ruff check .

format:
	ruff format .

generate:
	PYTHONPATH=src python -m finance_portfolio.generate_data

load:
	PYTHONPATH=src python -m finance_portfolio.load_duckdb --database $(DBT_DATABASE)

dbt-debug:
	FINANCE_DUCKDB_PATH=$(DBT_DATABASE) dbt debug $(DBT_FLAGS)

dbt-build:
	FINANCE_DUCKDB_PATH=$(DBT_DATABASE) dbt build $(DBT_FLAGS) --no-partial-parse

dbt-docs:
	FINANCE_DUCKDB_PATH=$(DBT_DATABASE) dbt docs generate $(DBT_FLAGS) --no-partial-parse

pipeline: generate load dbt-build

check: lint test
