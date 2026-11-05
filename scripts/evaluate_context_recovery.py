"""Paired recovery evaluation. Before captures actual V1 once; after reuses its scores.
Never trains, edits labels, or scores independent test labels.
"""
import argparse,csv,json,os,sys,shutil
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from synthetic_data.pipeline import atomic_json,file_sha
OUT=ROOT/'reports/ai_update/context_recovery_20261103';DATA=ROOT/'datasets/fixtures/context_recovery_v1'

def load_inputs():
 ref=json.loads((DATA/'game_rank_30_reference.json').read_text(encoding='utf-8'));items=[]
 p=ROOT/ref['input_file'];assert file_sha(p)==ref['input_sha256']
 items.append({'group':'GAME_USER_REFERENCE','payload':json.loads(p.read_text(encoding='utf-8')),'labels':ref['labels'],'reference_source':'user_provided_reference_not_gold'})
 tags={(r['thread_id'],r['comment_id']):r['reference_tag'] for r in csv.DictReader((ROOT/'datasets/fixtures/genz_regression/synthetic_reference_tags.csv').open(encoding='utf-8-sig'))}
 for p in sorted((ROOT/'datasets/fixtures/genz_regression').glob('*.json')):
  payload=json.loads(p.read_text(encoding='utf-8'))
  if payload['thread_id']==ref['thread_id']:continue
  labels={c['comment_id']:'TOXIC' if tags[(payload['thread_id'],c['comment_id'])]=='DIRECTED_INSULT' else 'UNCERTAIN' if tags[(payload['thread_id'],c['comment_id'])]=='DIRECTED_ACCUSATION' else 'CLEAN' for c in payload['comments']}
  items.append({'group':'OTHER_FOUR_REGRESSION','payload':payload,'labels':labels,'reference_source':'existing_synthetic_tag_projection_not_gold'})
 for p in sorted((DATA/'threads').glob('*.json')):
  t=json.loads(p.read_text(encoding='utf-8'));payload=json.loads((DATA/'dashboard_threads'/p.name).read_text(encoding='utf-8'))
  items.append({'group':'NEW_SYNTHETIC_RECOVERY','payload':payload,'labels':{c['comment_id']:c['annotation']['label'] for c in t['comments']},'reference_source':'AI_authored_not_gold'})
 for line in (ROOT/'datasets/synthetic_conversations/genz_v2/development_threads.jsonl').read_text(encoding='utf-8').splitlines():
  t=json.loads(line);payload=json.loads((ROOT/'datasets/synthetic_conversations/genz_v2/dashboard_threads'/(t['thread_id']+'.json')).read_text(encoding='utf-8'))
  items.append({'group':'EXISTING_GENZ_DEVELOPMENT','payload':payload,'labels':{c['comment_id']:c['annotation']['label'] for c in t['comments']},'reference_source':'already_viewed_AI_development_not_independent_test'})
 return items

def evaluate(items,scores):
 from app.schemas import AnalyzeRequest,AnalyzeResponseV2
 from app.signal_engine import analyze_thread_v2
 result=[]
 for item in items:
  payload=item['payload'];cache=dict(zip([c['text'] for c in payload['comments']],scores[payload['thread_id']]))
  class Cached:
   threshold=.41;name='Original V1 actual CPU score cache'
   def predict_scores(self,texts):return [cache[t] for t in texts]
  out=AnalyzeResponseV2.model_validate(analyze_thread_v2(AnalyzeRequest.model_validate(payload),Cached())).model_dump(mode='json')
  result.append({'group':item['group'],'labels':item['labels'],'reference_source':item['reference_source'],'output':out})
 return result

def stats(rows,field):
 known=[r for r in rows if r['reference']!='UNCERTAIN'];covered=[r for r in known if r[field]!='UNCERTAIN']
 tp=sum(r['reference']=='TOXIC' and r[field]=='TOXIC' for r in covered);fp=sum(r['reference']=='CLEAN' and r[field]=='TOXIC' for r in covered)
 tn=sum(r['reference']=='CLEAN' and r[field]=='CLEAN' for r in covered);fn=sum(r['reference']=='TOXIC' and r[field]=='CLEAN' for r in covered)
 return {'reference_comments':len(known),'covered':len(covered),'abstentions':len(known)-len(covered),'tp':tp,'fp':fp,'tn':tn,'fn':fn,
  'unresolved_toxic':sum(r['reference']=='TOXIC' and r[field]=='UNCERTAIN' for r in known),'unresolved_clean':sum(r['reference']=='CLEAN' and r[field]=='UNCERTAIN' for r in known)}

def report(before,after):
 paired=[];new_errors=[]
 for left,right in zip(before,after):
  assert left['output']['thread_id']==right['output']['thread_id']
  for a,b in zip(left['output']['comments'],right['output']['comments']):
   assert a['comment_id']==b['comment_id'] and a['toxicity_score']==b['toxicity_score'] and a['toxic_for_moderation']==b['toxic_for_moderation']
   raw='TOXIC' if a['toxic_for_moderation'] else 'CLEAN';final=b.get('moderation_assessment')
   row={'group':left['group'],'thread_id':left['output']['thread_id'],'comment_id':a['comment_id'],'reference':left['labels'][a['comment_id']],
    'raw_score':a['toxicity_score'],'raw_label':raw,'before_display':raw,'after_assessment':final['label'] if final else raw,
    'before_context':a['analysis_signals']['context_tags'],'after_context':b['analysis_signals']['context_tags'],
    'before_attack':a['analysis_signals']['directed_attack_candidate'],'after_attack':b['analysis_signals']['directed_attack_candidate'],
    'reply_to_user_id':b.get('reply_to_user_id'),'directed_at_user_id':b.get('directed_at_user_id')}
   paired.append(row)
   if row['reference']!='UNCERTAIN' and row['before_display']==row['reference'] and row['after_assessment']!=row['reference']:new_errors.append(row)
 result={'human_gold':False,'independent_test_scored':False,'raw_invariant':True,'before_final_definition':'No separate final field existed; the UI badge was raw ViSoBERT.',
   'groups':{g:{'raw_before_and_after':stats([r for r in paired if r['group']==g],'raw_label'),'after_assessment':stats([r for r in paired if r['group']==g],'after_assessment'),
   'context_before':stats([{**r,'attack':'TOXIC' if r['before_attack'] else 'CLEAN'} for r in paired if r['group']==g],'attack'),
   'context_after':stats([{**r,'attack':'TOXIC' if r['after_attack'] else 'CLEAN'} for r in paired if r['group']==g],'attack')} for g in sorted({r['group'] for r in paired})},
   'new_errors_or_abstentions_versus_raw':new_errors,'new_errors_count':len(new_errors)}
 atomic_json(OUT/'before_after.json',result);atomic_json(OUT/'paired_comments.json',paired)
 game=next(x for x in after if x['group']=='GAME_USER_REFERENCE')['output'];atomic_json(OUT/'game_after_api.json',game)
 print(json.dumps({'game':result['groups']['GAME_USER_REFERENCE'],'other_groups':{g:v['after_assessment'] for g,v in result['groups'].items() if g!='GAME_USER_REFERENCE'},'new_errors_or_abstentions':len(new_errors)},ensure_ascii=True))
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['before','after']);a=p.parse_args();items=load_inputs()
 if a.phase=='before':
  if (OUT/'before.json').exists():raise FileExistsError('Before is immutable')
  os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
  import torch;torch.set_num_threads(4)
  from app.predictor import ViSoBERTPredictor
  registry=json.loads((ROOT/'configs/model_registry.local.json').read_text(encoding='utf-8'));base=Path(registry['models']['v1']['path'])
  predictor=ViSoBERTPredictor(str(base));scores={}
  for item in items:
   payload=item['payload'];scores[payload['thread_id']]=predictor.predict_scores([c['text'] for c in payload['comments']])
  atomic_json(OUT/'score_cache.json',scores);atomic_json(OUT/'inputs.json',items)
  files=[ROOT/'services/moderation-ai/app'/n for n in ('context_signals.py','signal_engine.py','target_signals.py','schemas.py','engine.py','lexical.py')]+[ROOT/'apps/moderation-web/legacy-v3/src/App.jsx']
  snapshot=OUT/'before_sources';snapshot.mkdir(exist_ok=True)
  for path in files:shutil.copyfile(path,snapshot/(path.name if path.suffix!='.jsx' else 'Dashboard.App.jsx'))
  atomic_json(OUT/'before_lock.json',{'score_cache_sha256':file_sha(OUT/'score_cache.json'),'inputs_sha256':file_sha(OUT/'inputs.json'),
   'new_dataset_manifest_sha256':file_sha(DATA/'manifest.json'),'V1_weights_sha256':file_sha(base/'model.safetensors'),'threshold':.41,'actual_model_inference':True,
   'sources':{str(p.relative_to(ROOT)):file_sha(p) for p in files},'dataset_labels_frozen_before_app_changes':True})
  atomic_json(OUT/'before.json',evaluate(items,scores));print('Before captured: '+str(sum(len(i['payload']['comments']) for i in items))+' comments, actual V1 CPU, no training')
 else:
  lock=json.loads((OUT/'before_lock.json').read_text(encoding='utf-8'))
  assert file_sha(OUT/'inputs.json')==lock['inputs_sha256'] and file_sha(OUT/'score_cache.json')==lock['score_cache_sha256'] and file_sha(DATA/'manifest.json')==lock['new_dataset_manifest_sha256']
  frozen=json.loads((OUT/'inputs.json').read_text(encoding='utf-8'));assert items==frozen
  scores=json.loads((OUT/'score_cache.json').read_text(encoding='utf-8'));before=json.loads((OUT/'before.json').read_text(encoding='utf-8'));after=evaluate(items,scores)
  atomic_json(OUT/'after.json',after);report(before,after)
if __name__=='__main__':main()
