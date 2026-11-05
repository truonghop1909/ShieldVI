from pathlib import Path
import json,re,importlib.metadata,platform
R=Path.cwd();P=R/'reports/ai_update/all_tasks_cpu_20261103';cfg=json.loads((R/'configs/t029_genz500_cpu_head.json').read_text(encoding='utf-8'));training=json.loads((Path(cfg['output_dir'])/'training_report.json').read_text(encoding='utf-8'))
assert training['status']=='COMPLETE_HEAD_TRAINED_NOT_ACTIVATED' and training['optimizer_steps']>0 and training['encoder_unchanged'] and training['baseline_unchanged']
p=next((R/'tasks/moderation-ai').glob('T029-*.md'));s=p.read_text(encoding='utf-8').replace('- **Status:** IN_PROGRESS','- **Status:** DONE',1);s+='\n## Current CPU experiment evidence — DONE\n\nActual head-only training completed:11340rows(6942ViCTSD+4398synthetic),3epochs,534optimizersteps,400.94seconds.96,975,360encoderparametersfrozen;592,130headparameterstrained; only classifier.* weights changed. Encoder hash/base/source hashes unchanged; original0.41 retained. Validation selectedepoch3: MacroF1=.75304166 vsV1=.76370125, worse; no improvement claim. New checkpoint/tokenizer/config reload error0. Output models/candidates/T029_genz500_head_cpu_20261103_r03, training_report.json. Fullencoder/GPUfine-tune NOT_RUN; earlier GPU-only scope remains historical. T031 now reviews actual candidate and may reject promotion.\n';p.write_text(s,encoding='utf-8')
p=next((R/'tasks/moderation-ai').glob('T031-*.md'));s=p.read_text(encoding='utf-8').replace('- **Status:** TODO','- **Status:** IN_PROGRESS',1);p.write_text(s,encoding='utf-8')
state=json.loads((P/'progress.json').read_text(encoding='utf-8'));state.update(T029='DONE',T031='IN_PROGRESS',candidate=str(Path(cfg['output_dir']).relative_to(R)),optimizer_steps=training['optimizer_steps'],training_seconds=training['elapsed_seconds'],full_encoder_finetune=False,next='One final heldout audit and local shadow/fallback/rollback; record worse validation, never auto-promote');(P/'progress.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p in (R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md'):
 s=p.read_text(encoding='utf-8');lines=[]
 for line in s.splitlines():
  if line.startswith('| ') and any(t in line for t in ('**T029**','[T029](','**T031**','[T031](')):
   tid='T029' if 'T029' in line else 'T031';cols=line.split('|');status='DONE' if tid=='T029' else 'IN_PROGRESS';note='Actual CPU head trained534steps; encoder unchanged; validation worse, not activated' if tid=='T029' else 'Actual candidate final audit and local shadow/rollback in progress'
   if '**'+tid+'**' in line:cols[-3]=' '+status+' ';cols[-2]=' '+note+' '
   else:cols[-2]=' '+status+' ';cols[-3]=' '+note+' '
   line='|'.join(cols)
  lines.append(line)
 p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\nT029 DONE for revised head-only CPU scope: real534optimizersteps/3epochs/400.94s,11340trainingrows. Encoder/base/source unchanged, original0.41 unchanged, reloaderror0. Validation .76370125→.75304166 (worse), no activation or repeated training. Newcandidate models/candidates/T029_genz500_head_cpu_20261103_r03. T031 IN_PROGRESS: evaluate actual candidate once on finaltest, synthetic diagnostics and local registry/fallback/rollback; reject if gates fail. FullencoderGPU NOT_RUN.\n')
env={'python':platform.python_version(),'platform':platform.platform(),'versions':{n:importlib.metadata.version(n) for n in ('torch','transformers','huggingface-hub','tokenizers')},'training_cpu_threads':4,'external_cost':0}
(P/'environment.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8')
print('T029 actual training accepted as head-only scope; T031 evaluation started')
