"""Certificates API routes.

Handles:
- GET /api/v1/certificates/{certificate_id} — Download a generated certificate PDF
"""

import logging
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.exceptions.handlers import (
    CertificateNotFoundException,
    CertificateNotReadyException,
)
from app.models.certificate import CertificateStatus
from app.services.certificate_service import get_certificate, get_certificate_file_path

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/certificates/{certificate_id}",
    summary="Download Certificate PDF",
    description=(
        "Download the generated PDF certificate for a specific recipient. "
        "The certificate must have status COMPLETED before it can be downloaded. "
        "Returns the PDF file with Content-Type: application/pdf."
    ),
    responses={
        200: {"description": "PDF certificate file", "content": {"application/pdf": {}}},
        404: {"description": "Certificate not found"},
        422: {"description": "Certificate is not yet ready or generation failed"},
    },
    tags=["Certificates"],
)
async def download_certificate(
    certificate_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Download a generated certificate PDF.

    Args:
        certificate_id: UUID of the certificate to download.
        db: Database session (injected).

    Returns:
        FileResponse with the PDF file (Content-Type: application/pdf).

    Raises:
        CertificateNotFoundException: If no certificate with this ID exists.
        CertificateNotReadyException: If certificate is not COMPLETED.
    """
    certificate = get_certificate(certificate_id, db)

    if not certificate:
        raise CertificateNotFoundException(str(certificate_id))

    if certificate.status != CertificateStatus.COMPLETED:
        raise CertificateNotReadyException(str(certificate_id), certificate.status.value)

    file_path = get_certificate_file_path(certificate)
    if not file_path:
        logger.error(
            f"Certificate file missing | "
            f"certificate_id={certificate_id} "
            f"path={certificate.file_path}"
        )
        raise CertificateNotReadyException(str(certificate_id), "FILE_MISSING")

    download_filename = f"certificate_{certificate.recipient_name.replace(' ', '_')}.pdf"

    logger.info(
        f"Certificate downloaded | "
        f"certificate_id={certificate_id} "
        f"recipient={certificate.recipient_name!r}"
    )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=download_filename,
    )
