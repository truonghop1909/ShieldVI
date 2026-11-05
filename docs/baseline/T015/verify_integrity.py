"""Verify relocation mapping, rollback bytes and protected assets without DB writes."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'ShieldVI_V3_Hybrid_Review'


def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def mapped(path):
    if path.startswith('app/'):return 'services/moderation-ai/'+path
    if path.startswith('frontend/'):return 'apps/moderation-web/legacy-v3/'+path[len('frontend/'):]
    return path


before=json.loads((HERE/'before-manifest.json').read_text(encoding='utf-8'))
changes=[];missing=[];rollback_changed=[]
for row in before:
    target=ROOT/mapped(row['path'])
    if not target.is_file():missing.append(row['path'])
    elif sha(target)!=row['sha256']:changes.append(row['path'])
    if sha(HERE/'rollback-source'/row['path'])!=row['sha256']:rollback_changed.append(row['path'])
protected=json.loads((HERE/'protected-manifest.json').read_text(encoding='utf-8'))
changed_protected=[r['path'] for r in protected if sha(ROOT/r['path'])!=r['sha256']]
assert not missing and not rollback_changed and not changed_protected
assert not any(p.startswith(('app/data/','app/static/','frontend/src/')) for p in changes)
previous=json.loads((HERE.parent/'T014_T019/source-manifest.json').read_text(encoding='utf-8'))
social_ui_changes=[r['path'] for r in previous if r['path'].startswith(('apps/social-web/src/','apps/moderation-web/src/'))
    and sha(ROOT/r['path'])!=r['sha256']]
assert not social_ui_changes
db_path=ROOT/'services/social-api/data/social.sqlite3'
with closing(sqlite3.connect(db_path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
    schema=[r[0] for r in db.execute('SELECT version_num FROM alembic_version')]
real=json.loads((HERE/'real-http-smoke.json').read_text(encoding='utf-8'))
assert real['status']=='PASS' and real['real_cpu_inference'] and real['static_byte_equal']
record={'relocated_or_retained_source_files_checked':len(before),'intentional_changed_original_paths':changes,
    'missing_after_mapping':missing,'rollback_source_modified':rollback_changed,
    'protected_models_datasets_databases_checked':len(protected),'changed_protected_assets':changed_protected,
    'lexicon_static_react_v3_source_byte_unchanged':True,'social_web_product_changes':social_ui_changes,
    'default_social_db_schema_read_only':schema,'live_database_migration':False,
    'real_http_before_after_equal':True,'git_commit':None}
(HERE/'integrity-check.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
files=[]
for directory in ('app','frontend','services/moderation-ai','apps/moderation-web/legacy-v3','tests','scripts','notebooks'):
    for path in sorted((ROOT/directory).rglob('*')):
        relative=path.relative_to(ROOT)
        if not path.is_file() or any(p in {'__pycache__','node_modules','.venv','.pytest_cache'} for p in relative.parts):continue
        files.append({'path':relative.as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
(HERE/'after-manifest.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
for path in HERE.glob('*.txt'):
    raw=path.read_bytes()
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')):path.write_text(raw.decode('utf-16'),encoding='utf-8')
print(json.dumps(record))
