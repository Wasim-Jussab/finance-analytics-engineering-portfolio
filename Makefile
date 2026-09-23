.PHONY: test lint format generate load dbt-debug dbt-freshness dbt-build dbt-docs snapshot-history-check subscription-history-check subscription-removal-check incremental-payment-check pipeline check verify
.NOTPARALLEL: pipeline verify

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

dbt-freshness:
	FINANCE_DUCKDB_PATH=$(DBT_DATABASE) dbt source freshness $(DBT_FLAGS) --no-partial-parse

dbt-build:
	FINANCE_DUCKDB_PATH=$(DBT_DATABASE) dbt build $(DBT_FLAGS) --no-partial-parse

dbt-docs:
	FINANCE_DUCKDB_PATH=$(DBT_DATABASE) dbt docs generate $(DBT_FLAGS) --no-partial-parse

snapshot-history-check:
	PYTHONPATH=src python -m finance_portfolio.snapshot_history_check --database $(DBT_DATABASE)

subscription-history-check:
	PYTHONPATH=src python -m finance_portfolio.subscription_history_check --database $(DBT_DATABASE)

subscription-removal-check:
	PYTHONPATH=src python -m finance_portfolio.subscription_removal_check --database $(DBT_DATABASE)

incremental-payment-check:
	PYTHONPATH=src python -m finance_portfolio.incremental_payment_check --database $(DBT_DATABASE)

pipeline: generate load dbt-freshness dbt-build

check: lint test

verify: pipeline
	$(MAKE) snapshot-history-check
	$(MAKE) subscription-history-check
	$(MAKE) subscription-removal-check
	$(MAKE) incremental-payment-check
	$(MAKE) check
	$(MAKE) dbt-docs
