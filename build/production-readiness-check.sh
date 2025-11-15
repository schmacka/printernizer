#!/bin/bash
# Printernizer Milestone 1.1 Production Readiness Check
# Comprehensive validation script for German business deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
VERSION="${VERSION:-latest}"
NAMESPACE="printernizer"
CHECKLIST_PASSED=0
CHECKLIST_TOTAL=0

# Logging functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_pass() {
    success "✅ $1"
    ((CHECKLIST_PASSED++))
    ((CHECKLIST_TOTAL++))
}

check_fail() {
    error "❌ $1"
    ((CHECKLIST_TOTAL++))
}

# Header
echo "================================================================="
echo "🚀 Printernizer Milestone 1.1 - Production Readiness Check"
echo "================================================================="
echo "German 3D Print Management System for Porcus3D"
echo "Location: Kornwestheim, Germany"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "================================================================="

# 1. Infrastructure Prerequisites
log "1. Checking infrastructure prerequisites..."

if command -v docker &> /dev/null; then
    check_pass "Docker is installed and available"
else
    check_fail "Docker is not installed or not in PATH"
fi

if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed and available"
else
    check_fail "Docker Compose is not installed or not in PATH"
fi

if command -v kubectl &> /dev/null; then
    check_pass "kubectl is installed for Kubernetes deployments"
else
    warn "kubectl not found - Kubernetes deployment may not be available"
fi

# 2. Docker Configuration Validation
log "2. Validating Docker configuration..."

if [ -f "Dockerfile" ]; then
    check_pass "Backend Dockerfile exists"
    
    # Check for security best practices
    if grep -q "USER appuser" Dockerfile; then
        check_pass "Backend Dockerfile uses non-root user"
    else
        check_fail "Backend Dockerfile should use non-root user for security"
    fi
    
    if grep -q "HEALTHCHECK" Dockerfile; then
        check_pass "Backend Dockerfile includes health check"
    else
        check_fail "Backend Dockerfile should include health check"
    fi
else
    check_fail "Backend Dockerfile is missing"
fi

if [ -f "Dockerfile.frontend" ]; then
    check_pass "Frontend Dockerfile exists"
else
    check_fail "Frontend Dockerfile is missing"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "Docker Compose configuration exists"
    
    # Validate compose file structure
    if grep -q "printernizer-backend" docker-compose.yml; then
        check_pass "Backend service configured in Docker Compose"
    else
        check_fail "Backend service missing from Docker Compose"
    fi
    
    if grep -q "printernizer-frontend" docker-compose.yml; then
        check_pass "Frontend service configured in Docker Compose"
    else
        check_fail "Frontend service missing from Docker Compose"
    fi
    
    if grep -q "printernizer-redis" docker-compose.yml; then
        check_pass "Redis service configured for caching"
    else
        check_fail "Redis service missing from Docker Compose"
    fi
    
    if grep -q "printernizer-prometheus" docker-compose.yml; then
        check_pass "Prometheus monitoring configured"
    else
        check_fail "Prometheus monitoring missing from Docker Compose"
    fi
else
    check_fail "Docker Compose configuration is missing"
fi

# 3. Application Code Validation
log "3. Validating application code structure..."

if [ -f "src/main.py" ]; then
    check_pass "Main application entry point exists"
else
    check_fail "Main application file (src/main.py) is missing"
fi

if [ -d "src/api" ]; then
    check_pass "API modules directory exists"
else
    check_fail "API modules directory is missing"
fi

if [ -d "src/database" ]; then
    check_pass "Database modules directory exists"
else
    check_fail "Database modules directory is missing"
fi

if [ -d "src/services" ]; then
    check_pass "Services modules directory exists"
else
    check_fail "Services modules directory is missing"
fi

if [ -f "frontend/index.html" ]; then
    check_pass "Frontend main page exists"
else
    check_fail "Frontend main page (index.html) is missing"
fi

# 4. Configuration Validation
log "4. Validating configuration files..."

if [ -f ".env.example" ]; then
    check_pass "Environment configuration example exists"
else
    check_fail "Environment configuration example is missing"
fi

if [ -f "requirements.txt" ]; then
    check_pass "Python requirements file exists"
    
    # Check for essential dependencies
    if grep -q "fastapi" requirements.txt; then
        check_pass "FastAPI framework is included"
    else
        check_fail "FastAPI framework missing from requirements"
    fi
    
    if grep -q "uvicorn" requirements.txt; then
        check_pass "Uvicorn server is included"
    else
        check_fail "Uvicorn server missing from requirements"
    fi
    
    if grep -q "aiosqlite" requirements.txt; then
        check_pass "Async SQLite database driver is included"
    else
        check_fail "Async SQLite database driver missing from requirements"
    fi
    
    if grep -q "prometheus-client" requirements.txt; then
        check_pass "Prometheus monitoring client is included"
    else
        check_fail "Prometheus monitoring client missing from requirements"
    fi
else
    check_fail "Python requirements file is missing"
fi

if [ -f "database_schema.sql" ]; then
    check_pass "Database schema file exists"
else
    check_fail "Database schema file is missing"
fi

# 5. Security Configuration
log "5. Validating security configuration..."

if [ -d "security" ]; then
    check_pass "Security configuration directory exists"
    
    if [ -f "security/security-policy.yml" ]; then
        check_pass "Security policy configuration exists"
    else
        check_fail "Security policy configuration is missing"
    fi
    
    if [ -f "security/gdpr-compliance.md" ]; then
        check_pass "GDPR compliance documentation exists"
    else
        check_fail "GDPR compliance documentation is missing"
    fi
else
    check_fail "Security configuration directory is missing"
fi

# Check for security headers in nginx config
if [ -f "docker/nginx.conf" ]; then
    if grep -q "X-Frame-Options" docker/nginx.conf; then
        check_pass "Security headers configured in Nginx"
    else
        check_fail "Security headers missing from Nginx configuration"
    fi
    
    if grep -q "Content-Security-Policy" docker/nginx.conf; then
        check_pass "Content Security Policy configured"
    else
        check_fail "Content Security Policy missing from Nginx configuration"
    fi
else
    check_fail "Nginx configuration file is missing"
fi

# 6. Monitoring and Logging
log "6. Validating monitoring and logging setup..."

if [ -d "monitoring" ]; then
    check_pass "Monitoring configuration directory exists"
    
    if [ -f "monitoring/prometheus.yml" ]; then
        check_pass "Prometheus configuration exists"
    else
        check_fail "Prometheus configuration is missing"
    fi
    
    if [ -d "monitoring/grafana" ]; then
        check_pass "Grafana configuration directory exists"
    else
        check_fail "Grafana configuration directory is missing"
    fi
else
    check_fail "Monitoring configuration directory is missing"
fi

# 7. German Business Compliance
log "7. Validating German business compliance..."

if grep -q "Europe/Berlin" .env.example; then
    check_pass "German timezone (Europe/Berlin) configured"
else
    check_fail "German timezone not configured"
fi

if grep -q "GDPR_ENABLED=true" .env.example; then
    check_pass "GDPR compliance enabled"
else
    check_fail "GDPR compliance not enabled"
fi

if grep -q "VAT_RATE=0.19" .env.example; then
    check_pass "German VAT rate configured"
else
    check_fail "German VAT rate not configured"
fi

if grep -q "CURRENCY=EUR" .env.example; then
    check_pass "Euro currency configured"
else
    check_fail "Euro currency not configured"
fi

if grep -q "DATA_RETENTION_DAYS=2555" .env.example; then
    check_pass "German business data retention period configured (7 years)"
else
    check_fail "German business data retention period not configured"
fi

# 8. CI/CD Pipeline
log "8. Validating CI/CD pipeline..."

if [ -f ".github/workflows/ci-cd.yml" ]; then
    check_pass "GitHub Actions CI/CD pipeline exists"
    
    if grep -q "test-backend" .github/workflows/ci-cd.yml; then
        check_pass "Backend testing configured in CI/CD"
    else
        check_fail "Backend testing missing from CI/CD"
    fi
    
    if grep -q "security-scan" .github/workflows/ci-cd.yml; then
        check_pass "Security scanning configured in CI/CD"
    else
        check_fail "Security scanning missing from CI/CD"
    fi
    
    if grep -q "deploy-production" .github/workflows/ci-cd.yml; then
        check_pass "Production deployment configured in CI/CD"
    else
        check_fail "Production deployment missing from CI/CD"
    fi
else
    check_fail "CI/CD pipeline configuration is missing"
fi

# 9. Deployment Scripts
log "9. Validating deployment scripts..."

if [ -f "deploy.sh" ]; then
    check_pass "Production deployment script exists"
    
    if grep -q "health_check" deploy.sh; then
        check_pass "Health checks included in deployment script"
    else
        check_fail "Health checks missing from deployment script"
    fi
    
    if grep -q "rollback" deploy.sh; then
        check_pass "Rollback functionality included in deployment script"
    else
        check_fail "Rollback functionality missing from deployment script"
    fi
else
    check_fail "Production deployment script is missing"
fi

# 10. Kubernetes Configuration
log "10. Validating Kubernetes configuration..."

if [ -f "production.yml" ]; then
    check_pass "Kubernetes production configuration exists"
    
    if grep -q "HorizontalPodAutoscaler" production.yml; then
        check_pass "Auto-scaling configured for production"
    else
        check_fail "Auto-scaling not configured for production"
    fi
    
    if grep -q "NetworkPolicy" production.yml; then
        check_pass "Network security policies configured"
    else
        check_fail "Network security policies missing"
    fi
else
    check_fail "Kubernetes production configuration is missing"
fi

# Summary
echo "================================================================="
echo "📊 PRODUCTION READINESS SUMMARY"
echo "================================================================="
echo "Checks passed: $CHECKLIST_PASSED"
echo "Total checks: $CHECKLIST_TOTAL"

if [ $CHECKLIST_PASSED -eq $CHECKLIST_TOTAL ]; then
    success "🎉 ALL CHECKS PASSED - Printernizer Milestone 1.1 is production ready!"
    echo "✅ Ready for deployment to Porcus3D production environment"
    echo "🌍 German business compliance: ✅"
    echo "🔒 Security configuration: ✅"
    echo "📈 Monitoring setup: ✅"
    echo "🚀 CI/CD pipeline: ✅"
    exit 0
elif [ $CHECKLIST_PASSED -ge $((CHECKLIST_TOTAL * 80 / 100)) ]; then
    warn "⚠️  MOSTLY READY - $(echo "scale=1; $CHECKLIST_PASSED * 100 / $CHECKLIST_TOTAL" | bc)% checks passed"
    echo "🔧 Please address the failed checks before production deployment"
    exit 1
else
    error "❌ NOT READY - Only $(echo "scale=1; $CHECKLIST_PASSED * 100 / $CHECKLIST_TOTAL" | bc)% checks passed"
    echo "🛠️  Significant issues need to be resolved before production deployment"
    exit 2
fi