"""Pydantic schemas for certificate API responses."""

from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class CertificateStatusResponse(BaseModel):
    """Status of an individual certificate within a job."""

    certificate_id: UUID = Field(..., description="Unique certificate identifier")
    recipient_name: str = Field(..., description="Name of the recipient")
    recipient_email: str = Field(..., description="Email of the recipient")
    status: str = Field(..., description="Certificate status: PENDING, PROCESSING, COMPLETED, FAILED")
    download_url: Optional[str] = Field(
        None,
        description="URL to download the PDF (only present when status is COMPLETED)"
    )
    error: Optional[str] = Field(
        None,
        description="Error message (only present when status is FAILED)"
    )
    created_at: str = Field(..., description="When this certificate was created")
    completed_at: Optional[str] = Field(None, description="When generation completed")


class CertificateDetailResponse(BaseModel):
    """Detailed response for a single certificate."""

    certificate_id: UUID
    job_id: UUID
    recipient_name: str
    recipient_email: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
