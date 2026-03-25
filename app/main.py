"""
DocuSense - FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc
        openapi_url="/openapi.json",
    )

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    application.include_router(api_router, prefix=settings.api_prefix)

    return application


app = create_application()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns basic information about the API.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
