"""Verified development-source index for independent evaluation locking."""
import csv,json
from collections import defaultdict
from pathlib import Path
from .core import comparison,load_json,sha_bytes,sha_file

def development_index(data_root,project_root=None):
    project=Path(project_root or Path(__file__).resolve().parents[2]).resolve()
    known=load_json(Path(data_root)/'manifests/development_exclusions.json',{})
    if not known.get('audit_completed'):raise ValueError('Development/train leakage audit missing')
    threads=set(known.get('thread_ids',[]));texts=set(known.get('long_text_sha256',[]));groups=defaultdict(list)
    def add(text,tid=None):
        value=comparison(text)
        if len(value)>=80:texts.add(sha_bytes(value.encode()))
        if tid:groups[tid].append(text)
    for ref in known.get('source_records',[]):
        path=(project/ref['path']).resolve()
        if not path.is_relative_to(project) or not path.is_file() or sha_file(path)!=ref['sha256']:
            raise ValueError('Development exclusion source missing/changed')
        fmt=ref.get('format','comment_jsonl')
        if fmt=='csv':
            with path.open(encoding='utf-8-sig',newline='') as stream:
                for row in csv.DictReader(stream):add(row[ref['text_field']],row.get('thread_id'))
        elif fmt in ('thread_json','threads_jsonl','comment_jsonl'):
            rows=[load_json(path)] if fmt=='thread_json' else [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
            for row in rows:
                tid=row['thread_id'];threads.add(tid)
                if fmt=='comment_jsonl':add(row.get('raw_text',''),tid)
                else:
                    for c in row['comments']:add(c['text'],tid)
        else:raise ValueError('Unknown development exclusion format')
    return threads,texts,dict(groups)
