"""Existing durable worker with event hooks enabled; original worker unchanged."""
import time
from .config import Settings
from .db import make_engine
from .ai_client import AIClient,WorkerSettings
from .worker import Worker
from .live_store import require_live_schema

def run():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--incremental',action='store_true');args=parser.parse_args()
    engine=make_engine(Settings.from_env());require_live_schema(engine);engine.shieldvi_live_events=True
    settings=WorkerSettings.from_env()
    if args.incremental:
        from .live_ai_client import LiveAIClient
        from .live_analysis_worker import ConversationWorker
        ai=LiveAIClient(settings);worker=ConversationWorker(engine,settings,ai)
    else:ai=AIClient(settings);worker=Worker(engine,settings,ai)
    try:
        while True:
            if not worker.run_once():time.sleep(settings.poll_seconds)
    finally:ai.close();engine.dispose()

if __name__=='__main__':run()
