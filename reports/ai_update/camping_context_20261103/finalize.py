"""Finalize measured context fix; preserve checkpoints, references and prior decisions."""
import json,re,sys
from pathlib import Path
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def equal(paths):return all(Path(path).is_file() and file_sha(path)==value for path,value in paths.items())
def log(p):
    b=Path(p).read_bytes();return b.decode('utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
assert '540 passed' in log(P/'root_tests.log') and 'failed' not in log(P/'root_tests.log')
assert '18 failed, 73 passed' in log(P/'red_tests.log') and 'built in' in log(P/'build.log')
comparison=load(P/'before_after.json');live=load(P/'live_smoke.json');lock=load(P/'before_lock.json')
assert comparison['comments']==890 and comparison['raw_invariant'] and comparison['new_errors_count']==0
assert not comparison['new_clean_reference_event_evidence']
assert file_sha(P/'before.json')==lock['before_sha256'] and file_sha(P/'before_live.json')==lock['before_live_sha256']
assert file_sha(R/'tests/fixtures/ai_update/camping_reference.json')==lock['reference_sha256']
assert all(v['all30_AI_reference_labels_match'] and v['raw_scores_and_legacy_fields_unchanged'] and v['updated_bundle_served'] for v in live.values())
before=load(P/'before.json');after=load(P/'after.json')
for a,b in zip(before,after):
    for x,y in zip(a['output']['comments'],b['output']['comments']):
        for key in ('profanity_detected','lexical_review_recommended','directed_insult_candidate','reported_or_apology_context','lexical_signals'):
            assert x[key]==y[key],key
protected=load(R/'reports/ai_update/final/session_verification.json')['protected_hashes_unchanged'];assert equal(protected)
genz=R/'datasets/synthetic_conversations/genz_v2';m=load(genz/'dataset_manifest.json');l=load(genz/'development_lock.json')
assert equal({genz/'threads'/(name+'.json'):sha for name,sha in m['thread_sha256'].items()})
assert equal({genz/name:sha for name,sha in m['output_sha256'].items()})
assert file_sha(genz/'dataset_manifest.json')==l['dataset_manifest_sha256'] and file_sha(genz/'development_threads.jsonl')==l['development_sha256']
legacy=R/'datasets/synthetic_conversations';m=load(legacy/'manifest.json')
assert equal({legacy/'threads'/(name+'.json'):sha for name,sha in m['thread_checksums'].items()}) and equal({legacy/name:sha for name,sha in m['csv_checksums'].items()})
ctx=R/'datasets/fixtures/context_recovery_v1';m=load(ctx/'manifest.json')
assert equal({ctx/name:sha for name,sha in m['file_sha256'].items()}) and file_sha(ctx/'game_rank_30_reference.json')==m['user_reference_sha256']
for run in ('r03','r04','r05'):
    model=R/('models/candidates/T029_genz500_head_cpu_20261103_'+run)
    assert file_sha(model/'model.safetensors')==load(model/'training_report.json')['candidate_sha256']
for name in ('engine.py','lexical.py'):
    assert file_sha(R/'services/moderation-ai/app'/name)==file_sha(R/'reports/ai_update/context_recovery_20261103/before_sources'/name)
assert file_sha(R/'services/moderation-ai/app/target_signals.py')==lock['source_sha256']['target_signals.py']
atomic_json(P/'integrity_audit.json',{'status':'PASS','protected_originals':len(protected),'V1_defaultV1_1_r03_r04_r05_unchanged':True,
 'threshold':.41,'legacy200_GenZ500_unchanged':True,'context_references_unchanged':True,'original_test_validation_SQLite_unchanged':True,
 'raw_scores_legacy_recipients_and_lexicon_unchanged':True,'legacy_engine_and_target_module_unchanged':True,'training_performed':False,'production_changed':False})
report=R/'docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md'
lines=['# Camping30 — context, target and repeated evidence recovery','',
 '## Result','',
 'The pasted30comments exactly match the existing camping fixture. Labels remain the existing synthetic reference projection, not user-confirmed human gold. Before: c09advisoryCLEAN, onlyc12/c15/c18advisoryTOXIC, no grounded attack/repeated evidence in either actual V1.1 or r05 demo. After: all30reference labels match and the exact U04→U03 chain is c09/c12/c15/c18; apology, recovery and acceptance do not become new attacks.',
 '', '## Causes and general changes','',
 '- context-v2 lacked bounded disparagement constructions for personal incompetence/team burden. context-v3 checks such constructions together with an addressee or a local abuse-justifying clause; ordinary work criticism, negation, quoted reporting and new attacks after apology remain separate tests.',
 '- c18matched a broad passive-abuse defense cue. Clause-level endorsement of abuse now establishes an attack candidate and removes the contradictory DEFENSE tag. A quoted/past apology for that same language remains non-attack.',
 '- Existing target-v3 can ground c09/c12/c15from addressed replies, then continue the same grounded target at c18. The target module itself was not changed. Replies stay separate from directed attack targets; no parent/mention means no invented target.',
 '- repeated-v4uses qualified clause evidence plus a medium/high-confidence target, rather than requiring raw>=0.41. Raw toxicity_score/toxic_for_moderation/toxic_for_repeated_rule and all legacy fields stay unchanged. attack_instance_basis is additive in V2; policy remains advisory/unexecuted.',
 '- Can-ngan/boundary/self-responsibility cues now cover the missing discourse constructions. APOLOGY_ACCEPTANCE distinguishes receiving another person’s apology from ACKNOWLEDGEMENT of one’s own fault. Dashboard has the Vietnamese label “Chấp nhận xin lỗi”.',
 '', '## Actual local inference, before versus after','',
 '| Demo | c09raw (unchanged) | Advisory before→after | Repeated before→after |','|---|---:|---|---|']
for port,v in live.items():lines.append(f"| {port} | {100*v['c09_raw_score']:.3f}% | CLEAN→TOXIC | none→U04→U03:c09/c12/c15/c18 |")
lines+=['', 'Both actual APIs: health/model_loaded ready, legacy/V2 analysis200, Dashboard200 and new bundled UI served. Every one of the30 raw scores and legacy recipient fields matches before and the unchanged legacy API. This is actual model inference, not a constant-score test. Demo8020stilluses approvedV1.1;8021is the rejected-for-promotion experimentalr05. No model was retrained or promoted.',
 '', '## Broader paired regression','',
 'Same890comments and same frozen original-V1 CPU score cache before/after. One improved advisory decision (campingc09), zero new label errors/abstentions, one changed event (camping now has4correct reference attack turns), no newly added evidence carrying a CLEAN reference. The original GAME exact4attack-chain tests remain passing. These are previously viewed synthetic development references, not a blind benchmark.',
 '', '| Group | Known reference comments | Before TP/FP/TN/FN | After TP/FP/TN/FN | After abstentions |','|---|---:|---|---|---:|']
for group,values in comparison['groups'].items():
    a,b=values['before'],values['after']
    fmt=lambda m:'/'.join(str(m[k]) for k in ('tp','fp','tn','fn'))
    lines.append(f"| {group} | {a['reference_comments']} | {fmt(a)} | {fmt(b)} | {b['abstentions']} |")
lines+=['', 'Remaining errors in these groups are retained in the table and paired output; zero *new* errors does not mean all development cases are correct. Target/repeated reference checks do not establish real-world harassment accuracy.',
 '', '## Verification','',
 '- New regression beforefix:18failed/73passed. Focused context/target/repeated suite196passed before the additional schema compatibility test. Final full root suite:540passed/1knownStarlettewarning.',
 '- npm local buildPASS; old hashed assets kept for open tabs and prior index backed up. The first restart attempt stopped at a PowerShell nested-array ownership query before any file/process mutation; corrected array reading, verified exact owned PID/parent/repo/port, then restarted only these2demo processes.',
 '-31protected originals + V1/V1.1/r03/r04/r05,200legacy/500GenZ, frozen splits/user references, original validation/test/SQLite unchanged. Raw engine, lexical module/signals and target module unchanged. No training, downloads, production deploy or auto-hide.',
 '', '## Evidence and resume','',
 '- [Regression tests](../../../tests/test_camping_context_regression.py) · [Frozen synthetic reference](../../../tests/fixtures/ai_update/camping_reference.json) · [V2 schema](../../../contracts/analysis_response_v2.schema.json).',
 '- [Paired report](../../../reports/ai_update/camping_context_20261103/before_after.json) · [Actual live checks](../../../reports/ai_update/camping_context_20261103/live_smoke.json) · [Integrity](../../../reports/ai_update/camping_context_20261103/integrity_audit.json).',
 '- [Server state and owned PIDs](../../../reports/ai_update/camping_context_20261103/demo_after_server_state.json) · [Progress](../../../tasks/AUTO_PROGRESS.md).',
 '- Demo http://127.0.0.1:8020/dashboard/ and experimental http://127.0.0.1:8021/dashboard/. Refresh Ctrl+F5 and analyze again; old results already displayed in a tab are not recomputed automatically.']
report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
note='''\n\n## CURRENT camping context follow-up — COMPLETE\n\nPastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.\n\nFull540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.\n\nCurrent report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.\n'''
for name in ['tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md',
 'tasks/moderation-ai/T022-context-signals-apology-quote-defense-inte.md','tasks/moderation-ai/T024-target-detection-v3-explicit-and-abstain.md',
 'tasks/moderation-ai/T025-repeated-harassment-v3-evidence-aware.md','tasks/moderation-ai/T026-api-schema-dashboard-signals-policy-bounda.md']:
    with (R/name).open('a',encoding='utf-8') as f:f.write(note.replace('APLOGY_ACCEPTANCE','APOLOGY_ACCEPTANCE'))
atomic_json(P/'progress.json',{'status':'COMPLETE','root_tests_passed':540,'raw_invariant':True,'paired_comments':890,
 'new_label_errors':0,'live_demo_ports':[8020,8021],'all30_AI_reference_labels_match':True,'exact4attack_evidence':True,
 'human_gold':False,'training_performed':False,'production_changed':False,'report':report.relative_to(R).as_posix(),
 'next':'Refresh demo and reanalyze; keep promotion rejection and remaining development errors visible'})
files=[report,R/'tests/test_camping_context_regression.py',R/'tests/fixtures/ai_update/camping_reference.json',R/'contracts/analysis_response_v2.schema.json',R/'docs/ai-update/04_API_VERSIONING.md',
 R/'services/moderation-ai/app/context_signals.py',R/'services/moderation-ai/app/signal_engine.py',R/'services/moderation-ai/app/schemas.py',R/'apps/moderation-web/legacy-v3/src/App.jsx',
 R/'services/moderation-ai/app/static/index.html',R/'services/moderation-ai/app/static/assets/index-DJEu5Tzd.js']
files += [f for f in P.rglob('*') if f.is_file() and f.name!='ARTIFACTS.json']
broken=[]
for path in files:
    if path.suffix!='.md':continue
    for raw in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        raw=raw.strip('<>').split('#',1)[0]
        if raw and not raw.startswith(('http:','https:','mailto:')) and not (path.parent/unquote(raw)).resolve().exists():broken.append((str(path),raw))
assert not broken,broken
atomic_json(P/'ARTIFACTS.json',{'models_not_packaged':True,'broken_links':broken,
 'files':{path.relative_to(R).as_posix():{'sha256':file_sha(path),'bytes':path.stat().st_size} for path in sorted(set(files))}})
print(json.dumps({'status':'COMPLETE','root_passed':540,'paired_comments':890,'new_errors':0,'live_reference_match':'30/30 bothmodels',
 'raw_invariant':True,'protected':len(protected),'demo_ports':[8020,8021]}))
