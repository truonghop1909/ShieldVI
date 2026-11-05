from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import Settings
from .db import make_engine, session_factory
from .middleware import RequestBoundary
from .routes import router
from .content_routes import router as content_router
from .moderation_routes import router as moderation_router
from .review_routes import router as review_router
from .security import PASSWORD_HASHER, new_token

SCHEMA_REVISION = "0004_review"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = make_engine(settings)

    @asynccontextmanager
    async def lifespan(app):
        try:
            try:
                with engine.connect() as connection:
                    versions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
                    if versions != [SCHEMA_REVISION]:
                        raise RuntimeError("Social DB schema is not current; run alembic upgrade head")
            except SQLAlchemyError:
                raise RuntimeError("Social DB is unavailable or unmigrated; run alembic upgrade head") from None
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="ShieldVI Social API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = session_factory(engine)
    app.state.dummy_password_hash = PASSWORD_HASHER.hash(new_token())
    app.add_middleware(RequestBoundary)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                       allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
                       expose_headers=["Idempotency-Replayed"])

    @app.exception_handler(RequestValidationError)
    async def validation_error(_, exc):
        # FastAPI's default validation response includes input values/passwords.
        detail = [{"loc": [part if isinstance(part, int) or part in {"body", "query", "path", "header", "cookie"}
                           else "field" for part in error["loc"]], "type": error["type"], "msg": "Invalid request value"}
                  for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.get("/health")
    def health():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return {"status": "ready", "service": "social-api"}

    app.include_router(router)
    app.include_router(content_router)
    app.include_router(moderation_router)
    app.include_router(review_router)
    return app
