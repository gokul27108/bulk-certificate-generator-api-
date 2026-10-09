"""Pytest configuration and shared fixtures.

Provides:
- Test database setup (isolated from production)
- FastAPI TestClient
- Helper functions for creating test jobs
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# ── Test database setup ────────────────────────────────────────────────────────
# Use SQLite in-memory for tests — no PostgreSQL required for running tests
# This makes tests fast, isolated, and self-contained
TEST_DB_URL = "sqlite:///./test_certificates.db"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override the production DB session with the test DB session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Create all tables before each test, drop them after.

    This ensures each test starts with a clean database.
    """
    # Import models to ensure they are registered with Base
    from app.models import generation_job, certificate  # noqa

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client():
    """Return a FastAPI TestClient for making HTTP requests in tests."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def valid_job_payload():
    """A valid job creation request payload."""
    return {
        "certificate_title": "Certificate of Completion",
        "event_name": "Python Backend Development Workshop",
        "organization_name": "Aero",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Gokul M", "email": "gokul@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"},
            {"name": "Priya Sharma", "email": "priya@example.com"},
        ]
    }


@pytest.fixture
def single_recipient_payload():
    """A valid payload with one recipient."""
    return {
        "certificate_title": "Certificate of Achievement",
        "event_name": "Data Science Bootcamp",
        "organization_name": "TechCorp",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Test User", "email": "test@example.com"}
        ]
    }


@pytest.fixture
def test_output_dir(tmp_path):
    """Create and configure a temporary directory for test PDFs."""
    output_dir = tmp_path / "test_certificates"
    output_dir.mkdir()
    original = settings.CERTIFICATE_OUTPUT_DIR
    settings.CERTIFICATE_OUTPUT_DIR = str(output_dir)
    yield str(output_dir)
    settings.CERTIFICATE_OUTPUT_DIR = original
    # Cleanup generated test PDFs
    for pdf in output_dir.glob("*.pdf"):
        pdf.unlink()
