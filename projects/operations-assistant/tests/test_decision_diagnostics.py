from operations_assistant.intent_evaluation import run_intent_evaluation, summarize_decisions


def test_raw_labels_and_governed_outcomes_are_not_conflated():
    rows = [
        dict(
            expected="unsupported",
            model_label="delivery_summary",
            observed="unsupported",
            decision_reason="guardrail",
        ),
        dict(
            expected="compare_delivery_periods",
            model_label="delivery_summary",
            observed="unsupported",
            decision_reason="below_threshold",
        ),
        dict(
            expected="delivery_summary",
            model_label="delivery_summary",
            observed="delivery_summary",
            decision_reason="accepted",
        ),
    ]
    report = summarize_decisions(rows)
    assert report["raw_label_matches"] == 1
    assert report["governed_label_matches"] == 2
    assert report["decision_counts"] == dict(
        accepted=1, guardrail=1, model_unsupported=0, below_threshold=1
    )


def test_executed_diagnostics_reconcile_to_fixed_case_results():
    report = run_intent_evaluation()
    diagnostics = report["decision_diagnostics"]
    assert sum(diagnostics["decision_counts"].values()) == report["cases"] == 18
    assert diagnostics["governed_label_matches"] == report["passed"]
    assert diagnostics["raw_label_matches"] == sum(
        row["model_label"] == row["expected"] for row in report["results"]
    )
    for row in report["results"]:
        assert row["observed"] == (row["model_label"] if row["accepted"] else "unsupported")
        assert (row["decision_reason"] == "accepted") == row["accepted"]
        if row["guardrail"]:
            assert row["decision_reason"] == "guardrail"
    assert report["reference_training_overlap"]["independent_holdout_claim_supported"] is False
    slices = diagnostics["by_expected_intent"]
    assert set(slices) == {
        "delivery_summary",
        "compare_delivery_periods",
        "delivery_exceptions",
        "unsupported",
    }
    assert sum(s["cases"] for s in slices.values()) == report["cases"]
    for field in ("raw_label_matches", "governed_label_matches"):
        assert sum(s[field] for s in slices.values()) == diagnostics[field]
    for intent, summary in slices.items():
        rows = [r for r in report["results"] if r["expected"] == intent]
        assert summary["cases"] == len(rows)
        assert summary["raw_label_matches"] == sum(r["model_label"] == intent for r in rows)
        assert summary["governed_label_matches"] == sum(r["observed"] == intent for r in rows)
        for reason, count in summary["decision_counts"].items():
            assert count == sum(r["decision_reason"] == reason for r in rows)
        assert sum(summary["decision_counts"].values()) == len(rows)
