"""Launch the shared local reviewer with an isolated synthetic review overlay."""
import argparse
from real_dataset.review_app import create_app as create_shared_app
from .pipeline import DATA
from .review_store import SyntheticReviewStore,CATEGORIES

def create_app(data_root=DATA,test_mode=False):
    return create_shared_app(data_root,test_mode,store_factory=SyntheticReviewStore,
      profile={'mode':'synthetic','categories':CATEGORIES,'ai_reference_labels_visible':True})

def main():
    import uvicorn
    p=argparse.ArgumentParser(description='Review synthetic AI reference labels locally; never train.')
    p.add_argument('--port',type=int,default=8011);args=p.parse_args()
    if not 1024<=args.port<=65535:p.error('Choose a local port 1024..65535')
    uvicorn.run(create_app(),host='127.0.0.1',port=args.port)
