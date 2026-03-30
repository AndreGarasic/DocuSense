# DocuSense - FastAPI Application Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Build stage
FROM python:3.12-slim as builder

# Install build dependencies for sentence-transformers, PyMuPDF, and EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime stage
FROM python:3.12-slim as runtime

# Install runtime dependencies for EasyOCR and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    # Disable tokenizers parallelism warning
    TOKENIZERS_PARALLELISM=false

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Create uploads directory and model cache directory
RUN mkdir -p /app/uploads /home/appuser/.cache && \
    chown -R appuser:appgroup /app/uploads /home/appuser/.cache

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appgroup ./app ./app
COPY --chown=appuser:appgroup ./alembic ./alembic
COPY --chown=appuser:appgroup ./alembic.ini ./alembic.ini

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
