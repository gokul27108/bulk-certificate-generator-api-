"""Centralized exception handlers for the FastAPI application.

Converts internal exceptions into clean, consistent JSON responses.
Never exposes stack traces or internal implementation details to clients.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class JobNotFoundException(Exception):
    """Raised when a generation job is not found in the database."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Generation job not found: {job_id}")


class CertificateNotFoundException(Exception):
    """Raised when a certificate is not found in the database."""
    def __init__(self, certificate_id: str):
        self.certificate_id = certificate_id
        super().__init__(f"Certificate not found: {certificate_id}")


class CertificateNotReadyException(Exception):
    """Raised when a certificate exists but its PDF is not available."""
    def __init__(self, certificate_id: str, status: str):
        self.certificate_id = certificate_id
        self.cert_status = status
        super().__init__(f"Certificate {certificate_id} is not available (status: {status})")


async def job_not_found_handler(request: Request, exc: JobNotFoundException) -> JSONResponse:
    """Handle job not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Generation job not found: {exc.job_id}"},
    )


async def certificate_not_found_handler(
    request: Request, exc: CertificateNotFoundException
) -> JSONResponse:
    """Handle certificate not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Certificate not found: {exc.certificate_id}"},
    )


async def certificate_not_ready_handler(
    request: Request, exc: CertificateNotReadyException
) -> JSONResponse:
    """Handle requests for certificates that aren't ready for download."""
    status_map = {
        "PENDING": "Certificate generation has not started yet.",
        "PROCESSING": "Certificate is currently being generated. Please try again shortly.",
        "FAILED": "Certificate generation failed. No PDF is available.",
    }
    detail = status_map.get(exc.cert_status, f"Certificate is not available (status: {exc.cert_status})")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail, "status": exc.cert_status},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with clean error messages."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(f"Validation error | path={request.url.path} errors={errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": errors},
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors without exposing internals."""
    logger.exception(f"Database error | path={request.url.path} error={exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again."},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    logger.exception(f"Unexpected error | path={request.url.path} error={exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )
