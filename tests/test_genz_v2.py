import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data import pipeline as old
from synthetic_data.genz import load_candidates,validate,Thread,profanity,delex,DATA

def test_pilot_schema_and_legacy_lineage_are_honest():
    threads=load_candidates(220,20261103)
    assert len(threads)==220
    source=json.loads((old.DATA/'threads/SYN200_0001.json').read_text(encoding='utf-8'))
    assert [c['text'] for c in source['comments']]==[c['text'] for c in threads[0]['comments']]
    assert all(t['data_origin']=='synthetic' and not t['human_gold'] and not t['evaluation_eligible'] for t in threads)
    assert all(t['split']=='train' for t in threads[:200])
    assert all(type(c['annotation']['is_directed_attack']) is bool for t in threads for c in t['comments'])
    assert all(c['annotation']['needs_human_review'] for t in threads for c in t['comments'] if c['annotation']['label']=='UNCERTAIN')

def test_profanity_flag_does_not_assign_toxicity():
    assert profanity('Vcl, lag quá') and profanity('f.u.c.k') and profanity('sh1t')
    assert not profanity('NPC trong trò chơi đang đứng yên.')
    rows=load_candidates(220,20261103)
    assert any(c['annotation']['has_profanity'] and c['annotation']['label']=='CLEAN' for t in rows for c in t['comments'])

def test_compact_neutral_syntax_preserves_authored_words(tmp_path):
    text='@@1|unit|Unit scene\nA0 Hello in test only\nB1 Second test reply\nC2 Third unit response\n'
    (tmp_path/'scenarios_01.txt').write_text(text,encoding='utf-8')
    spec=old.read_catalogue(tmp_path)[0]
    assert spec['rows'][0]==['A','N','0','-','Hello in test only']

def test_targets_cannot_be_asserted_without_evidence():
    t=load_candidates(220,20261103)[0];t['comments'][5]['annotation']['target_evidence']=None
    with pytest.raises(ValueError,match='textual evidence'):Thread.model_validate(t)

def test_role_family_split_and_duplicate_checks():
    threads=load_candidates(220,20261103)
    report=validate(threads);assert report['status']=='PASS'
    family={}
    for t in threads:assert family.setdefault(t['scenario_family'],t['split'])==t['split']
    broken=copy.deepcopy(threads[:2]);broken[1]['comments'][0]['text']=broken[0]['comments'][0]['text']
    assert validate(broken)['exact_duplicate_comments']>=1

def test_dashboard_exports_have_no_labels_or_persona_leakage():
    from app.schemas import AnalyzeRequest
    p=DATA/'dashboard_threads/SGZ500_0001.json';obj=json.loads(p.read_text(encoding='utf-8'))
    AnalyzeRequest.model_validate(obj)
    assert set(obj)=={'thread_id','comments'}
    assert all('annotation' not in c for c in obj['comments'])
