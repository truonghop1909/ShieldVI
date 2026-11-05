"""Opt-in human review rows in SQLite, without raw comment text.

Local research prototype. No authentication: only expose behind trusted local
Colab session or a private authenticated reverse proxy.
"""
from __future__ import annotations
import csv
import io
import os
import sqlite3
from datetime import datetime, timezone
from .paths import storage_path


def review_db_path() -> str:
    return storage_path('REVIEW_DB_PATH', 'shieldvi_reviews.sqlite3')


def connect():
    path = review_db_path()
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    db = sqlite3.connect(path, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=20000')
    db.execute('''CREATE TABLE IF NOT EXISTS human_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT NOT NULL,
        comment_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        human_label TEXT NOT NULL CHECK(human_label IN ('clean','toxic','uncertain')),
        ai_label TEXT NOT NULL CHECK(ai_label IN ('clean','toxic')),
        toxicity_score REAL NOT NULL CHECK(toxicity_score >= 0 AND toxicity_score <= 1),
        lexical_flag INTEGER NOT NULL DEFAULT 0,
        updated_at_utc TEXT NOT NULL,
        UNIQUE(thread_id,comment_id,reviewer_id)
    )''')
    db.commit()
    return db


def save_reviews(batch):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        for item in batch.items:
            db.execute('''INSERT INTO human_reviews
                (thread_id,comment_id,reviewer_id,human_label,ai_label,toxicity_score,lexical_flag,updated_at_utc)
                VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(thread_id,comment_id,reviewer_id) DO UPDATE SET
                    human_label=excluded.human_label, ai_label=excluded.ai_label,
                    toxicity_score=excluded.toxicity_score, lexical_flag=excluded.lexical_flag,
                    updated_at_utc=excluded.updated_at_utc''',(
                batch.thread_id, item.comment_id, batch.reviewer_id, item.human_label,
                item.ai_label, item.toxicity_score, int(item.lexical_flag), now,
            ))
    return len(batch.items)


def list_reviews(thread_id=None, reviewer_id=None, limit=5000):
    clauses = []
    params = []
    if thread_id:
        clauses.append('thread_id=?')
        params.append(thread_id)
    if reviewer_id:
        clauses.append('reviewer_id=?')
        params.append(reviewer_id)
    where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
    sql = ('SELECT thread_id,comment_id,reviewer_id,human_label,ai_label,toxicity_score,lexical_flag,updated_at_utc '
           'FROM human_reviews' + where + ' ORDER BY updated_at_utc DESC, id DESC LIMIT ?')
    with connect() as db:
        return [dict(row) for row in db.execute(sql, params + [limit])]


def review_stats():
    with connect() as db:
        rows = [dict(row) for row in db.execute('SELECT human_label,ai_label FROM human_reviews')]
    labeled = [r for r in rows if r['human_label'] != 'uncertain']
    return {
        'total_reviews': len(rows),
        'confirmed': len(labeled),
        'uncertain': len(rows) - len(labeled),
        'true_positive': sum(r['human_label']=='toxic' and r['ai_label']=='toxic' for r in labeled),
        'true_negative': sum(r['human_label']=='clean' and r['ai_label']=='clean' for r in labeled),
        'false_positive': sum(r['human_label']=='clean' and r['ai_label']=='toxic' for r in labeled),
        'false_negative': sum(r['human_label']=='toxic' and r['ai_label']=='clean' for r in labeled),
        'limitation': 'Số liệu chỉ dựa vào nhãn người duyệt, không phải đánh giá trên tập gold độc lập.'
    }


def export_csv(rows):
    buf = io.StringIO(newline='')
    fields = ['thread_id','comment_id','reviewer_id','human_label','ai_label',
              'toxicity_score','lexical_flag','updated_at_utc']
    writer = csv.DictWriter(buf,fieldnames=fields)
    writer.writeheader()
    for record in rows:
        # Mitigate Excel formula injection when IDs are opened as spreadsheet cells.
        writer.writerow({key:("'" + str(record[key]) if isinstance(record.get(key),str) and
                         record[key].startswith(('=','+','-','@')) else record.get(key,'')) for key in fields})
    return '\ufeff' + buf.getvalue()
