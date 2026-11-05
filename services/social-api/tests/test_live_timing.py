import json
import pytest
from test_live_api import live,send
from shieldvi_social.live_timing import attach_enqueue_timing

def test_enqueue_measurement_has_no_text_or_token_and_is_not_duplicated(live,tmp_path):
    path=tmp_path/'enqueue.jsonl';engine=live[0].app.state.engine
    attach_enqueue_timing(engine,path);attach_enqueue_timing(engine,path)
    row=send(live,body='PRIVATE_TEXT_NEVER_LOG_PARAMETERS').json()
    records=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    assert len(records)==1 and records[0]['content_id']==row['id'] and records[0]['enqueue_sql_ms']>=0
    assert 'PRIVATE_TEXT_NEVER_LOG_PARAMETERS' not in path.read_text() and live[1]['Authorization'] not in path.read_text()

def test_enqueue_timing_path_cannot_escape_reports(live):
    with pytest.raises(ValueError,match='inside project reports'):attach_enqueue_timing(live[0].app.state.engine,'C:/outside-private/timing.jsonl')

def test_timing_output_failure_cannot_lose_message(live,tmp_path):
    directory=tmp_path/'directory';directory.mkdir();attach_enqueue_timing(live[0].app.state.engine,directory)
    assert send(live).status_code==201
