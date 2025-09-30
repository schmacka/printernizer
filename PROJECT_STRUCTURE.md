# Printernizer - Project Structure Documentation

**Professional 3D Printer Management System for Bambu Lab A1 and Prusa Core One**

Enterprise-grade fleet management with real-time monitoring, automated file handling, and business analytics. Perfect for 3D printing services, educational institutions, and production environments.

---

## 📋 Project Overview

### Core Purpose
Printernizer is a complete production-ready 3D printer management system that provides:
- Real-time printer monitoring via MQTT & HTTP APIs
- Unified file management with automated downloads
- Professional business interface with German compliance
- WebSocket real-time updates and live dashboards
- Enterprise deployment with Docker & Kubernetes support

### Target Environment
- **Business**: Porcus3D, Kornwestheim, Germany
- **Compliance**: German GDPR, business regulations, VAT (19%)
- **Timezone**: Europe/Berlin
- **Currency**: EUR
- **Language**: German interface with English code documentation

---

## 🏗️ Architecture Overview

### Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLite, WebSockets
- **Frontend**: HTML/CSS/JavaScript with responsive design
- **Database**: SQLite with business compliance schema
- **Infrastructure**: Docker, Kubernetes, Nginx, Redis, Prometheus
- **Deployment**: GitHub Actions CI/CD, automated deployment
- **Monitoring**: Grafana dashboards, structured logging, metrics

### Core Components
- **Backend API**: FastAPI application with 47+ REST endpoints
- **Frontend**: Nginx-served responsive web interface
- **Database**: SQLite with German business compliance schema
- **Monitoring**: Prometheus + Grafana for metrics
- **Caching**: Redis cluster for sessions and background tasks
- **Load Balancing**: Kubernetes ingress with SSL termination
- **Backup System**: Automated daily backups with S3 integration

---

## 📁 Directory Structure

```
printernizer/
├── 📄 Core Configuration Files
│   ├── README.md                 # Main project documentation
│   ├── requirements.txt          # Python dependencies
│   ├── requirements-test.txt     # Testing dependencies
│   ├── pytest.ini              # Test configuration
│   ├── database_schema.sql      # Database schema definition
│   ├── run.bat / run.sh         # Quick start scripts
│   ├── production-readiness-check.sh  # Deployment validation
│   └── CHANGELOG.md             # Version history
│
├── 🔧 Configuration & Settings
│   └── config/
│       ├── printers.json        # Printer configurations
│       ├── printers.example.json
│       ├── german-compliance.yml # German business settings
│       └── file-storage.yml     # File management config
│
├── 💻 Source Code
│   └── src/
│       ├── main.py              # Application entry point
│       ├── api/                 # REST API endpoints
│       │   └── routers/         # API route handlers
│       │       ├── health.py    # System health checks
│       │       ├── printers.py  # Printer management
│       │       ├── jobs.py      # Job monitoring
│       │       ├── files.py     # File operations
│       │       ├── analytics.py # Business analytics
│       │       ├── websocket.py # Real-time updates
│       │       ├── settings.py  # Configuration
│       │       ├── debug.py     # Debugging tools
│       │       ├── ideas.py     # Model discovery
│       │       └── ...
│       ├── models/              # Data models
│       │   ├── printer.py       # Printer data model
│       │   ├── job.py          # Print job model
│       │   ├── file.py         # File management model
│       │   ├── material.py     # Material management
│       │   └── ...
│       ├── services/            # Business logic
│       │   ├── printer_service.py      # Printer operations
│       │   ├── file_service.py         # File management
│       │   ├── job_service.py          # Job tracking
│       │   ├── analytics_service.py    # Business analytics
│       │   ├── config_service.py       # Configuration
│       │   ├── event_service.py        # Event handling
│       │   ├── bambu_ftp_service.py    # Bambu file access
│       │   ├── monitoring_service.py   # System monitoring
│       │   └── ...
│       ├── printers/            # Printer integrations
│       │   ├── base.py          # Base printer interface
│       │   ├── bambu_lab.py     # Bambu Lab integration
│       │   └── prusa.py         # Prusa integration
│       ├── database/            # Database layer
│       ├── integrations/        # External integrations
│       └── utils/               # Utility functions
│
├── 🌐 Frontend
│   └── frontend/
│       ├── index.html           # Main application
│       ├── debug.html           # Debug interface
│       ├── css/                 # Stylesheets
│       │   ├── main.css         # Core styles
│       │   ├── dashboard.css    # Dashboard styling
│       │   └── components.css   # Component styles
│       ├── js/                  # JavaScript modules
│       ├── assets/              # Images, icons, fonts
│       └── images/              # UI graphics
│
├── 🗄️ Data & Storage
│   ├── data/
│   │   ├── printernizer.db      # Main SQLite database
│   │   ├── logs/                # Application logs
│   │   └── thumbnails/          # File thumbnails
│   └── downloads/               # Downloaded print files
│
├── 🧪 Testing
│   └── tests/
│       ├── conftest.py          # Test configuration
│       ├── run_essential_tests.py  # Test runner
│       ├── test_essential_models.py     # Model tests
│       ├── test_essential_config.py     # Config tests
│       ├── test_essential_integration.py # Integration tests
│       ├── README_ESSENTIAL.md   # Test documentation
│       └── backend/             # Backend-specific tests
│
├── 📚 Documentation
│   └── docs/
│       ├── api_specification.md  # API documentation
│       ├── PRODUCTION_DEPLOYMENT.md # Deployment guide
│       ├── TESTING_GUIDE.md     # Testing procedures
│       ├── DEBUG_PROCEDURES.md  # Troubleshooting
│       ├── data_models.md       # Database documentation
│       ├── THUMBNAILS.md        # File handling
│       ├── development/         # Development guides
│       ├── deployment/          # Deployment configs
│       ├── features/            # Feature documentation
│       └── user-guide/          # User documentation
│
├── 🚀 Deployment
│   ├── docker/                  # Docker configurations
│   │   ├── entrypoint.sh        # Container startup
│   │   ├── nginx.conf           # Nginx configuration
│   │   └── default.conf         # Default server config
│   ├── monitoring/              # Monitoring setup
│   │   ├── prometheus.yml       # Metrics collection
│   │   └── grafana/             # Dashboard configs
│   ├── scaling/                 # Kubernetes configs
│   │   ├── load-balancer.yml    # Load balancing
│   │   └── websocket-lb.yml     # WebSocket load balancing
│   ├── backup/                  # Backup configurations
│   └── migrations/              # Database migrations
│
├── 🔒 Security & Compliance
│   └── security/
│       ├── gdpr-compliance.md   # GDPR documentation
│       ├── security-policy.yml  # Security policies
│       └── printer-credentials.yml # Credential management
│
└── 🛠️ Development Tools
    └── scripts/
        ├── debug_bambu_ftp.py   # Bambu debugging
        ├── test_bambu_credentials.py # Connection testing
        ├── download_bambu_files.py  # File operations
        └── README.md            # Script documentation
```

---

## 🎯 Core Features & Modules

### 1. Printer Management (`src/printers/`)
- **Base Interface**: Common printer abstraction
- **Bambu Lab Integration**: MQTT-based real-time monitoring
- **Prusa Integration**: HTTP API via PrusaLink
- **Multi-printer Support**: Simultaneous monitoring
- **Connection Health**: Automatic retry and error handling

### 2. File Management (`src/services/file_service.py`)
- **Unified Downloads**: Automatic file retrieval from printers
- **Thumbnail Generation**: Visual file previews
- **File Organization**: Structured storage system
- **Status Tracking**: Download progress and error handling
- **German Filename Support**: Umlaut and special character handling

### 3. Job Monitoring (`src/services/job_service.py`)
- **Real-time Status**: Live job progress tracking
- **Layer Progress**: Detailed printing progress
- **Time Estimates**: Completion time calculations
- **Error Detection**: Print failure identification
- **Business Analytics**: German business reporting

### 4. WebSocket Real-time Updates (`src/api/routers/websocket.py`)
- **Live Dashboard**: Real-time status updates
- **Printer Status**: Instant status changes
- **Job Progress**: Live printing progress
- **File Operations**: Download status updates
- **Connection Management**: Automatic reconnection

### 5. Business Analytics (`src/services/analytics_service.py`)
- **German Business Compliance**: VAT calculations, business reporting
- **Material Cost Tracking**: Cost analysis per print
- **Power Consumption**: Energy usage monitoring
- **Business vs Private**: Job classification
- **Customer Analytics**: Print statistics

### 6. Configuration Management (`src/services/config_service.py`)
- **Printer Configuration**: Connection settings
- **German Business Settings**: VAT rates, timezone, currency
- **File Storage Configuration**: Download paths, naming
- **System Settings**: Monitoring intervals, thresholds

---

## 🗄️ Database Schema

### Core Tables
- **printers**: Printer configurations and status
- **jobs**: Print job tracking and progress
- **files**: Downloaded file management
- **materials**: Material definitions and costs
- **snapshots**: Printer status snapshots
- **watch_folders**: File monitoring configuration
- **configuration**: System configuration

### German Business Fields
- **VAT calculations**: 19% German VAT rate
- **Customer classification**: Business vs private
- **Cost tracking**: Material and energy costs
- **Compliance logging**: GDPR audit trails

---

## 🌐 API Endpoints

### System Endpoints
- `GET /api/v1/health` - System health check
- `GET /api/v1/system/info` - System information
- `GET /api/v1/version` - Version information

### Printer Management
- `GET /api/v1/printers` - List all printers
- `POST /api/v1/printers` - Add new printer
- `GET /api/v1/printers/{id}` - Get printer details
- `PUT /api/v1/printers/{id}` - Update printer
- `DELETE /api/v1/printers/{id}` - Remove printer
- `GET /api/v1/printers/{id}/status` - Get printer status

### Job Monitoring
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `POST /api/v1/jobs/{id}/cancel` - Cancel job
- `GET /api/v1/jobs/{id}/progress` - Get job progress

### File Management
- `GET /api/v1/files` - List downloaded files
- `POST /api/v1/files/download` - Download file from printer
- `GET /api/v1/files/{id}` - Get file details
- `DELETE /api/v1/files/{id}` - Delete file

### Business Analytics
- `GET /api/v1/analytics` - Business analytics dashboard
- `GET /api/v1/analytics/costs` - Cost analysis
- `GET /api/v1/analytics/materials` - Material usage
- `GET /api/v1/analytics/export` - Export business data

### WebSocket
- `WS /ws` - Real-time updates connection

---

## 🧪 Testing Strategy

### Essential Tests (Milestone 1.1)
- **Model Validation**: Data model creation and validation
- **German Business Logic**: VAT, currency, timezone tests
- **API Health Checks**: Critical endpoint testing
- **Integration Workflow**: End-to-end printer setup
- **Configuration Tests**: System configuration validation

### Test Structure
```
tests/
├── test_essential_models.py      # Core model validation
├── test_essential_config.py      # German business config
├── test_essential_integration.py # E2E workflow tests
├── backend/test_api_health.py    # API endpoint tests
├── run_essential_tests.py        # Test runner
└── README_ESSENTIAL.md           # Test documentation
```

### Test Execution
```bash
# Run essential tests
python tests/run_essential_tests.py

# With coverage
python tests/run_essential_tests.py --coverage

# Individual test files
pytest tests/test_essential_models.py -v
```

---

## 🚀 Deployment Options

### 1. Local Development
```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# Access: http://localhost:8000
```

### 2. Docker Development
```bash
docker-compose up -d
# Access: http://localhost:3000
```

### 3. Production Deployment
```bash
# Kubernetes production
kubectl apply -f production.yml

# Docker production
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Automated CI/CD
- **GitHub Actions**: Comprehensive testing and deployment
- **Production Deployment**: Automated on tagged releases
- **Rollback Support**: Automatic rollback capabilities
- **Health Checks**: Deployment validation

---

## 🔒 Security & Compliance

### German GDPR Compliance
- **Data Protection by Design**: Privacy-first architecture
- **Right to Erasure**: Data deletion capabilities
- **Data Retention**: Automated cleanup policies
- **Audit Logging**: Comprehensive access logs
- **Consent Management**: Cookie and data consent

### Security Features
- **HTTPS/SSL Enforcement**: End-to-end encryption
- **Security Headers**: OWASP-compliant headers
- **Input Validation**: Comprehensive sanitization
- **Network Policies**: Restricted pod communication
- **Non-root Containers**: Security-hardened deployment

---

## 📈 Monitoring & Observability

### Metrics Collection
- **Prometheus**: System and application metrics
- **Grafana**: Business and technical dashboards
- **Performance Monitoring**: Response times, error rates
- **Resource Usage**: CPU, memory, disk monitoring

### Key Metrics
- **API Response Time**: < 200ms (95th percentile)
- **Error Rate**: < 1% of total requests
- **Printer Connectivity**: Connection status monitoring
- **Database Performance**: Query execution times
- **Business KPIs**: Print success rates, cost analysis

### Logging
- **Structured Logging**: JSON-formatted logs
- **German Business Logs**: Compliance-focused logging
- **Error Tracking**: Centralized error collection
- **Audit Trails**: User action logging

---

## 🛠️ Development Guidelines

### Code Organization
- **Clean Architecture**: Layered service architecture
- **Dependency Injection**: Loosely coupled components  
- **Type Hints**: Full Python type annotations
- **Documentation**: Comprehensive code documentation
- **German Comments**: Business logic in German where appropriate

### Quality Standards
- **Code Style**: Black formatting, consistent naming
- **Testing**: Essential test coverage for core functionality
- **Security**: Input validation, sanitization
- **Performance**: Optimized database queries, caching
- **Accessibility**: German language support, responsive design

### Development Workflow
1. **Feature Development**: Branch-based development
2. **Testing**: Essential tests for core functionality
3. **Code Review**: Quality and security validation
4. **CI/CD Pipeline**: Automated testing and deployment
5. **Production Deployment**: Staged rollout with monitoring

---

## 🎯 Future Roadmap

### Phase 2: Advanced Features
- **Advanced Analytics**: Machine learning insights
- **Mobile App**: iOS/Android companion app
- **Multi-location Support**: Distributed printer management
- **Advanced Scheduling**: Queue management and optimization
- **Integration Ecosystem**: Third-party plugin support

### Technical Improvements
- **Microservices**: Service decomposition for scalability
- **Event Sourcing**: Advanced data consistency
- **Real-time Streaming**: Enhanced WebSocket capabilities
- **AI Integration**: Predictive maintenance and optimization
- **Cloud Integration**: Multi-cloud deployment support

---

## 📞 Support & Resources

### Documentation
- **API Documentation**: `docs/api_specification.md`
- **Deployment Guide**: `docs/PRODUCTION_DEPLOYMENT.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Debug Procedures**: `docs/DEBUG_PROCEDURES.md`

### Development Tools
- **Debug Scripts**: `scripts/` directory
- **Database Tools**: Migration and backup scripts
- **Monitoring Tools**: Prometheus and Grafana configs
- **Test Tools**: Essential test suite

### Business Information
- **Company**: Porcus3D
- **Location**: Kornwestheim, Germany
- **Compliance**: German GDPR, business regulations
- **Support**: sebastian@porcus3d.de

---

**This documentation serves as the central reference for understanding Printernizer's architecture, components, and development practices. It should be updated as the project evolves to maintain accuracy for AI-assisted development and team collaboration.**