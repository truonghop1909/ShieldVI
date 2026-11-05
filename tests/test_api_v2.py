import json
from pathlib import Path
import pytest
from app.schemas import AnalyzeResponseV2
ROOT=Path(__file__).resolve().parents[1]
def request(text='Mình xin lỗi vì đã gọi bạn ngu.'):
    return {'thread_id':'v2test','comments':[{'comment_id':'c','user_id':'A','text':text,'timestamp':'2026-01-01T00:00:00Z'}]}
def test_v2_typed_and_v1_compatible_raw(client):
    p=request('[TEST_TOXIC] Mình xin lỗi vì đã gọi bạn ngu.')
    old=client.post('/api/analyze',json=p);new=client.post('/api/v2/analyze',json=p)
    assert old.status_code==new.status_code==200
    parsed=AnalyzeResponseV2.model_validate(new.json())
    assert parsed.analysis_version=='2.0' and not parsed.policy_executed
    assert old.json()['comments'][0]['toxicity_score']==parsed.comments[0].toxicity_score
    assert parsed.comments[0].toxic_for_moderation
    assert 'analysis_signals' not in old.json()['comments'][0]
    assert not parsed.comments[0].analysis_signals.attack_instance_candidate
    assert len(parsed.comments[0].analysis_signals.lexicon_version)==64
@pytest.mark.parametrize('path',sorted((ROOT/'datasets/fixtures/genz_regression').glob('*.json')),ids=lambda p:p.stem)
def test_v2_accepts_original_fixture_schema(client,path):
    result=client.post('/api/v2/analyze',json=json.loads(path.read_text(encoding='utf-8')))
    assert result.status_code==200
    assert len(AnalyzeResponseV2.model_validate(result.json()).comments)==30

def test_v2_unavailable_returns_503_without_fake_scores(client,monkeypatch):
    from app.main import app,get_predictor
    from fastapi import HTTPException
    def missing():raise HTTPException(503,'Model unavailable')
    app.dependency_overrides[get_predictor]=missing
    try:assert client.post('/api/v2/analyze',json=request()).status_code==503
    finally:app.dependency_overrides.pop(get_predictor,None)
