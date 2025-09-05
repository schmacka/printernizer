# Printernizer Home Assistant Add-on

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE.md)

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

Professional 3D print management system for Bambu Lab A1 and Prusa Core One printers with German business features, seamlessly integrated into Home Assistant.

![Printernizer Dashboard](images/dashboard-preview.png)

## About

Printernizer transforms your Home Assistant into a comprehensive 3D printing management hub. Designed specifically for Porcus3D's German 3D printing service, it provides enterprise-grade features while maintaining simplicity for individual users.

### Key Features

🖨️ **Multi-Printer Support**
- Bambu Lab A1 with real-time MQTT communication
- Prusa Core One with HTTP API integration
- Unified dashboard for all your printers

📊 **Real-time Monitoring** 
- Live status updates via WebSocket
- Temperature monitoring (bed/nozzle)
- Print progress tracking
- Job completion notifications

🇩🇪 **German Business Compliance**
- VAT calculations (configurable rate)
- EUR currency support
- German timezone (Europe/Berlin)
- GDPR-compliant data handling

📁 **Smart File Management**
- Automatic printer file discovery
- One-click downloads
- Organized storage by printer/date
- File status tracking

🏠 **Native Home Assistant Integration**
- Automatic MQTT device discovery
- Rich sensor entities for each printer
- Lovelace card compatibility
- Automation-friendly

## Screenshots

### Home Assistant Integration
![Home Assistant Entities](images/ha-entities.png)

### Web Interface  
![Printer Dashboard](images/printer-dashboard.png)
![File Management](images/file-management.png)

## Installation

### Prerequisites
- Home Assistant OS, Home Assistant Supervised, or Home Assistant Container
- MQTT Broker (Mosquitto broker add-on recommended)
- Network access to your 3D printers

### Method 1: Home Assistant Community Store (HACS) - Coming Soon

1. Open HACS in Home Assistant
2. Go to "Integrations" 
3. Search for "Printernizer"
4. Click "Download"
5. Restart Home Assistant

### Method 2: Manual Installation

1. **Add Custom Repository**:
   - Navigate to Settings → Add-ons → Add-on Store
   - Click ⋮ (three dots) → Repositories  
   - Add: `https://github.com/porcus3d/printernizer-addon`

2. **Install Add-on**:
   - Find "Printernizer" in the store
   - Click "Install"
   - Wait for installation to complete

3. **Configure**: See [Configuration](#configuration) section below

4. **Start**: Click "Start" and check logs for any errors

## Configuration

### Basic Setup

```yaml
timezone: Europe/Berlin
log_level: info
printer_polling_interval: 30
enable_websockets: true
business_features:
  enable_german_compliance: true
  vat_rate: 19.0
  currency: EUR
printers:
  - printer_id: "bambu_a1_001"
    name: "Bambu Lab A1" 
    type: "bambu_lab"
    ip_address: "192.168.1.100"
    access_code: "12345678"
    is_active: true
  - printer_id: "prusa_core_001"
    name: "Prusa Core One"
    type: "prusa"
    ip_address: "192.168.1.101"
    api_key: "your_prusa_api_key_here"
    is_active: true
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `timezone` | string | `Europe/Berlin` | Timezone for business operations |
| `log_level` | list | `info` | debug, info, warning, error, critical |
| `printer_polling_interval` | int | `30` | Status polling interval (10-300s) |
| `max_concurrent_downloads` | int | `5` | Max simultaneous downloads (1-10) |
| `enable_websockets` | bool | `true` | Real-time updates |
| `business_features.vat_rate` | float | `19.0` | VAT percentage (0-100) |

### Printer Configuration

#### Bambu Lab A1
```yaml
- printer_id: "unique_id"           # Required: Unique identifier
  name: "Display Name"              # Required: Human-readable name
  type: "bambu_lab"                 # Required: Printer type
  ip_address: "192.168.1.100"      # Required: IP address
  access_code: "12345678"           # Required: 8-digit access code
  serial_number: "01P00A123456789"  # Optional: Serial number
  is_active: true                   # Optional: Enable/disable
```

#### Prusa Core One  
```yaml
- printer_id: "unique_id"           # Required: Unique identifier
  name: "Display Name"              # Required: Human-readable name  
  type: "prusa"                     # Required: Printer type
  ip_address: "192.168.1.101"      # Required: IP address
  api_key: "your_api_key_here"      # Required: PrusaLink API key
  is_active: true                   # Optional: Enable/disable
```

## Home Assistant Entities

Printernizer automatically creates comprehensive sensor entities for each configured printer:

### Status & Control
- **Status**: Current printer state (printing, idle, error, etc.)
- **Progress**: Print completion percentage (0-100%)
- **Current Job**: Name of the currently running print job

### Temperature Monitoring  
- **Bed Temperature**: Heated bed temperature in °C
- **Nozzle Temperature**: Extruder temperature in °C

### Print Information
- **Time Remaining**: Estimated time to completion in minutes
- **Material Used**: Filament consumption in grams
- **Print Cost**: Total cost calculation in EUR

### Job History
- **Last Job**: Timestamp of last completed job

### Example Lovelace Card
```yaml
type: entities
title: 3D Printers
show_header_toggle: false
entities:
  - sensor.printernizer_bambu_a1_001_status
  - sensor.printernizer_bambu_a1_001_progress  
  - sensor.printernizer_bambu_a1_001_bed_temp
  - sensor.printernizer_bambu_a1_001_nozzle_temp
  - sensor.printernizer_bambu_a1_001_current_job
```

## Web Interface

Access the full-featured web interface:
- **Add-on UI**: Click "Open Web UI" button
- **Direct Access**: `http://homeassistant.local:8000`
- **IP Access**: `http://[HA_IP]:8000`

### Web Features
- 📊 Real-time printer dashboard
- 📁 File management with downloads
- 📈 Business analytics and reports  
- ⚙️ Configuration management
- 📱 Mobile-responsive design
- 🔄 Live WebSocket updates

## Supported Printers

### Bambu Lab A1
- ✅ Real-time MQTT communication
- ✅ Temperature monitoring
- ✅ Print progress tracking
- ✅ File management
- ✅ Job history

### Prusa Core One
- ✅ PrusaLink HTTP API
- ✅ Status monitoring
- ✅ File download support
- ✅ Print tracking
- ✅ Temperature sensors

### Coming Soon
- Bambu Lab X1 Carbon
- Prusa MK4/MK3S+
- Ultimaker S3/S5
- Custom printer API support

## Business Features

Perfect for 3D printing services and businesses:

### German Compliance
- 🇩🇪 German timezone (Europe/Berlin)
- 💶 EUR currency calculations
- 📊 VAT handling (configurable rate)
- 🔒 GDPR-compliant data processing
- 📋 Business vs. private job categorization

### Cost Tracking
- Material cost calculations
- Power consumption estimates
- Labor time tracking  
- Profit margin analysis
- Custom pricing models

### Export & Reporting
- 📊 Excel export for accounting
- 📈 CSV reports for analysis
- 📉 Material usage reports  
- 💼 Business analytics dashboard
- 📅 Time-based reporting

## Automation Examples

### Print Completion Notification
```yaml
automation:
  - alias: "3D Print Completed"
    trigger:
      - platform: state
        entity_id: sensor.printernizer_bambu_a1_001_status
        to: "completed"
    action:
      - service: notify.mobile_app
        data:
          message: "🎉 Print job completed on Bambu Lab A1!"
          title: "Printernizer Alert"
```

### Temperature Alert
```yaml
automation:
  - alias: "Printer Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.printernizer_bambu_a1_001_bed_temp
        above: 80
    action:
      - service: notify.home_assistant
        data:
          message: "⚠️ High bed temperature detected: {{ states('sensor.printernizer_bambu_a1_001_bed_temp') }}°C"
```

## Troubleshooting

### Common Issues

**Add-on won't start**
- Check logs for detailed error messages
- Verify printer IP addresses are accessible
- Ensure configuration YAML syntax is valid

**Printers not discovered**  
- Install and start Mosquitto broker add-on
- Enable MQTT integration in Home Assistant
- Check MQTT connection in add-on logs

**Cannot connect to printer**
- Verify network connectivity to printer IP
- Check printer API settings (PrusaLink enabled, correct access codes)
- Review firewall settings

### Debug Logging
Set `log_level: debug` in configuration for verbose logging.

### Support Channels
- 🐛 [GitHub Issues](https://github.com/porcus3d/printernizer/issues)
- 💬 [Home Assistant Community](https://community.home-assistant.io/)
- 📧 [Email Support](mailto:sebastian@porcus3d.de)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development
- **Language**: Python 3.11, TypeScript, HTML5
- **Framework**: FastAPI, AsyncIO  
- **Database**: SQLite
- **Frontend**: Vanilla JS, CSS3
- **Container**: Alpine Linux, S6-overlay

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

## Acknowledgments

- Home Assistant community for excellent add-on framework
- Bambu Lab and Prusa Research for printer API documentation  
- German 3D printing community for business requirements feedback

---

**Made with ❤️ by [Porcus3D](https://porcus3d.de)**  
*Professional 3D Printing Services*  
*Kornwestheim, Germany 🇩🇪*

[commits-shield]: https://img.shields.io/github/commit-activity/y/porcus3d/printernizer-addon.svg?style=for-the-badge
[commits]: https://github.com/porcus3d/printernizer-addon/commits/main
[license-shield]: https://img.shields.io/github/license/porcus3d/printernizer-addon.svg?style=for-the-badge  
[releases-shield]: https://img.shields.io/github/release/porcus3d/printernizer-addon.svg?style=for-the-badge
[releases]: https://github.com/porcus3d/printernizer-addon/releases
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg?style=for-the-badge
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg?style=for-the-badge
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg?style=for-the-badge
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg?style=for-the-badge
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg?style=for-the-badge