#!/bin/bash
# Printernizer Docker Rebuild Script
# Stops the existing container, removes it, and builds a fresh new one

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Printernizer Docker Rebuild Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "$DOCKER_DIR/docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found in $DOCKER_DIR${NC}"
    exit 1
fi

# Change to docker directory
cd "$DOCKER_DIR"

# Step 1: Stop and remove existing containers
echo -e "${YELLOW}Step 1: Stopping and removing existing containers...${NC}"
if docker-compose ps -q printernizer > /dev/null 2>&1; then
    docker-compose down
    echo -e "${GREEN}✓ Container stopped and removed${NC}"
else
    echo -e "${YELLOW}No running containers found${NC}"
fi
echo ""

# Step 2: Remove old image (optional - for truly fresh build)
echo -e "${YELLOW}Step 2: Removing old Docker image...${NC}"
if docker images printernizer:latest -q > /dev/null 2>&1; then
    docker rmi printernizer:latest || echo -e "${YELLOW}Warning: Could not remove image (may be in use)${NC}"
    echo -e "${GREEN}✓ Old image removed${NC}"
else
    echo -e "${YELLOW}No existing image found${NC}"
fi
echo ""

# Step 3: Build fresh image (no cache)
echo -e "${YELLOW}Step 3: Building fresh Docker image (no cache)...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Fresh image built successfully${NC}"
echo ""

# Step 4: Start the new container
echo -e "${YELLOW}Step 4: Starting new container...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Container started${NC}"
echo ""

# Step 5: Wait for health check
echo -e "${YELLOW}Step 5: Waiting for application to be healthy...${NC}"
echo -e "${BLUE}This may take up to 40 seconds...${NC}"

timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker inspect --format='{{.State.Health.Status}}' printernizer 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Application is healthy and ready!${NC}"
        break
    fi

    if [ $elapsed -eq $timeout ]; then
        echo -e "${RED}Warning: Health check timeout${NC}"
        echo -e "${YELLOW}Check container logs with: docker-compose logs -f${NC}"
    fi

    sleep 5
    elapsed=$((elapsed + 5))
    echo -e "${BLUE}Waiting... ($elapsed seconds)${NC}"
done
echo ""

# Display container status
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Container Status:${NC}"
echo -e "${BLUE}========================================${NC}"
docker-compose ps
echo ""

# Display useful commands
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Container is running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Application URL: ${BLUE}http://localhost:8000${NC}"
echo -e "Health Check:    ${BLUE}http://localhost:8000/api/v1/health${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  View logs:        ${BLUE}docker-compose logs -f${NC}"
echo -e "  Stop container:   ${BLUE}docker-compose stop${NC}"
echo -e "  Restart:          ${BLUE}docker-compose restart${NC}"
echo -e "  Remove all:       ${BLUE}docker-compose down${NC}"
echo -e "  Remove with data: ${BLUE}docker-compose down -v${NC}"
echo ""
