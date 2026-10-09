"""Repository for GenerationJob database operations.

Encapsulates all database queries related to generation jobs.
Uses SQLAlchemy sessions passed in from the service layer.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.generation_job import GenerationJob, JobStatus

logger = logging.getLogger(__name__)


class JobRepository:
    """Handles all database operations for GenerationJob records."""

    def __init__(self, db: Session):
        """Initialize with a database session.

        Args:
            db: Active SQLAlchemy session.
        """
        self.db = db

    def create(self, job: GenerationJob) -> GenerationJob:
        """Persist a new GenerationJob to the database.

        Args:
            job: The GenerationJob instance to save.

        Returns:
            The saved GenerationJob with ID populated.
        """
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logger.info(f"Job created | job_id={job.id} total_recipients={job.total_recipients}")
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Optional[GenerationJob]:
        """Fetch a job by its UUID.

        Args:
            job_id: UUID of the job to retrieve.

        Returns:
            GenerationJob if found, None otherwise.
        """
        return self.db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    def update_status(self, job_id: uuid.UUID, status: JobStatus) -> Optional[GenerationJob]:
        """Update the status of a job.

        Args:
            job_id: UUID of the job to update.
            status: New status to set.

        Returns:
            Updated GenerationJob, or None if not found.
        """
        job = self.get_by_id(job_id)
        if job:
            job.status = status
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)
        return job

    def mark_started(self, job_id: uuid.UUID) -> Optional[GenerationJob]:
        """Mark a job as PROCESSING with a started_at timestamp.

        Args:
            job_id: UUID of the job to update.

        Returns:
            Updated GenerationJob.
        """
        job = self.get_by_id(job_id)
        if job:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Job started | job_id={job_id}")
        return job

    def increment_success(self, job_id: uuid.UUID) -> None:
        """Atomically increment the successful_count for a job.

        Args:
            job_id: UUID of the job to update.
        """
        job = self.get_by_id(job_id)
        if job:
            job.successful_count += 1
            self.db.commit()

    def increment_failure(self, job_id: uuid.UUID) -> None:
        """Atomically increment the failed_count for a job.

        Args:
            job_id: UUID of the job to update.
        """
        job = self.get_by_id(job_id)
        if job:
            job.failed_count += 1
            self.db.commit()

    def mark_completed(self, job_id: uuid.UUID) -> Optional[GenerationJob]:
        """Mark a job as completed with the appropriate final status.

        Final status logic:
        - All succeeded -> COMPLETED
        - Some failed, some succeeded -> COMPLETED_WITH_ERRORS
        - All failed -> FAILED

        Args:
            job_id: UUID of the job to complete.

        Returns:
            Updated GenerationJob.
        """
        job = self.get_by_id(job_id)
        if job:
            job.completed_at = datetime.now(timezone.utc)

            if job.failed_count == 0:
                job.status = JobStatus.COMPLETED
            elif job.successful_count == 0:
                job.status = JobStatus.FAILED
            else:
                job.status = JobStatus.COMPLETED_WITH_ERRORS

            self.db.commit()
            self.db.refresh(job)
            logger.info(
                f"Job completed | job_id={job_id} status={job.status} "
                f"successful={job.successful_count} failed={job.failed_count}"
            )
        return job
