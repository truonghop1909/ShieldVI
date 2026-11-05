"""Read-only verification of a frozen research bundle; never loads/trains a model."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()

def verify_lock(path,root=ROOT):
    root=Path(root).resolve();data=json.loads(Path(path).read_text(encoding='utf-8'));errors=[]
    if data.get('schema_version')!=1 or data.get('status')!='FROZEN_RESEARCH_READINESS':errors.append('unsupported_lock')
    if data.get('threshold')!=.41 or data.get('training_allowed') is not False or data.get('production_activation_allowed') is not False:
        errors.append('unsafe_scope_or_threshold')
    if data.get('human_gold') is not False or data.get('T028_status')!='BLOCKED':errors.append('unsupported_evidence_claim')
    allowed=[root]+[Path(p).resolve() for p in data.get('external_model_roots',[])]
    files=data.get('files',{});seen=set()
    if not files:errors.append('empty_bundle')
    for name,expected in files.items():
        item=(root/name).resolve()
        if not any(item.is_relative_to(base) for base in allowed):errors.append('path_outside_bundle_roots:'+name);continue
        if item in seen:errors.append('duplicate_resolved_path:'+name);continue
        seen.add(item)
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):errors.append('invalid_sha256:'+name);continue
        if not item.is_file():errors.append('missing:'+name)
        elif digest(item)!=expected:errors.append('changed:'+name)
    return {'status':'PASS' if not errors else 'FAIL','files_checked':len(seen),'errors':errors,
        'lock_sha256':digest(path),'training_performed':False,'model_inference_performed':False,
        'production_changed':False,'human_gold':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lock',type=Path,required=True);a=p.parse_args()
    result=verify_lock(a.lock);print(json.dumps(result,ensure_ascii=True));raise SystemExit(0 if result['status']=='PASS' else 1)
