from datetime import date
from decimal import Decimal

from finance_portfolio.build_reporting_layer import (
    build_reporting_layer,
    validate_reporting_layer,
    write_reporting_layer,
)
from finance_portfolio.generate_data import GeneratorConfig, generate_dataset, write_dataset


def test_reporting_layer_preserves_payment_grain_and_reconciles(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    reporting_dir = tmp_path / "reporting"
    write_dataset(generate_dataset(GeneratorConfig(seed=42, customer_count=10)), raw_dir)

    reporting = build_reporting_layer(raw_dir, date(2025, 12, 31))

    assert len(reporting["fct_payment"]) > 0
    assert validate_reporting_layer(raw_dir, reporting) == []
    assert set(row["is_successful"] for row in reporting["fct_payment"]) <= {"0", "1"}

    paths = write_reporting_layer(reporting, reporting_dir)
    assert set(paths) == {"dim_customer", "dim_loan", "fct_payment"}
    assert all(path.exists() for path in paths.values())


def test_failed_payments_are_not_in_completed_summary(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    write_dataset(generate_dataset(GeneratorConfig(seed=42, customer_count=3)), raw_dir)

    reporting = build_reporting_layer(raw_dir, date(2025, 12, 31))
    failed_payments = [row for row in reporting["fct_payment"] if row["is_successful"] == "0"]
    assert failed_payments

    for loan in reporting["dim_loan"]:
        account_payments = [
            row for row in reporting["fct_payment"] if row["account_id"] == loan["account_id"]
        ]
        completed_count = sum(row["is_successful"] == "1" for row in account_payments)
        assert int(loan["completed_payment_count"]) == completed_count
        assert int(loan["completed_payment_count"]) <= len(account_payments)
