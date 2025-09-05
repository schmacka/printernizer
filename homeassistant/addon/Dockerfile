# Home Assistant Addon Dockerfile for Printernizer
# Multi-architecture support for Raspberry Pi and x86 systems

ARG BUILD_FROM=ghcr.io/hassio-addons/base/amd64:latest
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Environment variables for Python and Home Assistant
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Europe/Berlin \
    ENVIRONMENT=homeassistant \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2

# Copy add-on specific files
COPY rootfs/ /

# Install Python and dependencies
RUN \
    apk add --no-cache \
        python3=~3.11 \
        py3-pip=~23 \
        python3-dev=~3.11 \
        build-base \
        libffi-dev \
        openssl-dev \
        libmagic \
        curl \
        sqlite \
        tzdata \
    && \
    pip3 install --upgrade pip setuptools wheel \
    && \
    pip3 install --no-cache-dir \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        asyncio-mqtt==0.13.0 \
        aiosqlite==0.19.0 \
        pydantic==2.5.0 \
        pydantic-settings==2.1.0 \
        structlog==23.2.0 \
        aiofiles==23.2.1 \
        python-multipart==0.0.6 \
        websockets==12.0 \
        httpx==0.25.2 \
        redis==5.0.1 \
        paho-mqtt==1.6.1 \
        python-dotenv==1.0.0 \
    && \
    rm -rf /tmp/* \
    && \
    rm -rf /var/cache/apk/*

# Copy application files from project root
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY database_schema.sql /app/
COPY requirements.txt /app/
COPY pytest.ini /app/

# Create necessary directories
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/backups \
    /app/uploads \
    /app/printer-files \
    /app/temp \
    /data

# Set permissions
RUN chmod a+x /etc/services.d/printernizer/run \
    && chmod a+x /etc/services.d/printernizer/finish

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Labels for Home Assistant addon registry
LABEL \
    io.hass.name="Printernizer" \
    io.hass.description="Professional 3D print management system for Bambu Lab and Prusa printers" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386" \
    io.hass.type="addon" \
    io.hass.version="1.0.0" \
    maintainer="Porcus3D <sebastian@porcus3d.de>" \
    org.opencontainers.image.title="Printernizer Home Assistant Addon" \
    org.opencontainers.image.description="Professional 3D print management system with German business features" \
    org.opencontainers.image.vendor="Porcus3D" \
    org.opencontainers.image.authors="Porcus3D <sebastian@porcus3d.de>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/porcus3d/printernizer" \
    org.opencontainers.image.source="https://github.com/porcus3d/printernizer" \
    org.opencontainers.image.documentation="https://github.com/porcus3d/printernizer/blob/main/README.md"