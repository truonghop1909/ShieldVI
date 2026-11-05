import csv,json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(P))
from synthetic_data.pipeline import atomic_json,file_sha
from verify_ai_readiness_lock import verify_lock
from progress import record

def text_log(path):
    data=path.read_bytes();return data.decode('utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')

def statuses():
    out={}
    for path in (R/'tasks').rglob('T*.md'):
        values=re.findall(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*\s*(.+)$',path.read_text(encoding='utf-8-sig'),re.M)
        if values:out[str(path.relative_to(R)).replace('\\','/')]=values[0]
    return out

if __name__=='__main__':
    initial=statuses();assert len(initial)==27
    assert re.search(r'722 passed, 1 warning',text_log(P/'full_tests.log'))
    assert re.search(r'45 passed',text_log(P/'controls_final.log'))
    assert re.search(r'2 failed',text_log(P/'quote_red.log'))
    assert re.search(r'2 passed',text_log(P/'adjudication_final_tests.log'))
    lock=json.loads((P/'V62_LOCK.json').read_text())
    for name,digest in lock['files'].items():assert file_sha(R/name)==digest
    readiness=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert readiness['status']=='PASS'
    assert readiness['lock_sha256']==lock['readiness_lock_sha256']
    atomic_json(P/'readiness_final.json',readiness)
    for folder in ('nov10_regression_v1','fresh10_regression_v1'):
        d=R/'datasets/fixtures'/folder;manifest=json.loads((d/'manifest.json').read_text())
        for name,digest in manifest['files'].items():assert file_sha(d/name)==digest
    for name in ('nov10','fresh10','old890','postfix48','postfix24','nov_audit24','repeated74'):
        data=json.loads((P/'frozen_development'/name/'metrics.json').read_text());assert not data['new_label_errors']
    rows=list(csv.DictReader((P/'adjudication_v3/cases_with_full_context.csv').open(encoding='utf-8-sig',newline='')))
    assert len(rows)==24
    assert all(not any(row[k] for k in ('adjudicated_label','adjudicated_target','decision_reason','reviewer')) for row in rows)
    assert all(row['full_conversation_context'].count(' · reference=')==20 for row in rows)
    challenge=R/'datasets/fixtures/v62_postfreeze_challenge_v1';meta=json.loads((challenge/'manifest.json').read_text())
    assert meta['processor_lock_sha256']==file_sha(P/'V62_LOCK.json')
    for tid,digest in meta['thread_sha256'].items():assert file_sha(challenge/'threads'/(tid+'.json'))==digest
    scored=json.loads((P/'postfreeze_challenge/first_pass_metrics.json').read_text());assert not scored['new_label_errors']
    assert scored['processor_lock_sha256']==file_sha(P/'V62_LOCK.json')
    proof=json.loads((P/'exclusion_verification.json').read_text());assert proof['verified_threads']==16
    assert file_sha(R/proof['manifest'])==proof['manifest_sha256']
    targets=json.loads((P/'evidence_and_target_errors.json').read_text())
    assert not targets['emitted_target_errors'] and not targets['emitted_evidence_errors']
    note='''

## Controlled v6.2 research — 04/11/2026, EXPERIMENTAL

Completed safe research cycle, no formal acceptance/promotion. New research_v62.py leaves sealedv6.1/default untouched. Two quote expectation RED→GREEN (same inputs/assertions; currentv6.2 replay, originalv6.1JSON/probes unchanged), outside assignment/attribution/cau noun/cau addressee/NFC spans handled; new outsidequote attacks preserved.43processor+2adjudication targetedPASS; full722rootPASS/0FAIL/1warning.24owner cases exported with full20commentcontexts and blank decisions; latest adjudication_v3/HTML+CSV, timestamped decision annotationversions, no humanreview/gold or originalreference edits.

Bounded indirect grammars with negativecontrols; weak sarcasm cues diagnostic-only pending adjudication. NOV10TP7→8,FP3→3,FN15→14,TN174→174,Macro.694160→.719137,target0→2/22,repeated0→1/8(P1/R.125),evidence2/2correct but2/21coverage/full0of8events. Fresh10/old890 no regression; all7developmentcohorts no newlabelerrors. Some viewedchallenge gains; do not call independent.

V62_LOCK before new6threads/36comment authoring/inputfreeze/inference. One actualr06CPUoffline scorecache, no post-score tuning. Challengev6.1→v6.2 Macro.731744→.911330,TP3→6,FP0→0,FN5→2,TN28→28,target1→6/8,repeated0→2/3(P1/R.667),evidence4/4correct/4of6coverage. Two unseen metaphor/exclusion misses remain unchanged.52remainingbinaryerrors/12UNCERTAIN across8cohorts saved; emittedtarget/evidenceerrors0 on groundedreferences. Newversionedexclusionoverlay verifies10NOV10+6newchallenge excluded; defaultloader unchanged.

V1/r06/default/.41/readiness1311SHA unchangedPASS; no Dashboard/default runtime/DB edits, trainingr07, deploy or promotion. T028/T029formalBLOCKED,T030–T033PARTIAL; historicalDONE preserved. Report docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md; progress/evidence/changelog/SHA/reproduction reports/ai_update/v62_research_20261104/. Next owner adjudication when convenient, future independent research revision only; no automatic activation.
'''
    updates=['tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md',
        'tasks/moderation-ai/T030-paired-offline-evaluation-ablation.md','tasks/moderation-ai/T033-technical-report-thesis-handoff.md']
    protected=json.loads((R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json').read_text())['files']
    for name in updates:
        assert name not in protected
        path=R/name
        if '## Controlled v6.2 research — 04/11/2026, EXPERIMENTAL' not in path.read_text(encoding='utf-8-sig'):
            with path.open('a',encoding='utf-8') as stream:stream.write(note)
    scope_path=R/'tasks/CURRENT_AI_SCOPE.json';scope=json.loads(scope_path.read_text())
    scope['controlled_v62_research']={'status':'COMPLETED_SAFE_RESEARCH_EXPERIMENTAL','report':'docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md',
        'versions':{'context':'context-v6.2-research','target':'target-v6.2-research','repeated':'repeated-v6.2-research'},
        'quote_original_expectations_fixed_on_new_processor':True,'sealed_v61_unchanged':True,'root_tests_passed':722,
        'nov10_macro_f1':.7191365711913658,'nov10_target_correct':2,'nov10_reference_targets':22,'nov10_repeated_tp':1,'nov10_reference_events':8,
        'challenge_comments':36,'challenge_macro_f1':.9113300492610837,'challenge_repeated_tp':2,'challenge_reference_events':3,
        'post_score_tuning':False,'owner_adjudication_completed':0,'human_gold':False,'default_changed':False,
        'training_performed':False,'readiness_lock_changed':False,'activation_allowed':False}
    atomic_json(scope_path,scope)
    record('HANDOFF_COMPLETE_EXPERIMENTAL','All5authorized safe phases complete with documented remainingmisses and no formal task promotion.722rootPASS, samequoteassertionsPASS on v6.2 (sealedv6.1 untouched), originalsource/reference/model/readiness SHAverified. Owner adjudication prepared24fullcontexts/blankdecisions in adjudication_v3; no humanlabels/gold created. Locked36commentchallenge scoredonce, no rule/test editsafterfreeze;2FN/1missedevent retained. Report docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md; changelog/lock/errors/exclusion/preflight/inventory/reproduction in evidence directory. RemainT028/T029BLOCKED,T030–T033PARTIAL; no default/Dashboard/model/training/deploy changes.')
    assert statuses()==initial
    atomic_json(P/'verification.json',{'status':'PASS_SAFE_RESEARCH_ONLY','root_tests_passed':722,'quote_v62_expectations':'PASS',
        'historical_v61_artifacts_changed':False,'historical_task_statuses_preserved':27,'readiness':readiness,
        'reference_labels_changed':False,'human_decisions_created':0,'challenge_post_score_rule_changes':0,
        'remaining_misses':True,'promoted':False,'training_performed':False})
    report=R/'docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md'
    for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
        assert (report.parent/target).resolve().exists() or target.endswith('/ARTIFACTS.json'),target
    paths={path for root in (P,challenge) for path in root.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.name!='ARTIFACTS.json'}
    paths.update(R/name for name in updates+['tasks/AUTO_PROGRESS.md','tasks/CURRENT_AI_SCOPE.json',
        'services/moderation-ai/app/experiments/research_v62.py','scripts/evaluate_research_v62.py','scripts/prepare_nov10_adjudication.py',
        'tests/test_research_v62.py','tests/test_nov10_adjudication_export.py',proof['manifest']])
    paths.add(report)
    atomic_json(P/'ARTIFACTS.json',{'scope':'Controlledv6.2research only','files':{
        str(path.relative_to(R)).replace('\\','/'):file_sha(path) for path in sorted(paths)},'root_tests_passed':722,
        'readiness_lock_sha256':readiness['lock_sha256'],'processor_lock_sha256':file_sha(P/'V62_LOCK.json'),'activation_allowed':False})
    print(json.dumps({'status':'PASS_EXPERIMENTAL_HANDOFF','files':len(paths),'root_tests_passed':722,
        'original_quote_expectations_on_v62':'PASS','historical_task_statuses_preserved':len(initial),'readiness_files':1311}))
