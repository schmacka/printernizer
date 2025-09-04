#!/bin/bash
# Printernizer Production Deployment Script
# Comprehensive deployment automation for German hosting

set -e

# Configuration
NAMESPACE="printernizer"
ENVIRONMENT="${ENVIRONMENT:-production}"
VERSION="${VERSION:-latest}"
DRY_RUN="${DRY_RUN:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is required but not installed"
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        error "docker is required but not installed"
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi
    
    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        warn "Namespace $NAMESPACE does not exist, creating..."
        kubectl create namespace $NAMESPACE
    fi
    
    success "Prerequisites check passed"
}

# Build and push images
build_images() {
    log "Building Docker images for version: $VERSION"
    
    # Backend image
    log "Building backend image..."
    docker build -t ghcr.io/porcus3d/printernizer-backend:$VERSION .
    
    # Frontend image
    log "Building frontend image..."
    docker build -t ghcr.io/porcus3d/printernizer-frontend:$VERSION -f Dockerfile.frontend .
    
    if [ "$DRY_RUN" = "false" ]; then
        log "Pushing images to registry..."
        docker push ghcr.io/porcus3d/printernizer-backend:$VERSION
        docker push ghcr.io/porcus3d/printernizer-frontend:$VERSION
    else
        log "DRY_RUN: Skipping image push"
    fi
    
    success "Images built successfully"
}

# Deploy infrastructure components
deploy_infrastructure() {
    log "Deploying infrastructure components..."
    
    # Security policies
    log "Applying security policies..."
    kubectl apply -f security/security-policy.yml
    
    # Monitoring
    log "Deploying monitoring stack..."
    kubectl apply -f monitoring/
    
    # Backup system
    log "Setting up backup system..."
    kubectl apply -f backup/backup-system.yml
    
    # Load balancing and scaling
    log "Configuring load balancing and auto-scaling..."
    kubectl apply -f scaling/load-balancer.yml
    
    success "Infrastructure deployed"
}

# Deploy application
deploy_application() {
    log "Deploying Printernizer application..."
    
    # Update image tags in deployment
    sed -i "s/:latest/:$VERSION/g" production.yml
    
    # Apply application configuration
    if [ "$DRY_RUN" = "false" ]; then
        kubectl apply -f production.yml
    else
        log "DRY_RUN: Would apply production.yml"
        kubectl apply -f production.yml --dry-run=client
    fi
    
    success "Application deployed"
}

# Wait for deployment
wait_for_deployment() {
    log "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/printernizer-backend -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/printernizer-frontend -n $NAMESPACE
    
    success "Deployment is ready"
}

# Run health checks
health_check() {
    log "Running health checks..."
    
    # Get service IP
    BACKEND_IP=$(kubectl get service printernizer-backend -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    
    # Health check with retry
    for i in {1..10}; do
        if kubectl exec -n $NAMESPACE deployment/printernizer-backend -- curl -f http://localhost:8000/api/v1/health; then
            success "Backend health check passed"
            break
        else
            warn "Health check attempt $i failed, retrying..."
            sleep 10
        fi
        
        if [ $i -eq 10 ]; then
            error "Health check failed after 10 attempts"
        fi
    done
    
    # Check frontend
    if kubectl exec -n $NAMESPACE deployment/printernizer-frontend -- curl -f http://localhost/health; then
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
    fi
}

# Database migration
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    kubectl wait --for=condition=ready pod -l app=printernizer-backend -n $NAMESPACE --timeout=120s
    
    # Run migration job
    kubectl run migration-job --image=ghcr.io/porcus3d/printernizer-backend:$VERSION \
        --restart=Never \
        --rm -i --tty \
        --env="DATABASE_PATH=/app/data/printernizer.db" \
        --command -- python -c "
from database.database import Database
import asyncio
async def migrate():
    db = Database()
    await db.initialize()
    await db.run_migrations()
    print('Migrations completed')
asyncio.run(migrate())
"
    
    success "Database migrations completed"
}

# Rollback function
rollback() {
    local version=$1
    warn "Rolling back to version: $version"
    
    kubectl set image deployment/printernizer-backend printernizer-backend=ghcr.io/porcus3d/printernizer-backend:$version -n $NAMESPACE
    kubectl set image deployment/printernizer-frontend printernizer-frontend=ghcr.io/porcus3d/printernizer-frontend:$version -n $NAMESPACE
    
    kubectl rollout status deployment/printernizer-backend -n $NAMESPACE
    kubectl rollout status deployment/printernizer-frontend -n $NAMESPACE
    
    success "Rollback completed"
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove old ReplicaSets
    kubectl delete replicaset -n $NAMESPACE -l app=printernizer-backend --cascade=orphan | grep -v "no resources found" || true
    kubectl delete replicaset -n $NAMESPACE -l app=printernizer-frontend --cascade=orphan | grep -v "no resources found" || true
    
    # Cleanup old pods
    kubectl delete pod -n $NAMESPACE --field-selector=status.phase!=Running | grep -v "no resources found" || true
    
    success "Cleanup completed"
}

# Main deployment function
deploy() {
    log "Starting Printernizer deployment to $ENVIRONMENT environment"
    log "Version: $VERSION"
    log "Namespace: $NAMESPACE"
    log "Dry run: $DRY_RUN"
    
    check_prerequisites
    build_images
    deploy_infrastructure
    deploy_application
    run_migrations
    wait_for_deployment
    health_check
    cleanup
    
    success "Printernizer deployment completed successfully!"
    
    # Display access information
    log "Access Information:"
    kubectl get ingress -n $NAMESPACE
    kubectl get services -n $NAMESPACE
}

# Command line handling
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "rollback")
        if [ -z "$2" ]; then
            error "Rollback requires a version parameter"
        fi
        rollback $2
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "check")
        check_prerequisites
        ;;
    *)
        echo "Usage: $0 {deploy|rollback <version>|health|cleanup|check}"
        echo ""
        echo "Commands:"
        echo "  deploy                 Full deployment"
        echo "  rollback <version>     Rollback to specific version"
        echo "  health                 Run health checks"
        echo "  cleanup               Clean up old resources"
        echo "  check                 Check prerequisites"
        echo ""
        echo "Environment Variables:"
        echo "  ENVIRONMENT           Deployment environment (default: production)"
        echo "  VERSION               Image version (default: latest)" 
        echo "  DRY_RUN               Dry run mode (default: false)"
        exit 1
        ;;
esac