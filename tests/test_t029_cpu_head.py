import copy,hashlib,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from prepare_t029_training import validate_config
from train_t029_candidate import cpu_authorization_matches
CFG=json.loads((ROOT/'configs/t029_genz500_cpu_head.json').read_text(encoding='utf-8'))

def receipt():
    request='Run remaining tasks with feasible local alternatives'
    return {'authorization_type':'bounded_local_cpu_request_v1','authorized_local_task_execution':True,'paid_services_allowed':False,
       'source_user_request':request,'source_user_request_sha256':hashlib.sha256(request.encode()).hexdigest(),
       'config_sha256':'c'*64,'prepared_manifest_sha256':'d'*64,'resource':'local_CPU','max_training_seconds':900,'maximum_external_cost':0,'max_cpu_threads':4,
       'user_approved_exact_hyperparameters':False}

@pytest.mark.parametrize('field,value',[('resource','paid_GPU'),('cpu_threads',8),('max_training_seconds',3600),('maximum_external_cost',1),('epochs',4),('feature_batch_size',128),('evaluation_protocol','real_independent')])
def test_cpu_recipe_cannot_escalate_bounded_authority(field,value):
    cfg=copy.deepcopy(CFG);cfg[field]=value
    with pytest.raises(ValueError):validate_config(cfg)

@pytest.mark.parametrize('field,value',[('paid_services_allowed',True),('config_sha256','bad'),('prepared_manifest_sha256','bad'),('max_cpu_threads',12),('source_user_request_sha256','bad'),('resource','Colab_GPU')])
def test_local_authority_cannot_be_reused_for_modified_resources_or_inputs(field,value):
    r=receipt();r[field]=value
    assert not cpu_authorization_matches(CFG,'c'*64,'d'*64,r)

def test_authority_records_scope_instead_of_faking_manual_hyperparameter_approval():
    r=receipt();assert not r['user_approved_exact_hyperparameters']
    assert cpu_authorization_matches(CFG,'c'*64,'d'*64,r)
    assert not cpu_authorization_matches(CFG,'c'*64,'d'*64,{'approved':True,'cost_acknowledged':True})

def test_actual_cpu_candidate_has_optimizer_steps_and_unchanged_encoder():
    from refine_model import file_hash
    p=Path(CFG['output_dir']);r=json.loads((p/'training_report.json').read_text(encoding='utf-8'))
    assert r['status']=='COMPLETE_HEAD_TRAINED_NOT_ACTIVATED' and r['training_performed'] and r['optimizer_steps']>0
    assert r['encoder_unchanged'] and r['encoder_sha_before']==r['encoder_sha_after'] and r['baseline_unchanged']
    assert r['changed_parameter_names'] and all(name.startswith('classifier.') for name in r['changed_parameter_names'])
    assert not r['full_encoder_finetune'] and not r['test_scored_during_training'] and not r['activated']
    assert r['elapsed_seconds']<=CFG['max_training_seconds'] and r['reload_probe_max_error']<=1e-5
    assert file_hash(p/'model.safetensors')==r['candidate_sha256']


def test_actual_candidate_review_respects_frozen_gates_and_production_boundary():
    p=ROOT/'reports/ai_update/all_tasks_cpu_20261103/candidate_evaluation.json';r=json.loads(p.read_text(encoding='utf-8'))
    assert r['selection_from_validation_only'] and not r['test_used_for_selection_or_training'] and not r['production_changed']
    assert r['default_before']==r['default_after'] and r['input_hashes_unchanged']
    assert r['API_smoke']['internal_social_contract']==200 and r['API_smoke']['unavailable']==503 and r['API_smoke']['rollback_recovered']==200
    expected='APPROVE_LOCAL_SHADOW_ONLY' if all(r['gates'].values()) else 'REJECT_PROMOTION_KEEP_EXISTING_DEFAULT'
    assert r['decision']==expected and not r['production_activation_allowed']


def test_actual_candidate_registry_refuses_implicit_activation():
    from app.model_registry import LocalModelRegistry,RegistryError
    reg=LocalModelRegistry(ROOT/'configs/model_registry.cpu_r03.local.json')
    assert Path(reg.verify('candidate_cpu')).resolve()==Path(CFG['output_dir']).resolve()
    with pytest.raises(RegistryError,match='Unapproved'):reg.load('candidate_cpu')
