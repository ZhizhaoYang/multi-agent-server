"""
Simple wake-up endpoint for Render cron jobs.
Prevents cold starts by pinging every 40 minutes.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/wake-up")
async def wake_up_service():
    """
    Simple wake-up endpoint for Render cron jobs.
    Returns immediately to prevent cold starts.
    """
    return {
        "success": True,
        "status": "awake",
        "message": "Service is warm and ready"
    }


@router.get("/ping")
async def ping():
    """
    Ultra-simple ping endpoint.
    """
    return {
        "success": True,
        "status": "pong"
    }