"""Audit existing evidence and seal immutable research inputs; no inference/training."""
import ast,json,sqlite3,sys
from pathlib import Path
from datetime import datetime
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;OLD=R/'reports/ai_update/repeated_recovery_20261103'
sys.path.insert(0,str(R/'scripts'))
from verify_ai_readiness_lock import digest,verify_lock
from synthetic_data.pipeline import atomic_json
from real_dataset.validation import validate_dataset

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def progress(stage,detail):
    path=P/'progress.json';value=read(path) if path.exists() else {'training_performed':False,'milestones':[]}
    if any(x['stage']==stage and x['detail']==detail for x in value['milestones']):return
    value.update(current=stage);value['milestones'].append({'stage':stage,'detail':detail});atomic_json(path,value)
    with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as out:out.write('\n\n## Stabilization/readiness — '+stage+'\n\n'+detail+'\n')

if __name__=='__main__':
    lock_path=P/'READINESS_LOCK.json'
    if lock_path.exists():raise FileExistsError('Never reseal a frozen version; verify it or create a new version')
    frozen=read(OLD/'frozen_rule_lock.json')
    assert all(digest(R/'services/moderation-ai/app'/name)==h for name,h in frozen['rule_sha256'].items())
    assert read(P/'review_browser.json')['status']=='PASS' and read(P/'review_cleanup.json')['temporary_corpus_removed']
    assert '47 passed' in (P/'review_tests.log').read_bytes().decode('utf-16')
    prior=read(OLD/'evaluation/outputs.json')['r06']['after'];data=R/'datasets/fixtures/repeated_holdout_20261103'
    audits=[]
    for ident in ('REP_FRESH_02','REP_FRESH_11'):
        t=read(data/(ident+'.json'));out=next(x['output'] for x in prior if x['output']['thread_id']==ident)
        rows={c['comment_id']:c for c in out['comments']};attacks=[c for c in t['comments'] if c['annotation']['label']=='TOXIC']
        facts=[{'comment_id':c['comment_id'],'text':c['text'],'actor':c['user_id'],'reference_target':c['annotation']['directed_at_user_id'],
            'timestamp':c['timestamp'],'context_attack':rows[c['comment_id']]['analysis_signals']['directed_attack_candidate'],
            'attack_instance':rows[c['comment_id']]['analysis_signals']['attack_instance_candidate'],
            'target_evidence':rows[c['comment_id']]['analysis_signals']['target_evidence']} for c in attacks]
        if ident.endswith('02'):
            assert not facts[0]['context_attack'] and facts[1]['attack_instance']
            cause='Bounded context vocabulary does not recognize the new cục chì metaphor; only one qualified attack. Coverage limitation, not evidence grouping bug.'
        else:
            delta=(datetime.fromisoformat(attacks[1]['timestamp'])-datetime.fromisoformat(attacks[0]['timestamp'])).total_seconds()
            assert delta==3960 and delta>1800 and facts[0]['context_attack'] and facts[1]['attack_instance']
            assert not facts[0]['attack_instance']
            cause='66-minute gap exceeds the predeclared30-minute reciprocal root-target window; intended abstention. No window expansion to fit this challenge.'
        assert not out['evidence']
        audits.append({'thread_id':ident,'classification':'KNOWN_COVERAGE_OR_SAFETY_LIMIT','cause':cause,'technical_bug_proven':False,
            'runtime_changes_performed':False,'facts':facts})
    atomic_json(P/'repeated_misses_audit.json',{'status':'AUDITED_NO_TECHNICAL_FIX_JUSTIFIED','events':audits,
        'source_outputs_sha256':digest(OLD/'evaluation/outputs.json'),'rules_unchanged_since_pre_challenge_lock':True,
        'synthetic_reference_only':True,'repeated_challenge_result_unchanged':'4/6,P1.0,R0.6667,evidence8/8'})
    progress('TWO_MISSES_AUDITED','Both misses are known coverage/safety limits, no technical bug proven: unseen metaphor and66minute gap beyond30minute root exchange. No rule/label edits, no challenge re-inference; preserve4/6/evidence8/8.')
    quality=validate_dataset(R/'datasets/real_conversations');atomic_json(P/'T028_PREPARATION_SNAPSHOT.json',quality)
    assert quality['actual_threads']==0 and not quality['t028_real_acceptance_ready']
    assert read(R/'datasets/real_conversations/manifests/collection_policy.json')['collection_enabled'] is False
    progress('T028_TOOLS_VERIFIED','47protocol testsPASS; local Chrome UI readinessPASS with0review submissions/no AI predictions. Same-human Round2 rejects stale Round1 revisions at API lock; no runtime fix needed. Real valid0/200, manual intake quarantine is not an admitted cohort. Manual-source promotion still needs verified source receipt/supported adapter; no labels requested or fabricated.')
    files={}
    def add(p,expected=None):
        p=Path(p).resolve();name=p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix()
        actual=digest(p)
        if expected is not None:assert actual==expected,name
        files[name]=actual
    protected=read(OLD/'integrity.json')['protected_hashes']
    for name,h in protected.items():assert digest(Path(name))==h,name
    atomic_json(P/'protected_integrity.json',{'status':'PASS','protected_hashes_checked':len(protected),'live_SQLite_unchanged':True,
        'V1_and_candidates_unchanged':True,'canonical_labels_and_old_test_unchanged':True})
    # Freeze existing evidence in place; mutable task/progress files remain outside.
    for name,h in read(OLD/'ARTIFACTS.json')['sha256'].items():
        if not name.startswith('tasks/'):add(R/name,h)
    model_paths={name:Path(entry['path']) for name,entry in read(R/'configs/model_registry.repeated_recovery.local.json')['models'].items() if name in ('v1','v1_1','candidate_r05','candidate_r06')}
    models={}
    for name,path in model_paths.items():
        for p in path.iterdir():
            if p.is_file():add(p)
        models[name]={'path':str(path),'weights_sha256':digest(path/'model.safetensors'),'threshold':read(path/'threshold_config.json')['threshold']}
        assert models[name]['threshold']==.41
    sources=[R/'datasets/synthetic_conversations/genz_v2',R/'datasets/synthetic_genz']
    for directory in sources:
        m=read(directory/'dataset_manifest.json');add(directory/'dataset_manifest.json')
        for tid,h in m['thread_sha256'].items():add(directory/'threads'/(tid+'.json'),h)
        for name,h in m['output_sha256'].items():add(directory/name,h)
    for p in (R/'datasets/fixtures/context_recovery_v1').rglob('*'):
        if p.is_file():add(p)
    for p in (R/'datasets/fixtures/genz_regression').glob('*'):
        if p.is_file():add(p)
    for directory in [R/'services/moderation-ai/app',R/'services/social-api/src',R/'apps/social-web/src',R/'apps/moderation-web/src',R/'apps/moderation-web/legacy-v3/src',R/'scripts/real_dataset']:
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p) and p.suffix in ('.py','.js','.jsx','.css','.html','.json'):add(p)
    for p in (R/'contracts').glob('*.json'):add(p)
    for p in (R/'tests').glob('test_*.py'):add(p)
    for name in ('scripts/verify_ai_readiness_lock.py','templates/T028_MANUAL_INTAKE.example.json','configs/model_registry.local.json',
        'configs/t029_synthetic_only_cpu_r06.json','models/candidates/T029_synthetic_only_head_cpu_20261103_r06/checkpoint_manifest.json',
        'reports/ai_update/synthetic_experiment_r06_20261103/predeclared_protocol.json','reports/ai_update/synthetic_experiment_r06_20261103/training_execution.json',
        'reports/ai_update/synthetic_experiment_r06_20261103/evaluation/comparison.json','docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md'):add(R/name)
    for name in ('repeated_misses_audit.json','protected_integrity.json','T028_PREPARATION_SNAPSHOT.json','review_browser.json','review_cleanup.json','review_tests.log'):add(P/name)
    versions={}
    for name in ('context_signals','target_signals','signal_engine','context_assessment'):
        module=ast.parse((R/'services/moderation-ai/app'/(name+'.py')).read_text(encoding='utf-8-sig'))
        for node in module.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('VERSION','RULE_VERSION') for t in node.targets):versions[name]=ast.literal_eval(node.value)
    lock={'schema_version':1,'status':'FROZEN_RESEARCH_READINESS','snapshot_id':'r06_context-v5_target-v5_repeated-v5_20261103',
        'client_date':'2026-11-03','timezone':'Asia/Saigon','threshold':.41,'training_allowed':False,'production_activation_allowed':False,
        'human_gold':False,'T028_status':'BLOCKED','models':models,'rule_versions':versions,
        'external_model_roots':[str(path.resolve()) for path in model_paths.values() if not path.resolve().is_relative_to(R)],
        'frozen_evaluation':'V1/r05/r06 raw and context/target/repeated ablations; synthetic development only, no fresh inference',
        'test_evidence':{'AI_existing':610,'Social_existing':177,'new_review_protocol':47,'Social_browser':'PASS_FIXTURE_AI','model_ASGI_shadow_rollback':'PASS_ACTUAL_MODELS'},
        'live_annotation_databases_frozen':False,'reason_live_databases_excluded':'Human review will change them; immutable sources/evidence are locked, no operational DB write protection imposed.',
        'files':dict(sorted(files.items()))}
    atomic_json(lock_path,lock);result=verify_lock(lock_path);assert result['status']=='PASS',result
    atomic_json(P/'initial_lock_verification.json',result)
    progress('VERSION_AND_EVIDENCE_FROZEN',f"Frozen r06/ViSoBERT/V1.1/r05, context-v5,target-v5,repeated-v5, manifests/schema/evaluation/E2E/tests in READINESS_LOCK.json({len(files)}hashes). Read-only verifierPASS; no runtime/model modifications. Latest stabilization tests will be attached by separate attestation, never reseal this lock.")
    print(json.dumps({'status':result['status'],'frozen_files':len(files),'rule_versions':versions,'real_threads':quality['actual_threads'],'runtime_changes':0}))
