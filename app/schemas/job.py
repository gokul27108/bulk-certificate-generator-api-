"""Pydantic schemas for generation job API requests and responses.

These schemas handle validation of incoming requests and
serialization of outgoing responses.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from uuid import UUID

from app.schemas.certificate import CertificateStatusResponse


class RecipientInput(BaseModel):
    """A single recipient for certificate generation."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the recipient (printed on the certificate)",
        examples=["Gokul M"]
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address of the recipient",
        examples=["gokul@example.com"]
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Recipient name cannot be blank or whitespace only")
        return v


class CreateJobRequest(BaseModel):
    """Request body for creating a bulk certificate generation job."""

    certificate_title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title printed on the certificate",
        examples=["Certificate of Completion"]
    )
    event_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the event or course",
        examples=["Python Backend Development Workshop"]
    )
    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Organization issuing the certificate",
        examples=["Aero"]
    )
    issue_date: date = Field(
        ...,
        description="Date to print on certificate (YYYY-MM-DD)",
        examples=["2026-10-07"]
    )
    recipients: list[RecipientInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of recipients (1 to 1000)"
    )

    @field_validator("certificate_title", "event_name", "organization_name")
    @classmethod
    def strip_and_validate_not_blank(cls, v: str) -> str:
        """Strip whitespace and ensure fields are not blank."""
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be blank or whitespace only")
        return v

    @model_validator(mode="after")
    def validate_unique_emails(self) -> "CreateJobRequest":
        """Warn if duplicate emails exist but do not block the request."""
        emails = [r.email for r in self.recipients]
        # Allow duplicates - each gets their own certificate
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "certificate_title": "Certificate of Completion",
                    "event_name": "Python Backend Development Workshop",
                    "organization_name": "Aero",
                    "issue_date": "2026-10-07",
                    "recipients": [
                        {"name": "Gokul M", "email": "gokul@example.com"},
                        {"name": "Rahul Kumar", "email": "rahul@example.com"}
                    ]
                }
            ]
        }
    }


class JobCreatedResponse(BaseModel):
    """Response returned immediately after job creation (HTTP 202)."""

    job_id: UUID = Field(..., description="Unique identifier for tracking this job")
    status: str = Field(..., description="Initial job status (always PENDING)")
    total: int = Field(..., description="Total number of recipients to process")
    completed: int = Field(..., description="Certificates generated so far")
    failed: int = Field(..., description="Certificates that failed so far")
    message: str = Field(..., description="Human-readable status message")


class JobStatusResponse(BaseModel):
    """Detailed job status with all certificate details."""

    job_id: UUID = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    total: int = Field(..., description="Total number of recipients")
    completed: int = Field(..., description="Successfully generated certificates")
    failed: int = Field(..., description="Failed certificate generations")
    progress_percentage: int = Field(..., description="Percentage of job completed (0-100)")
    created_at: str = Field(..., description="Job creation timestamp")
    started_at: Optional[str] = Field(None, description="When processing started")
    completed_at: Optional[str] = Field(None, description="When processing finished")
    certificates: list[CertificateStatusResponse] = Field(
        ...,
        description="Status of each individual certificate"
    )
