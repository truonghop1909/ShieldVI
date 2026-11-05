"""Optional local summary storage. Raw messages are not stored by default."""
import os
import sqlite3
from datetime import datetime, timezone


def db_enabled() -> bool:
    return os.environ.get("STORE_SUMMARIES", "0") == "1"


def db_path() -> str:
    return os.environ.get("DB_PATH", "moderation_summaries.sqlite3")


def connect():
    db = sqlite3.connect(db_path())
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analyzed_at TEXT NOT NULL,
        thread_id TEXT NOT NULL,
        profile TEXT NOT NULL,
        comments_count INTEGER NOT NULL,
        flagged INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        risk_score_heuristic INTEGER NOT NULL
    )""")
    db.commit()
    return db


def save_result(result):
    if not db_enabled():
        return
    with connect() as db:
        db.execute(
            "INSERT INTO analyses (analyzed_at, thread_id, profile, comments_count, flagged, risk_level, risk_score_heuristic) VALUES (?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), result.thread_id, result.profile,
             len(result.comments), int(result.suspected_repeated_harassment),
             result.risk_level, result.risk_score_heuristic),
        )
        db.commit()


def recent_results(limit: int = 50):
    if not db_enabled():
        return []
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT analyzed_at, thread_id, profile, comments_count, flagged, risk_level, risk_score_heuristic FROM analyses ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()]
