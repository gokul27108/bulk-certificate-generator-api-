"""Database configuration and session management.

Uses SQLAlchemy 2.x with connection pooling for efficient database access.
Provides a dependency-injectable session factory for FastAPI.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def create_db_engine(database_url: str):
    """Create a SQLAlchemy engine with connection pooling.

    Args:
        database_url: The database connection URL.

    Returns:
        Configured SQLAlchemy engine.
    """
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,        # Number of persistent connections
        max_overflow=20,     # Extra connections during peak load
        pool_pre_ping=True,  # Verify connections before use
        echo=settings.DEBUG, # Log SQL in debug mode
    )
    return engine


# Primary application engine
engine = create_db_engine(settings.DATABASE_URL)

# Session factory - each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that provides a database session.

    Ensures the session is always closed after the request,
    even if an exception occurs.

    Yields:
        SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """Check if the database connection is working.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
