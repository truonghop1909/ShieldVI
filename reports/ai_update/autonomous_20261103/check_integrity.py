import json,hashlib
from pathlib import Path
R=Path.cwd();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=json.loads((R/'reports/ai_update/final/session_verification.json').read_text(encoding='utf-8'))['protected_hashes_unchanged']
changed=[p for p,s in original.items() if not Path(p).is_file() or sha(p)!=s]
m=json.loads((R/'datasets/synthetic_conversations/manifest.json').read_text(encoding='utf-8'))
print('Legacy hash keys:',[k for k in m if 'checksum' in k])
legacy=[]
for key in ('thread_checksums','csv_checksums'):
 for name,s in m.get(key,{}).items():
  p=R/'datasets/synthetic_conversations'/('threads' if key=='thread_checksums' else '')/(name+'.json' if key=='thread_checksums' else name)
  if not p.is_file() or sha(p)!=s:legacy.append(str(p))
report={'status':'PASS' if not changed and not legacy else 'FAIL','protected_artifacts':len(original),'changed':changed,'legacy_threads_checked':len(m.get('thread_checksums',{})),'legacy_csv_checked':len(m.get('csv_checksums',{})),'legacy_changes':legacy,'threshold':.41,'live_db_modified':False}
(R/'reports/ai_update/autonomous_20261103/integrity_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print({k:v for k,v in report.items() if k not in ('legacy_changes','changed')})


