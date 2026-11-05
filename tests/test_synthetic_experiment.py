import copy,json,math,sys
from pathlib import Path
import pytest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from prepare_t029_training import validate_config
from train_t029_candidate import experimental_scope_matches
from synthetic_data.experiment import verify_view
CFG=json.loads((R/'configs/t029_synthetic_only_cpu_r06.json').read_text(encoding='utf-8'))

def scope():return {'synthetic_experiment':{'authorized':True,'run_id':CFG['run_id'],'config_sha256':'a'*64,'maximum_external_cost':0,'max_candidate_runs':1}}

def test_only_explicit_synthetic_recipe_may_have_fraction_one():
    assert validate_config(CFG)['max_synthetic_fraction']==1.
    for delta in ({'data_recipe':'legacy_mixed'},{'original_train':'some_real_train.csv'},{'evaluation_protocol':'real_independent'}):
        with pytest.raises(ValueError):validate_config({**CFG,**delta})

@pytest.mark.parametrize('delta',[{'run_id':'different'},{'data_recipe':'legacy_mixed'},{'evaluation_protocol':'real_independent'},
 {'resource':'paid_GPU'},{'maximum_external_cost':1},{'training_strategy':'full_finetune_gpu'}])
def test_experimental_exception_cannot_authorize_other_training(delta):
    assert not experimental_scope_matches(scope(),{**CFG,**delta},'a'*64)

def test_exception_requires_exact_config_and_single_run_authority():
    assert experimental_scope_matches(scope(),CFG,'a'*64)
    assert not experimental_scope_matches(scope(),CFG,'b'*64)
    s=scope();s['synthetic_experiment']['authorized']=False
    assert not experimental_scope_matches(s,CFG,'a'*64)

def test_actual_dataset_lineage_family_isolation_and_batches():
    d=R/'datasets/synthetic_genz';m,threads,q=verify_view(d,R/'datasets/synthetic_conversations/genz_v2')
    assert len(threads)==500 and m['comments']==5115 and m['labels']=={'CLEAN':4667,'TOXIC':369,'UNCERTAIN':79}
    assert m['splits']=={'synthetic_train':440,'synthetic_challenge':30,'synthetic_validation':30}
    assert m['human_gold'] is False and m['new_utterances_generated']==0 and q['status']=='PASS'
    roles={}
    for t in threads:roles.setdefault(t['scenario_family'],set()).add(t['split'])
    assert all(len(values)==1 for values in roles.values())
    batches=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((d/'batches').glob('*.json'))]
    assert batches[0]['threads']==20 and sum(b['threads'] for b in batches)==500
    assert all(25<=b['threads']<=50 for b in batches[1:])

def test_actual_prepared_training_excludes_uncertain_and_real_data():
    p=R/'reports/ai_update/synthetic_experiment_r06_20261103/prepared';m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (p/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==m['total_train_rows']==4398 and m['gold_train_rows']==0 and m['synthetic_fraction']==1.
    assert m['test_labels_used'] is False and m['real_training_used'] is False
    assert {r['label_origin'] for r in rows}=={'AI_synthetic_user_accepted'} and {r['human_gold'] for r in rows}=={False}
    assert all(r['sample_weight']==(m['positive_sample_weight'] if r['label'] else 1.) for r in rows)
    assert 1<m['positive_sample_weight']<=4
    assert not ({r['thread_id'] for r in rows}&{json.loads(line)['thread_id'] for line in (p/'validation.jsonl').read_text(encoding='utf-8').splitlines()})

def test_actual_r06_checkpoint_is_trained_head_only_and_not_activated():
    from synthetic_data.pipeline import file_sha
    p=Path(CFG['output_dir']);t=json.loads((p/'training_report.json').read_text(encoding='utf-8'))
    assert t['training_performed'] and t['optimizer_steps']>0 and t['train_rows']==t['synthetic_rows']==4398
    assert t['encoder_unchanged'] and t['baseline_unchanged'] and t['source_hashes_unchanged']
    assert not t['full_encoder_finetune'] and not t['activated'] and not t['test_scored_during_training']
    assert file_sha(p/'model.safetensors')==t['candidate_sha256'] and t['reload_probe_max_error']<=1e-5
    assert t['elapsed_seconds']<=CFG['max_training_seconds']

def test_actual_three_model_comparison_is_same_population_and_no_real_claim():
    p=R/'reports/ai_update/synthetic_experiment_r06_20261103/evaluation'
    r=json.loads((p/'comparison.json').read_text(encoding='utf-8'))
    assert set(r['metrics'])=={'V1','r05','r06'} and not r['human_gold'] and not r['promotion_allowed'] and not r['historical_original_test_scored']
    assert not r['independent_real_metrics'] and r['r05_holdout_exact_overlap']==r['r05_holdout_near_overlap']==0
    assert len(set(r['encoder_sha256'].values()))==1 and max(r['full_forward_probe_max_errors'].values())<=1e-5
    for split,n in [('synthetic_validation',306),('synthetic_challenge',311)]:
        for result in r['metrics'].values():
            m=result[split]['raw'];assert m['n']==n and m['threshold']==.41
            assert m['tp']+m['fp']+m['tn']+m['fn']==n

def test_full_gpu_notebook_is_prepared_and_unexecuted():
    import ast
    n=json.loads((R/'notebooks/T029_Synthetic_Experimental_R06.ipynb').read_text(encoding='utf-8'))
    assert n['metadata']['shieldvi_status']=='PREPARED_NOT_EXECUTED_FULL_GPU'
    for cell in n['cells']:
        if cell['cell_type']=='code':
            assert cell['execution_count'] is None and not cell['outputs'];ast.parse(''.join(cell['source']))

@pytest.mark.parametrize('text,expected',[('t thấy vậy, m nghĩ sao?',True),('Đm app lại lỗi.',True),('f*ck lỗi tiếp rồi.',True),('Mình đang xem video.',False)])
def test_teencode_reporting_mask_covers_requested_forms_without_assigning_labels(text,expected):
    from evaluate_synthetic_candidate import is_teencode
    assert is_teencode(text)==expected
