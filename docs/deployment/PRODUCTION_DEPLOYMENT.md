# Printernizer Production Deployment Guide

## Overview

This document provides comprehensive instructions for deploying Printernizer Phase 1 to production. Printernizer is a professional 3D print management system built for Porcus3D's German 3D printing service in Kornwestheim, featuring enterprise-grade monitoring, GDPR compliance, and high availability.

## 🏗️ Architecture Summary

### Core Components
- **Backend API**: FastAPI application with 47 REST endpoints
- **Frontend**: Nginx-served responsive web interface with WebSocket support
- **Database**: SQLite with German business compliance schema
- **Monitoring**: Prometheus + Grafana for metrics and dashboards
- **Caching**: Redis cluster for session management and background tasks
- **Load Balancing**: Kubernetes ingress with SSL termination
- **Backup System**: Automated daily backups with S3 integration

### Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLite, bambulabs-api
- **Frontend**: HTML/CSS/JavaScript with WebSocket real-time updates
- **Infrastructure**: Docker, Kubernetes, Nginx, Redis, Prometheus
- **Deployment**: GitHub Actions CI/CD, Kubernetes manifests
- **Monitoring**: Grafana dashboards, structured logging, error tracking

## 🚀 Quick Start Deployment

### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured with cluster access
- Docker with registry access (GitHub Container Registry)
- German hosting provider for GDPR compliance

### 1. Clone and Configure
```bash
git clone https://github.com/porcus3d/printernizer.git
cd printernizer

# Copy and customize environment configuration
cp .env.example .env
# Edit .env with your production values
```

### 2. Deploy with Automated Script
```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh deploy

# Monitor deployment
kubectl get pods -n printernizer --watch
```

### 3. Verify Deployment
```bash
# Run health checks
./deploy.sh health

# Access application
kubectl get ingress -n printernizer
```

## 📋 Detailed Deployment Steps

### Step 1: Environment Preparation

#### 1.1 Kubernetes Cluster Setup
```bash
# Create namespace
kubectl create namespace printernizer

# Apply security policies
kubectl apply -f security/security-policy.yml

# Configure RBAC
kubectl apply -f security/rbac.yml
```

#### 1.2 Secrets Configuration
```bash
# Create production secrets
kubectl create secret generic printernizer-secrets \
  --from-literal=SECRET_KEY="your-production-secret-key" \
  --from-literal=SENTRY_DSN="your-sentry-dsn" \
  -n printernizer

# Create backup credentials
kubectl create secret generic backup-secrets \
  --from-literal=aws-access-key="your-aws-key" \
  --from-literal=aws-secret-key="your-aws-secret" \
  --from-literal=s3-bucket="printernizer-backups" \
  -n printernizer
```

### Step 2: Infrastructure Deployment

#### 2.1 Monitoring Stack
```bash
# Deploy Prometheus
kubectl apply -f monitoring/prometheus.yml

# Deploy Grafana with preconfigured dashboards
kubectl apply -f monitoring/grafana/

# Verify monitoring deployment
kubectl get pods -n printernizer -l app=prometheus
```

#### 2.2 Redis Cluster
```bash
# Deploy Redis for caching and sessions
kubectl apply -f scaling/load-balancer.yml

# Verify Redis cluster
kubectl exec -it redis-cluster-0 -n printernizer -- redis-cli cluster info
```

#### 2.3 Backup System
```bash
# Deploy automated backup jobs
kubectl apply -f backup/backup-system.yml

# Verify backup CronJobs
kubectl get cronjobs -n printernizer
```

### Step 3: Application Deployment

#### 3.1 Build and Push Images
```bash
# Build backend image
docker build -t ghcr.io/porcus3d/printernizer-backend:v1.0.0 .

# Build frontend image  
docker build -t ghcr.io/porcus3d/printernizer-frontend:v1.0.0 -f Dockerfile.frontend .

# Push to registry
docker push ghcr.io/porcus3d/printernizer-backend:v1.0.0
docker push ghcr.io/porcus3d/printernizer-frontend:v1.0.0
```

#### 3.2 Deploy Application
```bash
# Apply main application configuration
kubectl apply -f production.yml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/printernizer-backend -n printernizer
kubectl wait --for=condition=available --timeout=300s deployment/printernizer-frontend -n printernizer
```

#### 3.3 Database Initialization
```bash
# Run database migration
kubectl run migration-job --image=ghcr.io/porcus3d/printernizer-backend:v1.0.0 \
  --restart=Never --rm -i --tty \
  --env="DATABASE_PATH=/app/data/printernizer.db" \
  --command -- python -c "
from database.database import Database
import asyncio
async def init():
    db = Database()
    await db.initialize()
    print('Database initialized')
asyncio.run(init())
"
```

### Step 4: SSL and Domain Configuration

#### 4.1 SSL Certificate Setup
```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Configure Let's Encrypt issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: sebastian@porcus3d.de
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

#### 4.2 Domain Configuration
```bash
# Update DNS records to point to your cluster
# A record: printernizer.porcus3d.de -> [EXTERNAL-IP]

# Verify SSL certificate
kubectl describe certificate printernizer-tls -n printernizer
```

## 📊 Monitoring and Observability

### Grafana Dashboard Access
- URL: `http://[GRAFANA-EXTERNAL-IP]:3000`
- Default credentials: admin/admin123!
- Dashboards: Printernizer Overview, API Performance, Business Metrics

### Key Metrics to Monitor
- **API Response Time**: < 200ms for 95th percentile
- **Error Rate**: < 1% of total requests
- **Database Performance**: Query execution time
- **Printer Connectivity**: Connection status and response times
- **Memory Usage**: Container memory consumption
- **CPU Utilization**: Average below 70%

### Log Aggregation
```bash
# View application logs
kubectl logs -f deployment/printernizer-backend -n printernizer

# View nginx access logs
kubectl logs -f deployment/printernizer-frontend -n printernizer

# View all logs with labels
kubectl logs -l app=printernizer-backend -n printernizer --tail=100
```

## 🔒 Security and GDPR Compliance

### Security Features Implemented
- **Network Policies**: Restricted pod-to-pod communication
- **Pod Security Standards**: Non-root containers, read-only filesystem
- **RBAC**: Least-privilege access controls
- **SSL/TLS**: End-to-end encryption with Let's Encrypt certificates
- **Security Headers**: OWASP-compliant HTTP security headers
- **Input Validation**: Comprehensive request validation and sanitization

### GDPR Compliance Features
- **Data Retention**: Automatic data cleanup after retention periods
- **Right to Erasure**: API endpoints for data deletion
- **Data Portability**: Export functionality for customer data
- **Consent Management**: Cookie consent and opt-out mechanisms
- **Audit Logging**: Comprehensive access and modification logs
- **Privacy by Design**: Default privacy settings and data minimization

### Compliance Verification
```bash
# Check data retention policies
kubectl describe cronjob data-cleanup -n printernizer

# Verify backup encryption
kubectl logs cronjob/database-backup -n printernizer

# Review audit logs
kubectl exec deployment/printernizer-backend -n printernizer -- \
  tail -n 100 /app/logs/audit.log
```

## 🔄 Backup and Recovery

### Automated Backup Schedule
- **Database Backup**: Every 6 hours
- **File Backup**: Daily at 2 AM (Europe/Berlin)
- **Configuration Backup**: Weekly
- **Retention Policy**: 30 days local, 7 years S3

### Manual Backup
```bash
# Create immediate backup
kubectl create job --from=cronjob/database-backup manual-backup-$(date +%Y%m%d) -n printernizer

# Verify backup completion
kubectl get jobs -n printernizer
```

### Recovery Procedures
```bash
# List available backups
kubectl exec deployment/printernizer-backend -n printernizer -- \
  ls -la /app/backups/

# Restore from backup
kubectl run restore-job --image=ghcr.io/porcus3d/printernizer-backend:v1.0.0 \
  --restart=Never --rm -i --tty \
  --command -- /scripts/restore-database.sh backup_filename.db.gz
```

## 📈 Performance Optimization

### Auto-scaling Configuration
- **HPA**: 2-10 replicas based on CPU/memory usage
- **VPA**: Automatic resource request adjustments  
- **Cluster Autoscaler**: Node scaling based on pod requirements

### Performance Tuning
```bash
# Monitor resource usage
kubectl top pods -n printernizer

# Scale manually if needed
kubectl scale deployment printernizer-backend --replicas=5 -n printernizer

# Check autoscaling status
kubectl get hpa -n printernizer
```

### Database Performance
- **Connection Pooling**: 20 connections with 10 overflow
- **Query Optimization**: Indexed queries for common operations
- **Cache Strategy**: Redis caching for frequently accessed data

## 🔧 Maintenance Operations

### Regular Maintenance Tasks

#### Weekly
```bash
# Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces --field-selector=status.phase!=Running

# Review logs for errors
kubectl logs -l app=printernizer-backend -n printernizer --since=168h | grep ERROR

# Update SSL certificates (automatic with cert-manager)
kubectl describe certificate -n printernizer
```

#### Monthly
```bash
# Update container images
kubectl set image deployment/printernizer-backend printernizer-backend=ghcr.io/porcus3d/printernizer-backend:v1.1.0
kubectl set image deployment/printernizer-frontend printernizer-frontend=ghcr.io/porcus3d/printernizer-frontend:v1.1.0

# Clean up old backups
kubectl create job cleanup-old-backups --image=alpine:latest --command -- \
  sh -c "find /backups -name '*.gz' -mtime +30 -delete"

# Review security policies
kubectl get networkpolicies -n printernizer
```

### Emergency Procedures

#### Application Rollback
```bash
# Quick rollback to previous version
kubectl rollout undo deployment/printernizer-backend -n printernizer
kubectl rollout undo deployment/printernizer-frontend -n printernizer

# Rollback to specific version
kubectl rollout history deployment/printernizer-backend -n printernizer
kubectl rollout undo deployment/printernizer-backend --to-revision=3 -n printernizer
```

#### Database Recovery
```bash
# Stop application
kubectl scale deployment printernizer-backend --replicas=0 -n printernizer

# Restore database
kubectl run restore-emergency --image=ghcr.io/porcus3d/printernizer-backend:v1.0.0 \
  --restart=Never --rm -i --tty \
  --command -- /scripts/restore-database.sh [backup_file]

# Restart application
kubectl scale deployment printernizer-backend --replicas=2 -n printernizer
```

## 📞 Support and Troubleshooting

### Common Issues

#### Backend Pod Not Starting
```bash
# Check pod events
kubectl describe pod [pod-name] -n printernizer

# Check logs
kubectl logs [pod-name] -n printernizer --previous

# Check resource constraints
kubectl top pods -n printernizer
```

#### Database Connection Issues
```bash
# Check database pod status
kubectl get pods -l app=printernizer-backend -n printernizer

# Verify database file permissions
kubectl exec deployment/printernizer-backend -n printernizer -- \
  ls -la /app/data/

# Test database connectivity
kubectl exec deployment/printernizer-backend -n printernizer -- \
  python -c "from database.database import Database; import asyncio; asyncio.run(Database().health_check())"
```

#### SSL Certificate Problems
```bash
# Check certificate status
kubectl describe certificate printernizer-tls -n printernizer

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Manual certificate renewal
kubectl delete certificate printernizer-tls -n printernizer
kubectl apply -f production.yml
```

### Support Contacts
- **Technical Support**: sebastian@porcus3d.de
- **System Administrator**: [Admin contact]
- **GDPR/Privacy Officer**: datenschutz@porcus3d.de

### Monitoring Alerts
Configure alerts for:
- Pod restarts > 5 in 10 minutes
- API response time > 1 second
- Error rate > 5%
- Database size > 80% of allocated storage
- SSL certificate expiration < 30 days

## 🎯 Success Criteria

### Deployment Success Indicators
- ✅ All pods running and healthy
- ✅ Health checks passing
- ✅ SSL certificate valid
- ✅ Database migrations complete
- ✅ Backup jobs scheduled and running
- ✅ Monitoring dashboards accessible
- ✅ API endpoints responding correctly
- ✅ WebSocket connections working
- ✅ File upload/download functioning
- ✅ GDPR compliance features active

### Performance Targets
- **Availability**: 99.5% uptime
- **Response Time**: < 200ms for API calls
- **Throughput**: 1000 requests/minute sustained
- **Recovery Time**: < 5 minutes for application restart
- **Backup Recovery**: < 30 minutes for full restore

---

*Deployment Guide Version: 1.0*  
*Last Updated: September 2025*  
*Next Review: October 2025*

For additional support, refer to the [GitHub Issues](https://github.com/porcus3d/printernizer/issues) or contact the Porcus3D technical team.