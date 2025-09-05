# Printernizer Home Assistant Add-on Documentation

## About

Printernizer is a professional 3D print management system designed for managing Bambu Lab A1 and Prusa Core One printers. This Home Assistant add-on provides seamless integration with your Home Assistant installation, enabling automated printer monitoring, job tracking, and business analytics.

## Installation

### Prerequisites
- Home Assistant OS or Home Assistant Supervised
- MQTT Broker (recommended: Mosquitto broker add-on)
- Network access to your 3D printers

### Installation Steps

1. **Add Repository** (if installing from custom repository):
   - Navigate to Settings > Add-ons > Add-on Store
   - Click the three dots menu and select "Repositories"
   - Add: `https://github.com/porcus3d/printernizer-addon`

2. **Install Add-on**:
   - Find "Printernizer" in the add-on store
   - Click "Install" 
   - Wait for installation to complete

3. **Configure Add-on**:
   - Click on the "Configuration" tab
   - Configure your printer settings (see Configuration section below)
   - Save configuration

4. **Start Add-on**:
   - Click "Start"
   - Check the "Logs" tab for any errors
   - Enable "Show in sidebar" for easy access

## Configuration

### Basic Configuration

```yaml
timezone: Europe/Berlin
log_level: info
cors_origins: []
printer_polling_interval: 30
max_concurrent_downloads: 5
enable_websockets: true
business_features:
  enable_german_compliance: true
  vat_rate: 19.0
  currency: EUR
printers: []
```

### Printer Configuration

Add your printers to the `printers` array:

#### Bambu Lab A1 Configuration
```yaml
printers:
  - printer_id: "bambu_a1_001"
    name: "Bambu Lab A1"
    type: "bambu_lab"
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "01P00A123456789"
    is_active: true
```

#### Prusa Core One Configuration
```yaml
printers:
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
| `timezone` | string | `Europe/Berlin` | Timezone for German business operations |
| `log_level` | list | `info` | Logging level (debug, info, warning, error, critical) |
| `cors_origins` | list | `[]` | CORS origins for API access |
| `printer_polling_interval` | int | `30` | Printer status polling interval in seconds (10-300) |
| `max_concurrent_downloads` | int | `5` | Maximum concurrent file downloads (1-10) |
| `enable_websockets` | bool | `true` | Enable WebSocket real-time updates |
| `business_features.enable_german_compliance` | bool | `true` | Enable German business compliance features |
| `business_features.vat_rate` | float | `19.0` | VAT rate percentage (0-100) |
| `business_features.currency` | string | `EUR` | Currency for cost calculations |

### Printer Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `printer_id` | string | ✅ | Unique identifier for the printer |
| `name` | string | ✅ | Display name for the printer |
| `type` | string | ✅ | Printer type: `bambu_lab` or `prusa` |
| `ip_address` | string | ✅ | IP address of the printer |
| `api_key` | string | Prusa only | PrusaLink API key |
| `access_code` | string | Bambu Lab only | Bambu Lab access code |
| `serial_number` | string | Optional | Printer serial number |
| `is_active` | bool | Optional | Enable/disable printer (default: true) |

## Features

### Real-time Monitoring
- Live printer status updates
- Temperature monitoring (bed and nozzle)
- Print progress tracking
- Job completion notifications

### File Management
- Automatic file discovery on printers
- One-click file downloads
- Organized file storage by printer and date
- File status tracking (available, downloaded, local)

### German Business Compliance
- VAT calculations (configurable rate)
- EUR currency support
- German timezone (Europe/Berlin)
- GDPR-compliant data handling
- Business vs. private job categorization

### Home Assistant Integration
- Automatic MQTT device discovery
- Sensor entities for each printer:
  - Status sensor
  - Progress sensor (%)
  - Current job name
  - Bed temperature (°C)
  - Nozzle temperature (°C)
  - Time remaining (min)
  - Material used (g)
  - Print cost (EUR)
  - Last job completion timestamp

### Export & Analytics
- Excel/CSV export for accounting software
- Material consumption tracking
- Cost calculations (material + power)
- Business performance metrics

## Home Assistant Entities

Once configured, Printernizer will automatically create the following entities in Home Assistant for each printer:

### Sensors
- `sensor.printernizer_{printer_id}_status` - Current printer status
- `sensor.printernizer_{printer_id}_progress` - Print progress percentage
- `sensor.printernizer_{printer_id}_current_job` - Current job name
- `sensor.printernizer_{printer_id}_bed_temp` - Bed temperature
- `sensor.printernizer_{printer_id}_nozzle_temp` - Nozzle temperature  
- `sensor.printernizer_{printer_id}_time_remaining` - Estimated time remaining
- `sensor.printernizer_{printer_id}_material_used` - Material consumption
- `sensor.printernizer_{printer_id}_print_cost` - Print cost in EUR
- `sensor.printernizer_{printer_id}_last_job` - Last job completion time

### Device Information
Each printer appears as a device in Home Assistant with:
- Manufacturer: Bambu Lab or Prusa Research
- Model: A1 or Core One
- Identifiers: `printernizer_{printer_id}`
- Configuration URL: Link to Printernizer web interface

## Web Interface

The add-on provides a web interface accessible at:
- **Internal**: `http://homeassistant.local:8000` (or your HA IP:8000)
- **Add-on UI**: Click "Open Web UI" in the add-on interface

### Web Interface Features
- Real-time printer dashboard
- Job monitoring with live updates  
- File management interface
- Download progress tracking
- Business analytics and reports
- Settings and configuration panel

## Troubleshooting

### Common Issues

#### Add-on won't start
1. Check the "Logs" tab for error messages
2. Verify printer IP addresses are correct and accessible
3. Ensure MQTT broker is running (if using MQTT features)
4. Check configuration syntax is valid YAML

#### Printers not discovered in Home Assistant
1. Verify MQTT broker add-on is installed and running
2. Check MQTT integration is enabled in Home Assistant
3. Restart the add-on after MQTT configuration changes
4. Check add-on logs for MQTT connection errors

#### Cannot access printer
1. Verify IP address and network connectivity
2. For Bambu Lab: Ensure access code is correct
3. For Prusa: Verify API key is valid and PrusaLink is enabled
4. Check firewall settings on printer and Home Assistant host

### Log Files
Add-on logs are available in the "Log" tab of the add-on interface. Set `log_level: debug` for verbose logging.

### Network Requirements
- Home Assistant host must have network access to printers
- For Bambu Lab: MQTT communication on default ports
- For Prusa: HTTP API access to PrusaLink interface
- MQTT broker access (port 1883 or 8883 for SSL)

## Support

For issues and support:
- GitHub Issues: https://github.com/porcus3d/printernizer/issues
- Email: sebastian@porcus3d.de
- Home Assistant Community: Tag `@porcus3d`

## License

This add-on is licensed under the MIT License. See LICENSE file for details.

---

**Printernizer** - Professional 3D Print Management for Home Assistant
Made with ❤️ by [Porcus3D](https://porcus3d.de) in Kornwestheim, Germany 🇩🇪