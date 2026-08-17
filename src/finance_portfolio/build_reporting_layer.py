"""Build small reporting tables from the raw synthetic CSV files.

This is deliberately plain Python for now. The point of this step is to make
the grain and business rules explicit before introducing a database or dbt.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeAlias

Row: TypeAlias = dict[str, str]
ReportingLayer: TypeAlias = dict[str, list[Row]]


def _read_csv(path: Path) -> list[Row]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _money(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def _format_money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _months_between(start: date, end: date) -> int:
    """Return completed calendar months, avoiding a misleading fractional age."""

    months = (end.year - start.year) * 12 + end.month - start.month
    return max(0, months - int(end.day < start.day))


def build_reporting_layer(raw_dir: Path, as_of_date: date) -> ReportingLayer:
    """Create reporting tables while retaining failed payment rows."""

    customers = _read_csv(raw_dir / "customers.csv")
    loans = _read_csv(raw_dir / "loans.csv")
    payments = _read_csv(raw_dir / "payments.csv")

    payments_by_account: dict[str, list[Row]] = defaultdict(list)
    for payment in payments:
        payments_by_account[payment["account_id"]].append(payment)

    dim_customer = [
        {
            "customer_id": customer["customer_id"],
            "full_name": f"{customer['first_name']} {customer['last_name']}",
            "date_of_birth": customer["date_of_birth"],
            "postcode": customer["postcode"],
        }
        for customer in customers
    ]

    fct_payment: list[Row] = []
    for payment in payments:
        payment_date = date.fromisoformat(payment["payment_date"])
        is_successful = payment["payment_status"] == "Completed"
        fct_payment.append(
            {
                "payment_id": payment["payment_id"],
                "account_id": payment["account_id"],
                "payment_date": payment["payment_date"],
                "payment_month": payment_date.strftime("%Y-%m"),
                "amount": _format_money(_money(payment["amount"])),
                "payment_status": payment["payment_status"],
                "payment_method": payment["payment_method"],
                "is_successful": "1" if is_successful else "0",
            }
        )

    dim_loan: list[Row] = []
    for loan in loans:
        loan_payments = payments_by_account[loan["account_id"]]
        completed = [p for p in loan_payments if p["payment_status"] == "Completed"]
        completed_dates = [date.fromisoformat(p["payment_date"]) for p in completed]
        origination_date = date.fromisoformat(loan["origination_date"])
        dim_loan.append(
            {
                "account_id": loan["account_id"],
                "customer_id": loan["customer_id"],
                "product_code": loan["product_code"],
                "origination_date": loan["origination_date"],
                "loan_age_months": str(_months_between(origination_date, as_of_date)),
                "original_balance": _format_money(_money(loan["original_balance"])),
                "status": loan["status"],
                "completed_payment_count": str(len(completed)),
                "completed_payment_amount": _format_money(
                    sum((_money(p["amount"]) for p in completed), Decimal("0.00"))
                ),
                "last_completed_payment_date": (
                    max(completed_dates).isoformat() if completed_dates else ""
                ),
            }
        )

    return {
        "dim_customer": dim_customer,
        "dim_loan": dim_loan,
        "fct_payment": fct_payment,
    }


def validate_reporting_layer(raw_dir: Path, reporting: ReportingLayer) -> list[str]:
    """Return model-level errors without changing or hiding the output."""

    errors: list[str] = []
    keys = {
        "dim_customer": "customer_id",
        "dim_loan": "account_id",
        "fct_payment": "payment_id",
    }
    for table, key in keys.items():
        values = [row[key] for row in reporting[table]]
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            errors.append(f"{table} has duplicate {key}: {duplicates}")

    customer_ids = {row["customer_id"] for row in reporting["dim_customer"]}
    account_ids = {row["account_id"] for row in reporting["dim_loan"]}
    missing_loan_customers = sorted(
        {row["customer_id"] for row in reporting["dim_loan"]} - customer_ids
    )
    missing_payment_accounts = sorted(
        {row["account_id"] for row in reporting["fct_payment"]} - account_ids
    )
    if missing_loan_customers:
        errors.append(f"dim_loan references missing customers: {missing_loan_customers}")
    if missing_payment_accounts:
        errors.append(f"fct_payment references missing accounts: {missing_payment_accounts}")

    raw_payments = _read_csv(raw_dir / "payments.csv")
    raw_completed_total = sum(
        (_money(row["amount"]) for row in raw_payments if row["payment_status"] == "Completed"),
        Decimal("0.00"),
    )
    model_completed_total = sum(
        (_money(row["amount"]) for row in reporting["fct_payment"] if row["is_successful"] == "1"),
        Decimal("0.00"),
    )
    if raw_completed_total != model_completed_total:
        errors.append(
            "completed payment total does not reconcile: "
            f"raw={raw_completed_total} model={model_completed_total}"
        )

    loan_payment_total = sum(
        (_money(row["completed_payment_amount"]) for row in reporting["dim_loan"]),
        Decimal("0.00"),
    )
    if raw_completed_total != loan_payment_total:
        errors.append(
            "loan payment summary does not reconcile: "
            f"raw={raw_completed_total} summary={loan_payment_total}"
        )
    return errors


def write_reporting_layer(reporting: ReportingLayer, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    columns = {
        "dim_customer": ["customer_id", "full_name", "date_of_birth", "postcode"],
        "dim_loan": [
            "account_id", "customer_id", "product_code", "origination_date",
            "loan_age_months", "original_balance", "status", "completed_payment_count",
            "completed_payment_amount", "last_completed_payment_date",
        ],
        "fct_payment": [
            "payment_id", "account_id", "payment_date", "payment_month", "amount",
            "payment_status", "payment_method", "is_successful",
        ],
    }
    paths: dict[str, Path] = {}
    for table, rows in reporting.items():
        path = output_dir / f"{table}.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns[table])
            writer.writeheader()
            writer.writerows(rows)
        paths[table] = path
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Build reporting tables from generated CSVs")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/reporting"))
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2025, 12, 31))
    args = parser.parse_args()

    reporting = build_reporting_layer(args.raw_dir, args.as_of)
    errors = validate_reporting_layer(args.raw_dir, reporting)
    if errors:
        raise SystemExit("Reporting validation failed:\n- " + "\n- ".join(errors))

    paths = write_reporting_layer(reporting, args.output_dir)
    for table, path in paths.items():
        print(f"{table}: {len(reporting[table])} rows -> {path}")


if __name__ == "__main__":
    main()
