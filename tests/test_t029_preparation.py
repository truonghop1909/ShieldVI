"""T029 readiness and leakage tests. No optimizer or model training is executed."""
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from prepare_t029_training import validate_config,remove_near
from refine_model import clean_train,file_hash
import train_t029_candidate as runner

@pytest.fixture
def config():return json.loads((ROOT/'configs/t029_candidate.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('field,value',[('threshold',.5),('epochs',0),('learning_rate',.5),('max_synthetic_fraction',1),('max_length',9999),('max_training_seconds',999999)])
def test_rejects_unbounded_or_changed_proposal(config,field,value):
    config[field]=value
    with pytest.raises(ValueError):validate_config(config)

def test_exact_and_near_holdout_copies_are_excluded_but_source_not_changed():
    heldout='Một bình luận dài để kiểm tra dữ liệu gần trùng giữa training và tập đánh giá độc lập.'
    rows=[{'id':'exact','text':heldout,'label':1},{'id':'near','text':heldout[:-1]+'!','label':1},{'id':'safe','text':'Một ý tưởng khác hẳn về việc bố trí kệ sách và ánh sáng trong phòng.','label':0}]
    original=copy.deepcopy(rows);kept,counts=clean_train(rows,[heldout]);kept,removed=remove_near(kept,[heldout],.9,40)
    assert counts['overlap_removed']==1 and [r['id'] for r in removed]==['near']
    assert [r['id'] for r in kept]==['safe'] and rows==original

def test_short_exact_overlap_still_rejected_before_near_length_guard():
    rows=[{'id':'a','text':'Cảm ơn bạn!','label':0}]
    kept,counts=clean_train(rows,['cảm ơn bạn!']);assert not kept and counts['overlap_removed']==1

def test_default_preflight_never_enters_training(monkeypatch):
    report={'status':'BLOCKED','blockers':['G2 missing','G3 missing'],'training_performed':False}
    monkeypatch.setattr(runner,'checks',lambda *a:(report,{},{}))
    assert runner.run('unused','unused','unused')==report

def test_run_request_with_missing_gate_fails_before_model_or_optimizer(monkeypatch):
    monkeypatch.setattr(runner,'checks',lambda *a:({'status':'BLOCKED','blockers':['G2 missing']},{},{}))
    with pytest.raises(runner.TrainingBlocked,match='G2 missing'):runner.run('unused','unused','unused',execute=True)

def test_prepared_real_artifact_counts_provenance_and_hashes(config):
    root=ROOT/'reports/ai_update/T029/prepared';m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    assert m['status']=='PREPARED_NOT_TRAINED' and m['total_train_rows']==8936 and m['synthetic_train_rows']==1994
    assert m['synthetic_fraction']<=config['max_synthetic_fraction'] and not m['training_performed'] and not m['test_labels_used']
    for name,sha in m['output_sha256'].items():assert file_hash(root/name)==sha
    for source in m['sources'].values():assert file_hash(source['path'])==source['sha256']
    rows=[json.loads(line) for line in (root/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert sum(row['label_origin']=='AI_synthetic_user_accepted' for row in rows)==1994
    assert not (root/'test.jsonl').exists()
