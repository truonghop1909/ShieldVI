"""Check a versioned exclusion manifest without editing the sealed default index."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from real_dataset.leakage import development_index
from real_dataset.core import comparison,sha_bytes

def check(manifest,thread,project_root=R):
    with tempfile.TemporaryDirectory(prefix='shieldvi_exclusion_') as folder:
        root=Path(folder);(root/'manifests').mkdir()
        shutil.copyfile(manifest,root/'manifests/development_exclusions.json')
        ids,text_hashes,_=development_index(root,project_root)
    matches=[c['comment_id'] for c in thread['comments'] if len(comparison(c['text']))>=80 and sha_bytes(comparison(c['text']).encode()) in text_hashes]
    excluded=thread['thread_id'] in ids or bool(matches)
    return {'status':'EXCLUDED_DEVELOPMENT' if excluded else 'NOT_MATCHED_BY_THIS_GUARD',
        'thread_id_match':thread['thread_id'] in ids,'matching_long_comment_ids':matches,
        'independent_evaluation_approved':False,'note':'No match is not proof of independence; full provenance/privacy/near-duplicate audit still required.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--thread',type=Path,required=True);args=parser.parse_args()
    result=check(args.manifest,json.loads(args.thread.read_text(encoding='utf-8-sig')));print(json.dumps(result))
    raise SystemExit(2 if result['status']=='EXCLUDED_DEVELOPMENT' else 0)
