# Changelog - Printernizer Home Assistant Add-on

All notable changes to the Printernizer Home Assistant Add-on will be documented in this file.

## [2.0.21] - 2025-10-27

### Changed
- Version bump for maintenance release

## [2.0.20] - 2025-10-27

### Fixed
- **Critical Frontend Connection Fix**: Corrected API URL construction for Home Assistant Ingress mode
- Frontend now uses simple relative paths (`/api/v1`) instead of preserving Ingress prefix
- WebSocket connections also fixed to use simple relative paths
- Frontend can now successfully connect to backend when accessed through HA Ingress

### Technical Details
- **Root Cause**: Previous fix (2.0.17) incorrectly preserved the Ingress path prefix in API calls
  - Frontend was building: `/api/hassio_ingress/<uuid>/api/v1/...`
  - But HA Ingress automatically strips `/api/hassio_ingress/<uuid>/` before forwarding
  - Backend was receiving broken paths and returning 404 errors
- **Solution**: Use simple relative paths (`/api/v1` and `/ws`) in Ingress mode
  - HA Ingress handles the proxy prefix stripping automatically
  - No need to preserve or reconstruct the Ingress path in frontend code
- **Impact**: All API calls and WebSocket connections now work correctly through HA Ingress
- This completes the frontend connection fixes from 2.0.17-2.0.19

## [2.0.19] - 2025-10-26

### Fixed
- **Critical Ingress Security Fix**: Removed overly restrictive IP check that was blocking frontend connections
- Frontend can now connect to backend when accessed through Home Assistant Ingress
- Ingress middleware now trusts HA's built-in authentication instead of doing redundant IP filtering

### Changed
- Simplified Ingress security model to trust Home Assistant's authentication layer
- Removed 172.30.32.0/24 IP restriction that was incompatible with HA Ingress proxy architecture
- Added debug logging for Ingress requests (when debug level enabled)

### Technical Details
- **Root Cause**: Previous IP restriction (172.30.32.0/24) blocked legitimate Ingress-proxied requests
- **Solution**: Home Assistant Ingress already handles authentication and security before forwarding to add-on
- No additional IP filtering needed - HA's Ingress provides sufficient security
- This completes the frontend connection fixes from 2.0.16-2.0.17

## [2.0.18] - 2025-10-26

### Changed
- Version bump for maintenance release

## [2.0.17] - 2025-10-26

### Fixed
- **Critical Frontend Connection Fix**: Completely rewrote API path detection to properly support Home Assistant Ingress
- Frontend now correctly preserves Ingress base path when making API requests
- Fixed API URL construction to use relative paths including Ingress prefix (e.g., `/api/hassio_ingress/<uuid>/api/v1`)
- All frontend modules now connect properly through HA proxy

### Added
- **Comprehensive Debug Logging**: Added debug mode for troubleshooting connection issues
  - Enable with `?debug=true` in URL or `localStorage.setItem('printernizer_debug', 'true')` in console
  - Access debug info via `window.PrinternizerDebug.getConfig()` in browser console
  - Logs show detected paths, base URLs, and deployment mode

### Technical Details
- **Root Cause**: Previous implementation used absolute paths (`/api/v1`) which bypassed HA Ingress proxy
- **Solution**: Now extracts base path from `window.location.pathname` to preserve Ingress prefix
- **Path Detection**:
  - HA Ingress: `/api/hassio_ingress/<uuid>/` → API at `/api/hassio_ingress/<uuid>/api/v1`
  - Direct access: Port 8000 → API at `http://host:8000/api/v1`
- **WebSocket**: Updated to use same path detection logic for consistency
- **Debug utilities**: Browser console tools for configuration inspection

## [2.0.16] - 2025-10-26

### Fixed
- **Ideas API connection**: Fixed ideas.js module using hardcoded API URL that broke Home Assistant Ingress mode
- Ideas/bookmarks/trending features now properly connect through Ingress proxy
- Ideas module now uses centralized API configuration like all other modules

### Technical Details
- Replaced hardcoded port 8000 URL with CONFIG.API_BASE_URL
- Ensures proper relative path handling in HA Ingress mode
- Maintains compatibility with standalone and Docker deployments
- Completes the frontend connection fix for all frontend modules

## [2.0.15] - 2025-10-26

### Changed
- Version bump for maintenance release

## [2.0.14] - 2025-10-26

### Changed
- Version bump for maintenance release

## [2.0.13] - 2025-10-26

### Fixed
- **WebSocket URL construction**: Fixed WebSocket connection URL construction for Home Assistant Ingress
- WebSocket now correctly connects through Ingress proxy with proper URL handling
- Resolved connection issues when accessing add-on via Home Assistant UI

### Technical Details
- Improved WebSocket URL generation to handle Ingress path routing
- Ensures real-time updates work correctly in Ingress mode
- No changes to standalone deployment modes

## [2.0.12] - 2025-10-25

### Fixed
- **Frontend static file serving**: Fixed frontend not displaying correctly via Home Assistant Ingress
- Static files now mounted at root path instead of `/static` for proper resource loading
- Browser can now correctly load CSS, JavaScript, and assets from relative paths
- API routes preserved through proper registration order

### Technical Details
- Changed static file mount from `/static` to `/` with `html=True` parameter
- Ensures API routes registered with `/api/v1` prefix take precedence
- Frontend resources (css/, js/, assets/) now accessible from root paths
- Maintains Home Assistant Ingress double-slash handling compatibility

## [2.0.11] - 2025-10-24

### Fixed
- Minor improvements to Ingress compatibility

## [2.0.10] - 2025-10-24

### Fixed
- **Critical Ingress routing fix**: Added route handler for double-slash (`//`) path
- Fixed 404 error when accessing add-on via Home Assistant Ingress
- Home Assistant Ingress was forwarding requests to `//` instead of `/`

### Technical Details
- Added `@app.get("//")` route handler to serve frontend for double-slash requests
- This is a known Home Assistant Ingress behavior where trailing slashes in ingress paths result in double slashes
- No changes to application functionality - routing fix only

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
