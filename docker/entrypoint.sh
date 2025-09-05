#!/bin/bash
# Printernizer Production Entrypoint Script
# Enhanced for Milestone 1.2: Printer API Integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🖨️  Starting Printernizer - Professional 3D Print Management${NC}"
echo -e "${BLUE}📅 $(date) - Milestone 1.2: Printer API Integration${NC}"

# Environment validation
echo -e "${YELLOW}⚙️  Validating environment...${NC}"

# Required environment variables
REQUIRED_VARS=(
    "ENVIRONMENT"
    "TZ"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Missing required environment variable: $var${NC}"
        exit 1
    fi
done

# Set timezone
echo -e "${BLUE}🕐 Setting timezone to $TZ${NC}"
export TZ

# Create necessary directories
echo -e "${YELLOW}📁 Creating application directories...${NC}"
mkdir -p /app/data
mkdir -p /app/logs
mkdir -p /app/backups
mkdir -p /app/uploads
mkdir -p /app/printer-files
mkdir -p /app/temp

# Set proper permissions
chown -R appuser:appuser /app/data /app/logs /app/backups /app/uploads /app/printer-files /app/temp
chmod -R 755 /app/data /app/logs /app/backups /app/uploads /app/printer-files /app/temp

# Database initialization
DATABASE_PATH=${DATABASE_PATH:-/app/data/printernizer.db}
if [ ! -f "$DATABASE_PATH" ]; then
    echo -e "${YELLOW}🗄️  Initializing database...${NC}"
    if [ -f "/app/database_schema.sql" ]; then
        sqlite3 "$DATABASE_PATH" < /app/database_schema.sql
        echo -e "${GREEN}✅ Database initialized successfully${NC}"
    else
        echo -e "${RED}❌ Database schema file not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Database already exists${NC}"
fi

# Printer connectivity pre-checks
echo -e "${YELLOW}🔌 Running printer connectivity pre-checks...${NC}"

# Check if network connectivity is available
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "${GREEN}✅ Network connectivity: OK${NC}"
else
    echo -e "${YELLOW}⚠️  Limited network connectivity detected${NC}"
fi

# Performance optimization for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}🚀 Applying production optimizations...${NC}"
    
    # Set Python optimizations
    export PYTHONOPTIMIZE=1
    export PYTHONDONTWRITEBYTECODE=1
    
    # Set worker count based on CPU cores (for WebSocket, use 1 worker)
    WORKERS=${WORKERS:-1}
    echo -e "${BLUE}👥 Using $WORKERS worker process(es)${NC}"
fi

# Health check setup
echo -e "${YELLOW}🏥 Setting up health monitoring...${NC}"

# Background health check function
health_monitor() {
    while true; do
        sleep 30
        if ! curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            echo -e "${RED}⚠️  Health check failed at $(date)${NC}" >> /app/logs/health.log
        fi
    done
}

# Start health monitoring in background if in production
if [ "$ENVIRONMENT" = "production" ]; then
    health_monitor &
    HEALTH_PID=$!
    echo -e "${BLUE}📊 Health monitoring started (PID: $HEALTH_PID)${NC}"
fi

# Graceful shutdown handler
cleanup() {
    echo -e "${YELLOW}🛑 Graceful shutdown initiated...${NC}"
    
    if [ -n "$HEALTH_PID" ]; then
        echo -e "${BLUE}⏹️  Stopping health monitor...${NC}"
        kill "$HEALTH_PID" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
    exit 0
}

# Setup signal handlers
trap cleanup SIGTERM SIGINT

# Log startup information
echo -e "${GREEN}🎉 Printernizer startup completed successfully!${NC}"
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   • Environment: $ENVIRONMENT"
echo -e "   • Timezone: $TZ"
echo -e "   • Database: $DATABASE_PATH"
echo -e "   • Workers: ${WORKERS:-1}"
echo -e "   • Port: ${PORT:-8000}"

# Start the application
echo -e "${GREEN}🚀 Starting Printernizer application server...${NC}"
exec "$@"