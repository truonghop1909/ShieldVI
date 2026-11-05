from pathlib import Path
p=Path('scripts/prepare_t029_training.py');s=p.read_text(encoding='utf-8');needle='    return config\n'
replacement='''    strategy=config.get('training_strategy','full_finetune_gpu')
    if strategy not in ('full_finetune_gpu','frozen_encoder_head_cpu'):raise ValueError('Unknown training strategy')
    if strategy=='frozen_encoder_head_cpu':
        if config['resource']!='local_CPU' or config.get('maximum_external_cost')!=0:raise ValueError('CPU alternative cannot use paid or external resources')
        if not 1<=config.get('cpu_threads',0)<=4 or not 1<=config.get('feature_batch_size',0)<=32:raise ValueError('CPU resource limits exceeded')
        if config['max_training_seconds']>900 or config['epochs']>3 or config['gradient_accumulation_steps']!=1 or config['learning_rate']>.0001:raise ValueError('CPU experiment exceeds bounded recipe')
        if config.get('evaluation_protocol')!='synthetic_development' or config.get('synthetic_format')!='genz_v2':raise ValueError('CPU alternative requires verified GenZ research protocol')
        if not 0<=config.get('distillation_weight',-1)<=1:raise ValueError('Invalid CPU distillation weight')
    return config
'''
assert needle in s;s=s.replace(needle,replacement,1)
s=s.replace("'blockers':(['T028 independent real evaluation not complete'] if protocol=='real_independent' else [])+['G3 exact config/resource approval not recorded; local CUDA unavailable']", "'blockers':(['Bounded local CPU authorization not yet checked'] if cfg.get('training_strategy')=='frozen_encoder_head_cpu' else (['T028 independent real evaluation not complete'] if protocol=='real_independent' else [])+['G3 exact config/resource approval not recorded; local CUDA unavailable'])")
p.write_text(s,encoding='utf-8')
p=Path('scripts/train_t029_candidate.py');s=p.read_text(encoding='utf-8');s=s.replace('import argparse,copy,importlib.metadata,json,math,random,time','import argparse,copy,importlib.metadata,json,math,random,time,hashlib')
a=s.index('    if not (receipt.get(');b=s.index('    versions={}',a)
old=s[a:b]
new='''    cpu=cfg.get('training_strategy')=='frozen_encoder_head_cpu'
    if cpu:
        request=receipt.get('source_user_request','')
        if not (receipt.get('authorization_type')=='bounded_local_cpu_request_v1'
          and receipt.get('authorized_local_task_execution') is True and receipt.get('paid_services_allowed') is False
          and bool(request.strip()) and receipt.get('source_user_request_sha256')==hashlib.sha256(request.encode('utf-8')).hexdigest()
          and receipt.get('config_sha256')==file_hash(config_path) and receipt.get('prepared_manifest_sha256')==file_hash(prepared/'manifest.json')
          and receipt.get('resource')=='local_CPU' and receipt.get('max_training_seconds')==cfg['max_training_seconds']
          and receipt.get('maximum_external_cost')==0 and receipt.get('max_cpu_threads')==cfg['cpu_threads']):
            blocked.append('G3-CPU: bounded local request authorization missing or mismatched')
        if not Path(cfg['output_dir']).resolve().is_relative_to((Path(root)/'models/candidates').resolve()):blocked.append('CPU candidate must stay in repository models/candidates')
    else:
'''+''.join('    '+line+'\n' for line in old.splitlines())
s=s[:a]+new+s[b:]
s=s.replace("    if not torch.cuda.is_available():blocked.append('CUDA GPU unavailable; CPU training is disabled')", "    if not cpu and not torch.cuda.is_available():blocked.append('CUDA GPU unavailable; CPU training is disabled for full fine-tuning')")
needle="    if report['blockers']:raise TrainingBlocked('; '.join(report['blockers']))"
s=s.replace(needle,needle+"\n    if cfg.get('training_strategy')=='frozen_encoder_head_cpu':\n        from t029_cpu_head import train\n        return train(cfg,prepared,base_model,report)")
s=s.replace('Execution requires a matching resource receipt, verified protocol-specific data and CUDA.','Execution requires matching protocol-specific authorization and verified data. Full fine-tuning requires CUDA; the bounded CPU strategy freezes the encoder.')
p.write_text(s,encoding='utf-8')
print('Shared checks keep old GPU gates; added explicitly bounded CPU head strategy')
