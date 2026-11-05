import time
import uuid

from sqlalchemy import CheckConstraint, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'moderator', 'admin')", name="ck_users_role"),
        CheckConstraint("status IN ('active', 'suspended')", name="ck_users_status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_sessions_expiry"),
        Index("ix_auth_sessions_user_id", "user_id"),
        Index("ix_auth_sessions_expires_at", "expires_at"),
    )
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)


class AuthRateBucket(Base):
    __tablename__ = "auth_rate_buckets"
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)


PUBLIC_VISIBILITY = ("PUBLISHED", "PUBLISHED_FLAGGED")
VISIBILITY_SQL = "'PENDING_MODERATION','PUBLISHED','PUBLISHED_FLAGGED','HELD_FOR_REVIEW','HIDDEN','DELETED_BY_AUTHOR'"
REVIEW_SQL = "'NOT_REQUIRED','QUEUED','UNDER_REVIEW','APPROVED','REJECTED','APPEALED','RESOLVED'"


class ContentFields:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    decision_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visibility_status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING_MODERATION")
    review_status: Mapped[str] = mapped_column(String(16), nullable=False, default="QUEUED")
    risk_tier: Mapped[str] = mapped_column(String(8), nullable=False, default="UNKNOWN")
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    create_key: Mapped[str] = mapped_column(String(36), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))


def content_constraints(prefix):
    return (
        CheckConstraint(f"visibility_status IN ({VISIBILITY_SQL})", name=f"ck_{prefix}_visibility"),
        CheckConstraint(f"review_status IN ({REVIEW_SQL})", name=f"ck_{prefix}_review"),
        CheckConstraint("risk_tier IN ('LOW','REVIEW','HIGH','UNKNOWN')", name=f"ck_{prefix}_risk"),
        CheckConstraint("content_revision >= 1 AND decision_version >= 0", name=f"ck_{prefix}_versions"),
        CheckConstraint("length(body) BETWEEN 1 AND 8000", name=f"ck_{prefix}_body"),
        UniqueConstraint("author_id", "create_key", name=f"uq_{prefix}_create_key"),
    )


class Post(ContentFields, Base):
    __tablename__ = "posts"
    __table_args__ = (*content_constraints("posts"), Index("ix_posts_feed", "visibility_status", "created_at", "id"))


class Comment(ContentFields, Base):
    __tablename__ = "comments"
    __table_args__ = (*content_constraints("comments"),
        UniqueConstraint("id", "post_id", name="uq_comments_id_post"),
        ForeignKeyConstraint(["parent_id", "post_id"], ["comments.id", "comments.post_id"], name="fk_comments_parent_same_post"),
        CheckConstraint("parent_id IS NULL OR parent_id != id", name="ck_comments_not_self"),
        CheckConstraint("depth BETWEEN 0 AND 32", name="ck_comments_depth"),
        Index("ix_comments_thread", "post_id", "created_at", "id"),
        Index("ix_comments_parent", "parent_id"),
    )
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ModerationJob(Base):
    __tablename__ = "moderation_jobs"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "content_revision", name="uq_jobs_revision"),
        CheckConstraint("entity_type IN ('post','comment')", name="ck_jobs_entity"),
        CheckConstraint("status IN ('QUEUED','PROCESSING','SUCCEEDED','RETRY_WAIT','FAILED_PERMANENTLY')", name="ck_jobs_status"),
        Index("ix_jobs_ready", "status", "next_retry_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(8), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_decision_version: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="QUEUED")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    claim_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    lease_until: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    request_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_ai_check_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))


class ContentAudit(Base):
    __tablename__ = "content_audit"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(8), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    decision_version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False, default="user", server_default="user")
    actor_identifier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(16), nullable=False)
    event: Mapped[str] = mapped_column(String(24), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    before_visibility: Mapped[str | None] = mapped_column(String(24), nullable=True)
    after_visibility: Mapped[str] = mapped_column(String(24), nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))


class ContentRateBucket(Base):
    __tablename__ = "content_rate_buckets"
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)


class ModerationResult(Base):
    __tablename__ = "moderation_results"
    job_id: Mapped[str] = mapped_column(ForeignKey("moderation_jobs.id", ondelete="CASCADE"), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version: Mapped[str] = mapped_column(String(200), nullable=False)
    lexicon_version: Mapped[str] = mapped_column(String(100), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    ai_label: Mapped[str] = mapped_column(String(8), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(8), nullable=False)
    signals_json: Mapped[str] = mapped_column(Text, nullable=False)
    analyzed_at: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)


class ContentReport(Base):
    __tablename__ = "content_reports"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "content_revision", "reporter_id", name="uq_reports_reporter_revision"),
        CheckConstraint("entity_type IN ('post','comment')", name="ck_reports_entity"),
        CheckConstraint("status IN ('OPEN','CLOSED')", name="ck_reports_status"),
        Index("ix_reports_content", "entity_type", "entity_id", "content_revision", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(8), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, default="OPEN")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))


class Appeal(Base):
    __tablename__ = "appeals"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "content_revision", "appealed_decision_version", name="uq_appeals_decision"),
        CheckConstraint("entity_type IN ('post','comment')", name="ck_appeals_entity"),
        CheckConstraint("status IN ('OPEN','RESOLVED','CLOSED')", name="ck_appeals_status"),
        Index("ix_appeals_content", "entity_type", "entity_id", "content_revision", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(8), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    appealed_decision_version: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, default="OPEN")
    outcome: Mapped[str | None] = mapped_column(String(24), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=lambda: int(time.time()))


class ReviewClaim(Base):
    __tablename__ = "review_claims"
    entity_type: Mapped[str] = mapped_column(String(8), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    previous_review: Mapped[str] = mapped_column(String(16), nullable=False)
    lease_until: Mapped[int] = mapped_column(Integer, nullable=False)
