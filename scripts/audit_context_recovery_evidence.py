"""Audit target/repeated as separate tasks using synthetic/user references, never human gold."""
from pathlib import Path
from collections import defaultdict
import json
R=Path.cwd();P=R/'reports/ai_update/context_recovery_20261103';D=R/'datasets/fixtures/context_recovery_v1'
before=json.loads((P/'before.json').read_text(encoding='utf-8'));after=json.loads((P/'after.json').read_text(encoding='utf-8'))
ref={};groupmap={}
def add(t,group):
 groupmap[t['thread_id']]=group
 for c in t['comments']:ref[(t['thread_id'],c['comment_id'])]={'label':c['annotation']['label'],'actor':c['user_id'],'target':c['annotation']['directed_at_user_id'],'time':c['timestamp']}
for p in (D/'threads').glob('*.json'):add(json.loads(p.read_text(encoding='utf-8')),'NEW_SYNTHETIC_RECOVERY')
for line in (R/'datasets/synthetic_conversations/genz_v2/development_threads.jsonl').read_text(encoding='utf-8').splitlines():add(json.loads(line),'EXISTING_GENZ_DEVELOPMENT')
game_ref=json.loads((D/'game_rank_30_reference.json').read_text(encoding='utf-8'));game=json.loads((R/game_ref['input_file']).read_text(encoding='utf-8'));groupmap[game['thread_id']]='GAME_USER_REFERENCE'
for c in game['comments']:ref[(game['thread_id'],c['comment_id'])]={'label':game_ref['labels'][c['comment_id']],'actor':c['user_id'],'target':'U03' if game_ref['labels'][c['comment_id']]=='TOXIC' else None,'time':c['timestamp']}
rows={}
for group in sorted(set(groupmap.values())):
 known={k:v for k,v in ref.items() if groupmap[k[0]]==group and v['label']!='UNCERTAIN'}
 attacks={k:v for k,v in known.items() if v['label']=='TOXIC' and v['target'] is not None}
 chains=defaultdict(set)
 for (tid,cid),v in attacks.items():chains[(tid,v['actor'],v['target'])].add(v['time'])
 expected={k for k,v in chains.items() if len(v)>=2};metrics={}
 for name,data in [('before',before),('after',after)]:
  emitted={};events=set();evidence_good=evidence_total=0
  for t in data:
   tid=t['output']['thread_id']
   if groupmap.get(tid)!=group:continue
   for c in t['output']['comments']:
    sig=c['analysis_signals'];candidate=sig['target_candidate'] if sig['target_evidence']['confidence'] in ('medium','high') and sig['directed_attack_candidate'] else None
    if candidate is not None and (tid,c['comment_id']) in known:emitted[(tid,c['comment_id'])]=candidate
   for e in t['output']['evidence']:
    events.add((tid,e['actor_user_id'],e['target_user_id']))
    for cid in e['evidence_comment_ids']:
     v=known.get((tid,cid));evidence_total+=1
     evidence_good+=int(bool(v) and v['label']=='TOXIC' and v['actor']==e['actor_user_id'] and v['target']==e['target_user_id'])
  correct=sum(k in attacks and attacks[k]['target']==v for k,v in emitted.items())
  metrics[name]={'reference_attacks':len(attacks),'target_emissions':len(emitted),'target_correct':correct,'target_precision':correct/len(emitted) if emitted else None,
   'target_correct_recall':correct/len(attacks) if attacks else None,'event_reference':len(expected),'event_tp':len(events&expected),'event_fp':len(events-expected),'event_fn':len(expected-events),'evidence_support':evidence_good,'evidence_total':evidence_total}
 rows[group]=metrics
loss=[]
for b,a in zip(before,after):
 for x,y in zip(b['output']['comments'],a['output']['comments']):
  truth=b['labels'][x['comment_id']]
  if truth!='UNCERTAIN' and x['analysis_signals']['directed_attack_candidate']==(truth=='TOXIC') and y['analysis_signals']['directed_attack_candidate']!=(truth=='TOXIC'):loss.append({'thread_id':a['output']['thread_id'],'comment_id':x['comment_id'],'reference':truth})
r={'human_gold':False,'groups':rows,'new_context_error_ids':loss,'missing_reference_for_other_four_targets_events':True}
(P/'target_repeated_comparison.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r,ensure_ascii=True))
