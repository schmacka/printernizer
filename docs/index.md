# Printernizer Documentation

**Professional 3D Printer Management System for Bambu Lab & Prusa Printers**

Enterprise-grade fleet management with real-time monitoring, automated file handling, and business analytics. Perfect for 3D printing services, educational institutions, and production environments.

> **Tested with:** Bambu Lab A1 and Prusa Core One

---

## What is Printernizer?

Printernizer is a **complete production-ready** 3D printer management system that provides:

- **Real-time printer monitoring** - Live status, temperature, and job progress via MQTT & HTTP APIs
- **Unified file management** - Seamless file handling with one-click downloads and status tracking
- **Business-ready interface** - Professional dashboard with compliance features and analytics
- **WebSocket real-time updates** - Live dashboard with instant status updates
- **Enterprise deployment** - Docker, Kubernetes, monitoring, and CI/CD ready
- **Easy setup** - Multiple deployment options with comprehensive documentation

---

## Getting Started

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } **Quick Start**

    ---

    Get Printernizer up and running in 5-10 minutes with our streamlined installation guides.

    [:octicons-arrow-right-24: Installation Guide](getting-started/installation.md)

-   :material-cog:{ .lg .middle } **Configuration**

    ---

    Learn how to configure printers, customize settings, and optimize your setup.

    [:octicons-arrow-right-24: Configuration Reference](getting-started/configuration.md)

-   :material-file-document:{ .lg .middle } **User Guide**

    ---

    Explore features, learn best practices, and master the Printernizer interface.

    [:octicons-arrow-right-24: User Guide](user-guide/index.md)

-   :fontawesome-solid-code:{ .lg .middle } **API Reference**

    ---

    Complete API documentation for developers integrating with Printernizer.

    [:octicons-arrow-right-24: API Reference](api-reference/index.md)

</div>

---

## Key Features

### Printer Support
- **Bambu Lab Printers** - Full MQTT integration with real-time status updates
- **Prusa Printers** - HTTP API integration via PrusaLink
- **OctoPrint** - OctoPrint-managed printers via REST API with SockJS live updates
- **Auto-discovery** - Automatically find printers on your network (SSDP + mDNS)
- **Multi-printer management** - Simultaneous monitoring of multiple printers
- **Connection health monitoring** - Automatic retry and error handling

> **Tested with:** Bambu Lab A1 and Prusa Core One

### Real-time Monitoring
- **Live status updates** - Current printer state, temperatures, progress
- **Job tracking** - Layer-by-layer progress with time estimates
- **WebSocket connectivity** - Instant updates without page refresh
- **Mobile responsive** - Full functionality on phones and tablets

### File Management
- **Unified file browser** - See files from all printers in one place
- **One-click downloads** - Direct download from printer storage
- **Status tracking** - Visual indicators for file availability and download status
- **Smart filtering** - Filter by printer, status, and file type
- **3D preview thumbnails** - Automatic thumbnail generation for STL, 3MF, GCODE, and BGCODE files
- **Intelligent caching** - 30-day cache for fast preview loading

### Business Features
- **Professional dashboard** - Clean, business-ready interface
- **Analytics and reporting** - Usage statistics and performance metrics
- **Customer orders** - Track orders from `new` through to `delivered`, linked to jobs and files
- **Material inventory** - Spool tracking, consumption history, and Excel export
- **GDPR compliance** - Data privacy and retention controls

!!! note "No built-in user accounts"
    Printernizer does not currently ship authentication or role-based access
    control. Restrict access at the network layer, or run it behind Home
    Assistant Ingress, which handles authentication for you.

---

## Deployment Options

**Choose the deployment method that fits your needs:**

=== "Python Standalone"

    Direct Python installation - best for development and testing.

    **Setup time:** 5 minutes

    [Learn More →](deployment/index.md#python-standalone)

=== "Docker"

    Containerized deployment - best for production servers and NAS systems.

    **Setup time:** 5 minutes

    [Learn More →](deployment/index.md)

=== "Home Assistant"

    Integrated with Home Assistant - best for 24/7 operation.

    **Setup time:** 10 minutes

    [Learn More →](deployment/index.md)

=== "Raspberry Pi"

    Quick deployment on Raspberry Pi with automated setup script.

    **Setup time:** 10 minutes

    [Learn More →](deployment/index.md)

---

## Documentation Sections

### For Users

- [**Getting Started**](getting-started/installation.md) - Installation, quick start, and initial configuration
- [**User Guide**](user-guide/index.md) - How to use Printernizer's features
- [**Deployment**](deployment/index.md) - Production deployment options and guides
- [**Troubleshooting**](user-guide/troubleshooting.md) - Common issues and solutions

### For Developers

- [**Architecture**](architecture/index.md) - System design and technical overview
- [**API Reference**](api-reference/index.md) - Complete API documentation
- [**Development**](development/index.md) - Contributing guidelines and development workflow
- [**Testing**](testing/index.md) - Testing guide and coverage reports

### Additional Resources

- [**Features**](features/index.md) - Detailed feature documentation
- [**Changelog**](changelog.md) - Version history and release notes
- [**GitHub Repository**](https://github.com/schmacka/printernizer) - Source code and issues

---

## Current Status: Production Ready

**Core functionality implemented and tested:**

- ✅ Complete backend with FastAPI + async SQLite
- ✅ Professional web interface with mobile-responsive design
- ✅ Full printer integration (Bambu Lab & Prusa manufacturers)
- ✅ Real-time monitoring with WebSocket updates
- ✅ File management and download system
- ✅ 3D preview system (STL, 3MF, GCODE, BGCODE rendering)
- ✅ System optimization (error handling, monitoring, health checks)
- ✅ Business analytics and reporting features
- ✅ Docker containerization (standalone & Home Assistant)
- ✅ Multi-architecture support (x86_64, ARM64, ARMv7)
- ✅ Central library with deduplication, tagging, and metadata extraction
- ✅ Watch folders with per-folder rules and auto-slice
- ✅ Slicer integration (local PrusaSlicer/OrcaSlicer or remote slicer service)
- ✅ Customer orders, material inventory, and multi-channel notifications
- ✅ Browser-based parametric model generator (experimental)

**Coming Soon:**

- 🔄 Kubernetes orchestration
- 🔄 Advanced HA integration (MQTT discovery, sensors, automations)
- 🔄 Authentication and role-based access control

---

## Support & Contributing

- **Report Issues:** [GitHub Issues](https://github.com/schmacka/printernizer/issues)
- **Contribute:** [Contributing Guide](https://github.com/schmacka/printernizer/blob/master/CONTRIBUTING.md)
- **License:** [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0)

---

**Ready to get started?** Head over to the [Installation Guide](getting-started/installation.md) to begin your Printernizer journey!
