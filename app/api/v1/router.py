"""
DocuSense - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, items, qa, upload

api_router = APIRouter()

# Include health endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Include items endpoints
api_router.include_router(items.router, prefix="/items", tags=["Items"])

# Include upload endpoints
api_router.include_router(upload.router)

# Include QA endpoints
api_router.include_router(qa.router)
