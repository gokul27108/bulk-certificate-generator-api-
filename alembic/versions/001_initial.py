"""Initial migration - create generation_jobs and certificates tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-10-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create job_status enum type
    job_status = postgresql.ENUM(
        "PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED",
        name="job_status"
    )
    job_status.create(op.get_bind(), checkfirst=True)

    # Create certificate_status enum type
    cert_status = postgresql.ENUM(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED",
        name="certificate_status"
    )
    cert_status.create(op.get_bind(), checkfirst=True)

    # Create generation_jobs table
    op.create_table(
        "generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", name="job_status"), nullable=False),
        sa.Column("certificate_title", sa.String(255), nullable=False),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("organization_name", sa.String(255), nullable=False),
        sa.Column("issue_date", sa.String(20), nullable=False),
        sa.Column("total_recipients", sa.Integer(), nullable=False, default=0),
        sa.Column("successful_count", sa.Integer(), nullable=False, default=0),
        sa.Column("failed_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"])

    # Create certificates table
    op.create_table(
        "certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="certificate_status"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_certificates_job_id", "certificates", ["job_id"])
    op.create_index("ix_certificates_job_id_status", "certificates", ["job_id", "status"])


def downgrade() -> None:
    op.drop_table("certificates")
    op.drop_table("generation_jobs")

    op.execute("DROP TYPE IF EXISTS certificate_status")
    op.execute("DROP TYPE IF EXISTS job_status")
