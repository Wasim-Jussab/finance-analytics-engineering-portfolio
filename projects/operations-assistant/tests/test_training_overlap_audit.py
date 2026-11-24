import pytest
from operations_assistant.intent_evaluation import normalize_question, run_intent_evaluation


@pytest.mark.parametrize('question', [
    'Show changes in delivery outcomes',
    ' SHOW changes in delivery outcomes! ',
    'Show changes in delivery outcomes?',
])
def test_normalization_exposes_punctuation_and_case_variants(question):
    assert normalize_question(question) == 'show changes in delivery outcomes'


def test_report_discloses_reused_training_cases_without_changing_predictions():
    report = run_intent_evaluation()
    rows = {row['question']: row for row in report['results']}
    assert rows['Show changes in delivery outcomes']['overlaps_reference_training']
    assert not rows['Give me a snapshot of delivery results']['overlaps_reference_training']
    audit = report['reference_training_overlap']
    assert audit['overlapping_cases'] > 0
    assert audit['overlapping_cases'] == sum(
        row['overlaps_reference_training'] for row in report['results']
    )
    assert audit['overlapping_cases'] + audit['non_overlapping_cases'] == report['cases']
    assert audit['independent_holdout_claim_supported'] is False
    assert report['passed'] == report['cases'] == 18
