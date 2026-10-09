"""FastAPI application entry point.

This is the main application module that:
- Creates the FastAPI app instance
- Registers all routers
- Registers exception handlers
- Sets up logging
- Configures OpenAPI documentation
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.exceptions.handlers import (
    CertificateNotFoundException,
    CertificateNotReadyException,
    JobNotFoundException,
    certificate_not_found_handler,
    certificate_not_ready_handler,
    generic_exception_handler,
    job_not_found_handler,
    sqlalchemy_error_handler,
    validation_exception_handler,
)
from app.api.routes import health, jobs, certificates

# Configure logging before anything else
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: runs startup and shutdown logic."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Certificate output dir: {settings.CERTIFICATE_OUTPUT_DIR}")
    yield
    # Shutdown
    logger.info("Application shutting down")


# ── Create FastAPI app ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A production-quality bulk certificate generation API. "
        "Submit a list of recipients, and the system generates personalized "
        "PDF certificates in the background with full failure isolation. "
        "One failed certificate never stops other recipients from receiving theirs.\n\n"
        "## Quick Start\n"
        "1. `POST /api/v1/jobs` — Submit recipients and get a `job_id`\n"
        "2. `GET /api/v1/jobs/{job_id}` — Poll until status is COMPLETED\n"
        "3. `GET /api/v1/certificates/{certificate_id}` — Download each PDF\n"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Register exception handlers ────────────────────────────────────────────────
app.add_exception_handler(JobNotFoundException, job_not_found_handler)
app.add_exception_handler(CertificateNotFoundException, certificate_not_found_handler)
app.add_exception_handler(CertificateNotReadyException, certificate_not_ready_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Register routers ───────────────────────────────────────────────────────────
app.include_router(health.router)                          # GET /health
app.include_router(jobs.router, prefix="/api/v1")          # POST /api/v1/jobs, GET /api/v1/jobs/{id}
app.include_router(certificates.router, prefix="/api/v1")  # GET /api/v1/certificates/{id}


@app.get("/", include_in_schema=False)
async def root():
    """Redirect hint for the API root."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
