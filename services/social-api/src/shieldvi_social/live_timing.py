"""Explicit local benchmark hook: SQL duration/opaque IDs only, no SQL parameters."""
import json,os,time
from pathlib import Path
from sqlalchemy import event
ROOT=Path(__file__).resolve().parents[4]
def attach_enqueue_timing(engine,path):
    target=Path(path).resolve()
    if not target.is_relative_to(ROOT/'reports'):raise ValueError('Local timings must stay inside project reports')
    if getattr(engine,'shieldvi_enqueue_timing',False):return
    target.parent.mkdir(parents=True,exist_ok=True);engine.shieldvi_enqueue_timing=True
    @event.listens_for(engine,'before_cursor_execute')
    def before(connection,cursor,statement,parameters,context,many):
        if statement.lstrip().upper().startswith('INSERT INTO MODERATION_JOBS '):context.shieldvi_enqueue_start=time.perf_counter_ns()
    @event.listens_for(engine,'after_cursor_execute')
    def after(connection,cursor,statement,parameters,context,many):
        started=getattr(context,'shieldvi_enqueue_start',None)
        if started is None:return
        elapsed=(time.perf_counter_ns()-started)/1e6
        # Duration is SQL execution before commit. Final report joins only committed content IDs.
        try:
            if target.exists() and target.stat().st_size>=1048576:return
            rows=[{'content_id':row.get('entity_id'),'enqueue_sql_ms':elapsed,'batched':bool(many)} for row in context.compiled_parameters]
            with target.open('a',encoding='utf-8') as output:
                for row in rows:output.write(json.dumps(row)+'\n')
        except OSError:pass  # Observability never rolls back a user's content transaction.
