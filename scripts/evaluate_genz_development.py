"""Frozen synthetic-development comparison, real V1 forward only; no training."""
from __future__ import annotations
import argparse,csv,json,os,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from refine_model import file_hash,metrics
from synthetic_data.pipeline import atomic_json


def binary(labels,predictions):
    m=metrics(labels,[float(p) for p in predictions],.41)
    div=lambda a,b:a/b if b else 0.
    m.update(clean_precision=div(m['tn'],m['tn']+m['fn']),clean_recall=div(m['tn'],m['tn']+m['fp']),
        clean_f1=div(2*m['tn'],2*m['tn']+m['fp']+m['fn']),toxic_f1=div(2*m['tp'],2*m['tp']+m['fp']+m['fn']),
        confusion_matrix_rows_clean_toxic=[[m['tn'],m['fp']],[m['fn'],m['tp']]])
    # These are hard decisions; Brier/logloss do not represent calibrated probabilities.
    m.pop('brier');m.pop('log_loss');return m


def main():
    p=argparse.ArgumentParser();p.add_argument('--base-model',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'reports/ai_update/T030/genz500');a=p.parse_args()
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    if (out/'metrics.json').exists():raise FileExistsError('Use a new run directory; never overwrite an evaluated result')
    data=ROOT/'datasets/synthetic_conversations/genz_v2';lock=json.loads((data/'development_lock.json').read_text(encoding='utf-8'))
    if lock['development_sha256']!=file_hash(data/'development_threads.jsonl') or lock['dataset_manifest_sha256']!=file_hash(data/'dataset_manifest.json'):raise ValueError('Frozen source changed')
    threads=[json.loads(line) for line in (data/'development_threads.jsonl').read_text(encoding='utf-8').splitlines()]
    if [t['thread_id'] for t in threads]!=lock['thread_ids']:raise ValueError('Challenge ID order changed')
    sources=[ROOT/'services/moderation-ai/app'/n for n in ('engine.py','signal_engine.py','context_signals.py','target_signals.py','lexical.py')]
    experiment={'data_lock_sha256':file_hash(data/'development_lock.json'),'model_sha256':file_hash(a.base_model/'model.safetensors'),
      'threshold':.41,'seed':20261103,'protocol':'synthetic_development_only','human_gold':False,'training_performed':False,
      'candidate':'NOT_TRAINED','selection_or_tuning':False,'code_sha256':{str(q.relative_to(ROOT)):file_hash(q) for q in sources},
      'variants':{'V1_raw':'Original V1 classifier, same scores used by both APIs','legacy_api':'Current legacy API recipient heuristic (not reconstructed pre-update V3)','hybrid_v2':'Current context/target/repeated pipeline, raw model unchanged','B1_B2':'NOT_RUN: pre-update lexical/context snapshot unavailable'}}
    atomic_json(out/'frozen_experiment.json',experiment)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
    import torch
    torch.set_num_threads(min(4,os.cpu_count() or 1))
    from app.model_registry import LocalModelRegistry
    from app.predictor import ViSoBERTPredictor,default_model_path
    from app.schemas import AnalyzeRequest,AnalyzeResponseV2
    from app.engine import analyze_thread
    from app.signal_engine import analyze_thread_v2
    registry=LocalModelRegistry(ROOT/'configs/model_registry.local.json')
    predictor,audit=registry.load('v1')
    if Path(a.base_model).resolve()!=Path(registry.models['v1']['path']).resolve():raise ValueError('Registry base differs from requested model')
    model_audit={'real_model_inference':True,'device':str(predictor.device),'model':predictor.name,'threshold':predictor.threshold,
       'registry':audit,'existing_default_unchanged':default_model_path(),'optimizer_steps':0}
    atomic_json(out/'model_smoke.json',model_audit)
    started=time.monotonic();flat=[c for t in threads for c in t['comments']];scores=[]
    for start in range(0,len(flat),64):
        chunk=flat[start:start+64];scores.extend(predictor.predict_scores([c['text'] for c in chunk]))
        atomic_json(out/'inference_progress.json',{'completed_comments':len(scores),'total_comments':len(flat),'elapsed_seconds':round(time.monotonic()-started,2),'real_inference':True})
    score_by_text={c['text']:s for c,s in zip(flat,scores)}
    class Cached:
        name=predictor.name;threshold=.41
        def predict_scores(self,texts):return [score_by_text[t] for t in texts]
    rows=[];outputs=[];gold_pairs=set();pred_pairs=set();old_pairs=set();ev_good=ev_total=0;unchanged=True
    for t in threads:
        payload=AnalyzeRequest.model_validate(json.loads((data/'dashboard_threads'/(t['thread_id']+'.json')).read_text(encoding='utf-8')))
        before=analyze_thread(payload,Cached()).model_dump(mode='json');after=AnalyzeResponseV2.model_validate(analyze_thread_v2(payload,Cached())).model_dump(mode='json')
        outputs.append(after)
        for c,old,new in zip(t['comments'],before['comments'],after['comments']):
            ann=c['annotation'];sig=new['analysis_signals'];unchanged &= old['toxicity_score']==new['toxicity_score'] and old['toxic_for_moderation']==new['toxic_for_moderation']
            rows.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],'scenario':t['scenario_type'],'text':c['text'],'ai_reference':ann['label'],
              'reference_attack':ann['is_directed_attack'],'reference_target':ann['directed_at_user_id'],'semantic_role':ann['semantic_role'],
              'raw_score':new['toxicity_score'],'raw_toxic':new['toxic_for_moderation'],'hybrid_raw_toxic':new['toxic_for_moderation'],
              'hybrid_attack':sig['directed_attack_candidate'],'hybrid_target':sig['target_candidate'],'hybrid_qualified_attack':sig['attack_instance_candidate'],
              'context_tags':sig['context_tags'],'lexical_review':new['lexical_review_recommended'],'profanity_detected':new['profanity_detected'],'reference_profanity':ann['has_profanity']})
            if ann['is_repeated_attack']:gold_pairs.add((t['thread_id'],c['user_id'],ann['directed_at_user_id']))
        lookup={c['comment_id']:c for c in t['comments']}
        for variant,store in ((before,old_pairs),(after,pred_pairs)):
            for ev in variant['evidence']:store.add((t['thread_id'],ev['actor_user_id'],ev['target_user_id']))
        for ev in after['evidence']:
            for cid in ev['evidence_comment_ids']:
                c=lookup[cid];ann=c['annotation'];ev_total+=1
                ev_good+=int(c['user_id']==ev['actor_user_id'] and ann['directed_at_user_id']==ev['target_user_id'] and ann['is_directed_attack'] and ann['label']=='TOXIC')
    known=[r for r in rows if r['ai_reference']!='UNCERTAIN'];raw=binary([int(r['ai_reference']=='TOXIC') for r in known],[r['raw_toxic'] for r in known])
    probs=metrics([int(r['ai_reference']=='TOXIC') for r in known],[r['raw_score'] for r in known],.41)
    attack=binary([r['reference_attack'] for r in known],[r['hybrid_attack'] for r in known])
    emitted=[r for r in known if r['hybrid_target'] is not None];gold_attacks=[r for r in known if r['reference_attack']]
    correct=sum(r['reference_attack'] and r['hybrid_target']==r['reference_target'] for r in emitted)
    div=lambda n,d:n/d if d else None
    def event(pred):return {'tp':len(pred&gold_pairs),'fp':len(pred-gold_pairs),'fn':len(gold_pairs-pred),'precision':div(len(pred&gold_pairs),len(pred)),'recall':div(len(pred&gold_pairs),len(gold_pairs))}
    safe=[r for r in known if r['ai_reference']=='CLEAN'];lexclean=[r for r in safe if r['lexical_review']]
    result={'protocol':'synthetic_development_only','human_gold':False,'threads':len(threads),'comments':len(rows),'uncertain_excluded':len(rows)-len(known),
      'reference_label_counts':dict(Counter(r['ai_reference'] for r in rows)), 'V1_raw':raw,'V1_probability_diagnostics':probs,
      'hybrid_v2_raw':raw,'raw_scores_and_labels_unchanged':bool(unchanged),'hybrid_attack_candidate':attack,
      'hybrid_target':{'emitted':len(emitted),'reference_directed_attacks':len(gold_attacks),'correct':correct,'precision':div(correct,len(emitted)),
         'coverage_on_reference_attacks':div(sum(r['hybrid_target'] is not None for r in gold_attacks),len(gold_attacks)),
         'correct_target_recall':div(correct,len(gold_attacks)),'abstentions_on_reference_attacks':sum(r['hybrid_target'] is None for r in gold_attacks)},
      'repeated_events':{'reference':len(gold_pairs),'legacy_api_diagnostic':event(old_pairs),'hybrid_v2':event(pred_pairs),
          'hybrid_evidence_correct':ev_good,'hybrid_evidence_total':ev_total,'hybrid_evidence_correctness':div(ev_good,ev_total)},
      'lexicon':{'clean_comments':len(safe),'clean_review_flags':len(lexclean),'review_flag_rate_on_clean_not_toxic_FPR':div(len(lexclean),len(safe)),
         'profanity_detection':binary([r['reference_profanity'] for r in rows],[r['profanity_detected'] for r in rows])},
      'paired_raw_classifier':{'wins':0,'losses':0,'ties':len(known),'definition':'raw ViSoBERT label intentionally unchanged, not a new hybrid toxicity classifier'},
      'candidate':'NOT_TRAINED','B1_B2':'NOT_RUN_PRE_UPDATE_SNAPSHOT_MISSING','real_benchmark':'BLOCKED_NO_REAL_GOLD','ViCTSD_test':'NOT_SCORED_NO_CANDIDATE_SELECTION',
      'elapsed_seconds':round(time.monotonic()-started,2),'base_unchanged':file_hash(a.base_model/'model.safetensors')==experiment['model_sha256']}
    if not unchanged or not result['base_unchanged']:raise AssertionError('Baseline invariant violated')
    atomic_json(out/'metrics.json',result)
    with (out/'paired_predictions.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'hybrid_outputs.jsonl').write_text(''.join(json.dumps(o,ensure_ascii=False)+'\n' for o in outputs),encoding='utf-8')
    errors=[r for r in known if r['raw_toxic']!=(r['ai_reference']=='TOXIC') or r['hybrid_attack']!=r['reference_attack'] or (r['reference_attack'] and r['hybrid_target']!=r['reference_target'])]
    atomic_json(out/'errors.json',{'source':'synthetic AI references only','count':len(errors),'rows':errors})
    atomic_json(out/'paired_by_scenario.json',{s:{'n':len(group),'raw_fp':sum(r['raw_toxic'] and r['ai_reference']=='CLEAN' for r in group),'raw_fn':sum(not r['raw_toxic'] and r['ai_reference']=='TOXIC' for r in group),'new_raw_wins':0,'new_raw_losses':0} for s in sorted({r['scenario'] for r in known}) for group in [[r for r in known if r['scenario']==s]]})
    (out/'RESULTS.md').write_text('# Frozen GenZ development comparison\n\nReal V1 CPU inference; all scores frozen before rule analysis. Synthetic AI labels only, not human gold.\n\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n\nNo improvement claim. B1/B2 pre-update snapshot is missing; current legacy recipient fields are not attack-target labels. Review flags on CLEAN may be appropriate for quotes, so that rate is not toxicity false-positive rate. Error analysis did not change rules, labels, threshold or examples.\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('threads','comments','V1_raw','hybrid_target','raw_scores_and_labels_unchanged','elapsed_seconds')},ensure_ascii=True))

if __name__=='__main__':main()
