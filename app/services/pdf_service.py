"""PDF generation service.

Wraps the certificate template to handle file path generation,
error handling, and integration with the application configuration.
"""

import logging
import os
import uuid
from pathlib import Path

from app.core.config import settings
from templates.certificate_template import generate_certificate_pdf

logger = logging.getLogger(__name__)


def generate_pdf_for_recipient(
    certificate_id: uuid.UUID,
    recipient_name: str,
    certificate_title: str,
    event_name: str,
    organization_name: str,
    issue_date: str,
) -> str:
    """Generate a PDF certificate for one recipient.

    Creates the output directory if it doesn't exist, generates a
    unique filename based on the certificate ID (never user input),
    and returns the saved file path.

    Args:
        certificate_id: UUID of the certificate record (used for filename).
        recipient_name: Name to print on the certificate.
        certificate_title: Certificate title text.
        event_name: Event or course name.
        organization_name: Issuing organization name.
        issue_date: Formatted date string.

    Returns:
        Absolute path to the generated PDF file.

    Raises:
        Exception: If PDF generation or file writing fails.
    """
    # Ensure output directory exists
    output_dir = Path(settings.CERTIFICATE_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build safe filename - NEVER use user input in filename
    filename = f"certificate_{certificate_id}.pdf"
    output_path = str(output_dir / filename)

    logger.info(
        f"Generating PDF | certificate_id={certificate_id} "
        f"recipient={recipient_name!r} path={output_path}"
    )

    # Delegate to the template module
    generate_certificate_pdf(
        recipient_name=recipient_name,
        certificate_title=certificate_title,
        event_name=event_name,
        organization_name=organization_name,
        issue_date=issue_date,
        output_path=output_path,
    )

    # Verify the file was actually created
    if not os.path.exists(output_path):
        raise FileNotFoundError(
            f"PDF generation reported success but file not found: {output_path}"
        )

    file_size = os.path.getsize(output_path)
    logger.info(
        f"PDF generated successfully | certificate_id={certificate_id} "
        f"size={file_size} bytes"
    )

    return output_path
