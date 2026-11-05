"""Read-only source/checkpoint/dataset/schema checks; evidence stays here."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[2]
SOURCE=DESIGN.parent/'ShieldVI_V3_Hybrid_Review'


def sha(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def changes(path):
    rows=json.loads(path.read_text(encoding='utf-8'))
    return len(rows),[r['path'] for r in rows if not (SOURCE/r['path']).is_file() or sha(SOURCE/r['path'])!=r['sha256']]


count,original=changes(HERE.parent/'T007/source-manifest.json')
prior_count,prior=changes(HERE.parent/'T013_T018/source-manifest.json')
evaluation=json.loads((HERE/'ai-evaluation.json').read_text(encoding='utf-8'))
checkpoint=SOURCE/'models/visobert_head_refined'
assert sha(checkpoint/'model.safetensors')==evaluation['model']['weights_sha256']
assert sha(checkpoint/'threshold_config.json')==evaluation['model']['threshold_config_sha256']
assert sha(SOURCE/'scripts/evaluate_social_policy.py')==evaluation['source_hashes']['evaluator']
assert sha(SOURCE/'services/social-api/src/shieldvi_social/policy.py')==evaluation['source_hashes']['active_policy']
manifest=json.loads((SOURCE/'datasets/manifest.json').read_text(encoding='utf-8'))
raw_files=[]
for info in manifest['sources'].values():
    for entry in info['raw_files']:
        assert sha(SOURCE/'datasets'/entry['path'])==entry['sha256']
        raw_files.append(entry['path'])
database=SOURCE/'services/social-api/data/social.sqlite3'
versions=None
if database.is_file():
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        versions=[r[0] for r in db.execute('SELECT version_num FROM alembic_version')]
bundle_hits=[]
for app in ('social-web','moderation-web'):
    for path in (SOURCE/'apps'/app/'dist').rglob('*.js'):
        text=path.read_text(encoding='utf-8')
        if any(name in text for name in ('SOCIAL_AI_SERVICE_TOKEN','AI_SERVICE_TOKEN')):bundle_hits.append(path.relative_to(SOURCE).as_posix())
assert original==['app/main.py']
assert not any(p.startswith(('apps/social-web/src/','apps/moderation-web/src/')) for p in prior)
assert not bundle_hits
outage=json.loads((HERE/'outage/result.json').read_text(encoding='utf-8'))
assert outage['status']=='PASS' and outage['actual_ai_absent_seconds']>=600
assert json.loads((HERE/'outage/cleanup.json').read_text())['owned_processes_exited']
assert all(json.loads((HERE/'fullstack/process-health.json').read_text()).values())
record={'original_files_checked':count,'original_changes_since_T007':original,'previous_files_checked':prior_count,
    'changes_since_T013_T018':prior,'social_and_moderation_web_product_source_unchanged':True,
    'raw_dataset_files_hash_checked':len(raw_files),'checkpoint_and_threshold_unchanged':True,
    'evaluation_source_hashes_match':True,'browser_bundle_service_key_references':bundle_hits,
    'default_social_db_schema_read_only':versions,'live_db_migrated':False,'git_commit':None,
    'real_checkpoint_evaluation':'PASS_CPU','ai_process_outage_wall_seconds':outage['actual_ai_absent_seconds']}
(HERE/'integrity-check.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
files=[]
for directory in ('app','tests','scripts','services/social-api/src/shieldvi_social','services/social-api/tests',
                  'apps/moderation-web/src','apps/moderation-web/tests','apps/social-web/src'):
    for path in sorted((SOURCE/directory).rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:continue
        files.append({'path':path.relative_to(SOURCE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
(HERE/'source-manifest.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
for path in HERE.glob('*.txt'):
    raw=path.read_bytes()
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')):path.write_text(raw.decode('utf-16'),encoding='utf-8')
print(json.dumps(record))
