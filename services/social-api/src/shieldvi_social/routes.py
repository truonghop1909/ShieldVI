import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .dependencies import Principal, content_writer, current_principal, get_content_write_db, get_db, require_roles, unauthenticated
from .models import AuthSession, User
from .rate_limit import enforce_auth_limit
from .schemas import LoginInput, RegisterInput, TokenOutput, UserOutput
from .security import PASSWORD_HASHER, new_token, token_digest, verify_password

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", status_code=201, response_model=UserOutput)
def register(payload: RegisterInput, request: Request, db: Session = Depends(get_db)):
    if not request.app.state.settings.registration_enabled:
        raise HTTPException(403, "Registration is disabled for this private demo")
    enforce_auth_limit(request, "register", payload.username)
    user = User(username=payload.username, email=str(payload.email).lower(),
                password_hash=PASSWORD_HASHER.hash(payload.password.get_secret_value()),
                role="user", status="active")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account could not be registered") from None
    return UserOutput.from_user(user)


@router.post("/auth/login", response_model=TokenOutput)
def login(payload: LoginInput, request: Request, db: Session = Depends(get_db)):
    enforce_auth_limit(request, "login", payload.username)
    # Rate limiting committed in its own session above. Claim the SQLite writer
    # before reading the user; deferred read -> write upgrades can deadlock with
    # the worker even with busy_timeout configured.
    if db.bind.dialect.name == "sqlite":
        db.connection(execution_options={"sqlite_immediate": True})
    user = db.scalar(select(User).where(User.username == payload.username))
    encoded = user.password_hash if user else request.app.state.dummy_password_hash
    valid = verify_password(encoded, payload.password.get_secret_value())
    if not valid or user is None or user.status != "active":
        raise unauthenticated()
    if PASSWORD_HASHER.check_needs_rehash(encoded):
        user.password_hash = PASSWORD_HASHER.hash(payload.password.get_secret_value())
    now = int(time.time())
    # Prune expired sessions for this account on successful login, not raw tokens.
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id, AuthSession.expires_at <= now))
    token = new_token()
    ttl = request.app.state.settings.session_ttl_seconds
    db.add(AuthSession(token_hash=token_digest(token), user_id=user.id, created_at=now, expires_at=now + ttl))
    db.commit()
    return TokenOutput(access_token=token, expires_in=ttl)


@router.get("/me", response_model=UserOutput)
def me(principal: Principal = Depends(current_principal)):
    return UserOutput.from_user(principal.user)


@router.post("/auth/logout", status_code=204)
def logout(principal: Principal = Depends(content_writer), db: Session = Depends(get_content_write_db)):
    db.delete(principal.session)
    db.commit()
    return Response(status_code=204)


@router.get("/admin/access")
def admin_access(principal: Principal = Depends(require_roles("admin"))):
    """Read-only RBAC probe; no moderation/content features in T008."""
    return {"authorized": True, "role": principal.user.role}
