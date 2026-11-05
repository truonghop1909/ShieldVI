"""Append verified task evidence and inventory new research artifacts."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(P))
from synthetic_data.pipeline import atomic_json,file_sha
from verify_ai_readiness_lock import verify_lock

def statuses():
    out={}
    for path in (R/'tasks').rglob('T*.md'):
        matches=re.findall(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*\s*(.+)$',path.read_text(encoding='utf-8-sig'),re.M)
        if matches:out[str(path.relative_to(R)).replace('\\','/')]=matches[0]
    return out

if __name__=='__main__':
    initial=statuses();locked=json.loads((R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json').read_text())['files']
    updates=['tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md',
             'tasks/moderation-ai/T030-paired-offline-evaluation-ablation.md',
             'tasks/moderation-ai/T033-technical-report-thesis-handoff.md']
    note='''

## Fresh10 recovery — 04/11/2026, research only

648root tests PASS/0FAIL/1deprecation warning (28Fresh10 tests included). Imported10analysis JSONs/originalreference CSVs byte-preserved. Fresh10 development195binary: TP15→18,FP6→1,FN7→4,TN167→172,MacroF1.830105→.931861,target5→16/22,repeated2→6/7(P1/R.8571),evidence15/15correct,15/19coverage. Old890cached-V1 regression classification/target/repeated unchanged, no new errors.

Initial48comment post-freeze challenge exposed one new apology/report FP; original source/lock/outputs retained, then explicitly converted to development. Generic reporting-scope fix and v6.1 refreeze; another24comments first-scored after freeze: TP5/FP1/FN1/TN17,MacroF1.888889,target5/6,repeated1/2(P1/R.5),evidence2/2correct,2/4coverage. One metaphor FN/raw-score FP remain; no post-score tuning. All labels synthetic_reference, not human gold/independent real; no label edits.

Opt-in processor services/moderation-ai/app/experiments/fresh10_v6.py; evaluator scripts/evaluate_fresh10_recovery.py and evaluate_fresh10_challenge.py; tests/test_fresh10_recovery.py. API/Dashboard stillv5. V1/r06/default/0.41/readiness1311hashes unchanged; no training/deploy. New fixture exclusion extension prepared but NOT merged into locked runtime exclusions. T028/T029formalBLOCKED,T030–T033PARTIAL; historicalDONE preserved. Report docs/ai-update/final-report/FRESH10_RECOVERY.md, evidence reports/ai_update/fresh10_recovery_20261103/README.md, hashes ARTIFACTS.json. Continue only with separate future release/evaluation scope; no automatic activation or new training.
'''
    for name in updates:
        assert name not in locked
        path=R/name
        if '## Fresh10 recovery — 04/11/2026, research only' not in path.read_text(encoding='utf-8-sig'):
            with path.open('a',encoding='utf-8') as stream:stream.write(note)
    scope_path=R/'tasks/CURRENT_AI_SCOPE.json';assert 'tasks/CURRENT_AI_SCOPE.json' not in locked
    scope=json.loads(scope_path.read_text(encoding='utf-8'))
    scope['fresh10_recovery']={'status':'VERIFIED_OPT_IN_RESEARCH_ONLY','report':'docs/ai-update/final-report/FRESH10_RECOVERY.md',
        'versions':{'context':'context-v6.1-research','target':'target-v6.1-research','repeated':'repeated-v6.1-research'},
        'root_tests_passed':648,'root_tests_failed':0,'fresh10_final_macro_f1':.9318610664616676,'fresh10_target_correct':16,
        'fresh10_reference_targets':22,'fresh10_repeated_tp':6,'fresh10_reference_events':7,
        'final_unseen_at_scoring_comments':24,'final_challenge_repeated_tp':1,'final_challenge_repeated_reference':2,
        'first48_reclassified_as_development':True,'known_new_first48_fp_retained_in_history':True,
        'human_gold':False,'training_performed':False,'production_changed':False,'default_v5_changed':False,
        'readiness_lock_changed':False,'new_exclusion_extension_merged':False}
    atomic_json(scope_path,scope)
    assert statuses()==initial
    ready=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert ready['status']=='PASS'
    atomic_json(P/'readiness_final.json',ready)
    atomic_json(P/'task_status_integrity.json',{'status':'PASS','historical_first_statuses_preserved':len(initial),'statuses':initial,
        'current_formal_statuses':{'T028':'BLOCKED','T029':'BLOCKED','T030':'PARTIAL','T031':'PARTIAL','T032':'PARTIAL','T033':'PARTIAL'}})
    report=R/'docs/ai-update/final-report/FRESH10_RECOVERY.md'
    for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:')):continue
        assert (report.parent/target).resolve().exists() or target.endswith('/ARTIFACTS.json'),target
    roots=[P,R/'datasets/fixtures/fresh10_regression_v1',R/'datasets/fixtures/fresh10_postfix_holdout_v1',R/'datasets/fixtures/fresh10_postfix_holdout_v2',R/'services/moderation-ai/app/experiments']
    paths={path for root in roots for path in root.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.name!='ARTIFACTS.json'}
    paths.update(R/name for name in updates+['tasks/AUTO_PROGRESS.md','tasks/CURRENT_AI_SCOPE.json',
        'scripts/evaluate_fresh10_recovery.py','scripts/evaluate_fresh10_challenge.py','tests/test_fresh10_recovery.py'])
    paths.add(report)
    atomic_json(P/'ARTIFACTS.json',{'scope':'Fresh10 synthetic development; no default activation',
        'files':{str(path.relative_to(R)).replace('\\','/'):file_sha(path) for path in sorted(paths)},
        'training_performed':False,'readiness_lock_sha256':ready['lock_sha256'],'root_tests_passed':648,
        'report_links_checked':True,'historical_task_states_preserved':len(initial)})
    print(json.dumps({'status':'PASS','indexed_files':len(paths),'historical_task_statuses_preserved':len(initial),
                      'readiness_files':ready['files_checked'],'root_tests_passed':648}))
