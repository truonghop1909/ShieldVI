import argparse,json
from pathlib import Path
from real_dataset.validation import write_quality
from real_dataset.core import DATA
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=DATA);a=p.parse_args();r=write_quality(a.data_root);print(json.dumps({k:r[k] for k in ('actual_threads','comments','source_counts','annotations','errors')},ensure_ascii=True));raise SystemExit(1 if r['errors'] else 0)
