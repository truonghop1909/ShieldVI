"""Paired synthetic development metrics. Never scores real or independent test data."""
import argparse,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from evaluate_context_recovery import load_inputs,evaluate
from synthetic_data.pipeline import atomic_json,file_sha
ROOT=Path(__file__).resolve().parents[1]

def classification(rows):
    rows=[r for r in rows if r[0]!='UNCERTAIN']
    tp=sum(a=='TOXIC' and b=='TOXIC' for a,b in rows);fp=sum(a=='CLEAN' and b=='TOXIC' for a,b in rows)
    tn=sum(a=='CLEAN' and b=='CLEAN' for a,b in rows);fn=sum(a=='TOXIC' and b=='CLEAN' for a,b in rows)
    ac=sum(a=='CLEAN' and b=='UNCERTAIN' for a,b in rows);at=sum(a=='TOXIC' and b=='UNCERTAIN' for a,b in rows)
    div=lambda a,b:a/b if b else 0.
    return {'n':len(rows),'tp':tp,'fp':fp,'tn':tn,'fn':fn,'abstained_clean':ac,'abstained_toxic':at,
      'coverage':div(len(rows)-ac-at,len(rows)),'toxic_precision':div(tp,tp+fp),'toxic_recall':div(tp,tp+fn+at),
      'macro_f1':(div(2*tp,2*tp+fp+fn+at)+div(2*tn,2*tn+fp+fn+ac))/2,
      'macro_f1_definition':'Mean binary class F1; abstention counts as a miss for its reference class, not silently dropped.'}

def target_truth():
    truth={}
    def add(t):
        for c in t['comments']:
            a=c['annotation'];truth[(t['thread_id'],c['comment_id'])]={'label':a['label'],'actor':c['user_id'],
              'target':a.get('directed_at_user_id') if a.get('is_directed_attack') else None,'time':c['timestamp']}
    for path in (ROOT/'datasets/fixtures/context_recovery_v1/threads').glob('*.json'):add(json.loads(path.read_text(encoding='utf-8')))
    for line in (ROOT/'datasets/synthetic_conversations/genz_v2/development_threads.jsonl').read_text(encoding='utf-8').splitlines():add(json.loads(line))
    for path in (ROOT/'datasets/fixtures/context_recovery_v1/game_rank_30_reference.json',ROOT/'tests/fixtures/ai_update/camping_reference.json'):
        ref=json.loads(path.read_text(encoding='utf-8'));t=json.loads((ROOT/ref['input_file']).read_text(encoding='utf-8'))
        target=ref.get('attack_target','U03')
        for c in t['comments']:
            label=ref['labels'][c['comment_id']];truth[(t['thread_id'],c['comment_id'])]={'label':label,'actor':c['user_id'],'target':target if label=='TOXIC' else None,'time':c['timestamp']}
    return truth

def grounding_metrics(data,truth):
    known={k:v for k,v in truth.items() if v['label']!='UNCERTAIN'}
    attacks={k:v for k,v in known.items() if v['label']=='TOXIC' and v['target'] is not None}
    pairs=defaultdict(set)
    for (tid,_),v in attacks.items():
        if v['time']:pairs[(tid,v['actor'],v['target'])].add(datetime.fromisoformat(v['time'].replace('Z','+00:00')).astimezone(timezone.utc))
    expected={k for k,times in pairs.items() if len(times)>=2};emitted={};events=set();support=total=0
    for item in data:
        tid=item['output']['thread_id']
        if not any(k[0]==tid for k in known):continue
        for c in item['output']['comments']:
            if (tid,c['comment_id']) in known and c.get('directed_at_user_id') is not None:emitted[(tid,c['comment_id'])]=c['directed_at_user_id']
        for e in item['output']['evidence']:
            events.add((tid,e['actor_user_id'],e['target_user_id']))
            for cid in e['evidence_comment_ids']:
                v=known.get((tid,cid));total+=1
                support+=int(bool(v) and v['label']=='TOXIC' and v['actor']==e['actor_user_id'] and v['target']==e['target_user_id'])
    correct=sum(k in attacks and attacks[k]['target']==target for k,target in emitted.items());div=lambda a,b:a/b if b else 0.
    tp=len(events&expected);fp=len(events-expected);fn=len(expected-events)
    return {'reference_comments_with_target_coverage':len(known),'reference_attacks':len(attacks),'target_emissions':len(emitted),'target_correct':correct,
      'target_precision':div(correct,len(emitted)),'target_recall':div(correct,len(attacks)),
      'target_abstentions_on_reference_attacks':sum(k not in emitted for k in attacks),
      'repeated':{'tp':tp,'fp':fp,'fn':fn,'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),
        'evidence_correct':support,'evidence_total':total,'evidence_precision':div(support,total)}}

def run(before_path,output,score_cache):
    before_path,output,score_cache=map(Path,(before_path,output,score_cache))
    if output.exists():raise FileExistsError('Use a new output version; never overwrite evaluation evidence')
    before=json.loads(before_path.read_text(encoding='utf-8'));after=evaluate(load_inputs(),json.loads(score_cache.read_text(encoding='utf-8')))
    rows=[];regressions=[]
    for a,b in zip(before,after):
        assert a['labels']==b['labels'] and a['output']['thread_id']==b['output']['thread_id']
        for x,y in zip(a['output']['comments'],b['output']['comments']):
            for field in ('comment_id','toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence','lexical_signals'):assert x[field]==y[field]
            truth=a['labels'][x['comment_id']];old=x['moderation_assessment']['label'];new=y['moderation_assessment']['label']
            row={'thread_id':a['output']['thread_id'],'comment_id':x['comment_id'],'group':a['group'],'reference':truth,'before':old,'after':new,
              'before_target':x.get('directed_at_user_id'),'after_target':y.get('directed_at_user_id')}
            rows.append(row)
            if truth!='UNCERTAIN' and old==truth and new!=truth:regressions.append(row)
    truth=target_truth()
    result={'scope':'synthetic development only; no real-world or human-gold metric','human_gold':False,'independent_test_scored':False,
      'before_sha256':file_sha(before_path),'score_cache_sha256':file_sha(score_cache),'comments':len(rows),'raw_invariant':True,
      'classification':{phase:classification([(r['reference'],r[phase]) for r in rows]) for phase in ('before','after')},
      'groups':{g:{phase:classification([(r['reference'],r[phase]) for r in rows if r['group']==g]) for phase in ('before','after')} for g in sorted({r['group'] for r in rows})},
      'grounding':{'before':grounding_metrics(before,truth),'after':grounding_metrics(after,truth)},'new_label_errors':regressions,
      'changed_comments':[r for r in rows if r['before']!=r['after'] or r['before_target']!=r['after_target']],
      'remaining_errors':[r for r in rows if r['reference']!='UNCERTAIN' and r['after']!=r['reference']],
      'limitations':['Original V1 real CPU score cache reused; no fresh real inference in these aggregate metrics.','Target/repeated references unavailable for three legacy threads, which are omitted from grounding metrics.','Previously viewed development examples do not establish generalization.']}
    output.mkdir(parents=True);atomic_json(output/'metrics.json',result);atomic_json(output/'after.json',after);atomic_json(output/'paired.json',rows)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--score-cache',type=Path,default=ROOT/'reports/ai_update/context_recovery_20261103/score_cache.json');a=p.parse_args()
    r=run(a.before,a.output,a.score_cache)
    print(json.dumps({k:r[k] for k in ('comments','classification','grounding','new_label_errors')}))
if __name__=='__main__':main()
