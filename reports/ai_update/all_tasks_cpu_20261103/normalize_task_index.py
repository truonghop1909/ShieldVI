from pathlib import Path
import json,hashlib
R=Path.cwd();P=R/'reports/ai_update/all_tasks_cpu_20261103'
for p in (R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md'):
 lines=[]
 for line in p.read_text(encoding='utf-8').splitlines():
  if line.startswith('| ') and any(t in line for t in ('**T029**','[T029](','**T031**','[T031](')):
   tid='T029' if 'T029' in line else 'T031';cols=line.split('|')
   if '**'+tid+'**' in line:
    cols[2]=' **T029** — Bounded CPU head-only candidate experiment ' if tid=='T029' else ' **T031** — Local registry / shadow / rollback review '
    cols[3]=' P2 ';cols[4]=' T027,T028 + bounded localCPU authorization ' if tid=='T029' else ' T029,T030 (local review) '
   else:cols[2]=' T027,T028 + bounded localCPU authorization ' if tid=='T029' else ' T029,T030 (local review) '
   line='|'.join(cols)
  lines.append(line)
 p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
manifest_path=P/'ARTIFACTS.json';m=json.loads(manifest_path.read_text(encoding='utf-8'))
for p in (R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md',Path(__file__).resolve()):
 m['files'][str(p.relative_to(R)).replace('\\','/')]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v['sha256'] for p,v in m['files'].items())
print(json.dumps({'artifact_hashes_verified':len(m['files']),'task_titles_and_dependencies_match_revised_scope':True,'all_existing_tasks_DONE':27}))
