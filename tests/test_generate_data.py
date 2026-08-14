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

    assert set(paths) == {"customers", "loans", "subscriptions", "payments"}
    assert all(path.exists() for path in paths.values())
    assert paths["customers"].read_text(encoding="utf-8").splitlines()[0] == (
        "customer_id,first_name,last_name,date_of_birth,postcode"
    )
