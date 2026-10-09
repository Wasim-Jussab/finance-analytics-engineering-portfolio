.PHONY: test lint format generate load dbt-debug dbt-freshness dbt-build dbt-docs snapshot-history-check subscription-history-check subscription-removal-check incremental-payment-check pipeline pipeline-health pipeline-health-verify pipeline-health-check evidence-pack check verify
.NOTPARALLEL: pipeline verify

DBT_DATABASE ?= data/finance.duckdb
PIPELINE_LOCK ?= reports/pipeline.lock
DBT_SEND_ANONYMOUS_USAGE_STATS ?= false
export DBT_SEND_ANONYMOUS_USAGE_STATS
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
	PYTHONPATH=src python -m finance_portfolio.generate_dbt_docs --database $(DBT_DATABASE)

snapshot-history-check:
	PYTHONPATH=src python -m finance_portfolio.snapshot_history_check --database $(DBT_DATABASE)

subscription-history-check:
	PYTHONPATH=src python -m finance_portfolio.subscription_history_check --database $(DBT_DATABASE)

subscription-removal-check:
	PYTHONPATH=src python -m finance_portfolio.subscription_removal_check --database $(DBT_DATABASE)

incremental-payment-check:
	PYTHONPATH=src python -m finance_portfolio.incremental_payment_check --database $(DBT_DATABASE)

pipeline:
	PYTHONPATH=src python -m finance_portfolio.run_pipeline --database $(DBT_DATABASE) --lock $(PIPELINE_LOCK)

pipeline-health:
	PYTHONPATH=src python -m finance_portfolio.pipeline_health

pipeline-health-verify:
	PYTHONPATH=src python -m finance_portfolio.verify_pipeline_health

pipeline-health-check:
	PYTHONPATH=src python -m finance_portfolio.pipeline_health_scenario

evidence-pack:
	PYTHONPATH=src python -m finance_portfolio.evidence_pack

check: lint test

verify:
	PYTHONPATH=src python -m finance_portfolio.run_pipeline --verify --database $(DBT_DATABASE) --lock $(PIPELINE_LOCK)


.PHONY: operations-test operations-evaluate operations-verify
operations-test:
	python -m pytest projects/operations-assistant/tests

operations-evaluate:
	$(MAKE) -C projects/operations-assistant evaluate

operations-verify: operations-test operations-evaluate
