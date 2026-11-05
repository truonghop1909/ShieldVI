import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url

SERVICE_ROOT = Path(__file__).resolve().parents[2]


def positive_int(name: str, default: int, maximum: int) -> int:
    value = int(os.environ.get(name, default))
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} outside allowed range")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = f"sqlite:///{(SERVICE_ROOT / 'data/social.sqlite3').as_posix()}"
    registration_enabled: bool = False
    session_ttl_seconds: int = 3600
    cors_origins: tuple[str, ...] = ()
    auth_rate_limit: int = 10
    auth_rate_window_seconds: int = 60
    content_rate_limit: int = 30
    content_rate_window_seconds: int = 60

    def __post_init__(self):
        url = make_url(self.database_url)
        if url.drivername not in {"sqlite", "postgresql+psycopg"}:
            raise ValueError("Use SQLite or postgresql+psycopg for Social DB")
        if url.drivername == "sqlite":
            if not url.database or url.database == ":memory:" or url.query:
                raise ValueError("Use a dedicated file SQLite DB without URL query options")
            db_path = Path(url.database)
            if not db_path.is_absolute():
                raise ValueError("SQLite path must be absolute to avoid cwd-dependent databases")
            if db_path.name.lower() in {"shieldvi_reviews.sqlite3", "moderation_summaries.sqlite3", "shieldvi_v3_reviews.sqlite3"}:
                raise ValueError("Social DB must be separate from legacy AI databases")
        if not 60 <= self.session_ttl_seconds <= 86400:
            raise ValueError("Session TTL must be between 60 and 86400 seconds")
        if not 1 <= self.auth_rate_limit <= 1000 or not 1 <= self.auth_rate_window_seconds <= 3600:
            raise ValueError("Invalid auth rate limit")
        if not 1 <= self.content_rate_limit <= 1000 or not 1 <= self.content_rate_window_seconds <= 3600:
            raise ValueError("Invalid content rate limit")
        for origin in self.cors_origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or "*" in origin:
                raise ValueError("CORS origins must be exact HTTP(S) origins")

    @classmethod
    def from_env(cls):
        registration = os.environ.get("SOCIAL_REGISTRATION_ENABLED", "false").lower()
        if registration not in {"true", "false"}:
            raise ValueError("SOCIAL_REGISTRATION_ENABLED must be true or false")
        origins = json.loads(os.environ.get("SOCIAL_CORS_ORIGINS", "[]"))
        if not isinstance(origins, list) or not all(isinstance(item, str) for item in origins):
            raise ValueError("SOCIAL_CORS_ORIGINS must be a JSON array of origins")
        return cls(
            database_url=os.environ.get("SOCIAL_DATABASE_URL", cls.database_url),
            registration_enabled=registration == "true",
            session_ttl_seconds=positive_int("SOCIAL_SESSION_TTL_SECONDS", 3600, 86400),
            cors_origins=tuple(origins),
            auth_rate_limit=positive_int("SOCIAL_AUTH_RATE_LIMIT", 10, 1000),
            auth_rate_window_seconds=positive_int("SOCIAL_AUTH_RATE_WINDOW_SECONDS", 60, 3600),
            content_rate_limit=positive_int("SOCIAL_CONTENT_RATE_LIMIT", 30, 1000),
            content_rate_window_seconds=positive_int("SOCIAL_CONTENT_RATE_WINDOW_SECONDS", 60, 3600),
        )
