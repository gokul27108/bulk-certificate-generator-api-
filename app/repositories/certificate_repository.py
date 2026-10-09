"""Repository for Certificate database operations.

Encapsulates all database queries related to individual certificates.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.certificate import Certificate, CertificateStatus

logger = logging.getLogger(__name__)


class CertificateRepository:
    """Handles all database operations for Certificate records."""

    def __init__(self, db: Session):
        """Initialize with a database session.

        Args:
            db: Active SQLAlchemy session.
        """
        self.db = db

    def create_bulk(self, certificates: list[Certificate]) -> list[Certificate]:
        """Persist multiple Certificate records in a single transaction.

        Using bulk insert is more efficient than inserting one at a time,
        especially for large recipient lists.

        Args:
            certificates: List of Certificate instances to save.

        Returns:
            List of saved certificates.
        """
        self.db.add_all(certificates)
        self.db.commit()
        for cert in certificates:
            self.db.refresh(cert)
        logger.info(f"Created {len(certificates)} certificate records")
        return certificates

    def get_by_id(self, certificate_id: uuid.UUID) -> Optional[Certificate]:
        """Fetch a certificate by its UUID.

        Args:
            certificate_id: UUID of the certificate.

        Returns:
            Certificate if found, None otherwise.
        """
        return (
            self.db.query(Certificate)
            .filter(Certificate.id == certificate_id)
            .first()
        )

    def get_by_job_id(self, job_id: uuid.UUID) -> list[Certificate]:
        """Fetch all certificates for a specific job.

        Args:
            job_id: UUID of the parent job.

        Returns:
            List of certificates for this job.
        """
        return (
            self.db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.created_at)
            .all()
        )

    def mark_processing(self, certificate_id: uuid.UUID) -> Optional[Certificate]:
        """Mark a certificate as PROCESSING.

        Args:
            certificate_id: UUID of the certificate.

        Returns:
            Updated Certificate.
        """
        cert = self.get_by_id(certificate_id)
        if cert:
            cert.status = CertificateStatus.PROCESSING
            self.db.commit()
            self.db.refresh(cert)
        return cert

    def mark_completed(
        self, certificate_id: uuid.UUID, file_path: str
    ) -> Optional[Certificate]:
        """Mark a certificate as COMPLETED with its file path.

        Args:
            certificate_id: UUID of the certificate.
            file_path: Filesystem path to the generated PDF.

        Returns:
            Updated Certificate.
        """
        cert = self.get_by_id(certificate_id)
        if cert:
            cert.status = CertificateStatus.COMPLETED
            cert.file_path = file_path
            cert.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(cert)
            logger.info(
                f"Certificate completed | certificate_id={certificate_id} "
                f"recipient={cert.recipient_name!r}"
            )
        return cert

    def mark_failed(
        self, certificate_id: uuid.UUID, error_message: str
    ) -> Optional[Certificate]:
        """Mark a certificate as FAILED with an error message.

        Args:
            certificate_id: UUID of the certificate.
            error_message: Description of what went wrong.

        Returns:
            Updated Certificate.
        """
        cert = self.get_by_id(certificate_id)
        if cert:
            cert.status = CertificateStatus.FAILED
            cert.error_message = error_message
            cert.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(cert)
            logger.error(
                f"Certificate failed | certificate_id={certificate_id} "
                f"recipient={cert.recipient_name!r} error={error_message!r}"
            )
        return cert
