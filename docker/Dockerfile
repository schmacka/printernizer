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
#
# NOTE: This image uses a Debian (glibc) base rather than Alpine. The build123d
# parametric model generator depends on OpenCascade via the OCP bindings, which
# ship manylinux (glibc) wheels only — there is no musllinux build, so it cannot
# be installed on Alpine/musl.

# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Build dependencies. Most packages install as binary wheels on Debian/glibc;
# the toolchain covers the few that may build from source.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (prefer prebuilt wheels)
RUN pip install --no-cache-dir --user --prefer-binary -r requirements.txt

# Optional: build123d (parametric model generator). Best-effort — it has wheels
# for x86_64/aarch64 glibc only, so on other arches this is skipped and the
# generator simply reports itself unavailable.
RUN pip install --no-cache-dir --user --prefer-binary "build123d>=0.9.1" \
    || echo "build123d not installable on this platform; model generator disabled"

# Stage 2: Runtime
FROM python:3.11-slim-bookworm

LABEL maintainer="sebastian@porcus3d.de"
LABEL description="Printernizer - Professional 3D Printer Management System"
LABEL version="2.0.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEPLOYMENT_MODE=docker \
    TZ=Europe/Berlin \
    PATH=/home/appuser/.local/bin:$PATH

# Runtime dependencies.
# - sqlite3, curl, bash, tzdata, ffmpeg: core app
# - libGL/libGLU/libX* + fontconfig: required by OpenCascade/OCP (build123d)
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 \
        curl \
        bash \
        tzdata \
        ffmpeg \
        ca-certificates \
        libgl1 \
        libglu1-mesa \
        libxrender1 \
        libxext6 \
        libsm6 \
        libgomp1 \
        fontconfig \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -d /home/appuser appuser

# Create application directories
RUN mkdir -p /app/data \
    /app/logs \
    /app/backups \
    /app/uploads \
    /app/printer-files \
    /app/temp && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application files
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser frontend/ /app/frontend/
COPY --chown=appuser:appuser assets/database/schema.sql /app/database_schema.sql
COPY --chown=appuser:appuser docker/entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh && chown -R appuser:appuser /home/appuser/.local

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["python", "src/main.py"]
