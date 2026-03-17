# Multi-stage production Dockerfile for api-diet
# FastAPI + SQLAlchemy + Supabase on Fly.io

# ================================
# Stage 1: Build Dependencies
# ================================
FROM python:3.12-slim AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ================================
# Stage 2: Production Runtime
# ================================
FROM python:3.12-slim AS runtime

# Build arguments
ARG APP_USER=appuser
ARG APP_GROUP=appgroup
ARG APP_UID=1001
ARG APP_GID=1001

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH" \
    # Application settings
    PORT=8000 \
    UVICORN_WORKERS=2 \
    LOG_LEVEL=info

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -g ${APP_GID} ${APP_GROUP} && \
    useradd -u ${APP_UID} -g ${APP_GROUP} -d /app -s /sbin/nologin -c "App user" ${APP_USER}

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory and set ownership
RUN mkdir -p /app /data /app/logs && \
    chown -R ${APP_USER}:${APP_GROUP} /app /data

# Set working directory
WORKDIR /app

# Copy gunicorn configuration
COPY --chown=${APP_USER}:${APP_GROUP} gunicorn.conf.py ./

# Copy Alembic configuration and migrations
COPY --chown=${APP_USER}:${APP_GROUP} alembic.ini ./
COPY --chown=${APP_USER}:${APP_GROUP} alembic ./alembic

# Copy BAML generated client
COPY --chown=${APP_USER}:${APP_GROUP} baml_client ./baml_client

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} app ./app

# Switch to non-root user
USER ${APP_USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Production command: Gunicorn with Uvicorn workers
# - Uses uvloop for faster event loop (auto-detected)
# - Uses httptools for faster HTTP parsing (auto-detected)
# - Worker count controlled by UVICORN_WORKERS env var
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]