"""Reports, appeals, reviewer leases and structured audit metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0004_review"
down_revision = "0003_worker"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content_audit", sa.Column("details_json", sa.Text(), nullable=True))
    op.create_table("content_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(8), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.UniqueConstraint("entity_type", "entity_id", "content_revision", "reporter_id", name="uq_reports_reporter_revision"),
        sa.CheckConstraint("entity_type IN ('post','comment')", name="ck_reports_entity"),
        sa.CheckConstraint("status IN ('OPEN','CLOSED')", name="ck_reports_status"))
    op.create_index("ix_reports_content", "content_reports", ["entity_type", "entity_id", "content_revision", "status"])
    op.create_table("appeals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(8), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("appealed_decision_version", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("outcome", sa.String(24)), sa.Column("resolution_reason", sa.String(500)),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id")), sa.Column("resolved_at", sa.Integer()),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.UniqueConstraint("entity_type", "entity_id", "content_revision", "appealed_decision_version", name="uq_appeals_decision"),
        sa.CheckConstraint("entity_type IN ('post','comment')", name="ck_appeals_entity"),
        sa.CheckConstraint("status IN ('OPEN','RESOLVED','CLOSED')", name="ck_appeals_status"))
    op.create_index("ix_appeals_content", "appeals", ["entity_type", "entity_id", "content_revision", "status"])
    op.create_table("review_claims",
        sa.Column("entity_type", sa.String(8), primary_key=True),
        sa.Column("entity_id", sa.String(36), primary_key=True),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("previous_review", sa.String(16), nullable=False), sa.Column("lease_until", sa.Integer(), nullable=False))


def downgrade():
    if not op.get_context().as_sql:
        connection = op.get_bind()
        if any(connection.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
               for table in ("appeals", "content_reports", "review_claims")) or connection.execute(
                   sa.text("SELECT COUNT(*) FROM content_audit WHERE details_json IS NOT NULL")).scalar_one():
            raise RuntimeError("Review history exists; retain this schema or restore a verified backup")
    op.drop_table("review_claims")
    op.drop_table("appeals")
    op.drop_table("content_reports")
    with op.batch_alter_table("content_audit") as batch:
        batch.drop_column("details_json")
