"""Opt-in extension of the canonical Social app; no automatic DB migration."""
from .main import create_app as canonical_app
from .live_store import require_live_schema
from .live_routes import router
from .live_review_routes import router as review_router

def create_app(settings=None):
    app=canonical_app(settings);require_live_schema(app.state.engine)
    from starlette.middleware import Middleware
    from .middleware import RequestBoundary
    from .live_boundary import LiveRequestBoundary
    app.user_middleware=[Middleware(LiveRequestBoundary,**m.kwargs) if m.cls is RequestBoundary else m for m in app.user_middleware]
    app.state.engine.shieldvi_live_events=True
    app.include_router(router)
    app.include_router(review_router)
    from .live_quick_test import QuickTests,router as quick_test_router
    app.state.quick_tests=QuickTests()
    app.include_router(quick_test_router)
    from contextlib import asynccontextmanager
    from starlette.concurrency import run_in_threadpool
    original_lifespan=app.router.lifespan_context
    @asynccontextmanager
    async def quick_lifespan(instance):
        async with original_lifespan(instance):
            try:yield
            finally:await run_in_threadpool(instance.state.quick_tests.close)
    app.router.lifespan_context=quick_lifespan
    import os
    if os.environ.get('SHIELDVI_LIVE_SQL_TIMINGS'):
        from .live_timing import attach_enqueue_timing
        attach_enqueue_timing(app.state.engine,os.environ['SHIELDVI_LIVE_SQL_TIMINGS'])
    if os.environ.get('SHIELDVI_STUDIO_ROOT'):
        from .studio_routes import router as studio_router,DatasetStore
        app.state.studio=DatasetStore(os.environ['SHIELDVI_STUDIO_ROOT'])
        app.include_router(studio_router)
    return app
