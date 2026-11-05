import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .models import AuthSession, User
from .security import token_digest

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request):
    with request.app.state.sessions() as db:
        yield db


def unauthenticated():
    return HTTPException(401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})


@dataclass
class Principal:
    user: User
    session: AuthSession


def current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Principal:
    return authenticate(credentials, db)


def authenticate(credentials, db) -> Principal:
    if not credentials or len(credentials.credentials) != 43:
        raise unauthenticated()
    session = db.get(AuthSession, token_digest(credentials.credentials))
    if not session or session.expires_at <= int(time.time()):
        raise unauthenticated()
    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        raise unauthenticated()
    return Principal(user, session)


def get_content_write_db(request: Request):
    with request.app.state.sessions() as db:
        if db.bind.dialect.name == "sqlite":
            db.connection(execution_options={"sqlite_immediate": True})
        yield db


def content_writer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_content_write_db),
):
    return authenticate(credentials, db)


def require_roles(*roles: str):
    def check(principal: Principal = Depends(current_principal)):
        if principal.user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return principal
    return check
