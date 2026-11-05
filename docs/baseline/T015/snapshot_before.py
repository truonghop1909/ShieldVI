"""Capture migration source rollback bytes; no database/model copying or writes."""
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'ShieldVI_V3_Hybrid_Review'
SNAPSHOT=HERE/'rollback-source'
if SNAPSHOT.exists():raise RuntimeError('Snapshot already exists; never replace rollback evidence')
files=[]
for directory in ('app','frontend','tests','scripts','notebooks'):
    files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and
        not any(x in p.relative_to(ROOT).parts for x in ('node_modules','__pycache__','.pytest_cache')))
files.extend(ROOT/name for name in ('README.md','requirements.txt','requirements-dev.txt','pytest.ini','.gitignore','run_windows_dashboard.bat'))
records=[]
for path in sorted(files):
    target=SNAPSHOT/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)
    records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
protected=[]
for directory in ('models','datasets'):
    for path in (ROOT/directory).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and '.cache' not in path.parts:
            with path.open('rb') as handle:digest=hashlib.file_digest(handle,'sha256').hexdigest()
            protected.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest})
for path in (ROOT/'shieldvi_reviews.sqlite3',ROOT/'moderation_summaries.sqlite3',ROOT/'services/social-api/data/social.sqlite3'):
    if path.is_file():
        with path.open('rb') as handle:digest=hashlib.file_digest(handle,'sha256').hexdigest()
        protected.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest})
(HERE/'before-manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
(HERE/'protected-manifest.json').write_text(json.dumps(protected,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rollback_files':len(records),'protected_files':len(protected),'database_model_writes':False}))
