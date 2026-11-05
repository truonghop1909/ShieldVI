import argparse
from pathlib import Path
from real_dataset.store import ReviewStore
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);a=p.parse_args();print('Imported',ReviewStore().import_csv(a.csv.read_text(encoding='utf-8-sig')),'rows with revision checks; stale imports fail atomically.')
