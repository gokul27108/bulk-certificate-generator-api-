"""Jobs API routes.

Handles:
- POST /api/v1/jobs   — Create a bulk certificate generation job
- GET  /api/v1/jobs/{job_id} — Get job status and progress
"""

import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.exceptions.handlers import JobNotFoundException
from app.schemas.job import CreateJobRequest, JobCreatedResponse, JobStatusResponse
from app.services.job_service import create_job, get_job_status, process_job_background

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/jobs",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Bulk Certificate Generation Job",
    description=(
        "Submit a bulk certificate generation request for multiple recipients. "
        "The job is accepted immediately and processing happens in the background. "
        "Use the returned `job_id` to track progress via GET /api/v1/jobs/{job_id}."
    ),
    responses={
        202: {"description": "Job accepted and queued for processing"},
        422: {"description": "Validation error — check your request body"},
    },
    tags=["Jobs"],
)
async def create_generation_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreatedResponse:
    """Create a new bulk certificate generation job.

    **HTTP 202 Accepted** is used because:
    - The certificates are generated asynchronously in the background
    - The response is returned before all PDFs are ready
    - Clients should poll GET /jobs/{job_id} to check progress

    **Failure isolation**: if individual certificates fail, the job continues
    processing remaining recipients. Check `failed` count in job status.

    Args:
        request: Validated job creation payload.
        background_tasks: FastAPI background task manager.
        db: Database session (injected).

    Returns:
        Job ID and initial status (HTTP 202).
    """
    response = create_job(request, db)

    # Queue background processing AFTER returning the response
    # This ensures the client gets the job_id immediately
    background_tasks.add_task(process_job_background, response.job_id)

    logger.info(
        f"Job queued for background processing | "
        f"job_id={response.job_id} "
        f"recipients={response.total}"
    )

    return response


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status",
    description=(
        "Retrieve the current status and progress of a generation job, "
        "including the status of each individual certificate."
    ),
    responses={
        200: {"description": "Job status retrieved successfully"},
        404: {"description": "Job not found"},
    },
    tags=["Jobs"],
)
async def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    """Get the status and progress of a generation job.

    Poll this endpoint to monitor bulk processing progress.
    The response includes individual certificate statuses.

    Args:
        job_id: UUID of the job to retrieve.
        db: Database session (injected).

    Returns:
        Detailed job status with all certificate statuses.

    Raises:
        JobNotFoundException: If no job with this ID exists.
    """
    result = get_job_status(job_id, db)
    if not result:
        raise JobNotFoundException(str(job_id))
    return result
