import hashlib
import time

from fastapi import HTTPException, Request
from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .models import AuthRateBucket


def enforce_auth_limit(request: Request, action: str, username: str):
    """DB-atomic fixed window, both peer IP and account. No forwarded-header trust."""
    settings = request.app.state.settings
    now = int(time.time())
    width = settings.auth_rate_window_seconds
    window = now // width * width
    peer = request.client.host if request.client else "unknown"
    keys = [f"{action}:peer:{peer}", f"{action}:account:{username}"]
    counts = []
    with request.app.state.sessions.begin() as db:
        # Bound retention of buckets; old keys contain hashes, never raw IP/identity.
        db.execute(delete(AuthRateBucket).where(AuthRateBucket.window_start < window - width))
        insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
        for raw in sorted(keys):
            key = hashlib.sha256(raw.encode()).hexdigest()
            statement = insert(AuthRateBucket).values(key_hash=key, window_start=window, count=1)
            statement = statement.on_conflict_do_update(
                index_elements=[AuthRateBucket.key_hash],
                set_={
                    "count": case((AuthRateBucket.window_start == window, AuthRateBucket.count + 1), else_=1),
                    "window_start": window,
                },
            ).returning(AuthRateBucket.count)
            counts.append(db.execute(statement).scalar_one())
    if max(counts) > settings.auth_rate_limit:
        raise HTTPException(429, "Too many authentication attempts",
                            headers={"Retry-After": str(window + width - now)})
