"""Bounded internal HTTP client. No ML imports, proxies, redirects, or browser keys."""
import json
import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx
from pydantic import SecretStr, ValidationError

from .moderation_contract import ModerationResponse


@dataclass(frozen=True)
class WorkerSettings:
    service_token: SecretStr = field(repr=False)
    base_url: str = "http://127.0.0.1:8000"
    connect_timeout: float = 3
    read_timeout: float = 60
    lease_seconds: int = 180
    max_attempts: int = 3
    poll_seconds: float = 2

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.path not in {"", "/"} or url.query or url.fragment:
            raise ValueError("AI base URL must be an exact HTTP(S) origin")
        if len(self.service_token.get_secret_value()) < 32:
            raise ValueError("SOCIAL_AI_SERVICE_TOKEN must have at least 32 characters")
        if not 0 < self.connect_timeout <= 30 or not 0 < self.read_timeout <= 300:
            raise ValueError("Invalid AI timeouts")
        if not self.read_timeout + 3*self.connect_timeout + 5 <= self.lease_seconds <= 3600:
            raise ValueError("Lease must exceed the HTTP timeout budget")
        if not 1 <= self.max_attempts <= 10 or not .05 <= self.poll_seconds <= 60:
            raise ValueError("Invalid worker retry/poll settings")

    @classmethod
    def from_env(cls):
        return cls(service_token=SecretStr(os.environ.get("SOCIAL_AI_SERVICE_TOKEN", "")),
            base_url=os.environ.get("SOCIAL_AI_BASE_URL", "http://127.0.0.1:8000"),
            connect_timeout=float(os.environ.get("SOCIAL_AI_CONNECT_TIMEOUT", "3")),
            read_timeout=float(os.environ.get("SOCIAL_AI_READ_TIMEOUT", "60")),
            lease_seconds=int(os.environ.get("SOCIAL_WORKER_LEASE_SECONDS", "180")),
            max_attempts=int(os.environ.get("SOCIAL_WORKER_MAX_ATTEMPTS", "3")),
            poll_seconds=float(os.environ.get("SOCIAL_WORKER_POLL_SECONDS", "2")))


class AIError(Exception):
    def __init__(self, code, retryable, retry_after=0):
        super().__init__(code)
        self.code, self.retryable, self.retry_after = code, retryable, retry_after


class AIClient:
    def __init__(self, settings: WorkerSettings, transport=None):
        self.client = httpx.Client(base_url=settings.base_url.rstrip("/"),
            headers={"Authorization":"Bearer " + settings.service_token.get_secret_value()},
            timeout=httpx.Timeout(settings.read_timeout, connect=settings.connect_timeout,
                                  write=settings.connect_timeout, pool=settings.connect_timeout),
            follow_redirects=False, trust_env=False, transport=transport)

    def close(self):
        self.client.close()

    def moderate(self, payload):
        try:
            with self.client.stream("POST", "/api/v1/moderate/comment", json=payload.model_dump(mode="json")) as response:
                if response.status_code != 200:
                    retry = response.status_code == 429 or response.status_code >= 500
                    hint = response.headers.get("Retry-After", "")
                    retry_after = min(int(hint), 3600) if hint.isdigit() and len(hint) <= 6 else 0
                    raise AIError(f"AI_HTTP_{response.status_code}", retry, retry_after)
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 1048576:
                        raise AIError("AI_RESPONSE_TOO_LARGE", True)
                try:
                    result = ModerationResponse.model_validate_json(bytes(body))
                except (ValidationError, ValueError):
                    raise AIError("AI_INVALID_SCHEMA", True) from None
        except httpx.TimeoutException:
            raise AIError("AI_TIMEOUT", True) from None
        except httpx.HTTPError:
            raise AIError("AI_NETWORK_ERROR", True) from None
        if (result.request_id, result.content_id, result.content_revision) != (payload.request_id, payload.content_id, payload.content_revision):
            raise AIError("AI_CORRELATION_MISMATCH", True)
        # Evidence must concern this author/current comment and real supplied context.
        lookup = {row.comment_id: row for row in payload.context.recent_comments}
        lookup[payload.content_id] = payload
        for evidence in result.evidence:
            ids = evidence.evidence_comment_ids
            if evidence.actor_user_id != payload.user_id or payload.content_id not in ids or len(set(ids)) != len(ids) or any(key not in lookup for key in ids):
                raise AIError("AI_INVALID_EVIDENCE", True)
            timestamps = {lookup[key].timestamp for key in ids}
            if len(timestamps) < 2 or len(timestamps) != evidence.n_distinct_timestamps or any(lookup[key].user_id != payload.user_id for key in ids):
                raise AIError("AI_INVALID_EVIDENCE", True)
            for key in ids:
                row = lookup[key]
                explicit = [user for user in row.mentioned_user_ids if user != row.user_id]
                parent = lookup.get(row.parent_id)
                target = explicit[0] if len(set(explicit)) == 1 else parent.user_id if parent else None
                if target != evidence.target_user_id or target == row.user_id:
                    raise AIError("AI_INVALID_EVIDENCE", True)
        return result
