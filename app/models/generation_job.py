"""SQLAlchemy model for generation jobs.

A GenerationJob represents a bulk certificate generation request.
It tracks the overall status and progress of processing multiple recipients.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Possible statuses for a generation job.

    Lifecycle:
        PENDING -> PROCESSING -> COMPLETED
                              -> COMPLETED_WITH_ERRORS  (some certificates failed)
                              -> FAILED                 (all certificates failed or critical error)
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class GenerationJob(Base):
    """Represents a bulk certificate generation job.

    Each job contains metadata about the certificate (title, event, etc.)
    and tracks progress across all recipients.
    """
    __tablename__ = "generation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for this job"
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current processing status of the job"
    )
    certificate_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Title printed on the certificate"
    )
    event_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the event or course"
    )
    organization_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Organization issuing the certificate"
    )
    issue_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Date printed on the certificate (YYYY-MM-DD format)"
    )
    total_recipients: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of recipients in this job"
    )
    successful_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of successfully generated certificates"
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of failed certificate generations"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="When the job was created"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When background processing started"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When processing finished"
    )

    # One-to-many relationship: one job has many certificates
    certificates: Mapped[list["Certificate"]] = relationship(
        "Certificate",
        back_populates="job",
        lazy="select",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GenerationJob id={self.id} status={self.status} total={self.total_recipients}>"

    @property
    def progress_percentage(self) -> int:
        """Calculate completion percentage, safely avoiding division by zero."""
        if self.total_recipients == 0:
            return 0
        processed = self.successful_count + self.failed_count
        return int((processed / self.total_recipients) * 100)
