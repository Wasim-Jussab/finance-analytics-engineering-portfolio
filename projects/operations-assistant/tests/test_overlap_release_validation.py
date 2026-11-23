from copy import deepcopy
from pathlib import Path

import pytest
from operations_assistant.adversarial_evaluation import run_adversarial_evaluation
from operations_assistant.intent_evaluation import run_intent_evaluation
from operations_assistant.routing_release import evaluate_release, load_release_policy


@pytest.mark.parametrize('mutation', [
    'missing_audit', 'wrong_total', 'wrong_non_overlap', 'normalization',
    'independent_claim', 'missing_question', 'integer_flag', 'missing_flag',
    'float_total', 'coherent_false_flags',
])
def test_release_rejects_invalid_overlap_evidence(mutation):
    report = deepcopy(run_intent_evaluation())
    audit = report['reference_training_overlap']
    if mutation == 'missing_audit':
        report.pop('reference_training_overlap')
    elif mutation == 'wrong_total':
        audit['overlapping_cases'] += 1
    elif mutation == 'wrong_non_overlap':
        audit['non_overlapping_cases'] += 1
    elif mutation == 'normalization':
        audit['normalization'] = 'unapproved normalization'
    elif mutation == 'independent_claim':
        audit['independent_holdout_claim_supported'] = True
    elif mutation == 'missing_question':
        report['results'][0].pop('question')
    elif mutation == 'integer_flag':
        report['results'][0]['overlaps_reference_training'] = 0
    elif mutation == 'missing_flag':
        report['results'][0].pop('overlaps_reference_training')
    elif mutation == 'float_total':
        audit['overlapping_cases'] = float(audit['overlapping_cases'])
    else:
        row = next(r for r in report['results'] if r['overlaps_reference_training'])
        row['overlaps_reference_training'] = False
        audit['overlapping_cases'] -= 1
        audit['non_overlapping_cases'] += 1
    assert report['passed'] == report['cases'] == 18
    policy = load_release_policy(Path('config/routing-release-policy.json'))
    with pytest.raises(ValueError, match='[Oo]verlap|independent holdout'):
        evaluate_release(report, run_adversarial_evaluation(), policy)
