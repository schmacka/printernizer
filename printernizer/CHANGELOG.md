# Changelog - Printernizer Home Assistant Add-on

All notable changes to the Printernizer Home Assistant Add-on will be documented in this file.

## [2.0.9] - 2025-10-24

### Improved
- **Enhanced startup logging**: Added detailed status messages throughout the startup process
- Clear indicators for each service initialization step with ✓ checkmarks
- "BACKEND READY" message when all backend services are initialized
- "FRONTEND READY" message when frontend routes are configured
- Server configuration display showing host, port, and deployment mode
- Better visibility into Home Assistant Ingress mode activation

### Added
- Step-by-step logging for database initialization and migrations
- Service-by-service startup confirmation messages
- Uvicorn server startup information display
- Warning indicators (⚠) for non-critical failures during startup

### Technical Details
- Enhanced lifespan startup logging with visual separators
- Added logging for: database, migrations, services, file watcher, trending, printers
- Better error distinction between critical and non-critical startup failures
- Improved troubleshooting capabilities through detailed logs

## [2.0.8] - 2025-10-24

### Fixed
- **Critical startup fix**: Added missing CMD directive to Dockerfile to start the application
- Fixed 502 Bad Gateway error when accessing add-on via Home Assistant Ingress
- Moved run.sh to standard location (/) for proper execution by s6-overlay init system

### Technical Details
- Added `CMD ["/run.sh"]` to Dockerfile to ensure application starts correctly
- Relocated run.sh from /usr/bin/ to / (root) following HA add-on best practices
- No changes to application functionality - deployment fix only

## [2.0.2] - 2025-10-23

### Fixed
- **Critical build fix**: Replaced symlinks with actual file copies in add-on directory
- Resolved Docker build error "too many links" during Home Assistant installation
- Windows Git symlink compatibility issue resolved by copying files directly

### Technical Details
- Removed invalid text-based symlink files (src, frontend, requirements.txt, database_schema.sql)
- Copied actual source files into printernizer/ directory for proper Docker build context
- All files now accessible during Home Assistant add-on build process
- No changes to application functionality - deployment fix only

## [2.0.0] - 2025-10-22

### Added
- 🎉 **Initial Home Assistant Add-on release**
- Multi-architecture support (aarch64, amd64, armv7, armhf)
- Home Assistant Ingress integration for seamless UI access
- Configuration via Home Assistant UI
- Persistent storage in `/data/printernizer/`
- Automatic database initialization
- Health check integration
- WebSocket support for real-time updates
- Bashio integration for HA-native configuration parsing

### Features
- Real-time printer monitoring (Bambu Lab A1 & Prusa Core One)
- Unified file management with one-click downloads
- 3D preview generation for STL, 3MF, G-code files
- Business analytics and reporting
- Job tracking and history
- Temperature monitoring
- Connection health monitoring

### Configuration
- Timezone configuration (default: Europe/Berlin)
- Log level selection (debug, info, warning, error)
- Optional features toggles (3D preview, WebSockets, business reports)
- Multiple printer support with per-printer enable/disable

### Documentation
- Complete installation guide
- Printer setup instructions (Bambu Lab & Prusa)
- Troubleshooting section
- Advanced topics (backup, restore, integration)

### Technical
- Built on Home Assistant base images
- Optimized Alpine Linux with minimal dependencies
- SQLite database with automatic migrations
- Secure Ingress-only access (172.30.32.2)
- Graceful startup and shutdown handling

### Security
- Ingress security enforcement
- Non-root container operation
- Secure credential handling
- Network isolation support

---

## Future Releases

### Planned Features
- MQTT discovery for Home Assistant sensors
- Automation triggers for job completion
- Mobile app notifications
- Dashboard cards for Home Assistant UI
- Multi-user support with HA authentication
- Advanced analytics dashboard
- Cloud backup integration

### Under Consideration
- Printer firmware update notifications
- Material inventory tracking
- Automatic print queue management
- Integration with slicing software
- Print farm management features

---

## Version History

- **2.0.0** - Initial Home Assistant Add-on release (2025-10-22)

---

For complete project changelog, see: [Main CHANGELOG.md](https://github.com/schmacka/printernizer/blob/master/CHANGELOG.md)
