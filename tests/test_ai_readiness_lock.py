"""Hash/scope guard checks, using temporary plain files for tamper cases."""
import json,sys
from pathlib import Path
import pytest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from verify_ai_readiness_lock import digest,verify_lock

def make_lock(root,files,**changes):
    value={'schema_version':1,'status':'FROZEN_RESEARCH_READINESS','threshold':.41,'training_allowed':False,
        'production_activation_allowed':False,'human_gold':False,'T028_status':'BLOCKED','files':files,**changes}
    path=root/'fixture_lock.json';path.write_text(json.dumps(value),encoding='utf-8');return path

def test_actual_frozen_r06_rule_dataset_and_evidence_bundle_verifies_without_inference():
    result=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json')
    assert result['status']=='PASS' and result['files_checked']>100
    assert not result['training_performed'] and not result['model_inference_performed']

def test_changed_frozen_artifact_is_reported_not_resealed(tmp_path):
    p=tmp_path/'plain_fixture.txt';p.write_text('version one',encoding='utf-8')
    lock=make_lock(tmp_path,{'plain_fixture.txt':digest(p)})
    assert verify_lock(lock,tmp_path)['status']=='PASS'
    original=digest(lock);p.write_text('version two',encoding='utf-8')
    result=verify_lock(lock,tmp_path)
    assert result['status']=='FAIL' and result['errors']==['changed:plain_fixture.txt'] and digest(lock)==original

def test_bundle_cannot_read_unregistered_parent_path(tmp_path):
    lock=make_lock(tmp_path,{'../not_registered.txt':'0'*64})
    result=verify_lock(lock,tmp_path)
    assert result['status']=='FAIL' and result['errors']==['path_outside_bundle_roots:../not_registered.txt']

@pytest.mark.parametrize('change',[{'threshold':.42},{'training_allowed':True},{'production_activation_allowed':True},{'human_gold':True}])
def test_scope_changes_cannot_approve_training_production_or_gold(tmp_path,change):
    p=tmp_path/'plain_fixture.txt';p.write_text('plain test file',encoding='utf-8')
    lock=make_lock(tmp_path,{'plain_fixture.txt':digest(p)},**change)
    assert verify_lock(lock,tmp_path)['status']=='FAIL'
