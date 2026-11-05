"""Actual three-head inference on verified identical frozen encoders; synthetic only."""
import argparse,csv,json,os,re,time
from pathlib import Path
from collections import defaultdict
from refine_model import metrics,file_hash,clean_train
from prepare_t029_training import remove_near
from synthetic_data.experiment import verify_view
from synthetic_data.pipeline import atomic_json
from evaluate_synthetic_signals import classification,grounding_metrics
ROOT=Path(__file__).resolve().parents[1]

def is_teencode(text):
    # Reporting slice only, never a classifier label or training target.
    return bool(re.search(r'(?i)\b(?:ko|k|khum|t|m|mn|bt|dm|đm|dcm|vl|vcl|vkl|n0ob|l0ser|sh1t)\b|f\*ck|d\.m',text))

def run(config_path,prepared,output):
    import sys
    sys.path.insert(0,str(ROOT/'services/moderation-ai'))
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    from t029_cpu_head import encoder_sha
    from app.schemas import AnalyzeRequest
    from app.signal_engine import analyze_thread_v2
    torch.set_num_threads(4);started=time.monotonic()
    config_path,prepared,output=map(Path,(config_path,prepared,output))
    if output.exists():raise FileExistsError('Never overwrite a completed evaluation version')
    cfg=json.loads(config_path.read_text(encoding='utf-8'));candidate=Path(cfg['output_dir'])
    training=json.loads((candidate/'training_report.json').read_text(encoding='utf-8'))
    assert training['status']=='COMPLETE_HEAD_TRAINED_NOT_ACTIVATED' and training['encoder_unchanged'] and not training['activated']
    assert file_hash(candidate/'model.safetensors')==training['candidate_sha256']
    manifest,threads,_=verify_view(ROOT/cfg['experimental_dataset'],ROOT/cfg['synthetic_export'])
    held=[t for t in threads if t['split']!='synthetic_train'];rows=[{**c,'split':t['split'],'scenario_family':t['scenario_family']} for t in held for c in t['comments']]
    info=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'))
    r05=ROOT/'models/candidates/T029_genz500_head_cpu_20261103_r05'
    old_prepared=ROOT/'reports/ai_update/train_genz500_r05_20261103/prepared'
    r05report=json.loads((r05/'training_report.json').read_text(encoding='utf-8'))
    assert file_hash(old_prepared/'manifest.json')==r05report['prepared_manifest_sha256']
    oldrows=[json.loads(line) for line in (old_prepared/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    _,overlap=clean_train(oldrows,[r['text'] for r in rows]);_,near=remove_near(oldrows,[r['text'] for r in rows],.9,40)
    if overlap['overlap_removed'] or near:raise ValueError('r05 training overlaps proposed holdouts; no fair baseline claim')
    output.mkdir(parents=True)
    atomic_json(output/'evaluation_lock.json',{'candidate_sha256':training['candidate_sha256'],'selected_epoch':training['selected']['epoch'],
      'split_manifest_sha256':file_hash(ROOT/cfg['experimental_dataset']/'split_manifest.json'),'training_complete_before_scoring':True,
      'selection':'synthetic validation only; one challenge audit, no subsequent tuning','independent_real':False,'promotion_allowed':False})
    paths={'V1':Path(info['base_model_path']),'r05':r05,'r06':candidate}
    loaded={name:AutoModelForSequenceClassification.from_pretrained(str(path),local_files_only=True).cpu().eval() for name,path in paths.items()}
    tokenizers={name:AutoTokenizer.from_pretrained(str(path),local_files_only=True) for name,path in paths.items()}
    encoders={name:encoder_sha(model.roberta) for name,model in loaded.items()}
    assert len(set(encoders.values()))==1
    order=sorted(range(len(rows)),key=lambda i:len(rows[i]['text']));scores={name:[0.]*len(rows) for name in paths}
    probe_errors={name:0. for name in paths}
    with torch.inference_mode():
        for start in range(0,len(order),32):
            ids=order[start:start+32];texts=[rows[i]['text'] for i in ids]
            tokens={name:tok(texts,padding=True,truncation=True,max_length=cfg['max_length'],return_tensors='pt') for name,tok in tokenizers.items()}
            for name in paths:
                assert tokens[name].keys()==tokens['V1'].keys() and all(torch.equal(tokens[name][key],tokens['V1'][key]) for key in tokens['V1'])
            features=loaded['V1'].roberta(**tokens['V1']).last_hidden_state[:,0,:]
            for name,model in loaded.items():
                values=model.classifier(features[:,None,:]).softmax(-1)[:,1].tolist()
                for i,v in zip(ids,values):scores[name][i]=v
        for name,model in loaded.items():
            for split in ('synthetic_validation','synthetic_challenge'):
                ids=[i for i,r in enumerate(rows) if r['split']==split][:3]
                tokens=tokenizers[name]([rows[i]['text'] for i in ids],padding=True,truncation=True,max_length=cfg['max_length'],return_tensors='pt')
                actual=model(**tokens).logits.softmax(-1)[:,1].tolist()
                probe_errors[name]=max(probe_errors[name],max(abs(scores[name][i]-v) for i,v in zip(ids,actual)))
                assert probe_errors[name]<=1e-5
    lookup={name:{(r['thread_id'],r['comment_id']):v for r,v in zip(rows,values)} for name,values in scores.items()}
    summaries={};hybrid={};predictions=[]
    roles={'direct_insults':lambda c:c['is_directed_attack'] and 'indirect' not in c['semantic_role'],
      'indirect_insults':lambda c:'indirect' in c['semantic_role'],'sarcasm':lambda c:'indirect' in c['semantic_role'],
      'teencode':lambda c:is_teencode(c['text']),
      'apology':lambda c:c['is_apology'],'quote':lambda c:c['is_quote'],
      'intervention':lambda c:'intervention' in c['semantic_role'],'self_defense':lambda c:c['semantic_role'] in ('defense','self_defense','boundary')}
    for name,values in scores.items():
        model_summary={};outputs=[]
        for t in held:
            text_scores={c['text']:lookup[name][(t['thread_id'],c['comment_id'])] for c in t['comments']}
            class Cached:
                threshold=.41
                def predict_scores(self,texts):return [text_scores[text] for text in texts]
            cached=Cached();cached.name=name+' actual shared-frozen-encoder inference'
            payload={'thread_id':t['thread_id'],'profile':'conservative','comments':[{k:c[k] for k in ('comment_id','user_id','parent_id','timestamp','text')} for c in t['comments']]}
            out=analyze_thread_v2(AnalyzeRequest.model_validate(payload),cached)
            outputs.append({'output':out,'split':t['split']})
        outrows={(t['output']['thread_id'],c['comment_id']):c for t in outputs for c in t['output']['comments']}
        for split in ('synthetic_validation','synthetic_challenge'):
            ids=[i for i,r in enumerate(rows) if r['split']==split and r['label']!='UNCERTAIN']
            raw=metrics([int(rows[i]['label']=='TOXIC') for i in ids],[values[i] for i in ids],.41)
            p,r=raw['toxic_precision'],raw['toxic_recall'];raw['toxic_f1']=2*p*r/(p+r) if p+r else 0.
            advisory=classification([(rows[i]['label'],outrows[(rows[i]['thread_id'],rows[i]['comment_id'])]['moderation_assessment']['label']) for i in ids])
            truth={(c['thread_id'],c['comment_id']):{'label':c['label'],'actor':c['user_id'],'target':c['directed_at_user_id'] if c['is_directed_attack'] else None,'time':c['timestamp']} for c in rows if c['split']==split}
            groups={}
            for group,predicate in roles.items():
                indices=[i for i in ids if predicate(rows[i])]
                groups[group]={'raw':metrics([int(rows[i]['label']=='TOXIC') for i in indices],[values[i] for i in indices],.41) if indices else {'n':0},
                  'hybrid':classification([(rows[i]['label'],outrows[(rows[i]['thread_id'],rows[i]['comment_id'])]['moderation_assessment']['label']) for i in indices])}
            model_summary[split]={'raw':raw,'hybrid':advisory,'groups':groups,
              'target_repeated':grounding_metrics([x for x in outputs if x['split']==split],truth),
              'UNCERTAIN_reference_excluded':sum(c['label']=='UNCERTAIN' and c['split']==split for c in rows)}
        if name=='r06':assert abs(model_summary['synthetic_validation']['raw']['macro_f1']-training['candidate_validation']['macro_f1'])<=1e-6
        summaries[name]=model_summary;hybrid[name]=outputs
        for i,c in enumerate(rows):
            out=outrows[(c['thread_id'],c['comment_id'])]
            predictions.append({'model':name,'thread_id':c['thread_id'],'comment_id':c['comment_id'],'split':c['split'],'text':c['text'],
              'synthetic_reference':c['label'],'label_source':'synthetic','raw_score':values[i],'raw_label':'TOXIC' if values[i]>=.41 else 'CLEAN',
              'context_tags':out['analysis_signals']['context_tags'],'lexicon_signals':out['lexical_signals'],'advisory':out['moderation_assessment']['label'],
              'reply_to_user_id':out['reply_to_user_id'],'directed_at_user_id':out['directed_at_user_id'],'policy_risk':out['policy_risk'],'human_gold':False})
    errors=[r for r in predictions if r['synthetic_reference']!='UNCERTAIN' and (r['raw_label']!=r['synthetic_reference'] or r['advisory']!=r['synthetic_reference'])]
    result={'status':'COMPLETE_EXPERIMENTAL_SYNTHETIC_COMPARISON','dataset_sha256':file_hash(ROOT/cfg['experimental_dataset']/'dataset_manifest.json'),
      'training_report_sha256':file_hash(candidate/'training_report.json'),'metrics':summaries,'encoder_sha256':encoders,'full_forward_probe_max_errors':probe_errors,
      'r05_holdout_exact_overlap':overlap['overlap_removed'],'r05_holdout_near_overlap':len(near),'historical_original_test_scored':False,
      'independent_real_metrics':False,'human_gold':False,'promotion_allowed':False,'decision':'EXPERIMENTAL_KEEP_EXISTING_DEFAULT',
      'elapsed_seconds':round(time.monotonic()-started,2),'numerical_threshold_near_rows':sum(abs(v-.41)<1e-5 for vs in scores.values() for v in vs),
      'limitations':['Validation/challenge were already seen in rule research, never independent human gold.','Shared encoder requires identical encoder hash/tokenization; actual full-forward probes verified.','No semantic novelty or real-world superiority claim.','Sarcasm subgroup is approximated by authored indirect-attack role; it is not a separate human sarcasm annotation.']}
    atomic_json(output/'comparison.json',result);atomic_json(output/'predictions.json',predictions);atomic_json(output/'hybrid_outputs.json',hybrid);atomic_json(output/'errors.json',errors)
    with (output/'predictions.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(predictions[0]));writer.writeheader()
        for row in predictions:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.config,a.prepared,a.output)
    print(json.dumps({'status':r['status'],'validation':{name:m['synthetic_validation']['raw'] for name,m in r['metrics'].items()},'challenge':{name:m['synthetic_challenge']['raw'] for name,m in r['metrics'].items()},'promotion_allowed':False}))
if __name__=='__main__':main()
