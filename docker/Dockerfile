# Printernizer - Standalone Docker Deployment
# Multi-stage build for optimized production container
#
# ⚠️  IMPORTANT: Build Context Requirements
# This Dockerfile MUST be built with the repository root as the build context.
#
# Correct build commands:
#   From repo root: docker build -f docker/Dockerfile -t printernizer .
#   Using script:   ./build-docker.sh
#   Using compose:  cd docker && docker-compose up -d
#
# ❌ INCORRECT (will fail with "entrypoint.sh not found"):
#   cd docker && docker build -t printernizer .
#
# The build context must include: src/, frontend/, database_schema.sql, docker/

# Stage 1: Builder
FROM python:3.11-alpine as builder

# Set working directory
WORKDIR /build

# Install build dependencies
# Using --no-scripts to avoid QEMU emulation issues during cross-platform builds
RUN apk add --no-cache --no-scripts \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    libffi-dev \
    sqlite-dev \
    bash

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine

LABEL maintainer="sebastian@porcus3d.de"
LABEL description="Printernizer - Professional 3D Printer Management System"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEPLOYMENT_MODE=docker \
    TZ=Europe/Berlin

# Install runtime dependencies
# Using --no-scripts to avoid QEMU emulation issues during cross-platform builds
RUN apk add --no-cache --no-scripts \
    sqlite \
    curl \
    bash \
    tzdata \
    ffmpeg

# Create app user for security
RUN addgroup -g 1000 appuser && \
    adduser -u 1000 -G appuser -h /home/appuser -D appuser

# Create application directories
RUN mkdir -p /app/data \
    /app/logs \
    /app/backups \
    /app/uploads \
    /app/printer-files \
    /app/temp && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application files
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser frontend/ /app/frontend/
COPY --chown=appuser:appuser assets/database/schema.sql /app/database_schema.sql
COPY --chown=appuser:appuser docker/entrypoint.sh /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["python", "src/main.py"]
