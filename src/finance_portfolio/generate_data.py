"""Generate a small, repeatable finance dataset for local development.

The generator deliberately uses only the Python standard library. That keeps the
first working version easy to run and makes the data-generation assumptions
visible before any database or transformation tool is added.
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TypeAlias

Row: TypeAlias = dict[str, str]
Dataset: TypeAlias = dict[str, list[Row]]

TABLE_COLUMNS = {
    "customers": ["customer_id", "first_name", "last_name", "date_of_birth", "postcode"],
    "loans": [
        "account_id",
        "customer_id",
        "product_code",
        "origination_date",
        "original_balance",
        "status",
    ],
    "subscriptions": [
        "subscription_id",
        "customer_id",
        "product_code",
        "start_date",
        "billing_frequency",
        "status",
    ],
    "payments": [
        "payment_id",
        "account_id",
        "payment_date",
        "amount",
        "payment_status",
        "payment_method",
    ],
}

FIRST_NAMES = ["Aisha", "Ben", "Daniel", "Fatima", "Hannah", "Imran", "Leah", "Maya"]
LAST_NAMES = ["Ahmed", "Clarke", "Davies", "Khan", "Patel", "Roberts", "Smith", "Taylor"]
LOAN_PRODUCTS = ["LOAN-A", "LOAN-B", "LOAN-C"]
SUBSCRIPTION_PRODUCTS = ["SUB-1", "SUB-2"]
PAYMENT_METHODS = ["Direct Debit", "Card", "Bank Transfer"]


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42
    customer_count: int = 25
    start_date: date = date(2024, 1, 1)
    end_date: date = date(2025, 12, 31)


def _random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _money_from_pence(pence: int) -> str:
    return f"{Decimal(pence) / Decimal(100):.2f}"


def generate_customers(config: GeneratorConfig, rng: random.Random) -> list[Row]:
    rows: list[Row] = []
    for number in range(1, config.customer_count + 1):
        rows.append(
            {
                "customer_id": f"CUS-{number:05d}",
                "first_name": rng.choice(FIRST_NAMES),
                "last_name": rng.choice(LAST_NAMES),
                "date_of_birth": _random_date(
                    rng, date(1965, 1, 1), date(2002, 12, 31)
                ).isoformat(),
                "postcode": f"AB{rng.randint(1, 99)} {rng.randint(1, 9)}CD",
            }
        )
    return rows


def generate_loans(
    config: GeneratorConfig, rng: random.Random, customers: list[Row]
) -> list[Row]:
    rows: list[Row] = []
    for number, customer in enumerate(customers, start=1):
        origination_date = _random_date(rng, config.start_date, date(2025, 6, 30))
        rows.append(
            {
                "account_id": f"ACC-{number:06d}",
                "customer_id": customer["customer_id"],
                "product_code": rng.choice(LOAN_PRODUCTS),
                "origination_date": origination_date.isoformat(),
                "original_balance": _money_from_pence(
                    rng.randrange(50000, 500001, 5000)
                ),
                "status": rng.choice(["Open", "Open", "Open", "Pending", "Closed"]),
            }
        )
    return rows


def generate_subscriptions(
    config: GeneratorConfig, rng: random.Random, customers: list[Row]
) -> list[Row]:
    rows: list[Row] = []
    for number, customer in enumerate(customers, start=1):
        # Not every customer has a subscription. This creates a useful join case.
        if rng.random() >= 0.72:
            continue
        rows.append(
            {
                "subscription_id": f"SUB-{number:06d}",
                "customer_id": customer["customer_id"],
                "product_code": rng.choice(SUBSCRIPTION_PRODUCTS),
                "start_date": _random_date(
                    rng, config.start_date, date(2025, 9, 30)
                ).isoformat(),
                "billing_frequency": rng.choice(["Monthly", "Annual"]),
                "status": rng.choice(["Active", "Active", "Cancelled"]),
            }
        )
    return rows


def generate_payments(
    rng: random.Random, loans: list[Row]
) -> list[Row]:
    rows: list[Row] = []
    for loan in loans:
        origination_date = date.fromisoformat(loan["origination_date"])
        payment_count = rng.randint(2, 6)
        for sequence in range(1, payment_count + 1):
            payment_date = origination_date + timedelta(days=30 * sequence)
            rows.append(
                {
                    "payment_id": f"PAY-{len(rows) + 1:07d}",
                    "account_id": loan["account_id"],
                    "payment_date": payment_date.isoformat(),
                    "amount": _money_from_pence(rng.choice([5000, 7500, 10000, 15000])),
                    "payment_status": rng.choice(["Completed", "Completed", "Failed"]),
                    "payment_method": rng.choice(PAYMENT_METHODS),
                }
            )
    return rows


def generate_dataset(config: GeneratorConfig | None = None) -> Dataset:
    config = config or GeneratorConfig()
    if config.customer_count < 1:
        raise ValueError("customer_count must be at least 1")

    rng = random.Random(config.seed)
    customers = generate_customers(config, rng)
    loans = generate_loans(config, rng, customers)
    subscriptions = generate_subscriptions(config, rng, customers)
    payments = generate_payments(rng, loans)
    return {
        "customers": customers,
        "loans": loans,
        "subscriptions": subscriptions,
        "payments": payments,
    }


def validate_dataset(dataset: Dataset) -> list[str]:
    """Return validation errors instead of hiding them in the generator."""

    errors: list[str] = []
    key_fields = {
        "customers": "customer_id",
        "loans": "account_id",
        "subscriptions": "subscription_id",
        "payments": "payment_id",
    }

    for table, key_field in key_fields.items():
        keys = [row[key_field] for row in dataset[table]]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            errors.append(f"{table} has duplicate {key_field}: {duplicates}")

    customer_ids = {row["customer_id"] for row in dataset["customers"]}
    account_ids = {row["account_id"] for row in dataset["loans"]}

    missing_loan_customers = sorted(
        {row["customer_id"] for row in dataset["loans"]} - customer_ids
    )
    if missing_loan_customers:
        errors.append(f"loans reference missing customers: {missing_loan_customers}")

    missing_subscription_customers = sorted(
        {row["customer_id"] for row in dataset["subscriptions"]} - customer_ids
    )
    if missing_subscription_customers:
        errors.append(
            "subscriptions reference missing customers: "
            f"{missing_subscription_customers}"
        )

    missing_payment_accounts = sorted(
        {row["account_id"] for row in dataset["payments"]} - account_ids
    )
    if missing_payment_accounts:
        errors.append(f"payments reference missing accounts: {missing_payment_accounts}")

    loan_dates = {
        row["account_id"]: date.fromisoformat(row["origination_date"])
        for row in dataset["loans"]
    }
    for payment in dataset["payments"]:
        if date.fromisoformat(payment["payment_date"]) < loan_dates[payment["account_id"]]:
            errors.append(f"payment predates loan origination: {payment['payment_id']}")

    return errors


def write_dataset(dataset: Dataset, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: dict[str, Path] = {}
    for table, rows in dataset.items():
        path = output_dir / f"{table}.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=TABLE_COLUMNS[table])
            writer.writeheader()
            writer.writerows(rows)
        output_paths[table] = path
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic finance dataset")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=25)
    parser.add_argument("--output-dir", type=Path, default=Path("data/generated"))
    args = parser.parse_args()

    dataset = generate_dataset(
        GeneratorConfig(seed=args.seed, customer_count=args.customers)
    )
    errors = validate_dataset(dataset)
    if errors:
        raise SystemExit("Dataset validation failed:\n- " + "\n- ".join(errors))

    paths = write_dataset(dataset, args.output_dir)
    for table, path in paths.items():
        print(f"{table}: {len(dataset[table])} rows -> {path}")


if __name__ == "__main__":
    main()
