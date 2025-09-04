#!/bin/bash
# Printernizer Production Deployment Validation Script
# Post-deployment health checks and business functionality validation

set -e

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
NAMESPACE="${NAMESPACE:-printernizer}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:80}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results tracking
TESTS_PASSED=0
TESTS_TOTAL=0

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

test_pass() {
    success "✅ $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

test_fail() {
    error "❌ $1"
    ((TESTS_TOTAL++))
}

# Header
echo "================================================================="
echo "🧪 Printernizer Production Deployment Validation"
echo "================================================================="
echo "Environment: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"
echo "Backend URL: $BASE_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "================================================================="

# 1. Container Health Checks
log "1. Validating container health..."

if command -v kubectl &> /dev/null && kubectl get namespace $NAMESPACE &> /dev/null; then
    log "Using Kubernetes deployment for validation"
    
    # Backend pods
    if kubectl get pods -n $NAMESPACE -l app=printernizer-backend --field-selector=status.phase=Running | grep -q Running; then
        test_pass "Backend pods are running"
    else
        test_fail "Backend pods are not running"
    fi
    
    # Frontend pods  
    if kubectl get pods -n $NAMESPACE -l app=printernizer-frontend --field-selector=status.phase=Running | grep -q Running; then
        test_pass "Frontend pods are running"
    else
        test_fail "Frontend pods are not running"
    fi
    
    # Redis pods
    if kubectl get pods -n $NAMESPACE -l app=printernizer-redis --field-selector=status.phase=Running | grep -q Running; then
        test_pass "Redis pods are running"
    else
        test_fail "Redis pods are not running"
    fi
    
    # Check service endpoints
    BACKEND_IP=$(kubectl get service printernizer-backend -n $NAMESPACE -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
    if [ -n "$BACKEND_IP" ]; then
        test_pass "Backend service has ClusterIP: $BACKEND_IP"
        BASE_URL="http://$BACKEND_IP:8000"
    else
        test_fail "Backend service is not accessible"
    fi
    
else
    log "Using Docker Compose deployment for validation"
    
    # Check containers
    if docker-compose ps | grep -q "printernizer-backend.*Up"; then
        test_pass "Backend container is running"
    else
        test_fail "Backend container is not running"
    fi
    
    if docker-compose ps | grep -q "printernizer-frontend.*Up"; then
        test_pass "Frontend container is running"
    else
        test_fail "Frontend container is not running"
    fi
    
    if docker-compose ps | grep -q "printernizer-redis.*Up"; then
        test_pass "Redis container is running"
    else
        test_fail "Redis container is not running"
    fi
fi

# 2. API Health Check
log "2. Validating API health endpoints..."

# Wait for services to be ready
sleep 10

# Health endpoint test with retry
for attempt in {1..5}; do
    if curl -f -s "$BASE_URL/api/v1/health" > /dev/null 2>&1; then
        test_pass "API health endpoint is responding"
        break
    elif [ $attempt -eq 5 ]; then
        test_fail "API health endpoint is not responding after 5 attempts"
    else
        log "Health check attempt $attempt failed, retrying in 10s..."
        sleep 10
    fi
done

# API version endpoint
if curl -f -s "$BASE_URL/api/v1/system/info" | grep -q "version"; then
    test_pass "API version endpoint is responding"
else
    test_fail "API version endpoint is not responding"
fi

# 3. Core API Endpoints
log "3. Validating core API endpoints..."

# Printers endpoint
if curl -f -s "$BASE_URL/api/v1/printers" > /dev/null 2>&1; then
    test_pass "Printers API endpoint is accessible"
else
    test_fail "Printers API endpoint is not accessible"
fi

# Jobs endpoint  
if curl -f -s "$BASE_URL/api/v1/jobs" > /dev/null 2>&1; then
    test_pass "Jobs API endpoint is accessible"
else
    test_fail "Jobs API endpoint is not accessible"
fi

# Files endpoint
if curl -f -s "$BASE_URL/api/v1/files" > /dev/null 2>&1; then
    test_pass "Files API endpoint is accessible"
else
    test_fail "Files API endpoint is not accessible"
fi

# Analytics endpoint
if curl -f -s "$BASE_URL/api/v1/analytics/summary" > /dev/null 2>&1; then
    test_pass "Analytics API endpoint is accessible"
else
    test_fail "Analytics API endpoint is not accessible"
fi

# 4. Database Connectivity
log "4. Validating database connectivity..."

# Test database through API
if curl -f -s "$BASE_URL/api/v1/system/status" | grep -q "database"; then
    test_pass "Database connectivity through API is working"
else
    test_fail "Database connectivity through API is not working"
fi

# 5. WebSocket Connection
log "5. Validating WebSocket connectivity..."

# Basic WebSocket connection test (simplified)
if curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" "$BASE_URL/ws" 2>&1 | grep -q "101 Switching Protocols\|426 Upgrade Required"; then
    test_pass "WebSocket endpoint is accessible"
else
    test_fail "WebSocket endpoint is not accessible"
fi

# 6. Frontend Accessibility
log "6. Validating frontend accessibility..."

if curl -f -s "$FRONTEND_URL/" > /dev/null 2>&1; then
    test_pass "Frontend is accessible"
    
    # Check for key frontend assets
    if curl -f -s "$FRONTEND_URL/js/main.js" > /dev/null 2>&1; then
        test_pass "Frontend JavaScript assets are accessible"
    else
        test_fail "Frontend JavaScript assets are not accessible"
    fi
    
    if curl -f -s "$FRONTEND_URL/css/styles.css" > /dev/null 2>&1; then
        test_pass "Frontend CSS assets are accessible"
    else
        test_fail "Frontend CSS assets are not accessible"
    fi
else
    test_fail "Frontend is not accessible"
fi

# 7. Security Headers Validation
log "7. Validating security headers..."

SECURITY_HEADERS=$(curl -I -s "$FRONTEND_URL/" 2>/dev/null)

if echo "$SECURITY_HEADERS" | grep -q "X-Frame-Options"; then
    test_pass "X-Frame-Options security header is present"
else
    test_fail "X-Frame-Options security header is missing"
fi

if echo "$SECURITY_HEADERS" | grep -q "X-Content-Type-Options"; then
    test_pass "X-Content-Type-Options security header is present"
else
    test_fail "X-Content-Type-Options security header is missing"
fi

if echo "$SECURITY_HEADERS" | grep -q "Content-Security-Policy"; then
    test_pass "Content-Security-Policy header is present"
else
    test_fail "Content-Security-Policy header is missing"
fi

# 8. German Business Compliance Validation
log "8. Validating German business compliance..."

# Check timezone setting through API
if curl -f -s "$BASE_URL/api/v1/system/info" | grep -q "Europe/Berlin\|CET\|CEST"; then
    test_pass "German timezone (Europe/Berlin) is configured"
else
    test_fail "German timezone is not properly configured"
fi

# Check GDPR headers
if curl -I -s "$FRONTEND_URL/" | grep -q "X-Privacy-Policy\|X-Data-Protection"; then
    test_pass "GDPR compliance headers are present"
else
    test_fail "GDPR compliance headers are missing"
fi

# 9. Monitoring Endpoints
log "9. Validating monitoring endpoints..."

# Prometheus metrics
if curl -f -s "$BASE_URL/metrics" | grep -q "# HELP"; then
    test_pass "Prometheus metrics endpoint is accessible"
else
    test_fail "Prometheus metrics endpoint is not accessible"
fi

# 10. Performance Baseline Test
log "10. Running performance baseline test..."

# Simple response time test
START_TIME=$(date +%s%N)
if curl -f -s "$BASE_URL/api/v1/health" > /dev/null 2>&1; then
    END_TIME=$(date +%s%N)
    RESPONSE_TIME=$(((END_TIME - START_TIME) / 1000000))  # Convert to ms
    
    if [ $RESPONSE_TIME -lt 1000 ]; then
        test_pass "API response time is acceptable (${RESPONSE_TIME}ms < 1000ms)"
    else
        test_fail "API response time is too slow (${RESPONSE_TIME}ms >= 1000ms)"
    fi
else
    test_fail "Performance test failed - API not responding"
fi

# Summary
echo "================================================================="
echo "📊 VALIDATION SUMMARY"
echo "================================================================="
echo "Tests passed: $TESTS_PASSED"
echo "Total tests: $TESTS_TOTAL"

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    success "🎉 ALL VALIDATION TESTS PASSED!"
    echo "✅ Printernizer Milestone 1.1 is successfully deployed and operational"
    echo "🇩🇪 German business compliance: ✅"
    echo "🔒 Security configuration: ✅"
    echo "🚀 Performance: ✅"
    echo "📈 Monitoring: ✅"
    echo ""
    echo "🌐 System is ready for Porcus3D production use!"
    exit 0
elif [ $TESTS_PASSED -ge $((TESTS_TOTAL * 80 / 100)) ]; then
    warn "⚠️  PARTIAL SUCCESS - $(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)% tests passed"
    echo "🔧 Some issues detected - review failed tests"
    exit 1
else
    error "❌ VALIDATION FAILED - Only $(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)% tests passed"
    echo "🛠️  Critical issues detected - deployment may not be functional"
    exit 2
fi