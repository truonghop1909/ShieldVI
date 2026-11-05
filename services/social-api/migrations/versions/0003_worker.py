"""Durable worker ownership, request snapshots and advisory results."""
from alembic import op
import sqlalchemy as sa

revision = "0003_worker"
down_revision = "0002_content"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("moderation_jobs") as batch:
        batch.add_column(sa.Column("claim_token", sa.String(36), nullable=True))
        batch.add_column(sa.Column("lease_until", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("total_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("request_json", sa.Text(), nullable=True))
        batch.add_column(sa.Column("request_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("last_error", sa.String(64), nullable=True))
        batch.add_column(sa.Column("last_ai_check_at", sa.Integer(), nullable=True))
    with op.batch_alter_table("content_audit") as batch:
        batch.alter_column("actor_id", existing_type=sa.String(36), nullable=True)
        batch.add_column(sa.Column("actor_type", sa.String(16), nullable=False, server_default="user"))
        batch.add_column(sa.Column("actor_identifier", sa.String(120), nullable=True))
    op.create_table("moderation_results",
        sa.Column("job_id", sa.String(36), sa.ForeignKey("moderation_jobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(200), nullable=False),
        sa.Column("lexicon_version", sa.String(100), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("ai_label", sa.String(8), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("risk_tier", sa.String(8), nullable=False),
        sa.Column("signals_json", sa.Text(), nullable=False),
        sa.Column("analyzed_at", sa.String(64), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )


def downgrade():
    # Preserve system audit rows: 0002 cannot represent a nullable actor.
    # Refuse destructive audit conversion; downgrade only safe when no system rows exist.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM content_audit WHERE actor_id IS NULL")).scalar_one():
        raise RuntimeError("System audit exists; restore a verified pre-worker backup instead of downgrading")
    op.drop_table("moderation_results")
    with op.batch_alter_table("content_audit") as batch:
        batch.drop_column("actor_identifier")
        batch.drop_column("actor_type")
        batch.alter_column("actor_id", existing_type=sa.String(36), nullable=False)
    with op.batch_alter_table("moderation_jobs") as batch:
        for name in ("claim_token", "lease_until", "total_attempts", "retry_count", "request_json", "request_hash", "last_error", "last_ai_check_at"):
            batch.drop_column(name)
