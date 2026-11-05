"""User-authorized experimental continuation on synthetic AI labels plus ViCTSD replay.
Never changes the active checkpoint or the reviewed source dataset.
"""
import copy, csv, hashlib, json, os, random, sys, time
from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
sys.path.insert(0,str(Path(__file__).resolve().parent))
from refine_model import read_rows, clean_train, normalize, metrics, test_gate, file_hash
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'models'/'visobert_v2_synthetic_experiment'
BASE=ROOT/'models'/'visobert_head_refined'
SOURCE=ROOT/'datasets'/'review'/'conversations_100'/'conversations_labeled.json'
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    started=time.monotonic()
    if OUT.exists(): raise RuntimeError('Output already exists; choose a new OUT before rerunning.')
    OUT.mkdir(parents=True)
    torch.set_num_threads(6);torch.manual_seed(20261102);random.seed(20261102)
    baseline_hash=file_hash(BASE/'model.safetensors')
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    synth=[]
    for t in data['threads']:
        for c in t['comments']:
            synth.append({'id':c['comment_id'],'text':c['text'],'label':c['annotation']['suggested_toxicity']})
    valid=read_rows(ROOT/'datasets/raw/victsd/ViCTSD_valid.csv')
    test_text=read_rows(ROOT/'datasets/raw/victsd/ViCTSD_test.csv',with_labels=False)
    holdout=[r['text'] for r in valid+test_text]
    gold, gold_clean=clean_train(read_rows(ROOT/'datasets/prepared/victsd_train.csv'),holdout)
    synth,synth_clean=clean_train(synth,holdout)
    gold_keys={normalize(r['text']):r['label'] for r in gold}
    overlaps=[r for r in synth if normalize(r['text']) in gold_keys]
    synth=[r for r in synth if normalize(r['text']) not in gold_keys]
    rows=gold+synth
    weights=torch.tensor([1.0]*len(gold)+[3.0]*len(synth))
    with (OUT/'training_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['row_id','Comment','Toxicity','label_origin','sample_weight'])
        for j,r in enumerate(rows): w.writerow([r['id'],r['text'],r['label'],'ViCTSD_original' if j<len(gold) else 'AI_synthetic_proposed',1 if j<len(gold) else 3])
    report={'status':'training','experimental_only':True,'user_authorized_synthetic_training':True,
      'base_model':str(BASE),'base_sha256_before':baseline_hash,'synthetic_source_sha256':file_hash(SOURCE),
      'seed':20261102,'device':'cpu','encoder_frozen':True,'threshold':0.41,
      'synthetic_raw_count':sum(len(t['comments']) for t in data['threads']),
      'gold_train_count':len(gold),'synthetic_unique_train_count':len(synth),'unique_train_count':len(rows),
      'gold_cleanup':gold_clean,'synthetic_cleanup':synth_clean,'synthetic_gold_overlaps_removed':len(overlaps),
      'synthetic_human_verified':False,'synthetic_sample_weight':3,'epochs':3,'learning_rate':0.00003,
      'distillation_weight':1.0,'batch_size':64,'max_length':128,'validation_count':len(valid),
      'limitations':['Synthetic labels are AI proposals, not human gold.',
       'Synthetic training text has template repetition; no independent synthetic test exists.',
       'Classifier sees one comment, not parent/reply context.',
       'ViCTSD holdouts were used in earlier model development; this is not a fresh blind benchmark.',
       'Official test is scored only after candidate selection in this run; never used to choose another candidate.'],
      'data_sources':{k:{'path':str(p),'sha256':file_hash(p)} for k,p in {
        'gold_train':ROOT/'datasets/prepared/victsd_train.csv',
        'validation':ROOT/'datasets/raw/victsd/ViCTSD_valid.csv',
        'test':ROOT/'datasets/raw/victsd/ViCTSD_test.csv','synthetic':SOURCE}.items()}}
    dump(OUT/'experiment_report.json',report)
    print('DATA',len(gold),'gold +',len(synth),'unique synthetic',flush=True)
    tokenizer=AutoTokenizer.from_pretrained(str(BASE),local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(str(BASE),local_files_only=True).eval()
    for p in model.roberta.parameters(): p.requires_grad=False
    original=copy.deepcopy(model.classifier).eval()
    def features(items,name):
        values=torch.empty((len(items),model.config.hidden_size))
        order=sorted(range(len(items)),key=lambda j:len(items[j]['text']))
        with torch.inference_mode():
            for start in range(0,len(items),32):
                ids=order[start:start+32]
                tokens=tokenizer([items[j]['text'] for j in ids],padding=True,truncation=True,max_length=128,return_tensors='pt')
                values[ids]=model.roberta(**tokens).last_hidden_state[:,0,:]
                if start%512==0:print('FEATURES',name,min(start+32,len(items)),'/',len(items),flush=True)
        return values
    def probabilities(head,x):
        head.eval()
        with torch.no_grad(): return torch.cat([head(b[:,None,:]).softmax(-1)[:,1] for b in x.split(256)]).tolist()
    xv=features(valid,'validation'); yv=[r['label'] for r in valid]
    bv=metrics(yv,probabilities(original,xv)); report['baseline_validation']=bv
    print('BASELINE_VALID',json.dumps(bv),flush=True)
    xt=features(rows,'train').clone(); yt=torch.tensor([r['label'] for r in rows])
    with torch.no_grad(): teacher=torch.cat([original(b[:,None,:]) for b in xt.split(256)])
    head=copy.deepcopy(original)
    optimizer=torch.optim.AdamW(head.parameters(),lr=0.00003,weight_decay=0.01)
    best=None;best_state=None;experiments=[]
    for epoch in range(1,4):
        head.train();total=0
        for ids in torch.randperm(len(rows)).split(64):
            optimizer.zero_grad(set_to_none=True)
            logits=head(xt[ids,None,:])
            ce=torch.nn.functional.cross_entropy(logits,yt[ids],reduction='none')
            kl=torch.nn.functional.kl_div((logits/2).log_softmax(-1),(teacher[ids]/2).softmax(-1),reduction='none').sum(-1)*4
            loss=((ce+kl)*weights[ids]).sum()/weights[ids].sum()
            loss.backward();torch.nn.utils.clip_grad_norm_(head.parameters(),1.0);optimizer.step()
            total+=float(loss.detach())
        score=metrics(yv,probabilities(head,xv))
        rec={'epoch':epoch,'validation':score,'sum_batch_loss':total}
        experiments.append(rec);print('EPOCH',json.dumps(rec),flush=True)
        if best is None or score['macro_f1']>best['validation']['macro_f1']:
            best=rec;best_state=copy.deepcopy(head.state_dict())
    model.classifier.load_state_dict(best_state);model.eval()
    report['epochs_results']=experiments;report['selected']=best
    # Candidate selection is complete before test labels are opened.
    test=read_rows(ROOT/'datasets/raw/victsd/ViCTSD_test.csv')
    xx=features(test,'final_test');yy=[r['label'] for r in test]
    before=probabilities(original,xx);after=probabilities(model.classifier,xx)
    report['baseline_test']=metrics(yy,before);report['candidate_test']=metrics(yy,after)
    report['passes_existing_test_gate']=test_gate(report['baseline_test'],report['candidate_test'])
    report['passes_strict_validation_gate']=(best['validation']['macro_f1']>=bv['macro_f1']+0.005 and best['validation']['toxic_precision']>=bv['toxic_precision'] and best['validation']['toxic_recall']>=bv['toxic_recall'])
    with (OUT/'test_predictions.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['row_id','gold_toxicity','baseline_probability','candidate_probability'])
        w.writerows((r['id'],r['label'],b,a) for r,b,a in zip(test,before,after))
    model.save_pretrained(str(OUT),safe_serialization=True);tokenizer.save_pretrained(str(OUT))
    dump(OUT/'threshold_config.json',{'threshold':0.41,'model_version':'ViSoBERT V2 - synthetic experiment',
         'approval_status':'experimental_not_approved','report':'experiment_report.json','source_checkpoint':str(BASE),
         'selected_on':'ViCTSD validation; AI synthetic training labels'})
    report['base_sha256_after']=file_hash(BASE/'model.safetensors')
    assert report['base_sha256_after']==baseline_hash
    # Reload exported weights and verify predictions to catch an unusable export.
    del model
    reloaded=AutoModelForSequenceClassification.from_pretrained(str(OUT),local_files_only=True).eval()
    probe=tokenizer([test[0]['text']],return_tensors='pt',truncation=True,max_length=128)
    with torch.no_grad(): p=float(reloaded(**probe).logits.softmax(-1)[0,1])
    report['reload_probe_abs_error']=abs(p-after[0])
    assert report['reload_probe_abs_error']<0.00001
    report['status']='completed_experimental_not_activated';report['elapsed_seconds']=round(time.monotonic()-started,2)
    dump(OUT/'experiment_report.json',report)
    (OUT/'README.md').write_text('# ViSoBERT V2 synthetic experiment\n\nTrained at user request on original ViCTSD labels plus deduplicated AI-authored synthetic comments. Synthetic annotations remain unverified; source review files were not altered. Encoder frozen; classifier head trained for three epochs with ViCTSD replay, synthetic loss weight 3 and baseline distillation weight 1. Selection uses validation macro-F1; test scored after selection. Not activated and not automatically approved. See experiment_report.json for actual metrics, provenance, source hashes and limitations.\n',encoding='utf-8')
    print('RESULT',json.dumps({k:report[k] for k in ('status','selected','baseline_test','candidate_test','passes_existing_test_gate','passes_strict_validation_gate','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
