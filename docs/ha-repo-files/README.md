# Printernizer - Home Assistant Add-on

[![GitHub Release](https://img.shields.io/github/release/schmacka/printernizer-ha.svg)](https://github.com/schmacka/printernizer-ha/releases)
[![License](https://img.shields.io/github/license/schmacka/printernizer-ha.svg)](https://github.com/schmacka/printernizer-ha/blob/master/LICENSE)

Powerful 3D Printer Management for Home Assistant - Bambu Lab & Prusa printer support.

> **Tested with:** Bambu Lab A1 and Prusa Core One

## ⚠️ Auto-Synced Repository

This repository is **automatically synchronized** from the main [printernizer](https://github.com/schmacka/printernizer) repository.

- **Source Code**: Automatically synced from main repo on every commit
- **HA-Specific Files**: Maintained only in this repository
- **Version Management**: Tied to main repository releases

**Do not modify `src/`, `frontend/`, or `migrations/` directly in this repository** - changes will be overwritten. Contribute to the [main repository](https://github.com/schmacka/printernizer) instead.

---

## About

Printernizer is a powerful 3D print management system designed for managing Bambu Lab and Prusa printers. It provides automated job tracking, file downloads, and business reporting capabilities for 3D printing operations.

### Features

- 🖨️ **Multi-Printer Support**: Manage Bambu Lab and Prusa printers
- 📊 **Job Tracking**: Automatic job monitoring and history
- 📁 **File Management**: Organize and manage your 3D print files
- 📈 **Analytics**: Business reporting and usage statistics
- 🎥 **Timelapses**: Automatic timelapse generation from print jobs
- 🔍 **Discovery**: Automatic printer discovery on your network
- 🌐 **Web Interface**: Beautiful, responsive web UI
- 🏠 **Home Assistant**: Native HA add-on with Ingress support

---

## Installation

### Via Home Assistant Add-on Store

1. Navigate to **Supervisor** → **Add-on Store**
2. Click the menu (⋮) and select **Repositories**
3. Add this repository: `https://github.com/schmacka/printernizer-ha`
4. Find **Printernizer** in the add-on list
5. Click **Install**
6. Configure your printers (see Configuration below)
7. Start the add-on
8. Access via the **Printernizer** panel in your sidebar

### Manual Installation

1. Copy this entire repository to `/addons/printernizer/` in your Home Assistant configuration
2. Restart Home Assistant
3. Navigate to **Supervisor** → **Add-on Store**
4. Click **Reload** to refresh the add-on list
5. Find **Printernizer (local)** and install

---

## Configuration

### Basic Configuration

The add-on can be configured through the Home Assistant UI:

```yaml
log_level: info
timezone: Europe/Berlin
discovery_timeout_seconds: 10
discovery_scan_interval_minutes: 60
timelapse_enabled: true
job_creation_auto_create: true
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `log_level` | Logging level (debug, info, warning, error) | `info` |
| `timezone` | Timezone for timestamps | `Europe/Berlin` |
| `discovery_timeout_seconds` | Printer discovery timeout | `10` |
| `discovery_scan_interval_minutes` | How often to scan for new printers | `60` |
| `timelapse_enabled` | Enable automatic timelapse generation | `true` |
| `timelapse_source_folder` | Source folder for timelapse images | `/data/timelapse-images` |
| `timelapse_output_folder` | Output folder for generated timelapses | `/data/timelapses` |
| `timelapse_output_strategy` | Output strategy (same/separate/both) | `separate` |
| `timelapse_auto_process_timeout` | Auto-process timeout in seconds | `300` |
| `timelapse_cleanup_age_days` | Days to keep old timelapses | `30` |
| `job_creation_auto_create` | Automatically create jobs for new prints | `true` |

### Network Configuration

**Important**: Printer discovery requires `host_network: true` to access multicast traffic (SSDP/mDNS). This is enabled by default but can be disabled in the add-on Network settings if discovery is not needed.

### Adding Printers

After installation, add your printers through the Printernizer web interface:

1. Open the Printernizer panel in Home Assistant
2. Navigate to **Printers** → **Add Printer**
3. Choose your printer type (Bambu Lab or Prusa)
4. Enter connection details:
   - **Bambu Lab**: IP address, access code, serial number
   - **Prusa**: IP address, API key
5. Save and start monitoring

---

## Usage

### Web Interface

Access Printernizer through:
- **Home Assistant Panel**: Click "Printernizer" in your sidebar
- **Direct Access**: `http://homeassistant.local:8000` (if port enabled)
- **Ingress** (recommended): Uses Home Assistant authentication

### Features

- **Dashboard**: Overview of all printers and current jobs
- **Jobs**: Complete job history with filtering and search
- **Files**: Manage your 3D print files
- **Materials**: Track filament usage and costs
- **Analytics**: Business reporting and statistics
- **Timelapses**: View generated timelapses

---

## Data Persistence

All data is stored in `/data/` which is automatically backed up by Home Assistant:

- **Database**: SQLite database with all job and file data
- **Files**: Uploaded and downloaded 3D print files
- **Timelapses**: Generated timelapse videos
- **Configuration**: Printer configurations and settings

### Backup

The add-on supports Home Assistant's backup system:
- **Hot Backup**: Yes (backup while running)
- **Excluded**: Log files and temporary files

---

## Supported Architectures

- `aarch64` (ARM 64-bit)
- `amd64` (x86 64-bit)
- `armv7` (ARM 32-bit)
- `armhf` (ARM hard float)

---

## Support & Documentation

### Documentation

- **Full Documentation**: [Main Repository Docs](https://github.com/schmacka/printernizer#readme)
- **Configuration Guide**: [DOCS.md](DOCS.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

### Getting Help

- **Issues**: Report bugs in the [main repository](https://github.com/schmacka/printernizer/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/schmacka/printernizer/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

### Contributing

Want to contribute? Head over to the [main repository](https://github.com/schmacka/printernizer) and check out the [Contributing Guidelines](https://github.com/schmacka/printernizer/blob/master/CONTRIBUTING.md).

---

## Technical Details

### Repository Structure

```
printernizer-ha/
├── config.yaml          # HA add-on configuration
├── build.yaml           # Multi-architecture build config
├── Dockerfile           # HA-specific Docker build
├── run.sh              # Startup script
├── README.md           # This file
├── DOCS.md             # Detailed documentation
├── CHANGELOG.md        # Version history
├── icon.png            # Add-on icon
├── logo.png            # Logo
├── src/                # 🤖 Auto-synced from main repo
├── frontend/           # 🤖 Auto-synced from main repo
├── migrations/         # 🤖 Auto-synced from main repo
├── database_schema.sql # 🤖 Auto-synced from main repo
└── requirements.txt    # 🤖 Auto-synced from main repo
```

**🤖 Auto-synced files** are automatically updated from the [main repository](https://github.com/schmacka/printernizer).

### Build Process

The add-on is built locally by Home Assistant using the provided `Dockerfile`. No pre-built images are used, ensuring compatibility with all architectures.

### Version Management

Versions in this repository are automatically synchronized from the main repository:
- **Master branch**: Production versions (e.g., `2.8.4`)
- **Development branch**: Development versions (e.g., `2.8.4-dev`)
- **Tags**: Release tags are synchronized automatically

---

## License

**Free for private use.** Commercial/professional use requires a license.

See the [main repository](https://github.com/schmacka/printernizer#-license) for full licensing details.

---

## Acknowledgments

- **Bambu Lab**: For creating excellent 3D printers
- **Prusa Research**: For the Prusa Core One and open-source contributions
- **Home Assistant**: For the amazing smart home platform
- **Contributors**: Everyone who has contributed to this project

---

**Main Repository**: https://github.com/schmacka/printernizer
**HA Add-on Repository**: https://github.com/schmacka/printernizer-ha
**Author**: [@schmacka](https://github.com/schmacka)

---

*This is an auto-synced repository. Source code changes should be made in the [main repository](https://github.com/schmacka/printernizer).*
