"""Freeze existing AI references and actual/cached baseline before changing rules."""
import csv,json,re,shutil,sys,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_context_recovery import load_inputs,evaluate
fixture=R/'datasets/fixtures/genz_regression/SHIELDVI_04_DI_CAMPING_CHIA_TIEN_30.json'
payload=json.loads(fixture.read_text(encoding='utf-8'))
attachment=Path('C:/Users/admin/.codex/attachments/a4e18338-ccd2-46fe-9f1f-6ddf24a827b9/Pasted text.txt')
pasted={cid:text.strip() for cid,text in re.findall(r'(?m)^(c\d+) · U\d+\s*\r?\n([^\r\n]+)',attachment.read_text(encoding='utf-8'))}
assert len(pasted)==30 and all(pasted[c['comment_id']]==c['text'] for c in payload['comments'])
ref_path=R/'tests/fixtures/ai_update/camping_reference.json'
if ref_path.exists() or (P/'before.json').exists():raise FileExistsError('Before snapshot already exists')
tags={r['comment_id']:r['reference_tag'] for r in csv.DictReader((R/'datasets/fixtures/genz_regression/synthetic_reference_tags.csv').open(encoding='utf-8-sig')) if r['thread_id']==payload['thread_id']}
ref={'input_file':fixture.relative_to(R).as_posix(),'input_sha256':file_sha(fixture),'thread_id':payload['thread_id'],
  'label_source':'existing_synthetic_reference_projection','human_gold':False,'training_eligible':False,
  'attachment_sha256':file_sha(attachment),'labels':{cid:'TOXIC' if tag=='DIRECTED_INSULT' else 'CLEAN' for cid,tag in tags.items()},
  'attack_actor':'U04','attack_target':'U03','attack_evidence_ids':['c09','c12','c15','c18'],
  'focus_context_AI_reference':{'c11':'INTERVENTION','c13':'INTERVENTION','c14':'SET_BOUNDARY','c16':'INTERVENTION','c17':'DEFENSE','c19':'QUOTE','c22':'ACKNOWLEDGEMENT','c23':'SET_BOUNDARY','c24':'APOLOGY','c25':'APOLOGY_ACCEPTANCE'}}
atomic_json(ref_path,ref)
for name in ('context_signals.py','target_signals.py','signal_engine.py','schemas.py'):
    target=P/'before_sources'/name;target.parent.mkdir(exist_ok=True);shutil.copy2(R/'services/moderation-ai/app'/name,target)
shutil.copy2(R/'apps/moderation-web/legacy-v3/src/App.jsx',P/'before_sources/App.jsx')
items=load_inputs();scores=json.loads((R/'reports/ai_update/context_recovery_20261103/score_cache.json').read_text(encoding='utf-8'))
before=evaluate(items,scores);atomic_json(P/'before.json',before)
live={}
for port in (8020,8021):
    req=urllib.request.Request(f'http://127.0.0.1:{port}/api/v2/analyze',data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as response:live[str(port)]=json.load(response)
atomic_json(P/'before_live.json',live)
atomic_json(P/'before_lock.json',{'reference_sha256':file_sha(ref_path),'input_sha256':file_sha(fixture),
 'before_sha256':file_sha(P/'before.json'),'before_live_sha256':file_sha(P/'before_live.json'),
 'baseline_scores_sha256':file_sha(R/'reports/ai_update/context_recovery_20261103/score_cache.json'),
 'source_sha256':{name:file_sha(P/'before_sources'/name) for name in ('context_signals.py','target_signals.py','signal_engine.py','schemas.py','App.jsx')},
 'human_gold':False,'independent_test_scored':False,'rule_changes_started':False})
atomic_json(P/'progress.json',{'status':'IN_PROGRESS','focus':'Camping30 directed attacks/context/repeated',
 'before_comments':sum(len(r['output']['comments']) for r in before),'actual_live_models':[8020,8021],
 'next':'General clause rules and guard tests, paired regression, build, restart only owned demo processes'})
for name in ('tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md'):
    with (R/name).open('a',encoding='utf-8') as f:f.write('\n\n## CURRENT camping regression follow-up — IN_PROGRESS\n\nUser pasted camping30 demo. Existing synthetic references and actual V1.1/r05 API before outputs are frozen in reports/ai_update/camping_context_20261103/. Fix context/target/repeated with general rules; no training, checkpoint/threshold/data changes. Prior DONE states preserved; completion requires paired regression and actual local demo smoke.\n')
print(json.dumps({'status':'BEFORE_FROZEN','comments':sum(len(r['output']['comments']) for r in before),'source_matches_attachment':True,
  'live_before':{port:{'toxic':[c['comment_id'] for c in data['comments'] if c['moderation_assessment']['label']=='TOXIC'],'evidence':data['evidence']} for port,data in live.items()}}))
