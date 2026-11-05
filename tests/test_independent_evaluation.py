import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_ai_update import evaluate,gate

def verified(id='c',label='CLEAN'):
    # Explicitly fabricated unit-test metadata, never exported as real evaluation data.
    return {'thread_id':'unit','comment_id':id,'raw_text':'Unique standalone unit-only message '+id,'source_type':'real_anonymized','rights_status':'approved','rights_reference':'UNIT_TEST_ONLY',
      'split':'blind_evaluation','used_for_training':False,'used_for_rule_development':False,'review_status':'VERIFIED_SOLO','annotator_id':'test','reviewed_at':'2026-01-01T00:00:00Z','comment_label':label}

def test_missing_dataset_is_blocked_not_perfect_score():
    assert gate({'data_files':[]})['status']=='BLOCKED'
    with pytest.raises(ValueError):evaluate([],{})
@pytest.mark.parametrize('change',[{'source_type':'synthetic'},{'used_for_rule_development':True},{'used_for_training':True},{'review_status':'NEEDS_REVIEW'},{'rights_reference':''}])
def test_unverified_or_contaminated_records_cannot_publish_metrics(change):
    with pytest.raises(ValueError):evaluate([dict(verified(),**change)],{('unit','c'):0})
def test_real_calculator_has_known_nonperfect_confusion():
    result=evaluate([verified('a'),verified('b','TOXIC')],{('unit','a'):1,('unit','b'):1})
    assert result['metrics']['confusion_matrix']==[[0,1],[0,1]]
    assert result['metrics']['accuracy']==.5

def test_uncertain_is_explicitly_counted():
    result=evaluate([verified('a'),verified('b','UNCERTAIN')],{('unit','a'):0,('unit','b'):1})
    assert result['excluded_uncertain']==1 and result['metrics']['n']==1

def test_extra_prediction_ID_is_rejected():
    with pytest.raises(ValueError):evaluate([verified()],{('unit','c'):0,('unit','extra'):0})

def test_declared_real_metadata_cannot_hide_development_leakage():
    import json
    path=ROOT/'datasets/ai-update/review_v1/review.jsonl'
    sample=json.loads(path.read_text(encoding='utf-8').splitlines()[0])
    row=dict(verified(),raw_text=sample['raw_text'])
    with pytest.raises(ValueError,match='overlaps'):evaluate([row],{('unit','c'):0})
