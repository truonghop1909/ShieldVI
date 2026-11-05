"""New lock for a proved intake fix; preserves original seal and all model/rule hashes."""
import copy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from verify_ai_readiness_lock import digest,verify_lock
from synthetic_data.pipeline import atomic_json
from prepare_lock import progress
old=P/'READINESS_LOCK.json';new=P/'READINESS_LOCK_T028_v2.json'
if new.exists():raise FileExistsError('Never overwrite sealed tooling revision')
baseline=json.loads(old.read_text(encoding='utf-8'));result=verify_lock(old)
allowed={'scripts/real_dataset/intake.py','tests/test_real_review_lock_readiness.py','tests/test_ai_readiness_lock.py'}
assert result['status']=='FAIL' and set(result['errors'])=={'changed:'+name for name in allowed},result
log=(P/'review_tests_v2.log').read_bytes().decode('utf-16');assert '48 passed' in log
assert '500 == 422' in (P/'intake_empty_url_red_tests.log').read_bytes().decode('utf-16')
atomic_json(P/'baseline_lock_superseded_verification.json',result)
change={'reason':'Provenance source_url empty accepted then500/private-key side effect; API red test proves500 instead422. Enforce min_length1 before staging.',
    'changed_runtime_file':'scripts/real_dataset/intake.py','runtime_lines_changed':1,'labels_changed':False,
    'rules_changed':False,'models_changed':False,'threshold_changed':False,'same_human_protocol_changed':False,
    'before':'API500','after':'API422 with no quarantine/key writes','review_protocol_tests_passed':48,
    'parent_lock_sha256':digest(old),'human_gold_created':False}
atomic_json(P/'tooling_change.json',change)
current=copy.deepcopy(baseline)
for name in allowed:current['files'][name]=digest(R/name)
for p in (old,P/'baseline_lock_superseded_verification.json',P/'tooling_change.json',P/'review_tests_v2.log',P/'intake_empty_url_red_tests.log'):
    current['files'][p.relative_to(R).as_posix()]=digest(p)
current.update(snapshot_id=baseline['snapshot_id']+'+T028-intake-v2',supersedes_lock_sha256=digest(old),
    revision_reason='T028 intake empty-provenance technical fix only; original lock immutable and model/rule/data/evaluation evidence unchanged')
current['test_evidence']['new_review_protocol']=48
assert current['models']==baseline['models'] and current['rule_versions']==baseline['rule_versions']
atomic_json(new,current);verification=verify_lock(new);assert verification['status']=='PASS'
atomic_json(P/'tooling_lock_verification.json',verification)
progress('T028_PROVENANCE_TECHNICAL_FIX_VERIFIED','API empty-source URL reproduced500before fix; min_length1 now returns422before quarantine/key writes.48review testsPASS. Original1306file lock unchanged; new tooling-v2 lock appends5proofs, updates only intake/test hashes. Models/context/target/repeated/data/manifests/evaluations remain unchanged; no new gold or network.')
print(json.dumps({'status':'PASS','current_lock':new.name,'frozen_files':len(current['files']),'runtime_lines_changed':1,'models_rules_unchanged':True}))
