"""
DocuSense - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import ask, auth, health, upload

api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include health endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Include upload endpoints
api_router.include_router(upload.router)

# Include ASK endpoints
api_router.include_router(ask.router)
