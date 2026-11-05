"""Opt-in canonical AI app composition, default-v5 internal live endpoint."""
from fastapi import FastAPI,APIRouter,Depends,HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from . import main
from .moderation_adapter import service_auth,guard
from .moderation_contract import ModerationRequest
from .live_analysis_contract import LiveModerationResponse
from .live_analysis import IncrementalAnalyzer

class LiveBodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['path']!='/api/live/moderate/comment':return await self.app(scope,receive,send)
        messages=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            size+=len(message.get('body',b''))
            if size>1048576:return await JSONResponse({'detail':'Payload too large'},status_code=413)(scope,receive,send)
            messages.append(message)
            if not message.get('more_body',False):break
        async def replay():return messages.pop(0) if messages else await receive()
        return await self.app(scope,replay,send)

def create_app():
    app=FastAPI(title='ShieldVI AI canonical + live adapter',version='0.1.0-live',lifespan=main.lifespan)
    builtin={'/openapi.json','/docs','/docs/oauth2-redirect','/redoc'}
    app.router.routes.extend(route for route in main.app.routes if getattr(route,'path','') not in builtin)
    app.user_middleware=list(main.app.user_middleware);app.exception_handlers=dict(main.app.exception_handlers)
    app.add_middleware(LiveBodyLimit);app.state.live_analyzers={}
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        if request.url.path!='/api/live/moderate/comment':return await main.validation_error(request,exc)
        return JSONResponse(status_code=422,content={'detail':[{'type':error['type'],'msg':'Invalid moderation payload'} for error in exc.errors()]})
    @app.exception_handler(HTTPException)
    async def http_error(request,exc):
        if request.url.path=='/api/live/moderate/comment' and exc.status_code>=500:
            return JSONResponse(status_code=exc.status_code,content={'detail':'Moderation inference unavailable'})
        return await main.http_error(request,exc)
    router=APIRouter()
    @router.post('/api/live/moderate/comment',response_model=LiveModerationResponse,dependencies=[Depends(service_auth)])
    def analyze(payload:ModerationRequest,predictor=Depends(main.get_predictor)):
        if not guard.inference.acquire(blocking=False):raise HTTPException(429,'Inference busy',headers={'Retry-After':'2'})
        try:
            key=id(predictor)
            if key not in app.state.live_analyzers:app.state.live_analyzers[key]=IncrementalAnalyzer(predictor)
            return app.state.live_analyzers[key].analyze(payload)
        except HTTPException:raise
        except Exception:raise HTTPException(503,'Moderation inference unavailable') from None
        finally:guard.inference.release()
    app.include_router(router)
    return app
