"""B0-B3 on the five unchanged synthetic regression fixtures.

Uses the real V1 scores captured by T020, bound to original weights/input hashes.
B2 injects old per-text lexical detection only inside this offline process.
"""
import copy,csv,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from refine_model import file_hash
from synthetic_data.pipeline import atomic_json
from evaluate_genz_development import binary
from app.schemas import AnalyzeRequest
from app.engine import analyze_thread
from app.signal_engine import analyze_thread_v2
from app import context_signals


def main():
    out=ROOT/'reports/ai_update/T030/regression_ablation';out.mkdir(parents=True,exist_ok=True)
    if (out/'metrics.json').exists():raise FileExistsError('Preserve completed run; choose a new experiment version')
    archive=ROOT/'reports/ai_update/baseline/2026-11-02_T020';source=archive/'V1_immutable'
    summary=json.loads((source/'summary.json').read_text(encoding='utf-8'));before=json.loads((archive/'protected_before.json').read_text(encoding='utf-8'))
    engine=ROOT/'services/moderation-ai/app/engine.py'
    if file_hash(engine)!=before[str(engine)]['sha256']:raise ValueError('Cannot isolate B1: legacy engine changed')
    if file_hash(Path(summary['checkpoint_path'])/'model.safetensors')!=summary['weights_sha256']:raise ValueError('V1 identity changed')
    ref_path=ROOT/'datasets/fixtures/genz_regression/synthetic_reference_tags.csv'
    tags={(r['thread_id'],r['comment_id']):r['reference_tag'] for r in csv.DictReader(ref_path.open(encoding='utf-8-sig'))}
    inputs=[];hashes={str(engine.relative_to(ROOT)):file_hash(engine),str(ref_path.relative_to(ROOT)):file_hash(ref_path)}
    for item in summary['fixtures']:
        path=ROOT/item['input_file'];response=source/(path.stem+'.response.json')
        if file_hash(path)!=item['input_sha256']:raise ValueError('Original regression fixture changed')
        inputs.append((path,response));hashes[str(path.relative_to(ROOT))]=file_hash(path);hashes[str(response.relative_to(ROOT))]=file_hash(response)
    atomic_json(out/'frozen_experiment.json',{'weights_sha256':summary['weights_sha256'],'threshold':.41,'input_and_baseline_sha256':hashes,'real_inference_origin':'Cached real V1 T020; not a new forward in this script',
      'protocol':'existing_synthetic_development_regression_NOT_BLIND','reference_projection':{'DIRECTED_INSULT':'TOXIC','DIRECTED_ACCUSATION':'UNCERTAIN','other_tags':'CLEAN'},
      'variants':{'B0':'Original T020 V1+V3 capture','B1':'V1 + new lexical detector, verified byte-identical legacy engine/context/target behavior','B2':'V1 + original per-text lexical outputs + new context tags, old target/repeated retained','B3':'V1 + new lexicon/context/target/repeated'},'scope':'Five exact captured inputs only; cannot replay original lexical module on unseen GenZ500 texts'})
    all_rows=[];evidence_rows=[];variant_outputs={v:[] for v in ('B0','B1','B2','B3')}
    for path,response in inputs:
        obj=json.loads(path.read_text(encoding='utf-8'));payload=AnalyzeRequest.model_validate(obj);b0=json.loads(response.read_text(encoding='utf-8'))
        cached={c['text']:r for c,r in zip(obj['comments'],b0['comments'])}
        if any(c['comment_id']!=r['comment_id'] for c,r in zip(obj['comments'],b0['comments'])):raise ValueError('Captured row IDs differ')
        if any(abs(r['toxicity_score']-.41)<=1e-6 for r in b0['comments']):raise ValueError('Rounded score too close to threshold; cannot replay safely')
        class Cached:
            name=b0['model_name'];threshold=.41
            def predict_scores(self,texts):return [cached[t]['toxicity_score'] for t in texts]
        b1=analyze_thread(payload,Cached()).model_dump(mode='json')
        def old_detect(text):
            row=cached[text];signals=row['lexical_signals']
            return {**{k:row[k] for k in ('profanity_detected','lexical_review_recommended','directed_insult_candidate','reported_or_apology_context','lexical_signals')},'ambiguous_only':bool(signals) and all(s['category']=='ambiguous' for s in signals)}
        with patch.object(context_signals,'detect',old_detect):contexts={c.comment_id:context_signals.analyze_context(c.text).model_dump() for c in payload.comments}
        b2=copy.deepcopy(b0)
        for row in b2['comments']:row['context_only_ablation']=contexts[row['comment_id']]
        b3=analyze_thread_v2(payload,Cached())
        variants={'B0':b0,'B1':b1,'B2':b2,'B3':b3}
        for variant,data in variants.items():
            variant_outputs[variant].append(data)
            for original,row in zip(obj['comments'],data['comments']):
                old=cached[original['text']];assert row['toxicity_score']==old['toxicity_score'] and row['toxic_for_moderation']==old['toxic_for_moderation']
                tag=tags[(obj['thread_id'],row['comment_id'])];label='TOXIC' if tag=='DIRECTED_INSULT' else 'UNCERTAIN' if tag=='DIRECTED_ACCUSATION' else 'CLEAN'
                context=row.get('context_only_ablation') or row.get('analysis_signals',{}).get('context')
                all_rows.append({'variant':variant,'thread_id':obj['thread_id'],'comment_id':row['comment_id'],'reference_tag':tag,'reference_label':label,
                    'raw_score':row['toxicity_score'],'raw_toxic':row['toxic_for_moderation'],'lexical_review':row['lexical_review_recommended'],
                    'attack_candidate':context['attack_candidate'] if context else row['directed_insult_candidate'],
                    'attack_signal_definition':'context_attack' if context else 'lexical_directed_candidate','context_tags':context['tags'] if context else [],
                    'recipient_or_target':row.get('analysis_signals',{}).get('target_candidate') if variant=='B3' else row['target_user_id']})
            for ev in data['evidence']:
                for cid in ev['evidence_comment_ids']:evidence_rows.append({'variant':variant,'thread_id':obj['thread_id'],'actor':ev['actor_user_id'],'target':ev['target_user_id'],'comment_id':cid,'reference_tag':tags[(obj['thread_id'],cid)]})
    results={}
    for variant in variants:
        rows=[r for r in all_rows if r['variant']==variant and r['reference_label']!='UNCERTAIN'];clean=[r for r in rows if r['reference_label']=='CLEAN'];evs=[r for r in evidence_rows if r['variant']==variant]
        results[variant]={'comment_metrics':binary([r['reference_label']=='TOXIC' for r in rows],[r['raw_toxic'] for r in rows]),
          'attack_signal_diagnostic':binary([r['reference_label']=='TOXIC' for r in rows],[r['attack_candidate'] for r in rows]),
          'attack_signal_definition':rows[0]['attack_signal_definition'],'clean_lexical_review_flags':sum(r['lexical_review'] for r in clean),
          'evidence_comments':len(evs),'evidence_with_directed_insult_reference':sum(r['reference_tag']=='DIRECTED_INSULT' for r in evs),
          'non_attack_reference_evidence':dict(__import__('collections').Counter(r['reference_tag'] for r in evs if r['reference_tag']!='DIRECTED_INSULT')),
          'target_precision':'NOT_AVAILABLE_NO_TARGET_GOLD','repeated_event_precision_recall':'NOT_AVAILABLE_NO_EVENT_GOLD',
          'event_count':sum(len(o['evidence']) for o in variant_outputs[variant])}
    changes=[]
    index={(r['variant'],r['thread_id'],r['comment_id']):r for r in all_rows}
    for row in [r for r in all_rows if r['variant']=='B3']:
        old=index[('B0',row['thread_id'],row['comment_id'])]
        changes.append({'thread_id':row['thread_id'],'comment_id':row['comment_id'],'reference_tag':row['reference_tag'],'raw_win':False,'raw_loss':False,
          'lexical_flag_changed':old['lexical_review']!=row['lexical_review'],'attack_flag_changed':old['attack_candidate']!=row['attack_candidate'],
          'old_recipient':old['recipient_or_target'],'new_attack_target':row['recipient_or_target']})
    report={'status':'COMPLETE_DEVELOPMENT_ABLATION_NOT_REAL_BENCHMARK','threads':5,'comments':150,'binary_reference_comments':149,'uncertain_excluded':1,
      'human_gold':False,'new_model_inference':False,'cached_real_V1_T020':True,'variants':results,'raw_unchanged_all_variants':True,
      'limitations':['Reference labels are a documented projection of already-used synthetic script tags.','B2 uses original per-input lexical detection outputs, not an available original lexical module.','Lexical directed candidates and context attacks are different signals; diagnostic values are not a new toxicity classifier.','No target/event gold exists for these5fixtures, so those metrics remain unavailable.','No fresh benchmark or improvement claim.']}
    atomic_json(out/'metrics.json',report);atomic_json(out/'paired_changes.json',changes)
    with (out/'comment_variants.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0]));w.writeheader();w.writerows(all_rows)
    for variant,items in variant_outputs.items():(out/(variant+'.jsonl')).write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in items),encoding='utf-8')
    (out/'README.md').write_text('# B0–B3 existing synthetic regression\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n\nSee frozen_experiment for hash bindings and exact variant definitions. These150 previously used examples are separate from the60-thread GenZ challenge.\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'comments':150,'raw_unchanged':True,'evidence':{v:{k:d[k] for k in ('event_count','evidence_comments','non_attack_reference_evidence')} for v,d in results.items()}},ensure_ascii=True))

if __name__=='__main__':main()
