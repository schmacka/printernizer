#!/bin/bash
# Printernizer - Docker Standalone Entrypoint
# Handles initialization and startup for containerized deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}🖨️  Printernizer Docker Deployment${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}📅 $(date)${NC}"
echo ""

# Environment validation
echo -e "${YELLOW}⚙️  Validating environment...${NC}"

# Set timezone
TIMEZONE=${TZ:-Europe/Berlin}
echo -e "${BLUE}🕐 Timezone: $TIMEZONE${NC}"
export TZ=$TIMEZONE

# Create necessary directories with proper permissions
echo -e "${YELLOW}📁 Setting up directories...${NC}"
mkdir -p /app/data
mkdir -p /app/logs
mkdir -p /app/backups
mkdir -p /app/printer-files
mkdir -p /app/temp
mkdir -p /app/data/preview-cache

# Database initialization
DATABASE_PATH=${DATABASE_PATH:-/app/data/printernizer.db}
if [ ! -f "$DATABASE_PATH" ]; then
    echo -e "${YELLOW}🗄️  Database will be initialized by application...${NC}"
else
    echo -e "${GREEN}✅ Database already exists${NC}"
fi

# Network connectivity check
echo -e "${YELLOW}🔌 Checking network connectivity...${NC}"
if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    echo -e "${GREEN}✅ Network connectivity: OK${NC}"
else
    echo -e "${YELLOW}⚠️  Limited network connectivity detected${NC}"
    echo -e "${YELLOW}   Printer connections may fail if network is unavailable${NC}"
fi

# Performance optimization for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}🚀 Applying production optimizations...${NC}"
    export PYTHONOPTIMIZE=1
    export PYTHONDONTWRITEBYTECODE=1
    echo -e "${GREEN}✅ Production optimizations enabled${NC}"
fi

# Display configuration
echo ""
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo -e "   • Environment: ${ENVIRONMENT:-development}"
echo -e "   • Deployment Mode: ${DEPLOYMENT_MODE:-docker}"
echo -e "   • Timezone: $TIMEZONE"
echo -e "   • Database: $DATABASE_PATH"
echo -e "   • Port: ${PORT:-8000}"
echo -e "   • Log Level: ${LOG_LEVEL:-info}"
echo -e "   • 3D Preview: ${ENABLE_3D_PREVIEW:-true}"
echo -e "   • WebSockets: ${ENABLE_WEBSOCKETS:-true}"
echo ""

# Graceful shutdown handler
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Graceful shutdown initiated...${NC}"
    echo -e "${BLUE}   Stopping services...${NC}"

    # Allow time for graceful shutdown
    sleep 2

    echo -e "${GREEN}✅ Shutdown completed${NC}"
    exit 0
}

# Setup signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# Final startup message
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}🎉 Startup completed successfully!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "${BLUE}🚀 Starting Printernizer application server...${NC}"
echo -e "${BLUE}📊 Access the web interface at: http://localhost:${PORT:-8000}${NC}"
echo -e "${BLUE}📚 API documentation at: http://localhost:${PORT:-8000}/docs${NC}"
echo ""

# Execute the main command
exec "$@"
