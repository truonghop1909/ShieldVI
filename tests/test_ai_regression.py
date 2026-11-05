import csv,json,sys
from pathlib import Path
import pytest
from app.schemas import AnalyzeRequest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from ai_regression_data import load_threads,review_rows,export_review

def test_original_five_threads_and_reference_join():
    assert len(load_threads())==5
    rows=review_rows()
    assert len(rows)==150
    assert all(r['review_status']=='NEEDS_REVIEW' and not r['comment_label'] for r in rows)
    assert len({(r['thread_id'],r['comment_id']) for r in rows})==150

def test_review_export_never_overwrites_reviewer_work(tmp_path):
    p=tmp_path/'review.csv';export_review(p)
    p.write_text('human work',encoding='utf-8')
    with pytest.raises(FileExistsError):export_review(p)
    assert p.read_text()=='human work'

def test_counterexamples_include_mixed_attacks_and_non_attacks():
    data=json.loads((ROOT/'tests/fixtures/ai_update/counterexamples.json').read_text(encoding='utf-8'))
    assert data['source_type']=='synthetic' and not data['training_eligible']
    cases=data['cases'];assert len(cases)>=10 and len({c['text'] for c in cases})==len(cases)
    assert any(c['expected_attack'] and 'APOLOGY' in c['expected_context'] for c in cases)
    assert any(not c['expected_attack'] and 'QUOTE' in c['expected_context'] for c in cases)
    assert all(c['review_status']=='NEEDS_REVIEW' for c in cases)

def test_invalid_fixture_structure_is_rejected():
    with pytest.raises(ValueError):AnalyzeRequest.model_validate({'thread_id':'t','comments':[{'comment_id':'c','user_id':'u','parent_id':'missing','timestamp':'2026-01-01T00:00:00Z','text':'hello'}]})
