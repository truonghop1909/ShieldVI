import json
from synthetic_data.pipeline import DATA,validate,file_sha
if __name__=='__main__':
 manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
 threads=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((DATA/'threads').glob('*.json'))]
 report=validate(threads)
 assert report['threads']==manifest['actual_threads']
 for tid,sha in manifest['thread_checksums'].items():assert file_sha(DATA/'threads'/(tid+'.json'))==sha
 for name,sha in manifest['csv_checksums'].items():assert file_sha(DATA/name)==sha
 print(json.dumps({k:report[k] for k in ('status','threads','comments','labels','exact_duplicate_comments','near_duplicate_comments','near_duplicate_threads')},ensure_ascii=False))
 raise SystemExit(0 if report['status']=='PASS' else 1)
