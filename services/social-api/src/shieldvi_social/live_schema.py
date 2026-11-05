"""Explicit additive initialization for a named local/disposable Social DB."""
import argparse
from .config import Settings
from .db import make_engine
from .live_store import initialize,require_live_schema

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--database-url',required=True);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    engine=make_engine(Settings(database_url=args.database_url))
    try:
        (require_live_schema if args.verify_only else initialize)(engine)
        print('LIVE_SCHEMA_READY_BASE_0004_PRESERVED')
    finally:engine.dispose()
