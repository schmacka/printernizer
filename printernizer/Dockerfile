# Printernizer - Home Assistant Add-on
# Multi-architecture support for Home Assistant ecosystem

ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set environment variables
ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEPLOYMENT_MODE=homeassistant \
    HA_INGRESS=true

# Install base dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-brotli \
    sqlite \
    curl \
    jq \
    bash \
    tzdata \
    && rm -rf /var/cache/apk/*

# Install build dependencies temporarily
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    musl-dev \
    python3-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Remove build dependencies to reduce image size
RUN apk del .build-deps

# Copy application files
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY database_schema.sql /app/

# Copy Home Assistant specific files
COPY run.sh /
RUN chmod +x /run.sh

# Create necessary directories
RUN mkdir -p /data \
    /app/logs \
    /app/temp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port for Home Assistant Ingress
EXPOSE 8000

# Labels for Home Assistant
LABEL io.hass.name="Printernizer" \
      io.hass.description="Professional 3D Printer Management System" \
      io.hass.type="addon" \
      io.hass.version="2.0.13" \
      io.hass.arch="aarch64|amd64|armv7|armhf"

# Start the add-on service
CMD ["/run.sh"]
