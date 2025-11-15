#!/bin/bash
# Printernizer - Docker Build Script
# Ensures correct build context and prevents "entrypoint.sh not found" errors

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}🖨️  Printernizer Docker Build${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Ensure we're in the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verify required files exist
echo -e "${YELLOW}Verifying build requirements...${NC}"
required_files=(
    "docker/Dockerfile"
    "docker/entrypoint.sh"
    "src"
    "frontend"
    "assets/database/schema.sql"
)

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        echo -e "${RED}❌ Error: Required file/directory not found: $file${NC}"
        echo -e "${RED}   Make sure you're running this script from the repository root${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All required files found${NC}"
echo ""

# Parse arguments
IMAGE_NAME="${1:-printernizer}"
IMAGE_TAG="${2:-latest}"

echo -e "${YELLOW}Building Docker image...${NC}"
echo -e "   Image: ${GREEN}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "   Context: ${GREEN}$(pwd)${NC}"
echo -e "   Dockerfile: ${GREEN}docker/Dockerfile${NC}"
echo ""

# Build the image with correct context
# IMPORTANT: Context must be the repository root (.)
# The Dockerfile is in docker/ subdirectory
docker build \
    --file docker/Dockerfile \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    echo -e "To run the container:"
    echo -e "  ${GREEN}docker run -d -p 8000:8000 --name printernizer ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo ""
    echo -e "Or use docker-compose (recommended):"
    echo -e "  ${GREEN}cd docker && docker-compose up -d${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}=====================================${NC}"
    echo -e "${RED}❌ Build failed!${NC}"
    echo -e "${RED}=====================================${NC}"
    exit 1
fi
