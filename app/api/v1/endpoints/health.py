"""
DocuSense - Health Check Endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API.
    """
    return {
        "status": "healthy",
        "message": "DocuSense API is running"
    }


@router.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns whether the API is ready to accept requests.
    """
    return {
        "status": "ready",
        "message": "DocuSense API is ready to accept requests"
    }
