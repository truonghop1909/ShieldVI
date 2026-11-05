"""A waiting SQL read in SSE must not block the ASGI event loop."""
import asyncio
from threading import Event
from types import SimpleNamespace
from shieldvi_social import live_routes

def test_sse_database_pool_wait_does_not_block_other_request_cleanup(monkeypatch):
    started=Event();released=Event();calls=0
    def read(*args):
        nonlocal calls
        calls+=1
        if calls>1:
            started.set()
            if not released.wait(1):raise RuntimeError('SSE SQL pool wait blocked event-loop cleanup')
        return {'items':[],'cursor':0,'has_more':False}
    monkeypatch.setattr(live_routes,'read_page',read)
    async def disconnected():return False
    request=SimpleNamespace(query_params={},headers={},is_disconnected=disconnected)
    async def scenario():
        response=live_routes.stream_response(request,None,'post',0,False)
        iterator=response.body_iterator
        assert await anext(iterator)==': heartbeat\n\n'
        async def cleanup_other_request():
            while not started.is_set():await asyncio.sleep(.005)
            released.set()
        cleanup=asyncio.create_task(cleanup_other_request())
        try:
            assert await asyncio.wait_for(anext(iterator),2)==': heartbeat\n\n'
            await cleanup
        finally:
            released.set();cleanup.cancel();await iterator.aclose()
    asyncio.run(scenario())
