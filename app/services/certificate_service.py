"""Certificate retrieval service.

Handles retrieving a certificate record and its associated PDF file.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.certificate import Certificate, CertificateStatus
from app.repositories.certificate_repository import CertificateRepository

logger = logging.getLogger(__name__)


def get_certificate(certificate_id: uuid.UUID, db: Session) -> Optional[Certificate]:
    """Retrieve a certificate record by its ID.

    Args:
        certificate_id: UUID of the certificate.
        db: Database session.

    Returns:
        Certificate record if found, None otherwise.
    """
    cert_repo = CertificateRepository(db)
    return cert_repo.get_by_id(certificate_id)


def get_certificate_file_path(certificate: Certificate) -> Optional[str]:
    """Get the file path for a completed certificate.

    Args:
        certificate: The Certificate record.

    Returns:
        File path string if the certificate is completed and file exists,
        None otherwise.
    """
    if certificate.status != CertificateStatus.COMPLETED:
        return None

    if not certificate.file_path:
        return None

    file_path = Path(certificate.file_path)
    if not file_path.exists():
        logger.warning(
            f"Certificate file missing | "
            f"certificate_id={certificate.id} "
            f"path={certificate.file_path}"
        )
        return None

    return str(file_path)
