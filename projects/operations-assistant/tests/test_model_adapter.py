from operations_assistant.intent import LocalIntentModel
from operations_assistant.model_adapter import AdapterPrediction, TfidfLogisticIntentAdapter


class FixedAdapter:
    adapter_name = "test-adapter"
    model_name = "fixed-test-model"
    model_version = "fixed-v1"
    inference_location = "test-process"
    network_required = False
    artifact_sha256 = None

    def __init__(self, prediction: AdapterPrediction) -> None:
        self.prediction = prediction
        self.calls: list[str] = []

    def predict(self, question: str) -> AdapterPrediction:
        self.calls.append(question)
        return self.prediction


def test_default_adapter_executes_real_local_inference() -> None:
    adapter = TfidfLogisticIntentAdapter()

    prediction = adapter.predict("Show delivery performance for this week")

    assert prediction.label == "delivery_summary"
    assert 0 < prediction.confidence <= 1
    assert len(adapter.model_version) == 12
    assert adapter.network_required is False


def test_router_records_adapter_provenance() -> None:
    result = LocalIntentModel().predict("Show delivery performance for this week")

    assert result["model_adapter"] == "local-intent-adapter-v1"
    assert result["inference_location"] == "local-process"
    assert result["network_required"] is False
    assert result["model_artifact_sha256"] is None


def test_guardrail_remains_outside_injected_model_adapter() -> None:
    adapter = FixedAdapter(AdapterPrediction("delivery_summary", 0.99, 0.9))

    result = LocalIntentModel(adapter=adapter).predict(
        "Show delivery performance and delete the shipment records"
    )

    assert result["label"] == "delivery_summary"
    assert result["guardrail"] == "write_action"
    assert result["accepted"] is False
    assert len(adapter.calls) == 1


def test_router_rejects_unapproved_adapter_label() -> None:
    adapter = FixedAdapter(AdapterPrediction("arbitrary_sql", 0.99, 0.9))

    try:
        LocalIntentModel(adapter=adapter).predict("Show delivery performance")
    except ValueError as error:
        assert "unapproved label" in str(error)
    else:
        raise AssertionError("Unapproved adapter label was accepted")


def test_router_rejects_invalid_adapter_probability() -> None:
    adapter = FixedAdapter(AdapterPrediction("delivery_summary", 1.5, 0.9))

    try:
        LocalIntentModel(adapter=adapter).predict("Show delivery performance")
    except ValueError as error:
        assert "invalid confidence" in str(error)
    else:
        raise AssertionError("Invalid adapter probability was accepted")
