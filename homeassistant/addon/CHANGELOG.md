# Changelog - Printernizer Home Assistant Add-on

All notable changes to this Home Assistant add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-05

### Added
- 🎉 Initial release of Printernizer Home Assistant Add-on
- 🖨️ **Multi-Printer Support**: Bambu Lab A1 and Prusa Core One integration
- 🏠 **Home Assistant Integration**: Full MQTT discovery and device integration
- 📊 **Real-time Monitoring**: Live status updates via WebSocket
- 🇩🇪 **German Business Features**: VAT calculations, EUR currency, GDPR compliance
- 📁 **File Management**: Automatic printer file discovery and download
- 📈 **Analytics & Export**: Business reporting with Excel/CSV export
- 🌐 **Web Interface**: Professional responsive web UI
- 🔒 **Security**: Non-root container execution, health checks
- 📦 **Multi-Architecture**: Support for armhf, armv7, aarch64, amd64, i386

### Features
#### Printer Integration
- **Bambu Lab A1**: MQTT real-time communication
- **Prusa Core One**: HTTP API polling integration  
- **Status Monitoring**: Temperature, progress, job tracking
- **Connection Management**: Automatic reconnection and error handling

#### Home Assistant Entities
- Status sensors with device class support
- Temperature sensors (bed/nozzle) with °C units
- Progress tracking with percentage values
- Material usage and cost tracking in EUR
- Timestamp sensors for job completion
- Device registry integration with proper manufacturer info

#### Business Features
- German timezone support (Europe/Berlin)
- Configurable VAT rate (default 19%)
- EUR currency for all cost calculations
- GDPR-compliant data handling
- Business vs. private job categorization
- Material consumption tracking

#### File Management
- Automatic printer file detection
- Unified file listing (local + printer files)
- One-click download functionality
- Smart organization by printer/date
- File status tracking (📁 Available, ✓ Downloaded, 💾 Local)
- Download progress monitoring

#### Web Interface  
- Mobile-responsive design
- Real-time dashboard updates
- Printer status overview
- File management interface
- Business analytics and reports
- Configuration management panel

### Technical Details
#### Container Architecture
- Multi-stage Docker build for optimization
- Alpine Linux base with Python 3.11
- S6-overlay for service management
- Non-root user execution
- Health check endpoints

#### Data Persistence
- SQLite database for job tracking
- Persistent storage mapping to `/data`
- Automatic database initialization
- Configuration backup support

#### Network & Security  
- HTTP API on port 8000
- WebSocket support for real-time updates
- CORS configuration for multi-origin support
- MQTT integration with Home Assistant broker
- Printer network discovery and validation

### Configuration
#### Add-on Options
- Timezone configuration (default: Europe/Berlin)  
- Logging level selection (debug, info, warning, error, critical)
- CORS origins specification
- Printer polling interval (10-300 seconds)
- Concurrent download limits (1-10)
- WebSocket enable/disable
- German business compliance settings
- Multi-printer configuration array

#### Environment Integration
- Home Assistant addon configuration schema
- MQTT service auto-detection
- Persistent volume mapping
- Health check integration
- Watchdog monitoring

### Dependencies
#### Python Packages
- FastAPI 0.104.1 - Web framework
- Uvicorn 0.24.0 - ASGI server  
- AsyncIO-MQTT 0.13.0 - MQTT client
- Aiosqlite 0.19.0 - Async SQLite
- Pydantic 2.5.0 - Data validation
- Structlog 23.2.0 - Structured logging
- WebSockets 12.0 - Real-time communication
- HTTPX 0.25.2 - HTTP client
- Redis 5.0.1 - Caching support

#### System Dependencies
- SQLite3 - Database engine
- Curl - Health checks
- Python 3.11 - Runtime environment
- TZData - Timezone support

### Documentation
- Comprehensive installation guide
- Configuration examples for both printer types
- Troubleshooting section
- Home Assistant entity documentation
- API endpoint documentation

### Quality Assurance
- Multi-architecture build support
- Health check implementation
- Proper logging and error handling
- Configuration validation
- Service dependency management

---

## [Unreleased] - Future Enhancements

### Planned Features
- 📱 **Mobile App**: Dedicated iOS/Android companion app
- 🎨 **3D Preview**: STL/3MF file visualization  
- 🔔 **Advanced Notifications**: Email, Slack, Discord integration
- 📊 **Advanced Analytics**: Machine learning insights
- 🌍 **Multi-Language**: German, English, French interface
- 🏭 **Enterprise Features**: Multi-tenant support
- 🔐 **Authentication**: User management and access control
- 📡 **Cloud Sync**: Cross-device synchronization

### Under Consideration
- Integration with other slicer software (Cura, SuperSlicer)
- Support for additional printer brands (Ultimaker, Creality)
- Advanced material tracking with QR codes
- Integration with inventory management systems
- Custom dashboard widgets for Home Assistant
- Voice control integration (Google Assistant, Alexa)

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) format. For development updates and technical details, see the main project repository.

**Printernizer Add-on for Home Assistant**  
Developed by [Porcus3D](https://porcus3d.de) - Professional 3D Printing Services  
Kornwestheim, Germany 🇩🇪