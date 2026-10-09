"""Job and certificate processing services.

This module contains the core business logic for:
1. Creating generation jobs
2. Processing bulk certificate generation (background)
3. Retrieving job status

Key design: background processing runs in a separate thread so that
the POST /jobs endpoint returns immediately with a job ID.
"""

import logging
import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.certificate import Certificate, CertificateStatus
from app.models.generation_job import GenerationJob, JobStatus
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.job_repository import JobRepository
from app.schemas.job import CreateJobRequest, JobCreatedResponse, JobStatusResponse
from app.schemas.certificate import CertificateStatusResponse
from app.services.pdf_service import generate_pdf_for_recipient

logger = logging.getLogger(__name__)


def create_job(request: CreateJobRequest, db: Session) -> JobCreatedResponse:
    """Create a new generation job and its certificate records.

    This function:
    1. Creates the GenerationJob record
    2. Creates one Certificate record per recipient (all PENDING)
    3. Returns immediately without generating any PDFs

    PDF generation is handled separately by process_job_background().

    Args:
        request: Validated job creation request.
        db: Database session.

    Returns:
        JobCreatedResponse with job_id and initial state.
    """
    job_repo = JobRepository(db)
    cert_repo = CertificateRepository(db)

    # Create the parent job record
    job = GenerationJob(
        certificate_title=request.certificate_title,
        event_name=request.event_name,
        organization_name=request.organization_name,
        issue_date=str(request.issue_date),
        total_recipients=len(request.recipients),
        status=JobStatus.PENDING,
    )
    job = job_repo.create(job)

    # Create one Certificate record per recipient (bulk insert)
    certificates = [
        Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            status=CertificateStatus.PENDING,
        )
        for recipient in request.recipients
    ]
    cert_repo.create_bulk(certificates)

    logger.info(
        f"Job created | job_id={job.id} "
        f"recipients={len(request.recipients)} "
        f"title={request.certificate_title!r}"
    )

    return JobCreatedResponse(
        job_id=job.id,
        status=job.status.value,
        total=job.total_recipients,
        completed=0,
        failed=0,
        message=f"Job accepted. Processing {len(request.recipients)} certificates in the background.",
    )


def process_job_background(job_id: uuid.UUID) -> None:
    """Process all certificates for a job in the background.

    This function runs in a separate thread (via FastAPI BackgroundTasks).
    It creates its own database session because the request-scoped session
    is closed by the time background processing runs.

    Failure isolation: each certificate is processed independently.
    If one certificate fails, the error is recorded and processing
    CONTINUES for all remaining recipients.

    Args:
        job_id: UUID of the job to process.
    """
    # Create a new session for background thread
    db = SessionLocal()
    try:
        _process_job(job_id, db)
    except Exception as e:
        logger.exception(f"Critical error in background job | job_id={job_id} error={e}")
        # Mark job as FAILED if we couldn't even start processing
        try:
            job_repo = JobRepository(db)
            job_repo.update_status(job_id, JobStatus.FAILED)
        except Exception:
            pass
    finally:
        db.close()


def _process_job(job_id: uuid.UUID, db: Session) -> None:
    """Internal function that performs the actual bulk processing.

    Args:
        job_id: UUID of the job to process.
        db: Database session.
    """
    job_repo = JobRepository(db)
    cert_repo = CertificateRepository(db)

    # Mark the job as PROCESSING
    job = job_repo.mark_started(job_id)
    if not job:
        logger.error(f"Job not found during background processing | job_id={job_id}")
        return

    logger.info(
        f"Starting bulk processing | job_id={job_id} "
        f"total_recipients={job.total_recipients}"
    )

    # Fetch all pending certificates for this job
    certificates = cert_repo.get_by_job_id(job_id)

    # Process each certificate individually with failure isolation
    for cert in certificates:
        _process_single_certificate(
            certificate=cert,
            job=job,
            cert_repo=cert_repo,
            job_repo=job_repo,
        )

    # Mark the job as completed with the appropriate final status
    job_repo.mark_completed(job_id)
    logger.info(f"Bulk processing completed | job_id={job_id}")


def _process_single_certificate(
    certificate: Certificate,
    job: GenerationJob,
    cert_repo: CertificateRepository,
    job_repo: JobRepository,
) -> None:
    """Process one certificate with full failure isolation.

    Any exception during PDF generation is caught here.
    The certificate is marked FAILED and the error is stored.
    The job continues processing remaining certificates.

    Args:
        certificate: The Certificate record to process.
        job: The parent GenerationJob.
        cert_repo: Certificate repository instance.
        job_repo: Job repository instance.
    """
    cert_repo.mark_processing(certificate.id)

    try:
        # Generate the PDF
        file_path = generate_pdf_for_recipient(
            certificate_id=certificate.id,
            recipient_name=certificate.recipient_name,
            certificate_title=job.certificate_title,
            event_name=job.event_name,
            organization_name=job.organization_name,
            issue_date=job.issue_date,
        )

        # Mark as success
        cert_repo.mark_completed(certificate.id, file_path)
        job_repo.increment_success(job.id)

    except Exception as e:
        # *** FAILURE ISOLATION: one failure does NOT stop other certificates ***
        error_msg = str(e)
        logger.error(
            f"Certificate generation failed | "
            f"certificate_id={certificate.id} "
            f"recipient={certificate.recipient_name!r} "
            f"error={error_msg!r}"
        )
        cert_repo.mark_failed(certificate.id, error_msg)
        job_repo.increment_failure(job.id)
        # Processing CONTINUES for remaining certificates


def get_job_status(job_id: uuid.UUID, db: Session) -> Optional[JobStatusResponse]:
    """Retrieve the full status of a generation job.

    Args:
        job_id: UUID of the job to retrieve.
        db: Database session.

    Returns:
        JobStatusResponse with all certificate details, or None if not found.
    """
    job_repo = JobRepository(db)
    cert_repo = CertificateRepository(db)

    job = job_repo.get_by_id(job_id)
    if not job:
        return None

    certificates = cert_repo.get_by_job_id(job_id)

    cert_responses = [
        CertificateStatusResponse(
            certificate_id=cert.id,
            recipient_name=cert.recipient_name,
            recipient_email=cert.recipient_email,
            status=cert.status.value,
            download_url=(
                f"/api/v1/certificates/{cert.id}"
                if cert.status == CertificateStatus.COMPLETED
                else None
            ),
            error=cert.error_message if cert.status == CertificateStatus.FAILED else None,
            created_at=cert.created_at.isoformat(),
            completed_at=cert.completed_at.isoformat() if cert.completed_at else None,
        )
        for cert in certificates
    ]

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        total=job.total_recipients,
        completed=job.successful_count,
        failed=job.failed_count,
        progress_percentage=job.progress_percentage,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        certificates=cert_responses,
    )
