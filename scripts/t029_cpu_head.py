"""Bounded offline CPU head experiment. Encoder stays frozen; not full fine-tuning.

Invoked only after shared T029 source/protocol/authorization checks. No production selection.
"""
from __future__ import annotations
import copy,hashlib,json,random,time
from pathlib import Path
from refine_model import metrics,file_hash
from synthetic_data.pipeline import atomic_json


def encoder_sha(encoder):
    h=hashlib.sha256()
    for name,tensor in sorted(encoder.state_dict().items()):
        h.update(name.encode());h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def train(config,prepared,base_model,preflight):
    import torch
    from transformers import AutoModelForSequenceClassification,AutoTokenizer
    from torch.nn import functional as F
    started=time.monotonic();output=Path(config['output_dir']);prepared=Path(prepared);base_model=Path(base_model)
    output.mkdir(parents=True,exist_ok=False)
    budget=config['max_training_seconds']
    torch.set_num_threads(config['cpu_threads']);random.seed(config['seed']);torch.manual_seed(config['seed'])
    report={'status':'RUNNING','training_performed':False,'optimizer_steps':0,'training_strategy':'frozen_encoder_head_cpu',
      'full_encoder_finetune':False,'encoder_frozen':True,'device':'cpu','external_cost':0,'max_seconds':budget,'config':config,
      'prepared_manifest_sha256':file_hash(prepared/'manifest.json'),'base_sha256_before':file_hash(base_model/'model.safetensors'),
      'threshold':.41,'activated':False,'test_scored_during_training':False,'epochs':[],'preflight':preflight}
    def save():atomic_json(output/'training_report.json',report)
    def deadline():
        if time.monotonic()-started>budget:raise TimeoutError('Bounded CPU training time exhausted')
    def progress(stage,done,total):
        deadline();report.update(stage=stage,completed=done,total=total,elapsed_seconds=round(time.monotonic()-started,2));save()
        print(json.dumps({'stage':stage,'completed':done,'total':total,'elapsed':report['elapsed_seconds']}),flush=True)
    save()
    try:
        tokenizer=AutoTokenizer.from_pretrained(str(base_model),local_files_only=True)
        model=AutoModelForSequenceClassification.from_pretrained(str(base_model),local_files_only=True).cpu().eval()
        if model.config.num_labels!=2 or not hasattr(model,'roberta') or not hasattr(model,'classifier'):raise ValueError('Expected ViSoBERT/RoBERTa binary architecture')
        for parameter in model.parameters():parameter.requires_grad=False
        original=copy.deepcopy(model.classifier).eval();head=copy.deepcopy(original)
        for parameter in head.parameters():parameter.requires_grad=True
        report['encoder_sha_before']=encoder_sha(model.roberta)
        report['trainable_parameter_names']=['classifier.'+n for n,p in head.named_parameters() if p.requires_grad]
        report['trainable_parameters']=sum(p.numel() for p in head.parameters() if p.requires_grad)
        report['frozen_encoder_parameters']=sum(p.numel() for p in model.roberta.parameters())
        train_rows=[json.loads(line) for line in (prepared/'train.jsonl').read_text(encoding='utf-8').splitlines()]
        valid_rows=[json.loads(line) for line in (prepared/'validation.jsonl').read_text(encoding='utf-8').splitlines()]
        report.update(train_rows=len(train_rows),validation_rows=len(valid_rows),synthetic_rows=sum(r['label_origin']=='AI_synthetic_user_accepted' for r in train_rows))
        def features(rows,stage):
            values=torch.empty((len(rows),model.config.hidden_size),dtype=torch.float32)
            order=sorted(range(len(rows)),key=lambda i:len(rows[i]['text']));batch=config['feature_batch_size']
            with torch.no_grad():
                for start in range(0,len(rows),batch):
                    deadline();ids=order[start:start+batch]
                    tokens=tokenizer([rows[i]['text'] for i in ids],padding=True,truncation=True,max_length=config['max_length'],return_tensors='pt')
                    values[ids]=model.roberta(**tokens).last_hidden_state[:,0,:]
                    if start%256==0 or start+batch>=len(rows):progress(stage,min(start+batch,len(rows)),len(rows))
            return values
        def probabilities(classifier,x):
            classifier.eval()
            with torch.no_grad():return torch.cat([classifier(chunk[:,None,:]).softmax(-1)[:,1] for chunk in x.split(256)]).tolist()
        xv=features(valid_rows,'validation_features');yv=[r['label'] for r in valid_rows]
        report['baseline_validation']=metrics(yv,probabilities(original,xv),.41);save()
        xt=features(train_rows,'train_features');yt=torch.tensor([r['label'] for r in train_rows]);weights=torch.tensor([r.get('sample_weight',1.) for r in train_rows])
        with torch.no_grad():teacher=torch.cat([original(chunk[:,None,:]) for chunk in xt.split(256)])
        deadline();optimizer=torch.optim.AdamW(head.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
        best=None;best_state=None;stale=0
        for epoch in range(1,config['epochs']+1):
            head.train();loss_sum=0.;batch_count=0
            for ids in torch.randperm(len(train_rows)).split(config['batch_size']):
                deadline();optimizer.zero_grad(set_to_none=True)
                logits=head(xt[ids,None,:]);ce=F.cross_entropy(logits,yt[ids],reduction='none')
                kl=F.kl_div((logits/2).log_softmax(-1),(teacher[ids]/2).softmax(-1),reduction='none').sum(-1)*4
                loss=((ce+config['distillation_weight']*kl)*weights[ids]).sum()/weights[ids].sum()
                loss.backward();torch.nn.utils.clip_grad_norm_(head.parameters(),1.);optimizer.step()
                report['optimizer_steps']+=1;report['training_performed']=True;loss_sum+=float(loss.detach());batch_count+=1
            validation=metrics(yv,probabilities(head,xv),.41);record={'epoch':epoch,'mean_batch_loss':loss_sum/batch_count,'validation':validation};report['epochs'].append(record)
            if best is None or validation['macro_f1']>best['validation']['macro_f1']:
                best=record;best_state={k:v.detach().clone() for k,v in head.state_dict().items()};stale=0
            else:stale+=1
            report['selected']=best;progress('head_epoch',epoch,config['epochs'])
            if stale>=config['early_stopping_patience']:break
        if not best_state or report['optimizer_steps']<1:raise ValueError('No real training performed')
        model.classifier.load_state_dict(best_state);model.eval()
        report['encoder_sha_after']=encoder_sha(model.roberta);report['encoder_unchanged']=report['encoder_sha_before']==report['encoder_sha_after']
        report['changed_parameter_names']=['classifier.'+n for n,t in model.classifier.state_dict().items() if not torch.equal(t,original.state_dict()[n])]
        if not report['encoder_unchanged'] or not report['changed_parameter_names']:raise AssertionError('Head-only training invariant failed')
        deadline();model.save_pretrained(output,safe_serialization=True);tokenizer.save_pretrained(output)
        atomic_json(output/'threshold_config.json',{'threshold':.41,'model_version':config['run_id']+' (frozen encoder, CPU head)','approval_status':'shadow_only_not_activated','training_strategy':'frozen_encoder_head_cpu','selected_epoch':best['epoch'],'validation_macro_f1':best['validation']['macro_f1']})
        probes=[r['text'] for r in valid_rows[:3]];tokens=tokenizer(probes,padding=True,truncation=True,max_length=config['max_length'],return_tensors='pt')
        with torch.no_grad():expected=model(**tokens).logits.softmax(-1)[:,1].tolist()
        reloaded=AutoModelForSequenceClassification.from_pretrained(str(output),local_files_only=True).eval()
        with torch.no_grad():actual=reloaded(**tokens).logits.softmax(-1)[:,1].tolist()
        error=max(abs(a-b) for a,b in zip(expected,actual));report['reload_probe_max_error']=error
        if error>1e-5:raise AssertionError('Candidate reload changed scores')
        report.update(status='COMPLETE_HEAD_TRAINED_NOT_ACTIVATED',candidate_validation=best['validation'],test_scored_during_training=False,
            candidate_sha256=file_hash(output/'model.safetensors'),elapsed_seconds=round(time.monotonic()-started,2))
        (output/'README.md').write_text('# Local head-only research candidate\n\nActual CPU training on prepared ViCTSD+AI synthetic labels. Encoder frozen; not full encoder fine-tuning. Threshold0.41. Selection uses historical ViCTSD validation only. No model/test/default/production overwrite. Training sources/seed/limits/epochs/reload metrics in training_report.json. AI labels are not human gold; this is not a release approval.\n',encoding='utf-8')
    except BaseException as exc:
        report.update(status='FAILED_NOT_ACTIVATED',error_type=type(exc).__name__,elapsed_seconds=round(time.monotonic()-started,2));raise
    finally:
        report['base_sha256_after']=file_hash(base_model/'model.safetensors');report['baseline_unchanged']=report['base_sha256_before']==report['base_sha256_after']
        info=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'));report['source_hashes_unchanged']=all(file_hash(Path(v['path']))==v['sha256'] for v in info['sources'].values());save()
        if not report['baseline_unchanged'] or not report['source_hashes_unchanged']:raise AssertionError('Protected source changed')
    print(json.dumps({k:report[k] for k in ('status','optimizer_steps','selected','elapsed_seconds','encoder_unchanged','baseline_unchanged')}),flush=True)
    return report
