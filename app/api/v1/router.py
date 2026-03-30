"""
DocuSense - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, items, asl, upload

api_router = APIRouter()

# Include health endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Include upload endpoints
api_router.include_router(upload.router)

# Include ASL endpoints
api_router.include_router(asl.router)
