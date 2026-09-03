from finance_portfolio.generate_data import (
    GeneratorConfig,
    generate_dataset,
    validate_dataset,
    write_dataset,
)


def test_same_seed_produces_same_dataset() -> None:
    config = GeneratorConfig(seed=42, customer_count=10)

    assert generate_dataset(config) == generate_dataset(config)


def test_generated_relationships_are_valid() -> None:
    dataset = generate_dataset(GeneratorConfig(seed=42, customer_count=10))

    assert validate_dataset(dataset) == []


def test_different_seed_changes_the_generated_data() -> None:
    first = generate_dataset(GeneratorConfig(seed=42, customer_count=10))
    second = generate_dataset(GeneratorConfig(seed=99, customer_count=10))

    assert first != second


def test_csv_outputs_can_be_written(tmp_path) -> None:
    dataset = generate_dataset(GeneratorConfig(seed=42, customer_count=3))

    paths = write_dataset(dataset, tmp_path)

    assert set(paths) == {
        "customers",
        "loans",
        "subscriptions",
        "payments",
        "subscription_payments",
    }
    assert all(path.exists() for path in paths.values())
    assert paths["customers"].read_text(encoding="utf-8").splitlines()[0] == (
        "customer_id,first_name,last_name,date_of_birth,postcode"
    )


def test_subscription_payments_have_valid_agreement_references() -> None:
    dataset = generate_dataset(GeneratorConfig(seed=42, customer_count=10))

    assert dataset["subscription_payments"]
    subscription_ids = {
        row["subscription_id"] for row in dataset["subscriptions"]
    }
    assert {
        row["subscription_id"] for row in dataset["subscription_payments"]
    } <= subscription_ids


def test_seed_42_preserves_the_published_row_count_baseline() -> None:
    dataset = generate_dataset(GeneratorConfig(seed=42))

    assert len(dataset["customers"]) == 25
    assert len(dataset["loans"]) == 25
    assert len(dataset["subscriptions"]) == 20
    assert len(dataset["payments"]) == 99
    assert len(dataset["subscription_payments"]) == 150


def test_orphan_subscription_payment_is_reported() -> None:
    dataset = generate_dataset(GeneratorConfig(seed=42, customer_count=10))
    dataset["subscription_payments"][0]["subscription_id"] = "SUB-MISSING"

    assert validate_dataset(dataset) == [
        "subscription payments reference missing subscriptions: ['SUB-MISSING']"
    ]
