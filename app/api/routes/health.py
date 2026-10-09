"""Health check API endpoint."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the API and database are running correctly.",
    tags=["Health"],
)
async def health_check():
    """Return the health status of the API and database connection.

    Returns:
        JSON with status 'healthy' or 'degraded' based on DB connectivity.
    """
    db_ok = check_database_connection()
    if db_ok:
        return {"status": "healthy", "database": "connected"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "disconnected"},
        )
