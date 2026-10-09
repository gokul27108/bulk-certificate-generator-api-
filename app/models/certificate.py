"""SQLAlchemy model for individual certificates.

Each Certificate belongs to a GenerationJob and tracks
the status of generating one recipient's certificate PDF.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class CertificateStatus(str, enum.Enum):
    """Possible statuses for an individual certificate.

    Lifecycle:
        PENDING -> PROCESSING -> COMPLETED
                              -> FAILED
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Certificate(Base):
    """Represents one generated certificate for one recipient.

    Tracks status, file path, and any error that occurred during generation.
    Failed certificates do not stop other certificates from being processed.
    """
    __tablename__ = "certificates"

    # Composite index on job_id + status for efficient progress queries
    __table_args__ = (
        Index("ix_certificates_job_id_status", "job_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for this certificate"
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the parent generation job"
    )
    recipient_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the certificate recipient"
    )
    recipient_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Email of the certificate recipient"
    )
    status: Mapped[CertificateStatus] = mapped_column(
        SAEnum(CertificateStatus, name="certificate_status"),
        default=CertificateStatus.PENDING,
        nullable=False,
        doc="Current status of this certificate"
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Filesystem path to the generated PDF file"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error description if generation failed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="When this certificate record was created"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When generation completed (success or failure)"
    )

    # Many-to-one: many certificates belong to one job
    job: Mapped["GenerationJob"] = relationship(
        "GenerationJob",
        back_populates="certificates"
    )

    def __repr__(self) -> str:
        return f"<Certificate id={self.id} recipient={self.recipient_name} status={self.status}>"
