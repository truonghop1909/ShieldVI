"""Authenticated, advisory adapter; never reads or writes Social DB."""
import hashlib
import hmac
import os
import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .engine import analyze_thread
from .lexical import DATA_DIR
from .moderation_contract import ModerationRequest, ModerationResponse
from .schemas import AnalyzeRequest

LEXICON_VERSION = hashlib.sha256((DATA_DIR / "active.json").read_bytes()).hexdigest()


class ServiceGuard:
    def __init__(self):
        self.lock = threading.Lock()
        self.window = 0
        self.count = 0
        self.inference = threading.BoundedSemaphore(1)

    def admit(self, limit):
        window = int(time.monotonic()) // 60
        with self.lock:
            if self.window != window:
                self.window, self.count = window, 0
            self.count += 1
            if self.count > limit:
                raise HTTPException(429, "Service request limit exceeded", headers={"Retry-After": "60"})


guard = ServiceGuard()


def service_auth(request: Request):
    expected = os.environ.get("AI_SERVICE_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(503, "Internal moderation authentication is not configured")
    provided = request.headers.get("Authorization", "")
    if not hmac.compare_digest(provided.encode(), ("Bearer " + expected).encode()):
        raise HTTPException(401, "Invalid service credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        limit = int(os.environ.get("AI_SERVICE_RATE_LIMIT", "60"))
        if not 1 <= limit <= 1000:
            raise ValueError
    except ValueError:
        raise HTTPException(503, "Invalid service rate configuration") from None
    guard.admit(limit)


class InternalBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] != "/api/v1/moderate/comment":
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > 1048576:
                return await JSONResponse({"detail": "Payload too large"}, status_code=413)(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return messages.pop(0) if messages else await receive()

        await self.app(scope, replay, send)


def moderate(payload: ModerationRequest, predictor):
    if predictor.threshold != 0.41:
        raise HTTPException(503, "Checkpoint threshold is incompatible with contract 1.0")
    rows = [row.model_dump() for row in payload.context.recent_comments]
    rows.append({"comment_id": payload.content_id, "user_id": payload.user_id, "text": payload.text,
        "timestamp": payload.timestamp, "parent_id": payload.parent_id, "mentioned_user_ids": payload.mentioned_user_ids})
    thread = AnalyzeRequest(thread_id=payload.context.post_id, profile="conservative", comments=rows)

    class RecordingPredictor:
        threshold = predictor.threshold
        name = getattr(predictor, "name", "unknown")

        def predict_scores(self, texts):
            self.scores = predictor.predict_scores(texts)
            return self.scores

    recording = RecordingPredictor()
    result = analyze_thread(thread, recording)
    ordered = sorted(thread.comments, key=lambda row: (row.timestamp, row.comment_id))
    index = next(i for i, row in enumerate(ordered) if row.comment_id == payload.content_id)
    current = result.comments[index]
    evidence = [row.model_dump() for row in result.evidence
                if row.actor_user_id == payload.user_id and payload.content_id in row.evidence_comment_ids]
    limitations = list(result.warnings)
    if not payload.context.recent_comments:
        limitations.append("No thread context; repeated harassment cannot be established from one content item.")
    if not payload.context.complete:
        limitations.append("Context is a bounded or incomplete window; evidence is advisory.")
    return ModerationResponse(schema_version="1.0", request_id=payload.request_id, content_id=payload.content_id,
        content_revision=payload.content_revision, model_name=result.model_name, model_version=recording.name,
        lexicon_version=LEXICON_VERSION, analyzed_at=datetime.now(timezone.utc), model_threshold=0.41,
        toxicity_score=float(recording.scores[index]), ai_label="TOXIC" if current.toxic_for_moderation else "CLEAN",
        lexical_review_recommended=current.lexical_review_recommended,
        directed_insult_candidate=current.directed_insult_candidate, reported_or_apology_context=current.reported_or_apology_context,
        lexical_signals=[row.model_dump() for row in current.lexical_signals],
        target_evidence={"target_user_id": current.target_user_id, "method": current.target_method, "confidence": current.target_confidence},
        suspected_repeated_harassment=bool(evidence), evidence=evidence,
        suggested_action="needs_review" if current.review_recommended or evidence else "approve",
        decision_authority="advisory", limitations=limitations)


def build_router(predictor_dependency):
    router = APIRouter(tags=["internal-moderation"])

    @router.post("/api/v1/moderate/comment", response_model=ModerationResponse, dependencies=[Depends(service_auth)])
    def endpoint(payload: ModerationRequest, predictor=Depends(predictor_dependency)):
        if not guard.inference.acquire(blocking=False):
            raise HTTPException(429, "Inference is busy", headers={"Retry-After": "2"})
        try:
            return moderate(payload, predictor)
        except HTTPException:
            raise
        except Exception:
            # No text/model path/credentials in error responses or logs.
            raise HTTPException(503, "Moderation inference unavailable") from None
        finally:
            guard.inference.release()

    return router
