"""Freeze current evidence, preserve prior DONE scopes, open independent criteria."""
import json,re,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_context_recovery import load_inputs,evaluate
if (P/'progress.json').exists():raise FileExistsError('Session already initialized')
history=[]
for path in sorted((R/'tasks').rglob('T[0-9][0-9][0-9]-*.md')):
    text=path.read_text(encoding='utf-8');m=re.search(r'(?:Status|Trạng thái):\*\*\s*(DONE|IN_PROGRESS|TODO|BLOCKED|WAITING_APPROVAL)',text,re.I)
    if m:history.append({'file':path.relative_to(R).as_posix(),'historical_status':m[1]})
atomic_json(P/'historical_task_states.json',history)
scores_path=R/'reports/ai_update/context_recovery_20261103/score_cache.json'
before=evaluate(load_inputs(),json.loads(scores_path.read_text(encoding='utf-8')));atomic_json(P/'before.json',before)
source_paths=['services/moderation-ai/app/context_signals.py','services/moderation-ai/app/target_signals.py','services/moderation-ai/app/signal_engine.py',
 'scripts/real_dataset/store.py','scripts/real_dataset/collector.py','scripts/real_dataset/review_app.py','scripts/real_dataset/validation.py']
source_hashes={}
for rel in source_paths:
    path=R/rel;dest=P/'before_sources'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);source_hashes[rel]=file_sha(path)
frozen={str(path.relative_to(R)):file_sha(path) for path in (R/'tests/fixtures/ai_update').glob('*.json')}
atomic_json(P/'before_lock.json',{'before_sha256':file_sha(P/'before.json'),'score_cache_sha256':file_sha(scores_path),'source_hashes':source_hashes,
 'reference_hashes':frozen,'comments':sum(len(x['output']['comments']) for x in before),'human_gold':False})
scope={'authority':'Latest PartsA/B/C and follow-up: real T028 criteria restored; no contact requests or new training.',
 'historical_statuses_preserved':True,'historical_task_files':len(history),'T028':{'historical_scope':'synthetic context recovery','historical_status':'DONE',
 'current_scope':'200 permitted real conversations, one human two rounds, privacy/leakage checks, locked evaluation','current_status':'BLOCKED',
 'actual_valid_real_threads':0,'missing':['200 valid real threads','source permission/provenance','human Round1 and Round2','locked independent evaluation']},
 'T029':{'historical_status':'DONE','preparation':'IMPLEMENTED_PENDING_RECHECK','new_training':'BLOCKED','dependencies':['T028 real acceptance','new explicit matching training approval']},
 'T030':{'development':'IN_PROGRESS','real_world_metrics':'BLOCKED'},'T031':{'local_registry_rollback':'IN_PROGRESS','production_activation':'NOT_AUTHORIZED'},
 'T032':{'safe_integration_tests':'IN_PROGRESS'},'T033':{'provisional_report':'IN_PROGRESS','real_world_conclusions':'BLOCKED'},
 'collection':{'Wikimedia':'PAUSED_BY_USER','fake_contact_or_browser_impersonation_allowed':False,'ask_contact_again_this_session':False},
 'training_allowed_this_session':False,'threshold':.41}
atomic_json(R/'tasks/CURRENT_AI_SCOPE.json',scope)
atomic_json(R/'datasets/real_conversations/manifests/collection_policy.json',{'collection_enabled':False,
 'reason':'User paused Wikimedia collection: no operator contact; do not invent contact, accounts, URLs or browser User-Agent.',
 'fake_contact_allowed':False,'browser_impersonation_allowed':False,'future_resume_requires_explicit_user_change':True})
banner='''
## CURRENT AUTHORITY — real evaluation criteria restored, historical DONE preserved

Latest PartsA/B/C + follow-up override earlier synthetic-only/CPU permission for new work. **T028 real-evaluation criteria: BLOCKED** until permitted200real threads, the same human's manual Round1/Round2, privacy/leakage checks and evaluation lock. Earlier synthetic T028 DONE is historical scope evidence, not real completion. All other confirmed DONE records are retained. Current machine-readable criteria: `tasks/CURRENT_AI_SCOPE.json`; evidence: `reports/ai_update/independent_readiness_20261103/`.

Wikimedia collector PAUSED by user; no further contact/path questions in this session, no fake identity or browser impersonation. Research other public licenses; do not ingest unclear rights. Continue independent synthetic development, preparation/local registry/integration/reporting. New training and production changes are not authorized. Distinguish preparation/development DONE from blocked real-world acceptance; dependencies remain visible.

'''
for rel in ('tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','tasks/AUTO_PROGRESS.md','tasks/moderation-ai/T028-independent-evaluation-solo-review-protoco.md'):
    path=R/rel;path.write_text(banner+path.read_text(encoding='utf-8'),encoding='utf-8')
with (R/'AGENTS.md').open('a',encoding='utf-8') as f:
    f.write('\n- Latest PartsA/B/C request restores T028 real/human criteria (BLOCKED separately from historical synthetic DONE). Wikimedia paused, no contact questions/fake contact/browser impersonation. Continue safe independent development/preparation; no new training or production activation. Current criteria: tasks/CURRENT_AI_SCOPE.json. Earlier CPU permissions are historical for completed runs.\n')
atomic_json(P/'progress.json',{'status':'IN_PROGRESS','completed':[],'blocked':['T028 real200/human gold','new T029 training'],
 'next':'Audit old30/source options, indirect/context fixes, reviewer/intake readiness, regression/integration/local registry checks','training_performed':False})
print(json.dumps({'status':'STARTED','historical_tasks':len(history),'before_comments':sum(len(x['output']['comments']) for x in before),'T028_real':'BLOCKED','collector':'PAUSED'}))
