"""Verify audit evidence, append factual task notes, retain known failures."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from verify_ai_readiness_lock import verify_lock
from audit_nov10 import save_progress

def log_text(path):
    data=path.read_bytes()
    return data.decode('utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')

def statuses():
    out={}
    for path in (R/'tasks').rglob('T*.md'):
        matches=re.findall(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*\s*(.+)$',path.read_text(encoding='utf-8-sig'),re.M)
        if matches:out[str(path.relative_to(R)).replace('\\','/')]=matches[0]
    return out

if __name__=='__main__':
    initial=statuses();assert len(initial)==27
    assert re.search(r'677 passed, 1 warning',log_text(P/'full_tests.log'))
    assert re.search(r'2 failed, 1 passed',log_text(P/'quote_red_tests.log'))
    ready_path=R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json'
    ready=verify_lock(ready_path);assert ready['status']=='PASS'
    lock=json.loads((P/'challenge_lock.json').read_text())
    assert file_sha(R/'services/moderation-ai/app/experiments/fresh10_v6.py')==lock['experimental_module_sha256']
    assert file_sha(ready_path)==lock['readiness_lock_sha256']
    metrics=json.loads((P/'metrics.json').read_text());assert metrics['before']==metrics['after']
    assert metrics['pattern_hit_counts']=={} and metrics['wire_exact_replay_threads']==10
    for name in ('fresh10_metrics.json','old_regression_metrics.json'):
        a=json.loads((P/'old_regression'/name).read_text());b=json.loads((R/'reports/ai_update/fresh10_recovery_20261103/development_v3'/name).read_text())
        for key in ('classification','grounding'):assert a[key]==b[key]
    d=R/'datasets/fixtures/nov10_regression_v1';manifest=json.loads((d/'manifest.json').read_text())
    for name,digest in manifest['files'].items():assert file_sha(d/name)==digest
    c=R/'datasets/fixtures/nov10_audit_challenge_v1';challenge=json.loads((c/'manifest.json').read_text())
    assert challenge['experiment_lock_sha256']==file_sha(P/'challenge_lock.json')
    for tid,digest in challenge['thread_sha256'].items():assert file_sha(c/'threads'/(tid+'.json'))==digest
    overlay=R/'datasets/real_conversations/manifests/development_exclusions.research_20261104.json'
    exclusion=json.loads((P/'exclusion_verification.json').read_text());assert file_sha(overlay)==exclusion['manifest_sha256']
    assert all(x['status']=='EXCLUDED_DEVELOPMENT' for x in exclusion['nov10_checks'])
    runtime=json.loads((P/'runtime_probe.json').read_text());assert runtime['status']=='PASS' and len(runtime['calls'])==63
    atomic_json(P/'readiness_final.json',ready)
    updates=['tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md',
        'tasks/moderation-ai/T030-paired-offline-evaluation-ablation.md','tasks/moderation-ai/T033-technical-report-thesis-handoff.md']
    locked=json.loads(ready_path.read_text())['files']
    note='''

## NOV10 root-cause audit — 04/11/2026

Audit complete; rules/checkpoints/default unchanged. Imported10inputs/10v6.1analysis/200comments and original synthetic_reference CSVs. Exact wire replay10/10; 7attack predicate families have0matches before/after masking on all200comments, so context.attack_candidatefalse causes infer_target earlyreturn and0instances. Actual canonical ASGI r06 probe63comments PASS: contextcalled20times/thread forTest12/15/20, rawdiff0; positivecontrol repeatedPASS. Not a Dashboard-v5 assumption or global disable. Eight referencepairs10–20min have0qualifiedinstances, not time-window rejection.

NOV10 unchanged:199binary,TP7/FP3/FN15/TN174,MacroF1.694160,target0/22,repeated0/8. OldFresh10+890cachedregression unchanged.24adjudication candidates pending/no reference edits. Versioned development_exclusions.research_20261104.json registers NOV10/Fresh10/challenges;10/10NOV10 excluded via explicit overlay preflight, sealed defaultmanifest/loader unchanged.

Standardroot677PASS/0FAIL/1warning. Separate supplemental quote-scope red probes2FAIL/1PASS: new locked24comment challenge found narrative-quote attribution bug; NOT fixed or hidden. Challengev6.1:23binary TP6/FP1/FN0/TN16,Macro.946387,target5/6,repeated1/2(P1/R.5),evidence2/2correct/2of4referencecoverage. No post-inference tuning. Audit scope complete, quote fix/indirect coverage still OPEN; next revision needs red-before-fix and fresh challenge. Readiness1311SHA PASS; no train/deploy/DB/default edits. FormalT028/T029BLOCKED,T030–T033PARTIAL/historicalDONE preserved.

Report docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md; evidence/reproduction reports/ai_update/nov10_audit_20261104/README.md; labels-to-review adjudication_candidates.csv; source/hash inventory ARTIFACTS.json.
'''
    for name in updates:
        assert name not in locked
        path=R/name
        if '## NOV10 root-cause audit — 04/11/2026' not in path.read_text(encoding='utf-8-sig'):
            with path.open('a',encoding='utf-8') as stream:stream.write(note)
    scope_path=R/'tasks/CURRENT_AI_SCOPE.json';scope=json.loads(scope_path.read_text())
    scope['nov10_audit']={'status':'AUDIT_COMPLETE_RULES_UNCHANGED','report':'docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md',
        'root_tests_passed':677,'root_tests_failed':0,'supplemental_red_failed':2,'supplemental_red_passed':1,
        'runtime_actual_r06_probe_comments':63,'wire_exact_replay_threads':10,'attack_predicate_hits_all200':0,
        'nov10_macro_f1':.6941598360655737,'nov10_target_correct':0,'nov10_reference_targets':22,'nov10_repeated_tp':0,'nov10_reference_events':8,
        'coverage_fixed':False,'open_verified_bug':'narrative_quote_assignment_scope_on_new_challenge',
        'overlay_exclusion_verified_threads':10,'default_exclusion_loader_changed':False,
        'training_performed':False,'rules_modified':False,'default_changed':False,'readiness_lock_modified':False,'human_gold':False}
    atomic_json(scope_path,scope)
    save_progress('AUDIT_COMPLETE_WITH_OPEN_COVERAGE_AND_QUOTE_BUG','Root677PASS/0FAIL/1warning; actualASGI r06 probes63commentsPASS, exactwire10/10. NOV10 all7attackpredicatefamilies0hits before/aftermasking; targetearlyreturn→0instances→0/8events, not globaldisable/timewindow. NOV10 metrics unchangedTP7/FP3/FN15/TN174,Macro.694160,target0/22. OldFresh10+890regression unchanged. Newpostfreeze24commentchallenge:23binaryTP6/FP1/FN0/TN16,Macro.946387,target5/6,repeated1/2,evidence2/2correct/2of4coverage; found narrativequote scopebug, supplementalred2FAIL/1PASS retained, NOTfixed.24adjudicationcandidates pending, no referencemodification. Explicitversionedoverlay excludes10/10NOV10; defaultlockedloader unchanged. No model/rule/train/default/deploy/readiness changes. AuditDONE; coverage/quoteimplementationOPEN; T028/T029formalBLOCKED,T030–T033PARTIAL. Report docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md; resume evidence README, no need to rerun inference.')
    assert statuses()==initial
    atomic_json(P/'verification.json',{'status':'AUDIT_VERIFIED_WITH_OPEN_FAILURES','all_acceptance_passed':False,
        'readiness':ready,'root_tests_passed':677,'supplemental_red_failed':2,'supplemental_red_passed':1,
        'historical_task_states_preserved':len(initial),'source_reference_files_verified':len(manifest['files']),
        'processor_unchanged':True,'old_regression_metrics_unchanged':True,'labels_changed':False,'human_gold':False})
    report=R/'docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md'
    for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
        assert (report.parent/target).resolve().exists() or target.endswith('/ARTIFACTS.json'),target
    paths={path for root in (P,d,c) for path in root.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.tmp' and path.name!='ARTIFACTS.json'}
    paths.update(R/name for name in updates+['tasks/AUTO_PROGRESS.md','tasks/CURRENT_AI_SCOPE.json','scripts/audit_nov10.py',
        'scripts/check_development_exclusions.py','tests/test_nov10_audit.py','tests/test_development_exclusion_overlay.py'])
    paths.update([overlay,report])
    atomic_json(P/'ARTIFACTS.json',{'scope':'NOV10 root-cause audit, no rule fix','files':{
        str(path.relative_to(R)).replace('\\','/'):file_sha(path) for path in sorted(paths)},
        'known_failures_retained':2,'root_tests_passed':677,'readiness_lock_sha256':ready['lock_sha256'],
        'historical_task_statuses_preserved':len(initial),'all_acceptance_passed':False})
    print(json.dumps({'status':'AUDIT_COMPLETE_KNOWN_FAILURES_OPEN','files':len(paths),'root_tests_passed':677,
                      'supplemental_red_failures':2,'readiness_files':ready['files_checked'],'historical_states_preserved':len(initial)}))
