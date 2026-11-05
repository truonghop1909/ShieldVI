import argparse,json
from real_dataset.store import ReviewStore
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reviewer',required=True);a=p.parse_args();rows=ReviewStore().round2_queue(a.reviewer);print(json.dumps({'pending_round2':len(rows),'comment_ids':[r['comment_id'] for r in rows]},ensure_ascii=True));print('Use local UI Round 2; no labels are automatically confirmed.')
