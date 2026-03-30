"""
DocuSense - FastAPI Main Application
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.rate_limiter import get_limiter
from app.db.session import engine
from app.services.model_loader import get_model_loader

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _preload_models_async() -> dict[str, bool]:
    """Preload ML models in a thread pool to avoid blocking."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        model_loader = get_model_loader()
        status = await loop.run_in_executor(executor, model_loader.preload_all)
    return status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting DocuSense API...")

    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory: {settings.upload_dir.absolute()}")

    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("API will start but database features will not work")

    # Preload ML models in background thread
    try:
        logger.info("Preloading ML models (this may take a moment)...")
        model_status = await _preload_models_async()
        
        if not model_status.get("ocr"):
            logger.warning("OCR model failed to load - OCR features will be unavailable")
        if not model_status.get("qa"):
            logger.warning("QA model failed to load - QA features will be unavailable")
            
        if all(model_status.values()):
            logger.info("All ML models loaded successfully")
    except Exception as e:
        logger.error(f"Error during model preloading: {e}")
        logger.warning("ML features may be unavailable")

    yield

    # Shutdown
    logger.info("Shutting down DocuSense API...")
    
    # Cleanup ML models
    try:
        model_loader = get_model_loader()
        model_loader.cleanup()
    except Exception as e:
        logger.error(f"Error during model cleanup: {e}")
    
    await engine.dispose()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure rate limiter
    limiter = get_limiter()
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
