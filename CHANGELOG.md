# Changelog

All notable changes to Printernizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-10-02

### Added - Phase 2: Enhanced 3D Model Metadata Display (Issue #43, #45)
- **Enhanced Metadata Display Component** (`frontend/js/enhanced-metadata.js`)
  - Comprehensive metadata viewer with async loading and caching
  - Summary cards showing dimensions, cost, quality score, and object count
  - Detailed sections for physical properties, print settings, materials, costs, quality metrics, and compatibility
  - Smart caching with 5-minute TTL to reduce API calls
  - Loading, error, and empty state handling
  
- **Enhanced Metadata Styles** (`frontend/css/enhanced-metadata.css`)
  - Modern card-based design system with responsive grid layouts
  - Full responsive design support (desktop, tablet, mobile, small mobile)
  - Dark/light theme compatibility with both media query and class-based support
  - Color-coded quality indicators (green/yellow/red)
  - Smooth animations and transitions for better UX
  - Icon system using emoji for universal recognition
  
- **File Browser Integration**
  - Integrated enhanced metadata into file preview modal
  - Non-blocking async metadata loading for better performance
  - Enhanced 3D file preview with comprehensive information display
  
- **Documentation**
  - Comprehensive Phase 2 implementation documentation
  - Integration verification script
  - Test HTML file for component validation

### Changed
- Updated application version to 1.2.0 in health check endpoint
- Modified file preview rendering to include metadata container
- Enhanced files.js with async metadata loading functionality

### Technical Details
- ES6+ JavaScript with async/await patterns
- Responsive CSS Grid layouts with mobile-first approach
- WCAG 2.1 AA accessibility compliance
- Browser compatibility: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## [1.1.6] - Previous Version

### Added
- Project cleanup for public GitHub release
- Comprehensive documentation structure in `docs/`
- GitHub community files (CONTRIBUTING.md, SECURITY.md)
- Professional LICENSE file with dual licensing

### Changed
- Moved development documents to `docs/development/`
- Improved .gitignore with comprehensive exclusions
- Organized project structure for public release

### Removed
- Docker files (temporarily removed - not working)
- Temporary debugging and test files
- Development artifacts and cache files

## [1.0.0] - 2025-09-25

### Added
- **Complete Printer Integration**: Full support for Bambu Lab A1 (MQTT) and Prusa Core One (HTTP API)
- **Real-time Monitoring**: Live printer status, temperatures, and job progress with WebSocket updates
- **Drucker-Dateien System**: Unified file management with one-click downloads from all printers
- **German Business Compliance**: VAT calculations, EUR currency, GDPR compliance, timezone support
- **Professional Web Interface**: Mobile-responsive dashboard with accessibility features
- **Business Analytics**: Cost calculations, material tracking, and export capabilities
- **Job Management**: Complete job tracking with business vs. private categorization
- **File Download System**: Smart organization by printer/date with status tracking
- **WebSocket Real-time Updates**: Live dashboard updates without page refresh
- **Advanced Error Handling**: Comprehensive error tracking and monitoring system
- **Database Management**: SQLite with migrations and optimization
- **API Documentation**: Complete REST API with Swagger/OpenAPI documentation
- **Test Suite**: Comprehensive testing framework for backend and frontend
- **Monitoring Integration**: Prometheus metrics and Grafana dashboards ready
- **Security Features**: GDPR compliance, secure credential storage, input validation

### Core Features Completed
- ✅ FastAPI backend with async SQLite database
- ✅ Bambu Lab A1 integration via MQTT (bambulabs-api)
- ✅ Prusa Core One integration via PrusaLink HTTP API
- ✅ Real-time printer monitoring with 30-second polling
- ✅ File management with automatic discovery and downloads
- ✅ German business interface with VAT and EUR support
- ✅ WebSocket connectivity for live updates
- ✅ Mobile-responsive web interface
- ✅ Business analytics and reporting
- ✅ Professional deployment configuration
- ✅ Comprehensive error handling and logging

### Technical Architecture
- **Backend**: FastAPI with async/await patterns
- **Database**: SQLite with SQLAlchemy ORM and migrations
- **Real-time**: WebSocket integration for live updates
- **Printer APIs**: MQTT (Bambu Lab) and HTTP REST (Prusa)
- **Frontend**: Modern vanilla JavaScript with modular components
- **Testing**: pytest with comprehensive test coverage
- **Documentation**: Sphinx-ready documentation structure

### Business Features
- German language interface and error messages
- VAT calculations with 19% German tax rate
- GDPR-compliant data handling and retention
- EUR currency formatting (1.234,56 €)
- Europe/Berlin timezone support
- Export capabilities for German accounting software
- Business vs. private job classification
- Material cost tracking and reporting

### Deployment Ready
- Production-ready FastAPI application
- Environment-based configuration
- Health check endpoints
- Monitoring and logging integration
- Security headers and CORS protection
- Database migrations and versioning

## Development Phases Completed

### Phase 1: Foundation & Core Infrastructure ✅
- Project setup with proper Python structure
- SQLite database with job-based architecture
- Configuration management system
- Logging and error handling framework

### Phase 2: Printer Integration ✅
- Bambu Lab A1 MQTT integration
- Prusa Core One HTTP API integration
- Real-time status monitoring
- Connection health monitoring and recovery

### Phase 3: File Management System ✅
- Automatic file discovery on both printer types
- One-click download system with progress tracking
- Smart file organization by printer and date
- File status tracking (Available, Downloaded, Local)

### Phase 4: Web Interface Development ✅
- Professional responsive web design
- Real-time dashboard with WebSocket updates
- Intuitive file management interface
- Mobile-first approach with accessibility

### Phase 5: Business & Analytics Features ✅
- German business compliance and localization
- Cost calculation system for materials and power
- Export functionality for accounting software
- Business statistics and performance analytics

## Future Roadmap

### Phase 6: 3D Preview System (Planned)
- STL/3MF/G-Code visualization
- Multiple rendering backends
- Interactive preview interface
- Performance optimization for large files

### Phase 7: Advanced Features (Planned)
- Desktop GUI application
- Home Assistant addon integration
- Advanced monitoring and alerting
- Multi-user authentication system

### Phase 8: Enterprise Features (Planned)
- Role-based access control
- Advanced reporting and analytics
- API rate limiting and quotas
- Enterprise deployment options

---

**Note**: This project has successfully completed all core features and is production-ready for 3D printer fleet management. The system provides enterprise-grade functionality while maintaining ease of use for individual users.

**Status**: ✅ Production Ready - Core features complete and tested