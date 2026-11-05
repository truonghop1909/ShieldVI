"""Posts, comments, durable moderation outbox and content audit (no AI worker)."""
from alembic import op
import sqlalchemy as sa

revision = "0002_content"
down_revision = "0001_users"
branch_labels = None
depends_on = None


def content_columns():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("decision_version", sa.Integer(), nullable=False),
        sa.Column("visibility_status", sa.String(24), nullable=False),
        sa.Column("review_status", sa.String(16), nullable=False),
        sa.Column("risk_tier", sa.String(8), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=True),
        sa.Column("create_key", sa.String(36), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
    ]


def constraints(prefix):
    return [
        sa.CheckConstraint("visibility_status IN ('PENDING_MODERATION','PUBLISHED','PUBLISHED_FLAGGED','HELD_FOR_REVIEW','HIDDEN','DELETED_BY_AUTHOR')", name=f"ck_{prefix}_visibility"),
        sa.CheckConstraint("review_status IN ('NOT_REQUIRED','QUEUED','UNDER_REVIEW','APPROVED','REJECTED','APPEALED','RESOLVED')", name=f"ck_{prefix}_review"),
        sa.CheckConstraint("risk_tier IN ('LOW','REVIEW','HIGH','UNKNOWN')", name=f"ck_{prefix}_risk"),
        sa.CheckConstraint("content_revision >= 1 AND decision_version >= 0", name=f"ck_{prefix}_versions"),
        sa.CheckConstraint("length(body) BETWEEN 1 AND 8000", name=f"ck_{prefix}_body"),
        sa.UniqueConstraint("author_id", "create_key", name=f"uq_{prefix}_create_key"),
    ]


def upgrade():
    op.create_table("posts", *content_columns(), *constraints("posts"))
    op.create_index("ix_posts_feed", "posts", ["visibility_status", "created_at", "id"])
    op.create_table("comments", *content_columns(),
        sa.Column("post_id", sa.String(36), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False),
        *constraints("comments"),
        sa.UniqueConstraint("id", "post_id", name="uq_comments_id_post"),
        sa.ForeignKeyConstraint(["parent_id", "post_id"], ["comments.id", "comments.post_id"], name="fk_comments_parent_same_post"),
        sa.CheckConstraint("parent_id IS NULL OR parent_id != id", name="ck_comments_not_self"),
        sa.CheckConstraint("depth BETWEEN 0 AND 32", name="ck_comments_depth"),
    )
    op.create_index("ix_comments_thread", "comments", ["post_id", "created_at", "id"])
    op.create_index("ix_comments_parent", "comments", ["parent_id"])
    op.create_table("moderation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False, unique=True),
        sa.Column("entity_type", sa.String(8), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("expected_decision_version", sa.Integer(), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.UniqueConstraint("entity_type", "entity_id", "content_revision", name="uq_jobs_revision"),
        sa.CheckConstraint("entity_type IN ('post','comment')", name="ck_jobs_entity"),
        sa.CheckConstraint("status IN ('QUEUED','PROCESSING','SUCCEEDED','RETRY_WAIT','FAILED_PERMANENTLY')", name="ck_jobs_status"),
    )
    op.create_index("ix_jobs_ready", "moderation_jobs", ["status", "next_retry_at"])
    op.create_table("content_audit",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(8), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("decision_version", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_role", sa.String(16), nullable=False),
        sa.Column("event", sa.String(24), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("before_visibility", sa.String(24), nullable=True),
        sa.Column("after_visibility", sa.String(24), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )
    op.create_table("content_rate_buckets",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("window_start", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("content_rate_buckets")
    op.drop_table("content_audit")
    op.drop_table("moderation_jobs")
    op.drop_table("comments")
    op.drop_table("posts")
