import copy,json,hashlib,sys
from pathlib import Path
import pytest
from app.model_registry import LocalModelRegistry,RegistryError
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data.genz import DATA,verified_export
from prepare_t029_training import validate_config
from refine_model import normalize,file_hash

class Predictor:
    threshold=.41
    def predict_scores(self,texts):return [.2]*len(texts)

def registry(tmp_path):
    base=tmp_path/'base';base.mkdir()
    for n in ('model.safetensors','config.json','tokenizer_config.json'):(base/n).write_bytes(b'unit artifact only')
    (base/'threshold_config.json').write_text('{"threshold":0.41}',encoding='utf-8')
    hashes={p.name:file_hash(p) for p in base.iterdir()}
    entry={'path':str(base),'threshold':.41,'role':'baseline','approved_for_selection':True,'sha256':hashes}
    manifest={'schema_version':1,'threshold':.41,'fallback':'v1','models':{'v1':entry,'candidate':{**entry,'path':str(tmp_path/'missing'),'role':'candidate','approved_for_selection':False}}}
    p=tmp_path/'registry.json';p.write_text(json.dumps(manifest),encoding='utf-8');return LocalModelRegistry(p),base

def test_local_shadow_missing_candidate_falls_back_without_env_changes(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_PATH','unchanged-live-path')
    r,_=registry(tmp_path);p,audit=r.load('candidate',shadow=True,loader=lambda path:Predictor())
    import os
    assert audit['fallback_used'] and audit['selected']=='v1' and not audit['production_changed']
    assert os.environ['MODEL_PATH']=='unchanged-live-path' and p.threshold==.41

def test_registry_rejects_unapproved_selection_and_corrupt_baseline(tmp_path):
    r,base=registry(tmp_path)
    with pytest.raises(RegistryError,match='Unapproved'):r.load('candidate',loader=lambda p:Predictor())
    (base/'model.safetensors').write_bytes(b'corrupt unit artifact')
    with pytest.raises(RegistryError,match='integrity'):r.load('v1',loader=lambda p:Predictor())

def test_shadow_rejects_invalid_probabilities_and_misaligned_scores(tmp_path):
    r,_=registry(tmp_path)
    class Broken(Predictor):
        def predict_scores(self,texts):return [float('nan')]*len(texts)
    with pytest.raises(RegistryError,match='probabilities'):r.shadow_compare(Predictor(),Broken(),['unit text'])
    class Short(Predictor):
        def predict_scores(self,texts):return []
    with pytest.raises(RegistryError,match='count'):r.shadow_compare(Predictor(),Short(),['unit text'])

def test_complete_genz_source_and_prepared_challenge_are_isolated():
    m,threads,r=verified_export();assert m['threads']==500 and r['comments']==5115
    prepared=ROOT/'reports/ai_update/T029/genz500_prepared'
    p=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'))
    assert p['evaluation_protocol']=='synthetic_development' and p['total_train_rows']==11340
    dev={normalize(c['text']) for t in threads if t['split']=='development_challenge' for c in t['comments']}
    rows=[json.loads(l) for l in (prepared/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert not dev & {normalize(row['text']) for row in rows}
    assert all(row['label'] in (0,1) for row in rows) and not p['training_performed']
    assert all(file_hash(prepared/name)==sha for name,sha in p['output_sha256'].items())

def test_unknown_training_protocol_cannot_bypass_gates():
    c=json.loads((ROOT/'configs/t029_genz500_candidate.json').read_text(encoding='utf-8'))
    c['evaluation_protocol']='trust_ai_as_real'
    with pytest.raises(ValueError,match='protocol'):validate_config(c)

def test_altered_export_not_accepted_by_readiness_marker(tmp_path):
    manifest=json.loads((DATA/'dataset_manifest.json').read_text(encoding='utf-8'))
    manifest['status']='READY'
    first=next(iter(manifest['output_sha256']))
    (tmp_path/'dataset_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    (tmp_path/first).write_text('changed data cannot be approved with a marker',encoding='utf-8')
    with pytest.raises(ValueError,match='checksum'):verified_export(tmp_path)

def test_synthetic_protocol_still_requires_resource_receipt_and_cuda():
    import train_t029_candidate as runner
    report,_,_=runner.checks(ROOT/'configs/t029_genz500_candidate.json',ROOT/'reports/ai_update/T029/genz500_prepared',Path('C:/Users/admin/Downloads/visobert_toxic_final'))
    assert report['status']=='BLOCKED' and not report['training_performed']
    assert any('G3' in b for b in report['blockers']) and not any('G2:' in b for b in report['blockers'])

def test_frozen_baseline_ablation_preserves_raw_and_documents_reference_scope():
    d=ROOT/'reports/ai_update/T030/regression_ablation'
    m=json.loads((d/'metrics.json').read_text(encoding='utf-8'))
    assert m['cached_real_V1_T020'] and not m['new_model_inference'] and not m['human_gold']
    assert set(m['variants'])=={'B0','B1','B2','B3'} and m['raw_unchanged_all_variants']
    baseline=m['variants']['B0']['comment_metrics']
    assert all(v['comment_metrics']==baseline for v in m['variants'].values())
    lock=json.loads((d/'frozen_experiment.json').read_text(encoding='utf-8'))
    assert all(file_hash(ROOT/p)==sha for p,sha in lock['input_and_baseline_sha256'].items())
