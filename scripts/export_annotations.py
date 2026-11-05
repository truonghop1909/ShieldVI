import argparse
from pathlib import Path
from real_dataset.store import ReviewStore
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reviewer');a=p.parse_args();s=ReviewStore();
 if a.output.exists():raise SystemExit('Output exists; choose a new filename')
 a.output.write_text(s.export_csv(a.reviewer),encoding='utf-8');print('Manual annotations exported; no model predictions or raw source identities.')
