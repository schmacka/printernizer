# Home Assistant Integration for Printernizer

## Overview

Printernizer provides seamless integration with Home Assistant through a dedicated add-on and MQTT discovery protocol. This integration enables automatic device discovery, real-time sensor data, and native Home Assistant automation capabilities for your 3D printers.

## Features

### Automatic Device Discovery
- MQTT auto-discovery protocol
- Automatic device registration in Home Assistant
- Proper device information with manufacturer details
- Unique device identifiers for reliable tracking

### Comprehensive Sensor Entities
Each printer creates the following sensor entities:
- **Status Sensor**: Current printer state (printing, idle, error, etc.)
- **Progress Sensor**: Print completion percentage with % unit
- **Current Job Sensor**: Name of active print job
- **Bed Temperature**: Heated bed temperature in °C
- **Nozzle Temperature**: Extruder temperature in °C  
- **Time Remaining**: Estimated completion time in minutes
- **Material Used**: Filament consumption in grams
- **Print Cost**: Total job cost in EUR (German business feature)
- **Last Job Completion**: Timestamp of last finished job

### German Business Compliance
- EUR currency calculations
- German timezone (Europe/Berlin)
- VAT rate integration (configurable)
- GDPR-compliant data handling
- Business vs. private job categorization

## Installation

### Prerequisites
- Home Assistant OS, Supervised, or Container
- MQTT Broker (Mosquitto add-on recommended)
- Network access to 3D printers
- Home Assistant 2023.1.0 or later

### Method 1: Home Assistant Add-on (Recommended)

1. **Add Repository**:
   - Navigate to Settings → Add-ons → Add-on Store
   - Click ⋮ menu → Repositories
   - Add: `https://github.com/porcus3d/printernizer-addon`

2. **Install Add-on**:
   - Find "Printernizer" in the store
   - Click "Install"
   - Configure printers (see Configuration section)
   - Click "Start"

### Method 2: Standalone Docker with MQTT

```yaml
version: '3.8'
services:
  printernizer:
    image: porcus3d/printernizer:latest
    environment:
      - MQTT_HOST=homeassistant.local
      - MQTT_PORT=1883
      - MQTT_USERNAME=mqttuser
      - MQTT_PASSWORD=mqttpass
      - ENVIRONMENT=homeassistant
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    ports:
      - "8000:8000"
```

## Configuration

### Home Assistant Add-on Configuration

```yaml
# Basic Settings
timezone: Europe/Berlin
log_level: info
printer_polling_interval: 30
enable_websockets: true

# German Business Features  
business_features:
  enable_german_compliance: true
  vat_rate: 19.0
  currency: EUR

# Printer Configuration
printers:
  # Bambu Lab A1 Configuration
  - printer_id: "bambu_a1_main"
    name: "Bambu Lab A1 Production"
    type: "bambu_lab"
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "01P00A123456789"
    is_active: true
    
  # Prusa Core One Configuration
  - printer_id: "prusa_core_office"
    name: "Prusa Core One Office"
    type: "prusa"
    ip_address: "192.168.1.101"
    api_key: "your_prusa_api_key_here"
    is_active: true
```

### MQTT Integration Settings

The add-on automatically detects and uses Home Assistant's MQTT broker. For manual configuration:

```yaml
# Environment variables for Docker deployment
MQTT_HOST: homeassistant.local
MQTT_PORT: 1883
MQTT_USERNAME: your_mqtt_username
MQTT_PASSWORD: your_mqtt_password
MQTT_DISCOVERY_PREFIX: homeassistant
```

### Printer-Specific Configuration

#### Bambu Lab A1 Setup
1. Enable network mode on printer
2. Note the IP address from printer display
3. Generate access code in printer settings
4. Optional: Find serial number on printer label

#### Prusa Core One Setup
1. Enable PrusaLink in printer firmware
2. Set IP address (static recommended)
3. Generate API key in PrusaLink interface
4. Test API access: `http://printer-ip/api/version`

## Home Assistant Entities

### Device Information
Each printer appears as a device with:
- **Device ID**: `printernizer_{printer_id}`
- **Manufacturer**: Bambu Lab or Prusa Research
- **Model**: A1 or Core One
- **Name**: Printernizer {Printer Name}
- **Configuration URL**: Link to Printernizer web interface

### Entity Naming Convention
- **Format**: `sensor.printernizer_{printer_id}_{entity}`
- **Examples**:
  - `sensor.printernizer_bambu_a1_main_status`
  - `sensor.printernizer_bambu_a1_main_progress`
  - `sensor.printernizer_prusa_core_office_bed_temp`

### Entity Details

#### Status Sensor
- **Entity ID**: `sensor.printernizer_{printer_id}_status`
- **Values**: `idle`, `printing`, `paused`, `completed`, `error`, `offline`
- **Icon**: `mdi:printer-3d`
- **Category**: Diagnostic

#### Progress Sensor  
- **Entity ID**: `sensor.printernizer_{printer_id}_progress`
- **Unit**: `%`
- **Range**: 0-100
- **Device Class**: `percentage`
- **Icon**: `mdi:progress-check`

#### Temperature Sensors
- **Bed**: `sensor.printernizer_{printer_id}_bed_temp`
- **Nozzle**: `sensor.printernizer_{printer_id}_nozzle_temp`
- **Unit**: `°C`
- **Device Class**: `temperature`
- **Icon**: `mdi:thermometer`

#### Time and Material Sensors
- **Time Remaining**: Minutes until completion
- **Material Used**: Grams of filament consumed
- **Print Cost**: EUR cost calculation (German business feature)

## Lovelace Dashboard Integration

### Basic Printer Card
```yaml
type: entities
title: 3D Printers
show_header_toggle: false
entities:
  - entity: sensor.printernizer_bambu_a1_main_status
    name: "Status"
  - entity: sensor.printernizer_bambu_a1_main_progress
    name: "Progress"
  - entity: sensor.printernizer_bambu_a1_main_bed_temp
    name: "Bed"
  - entity: sensor.printernizer_bambu_a1_main_nozzle_temp
    name: "Nozzle"
  - entity: sensor.printernizer_bambu_a1_main_current_job
    name: "Current Job"
```

### Advanced Printer Dashboard
```yaml
type: vertical-stack
cards:
  # Status Overview
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.printernizer_bambu_a1_main_status
        name: "Printer Status"
        icon: mdi:printer-3d
      - type: entity
        entity: sensor.printernizer_bambu_a1_main_progress
        name: "Progress"
        icon: mdi:progress-check
        
  # Temperature Monitoring
  - type: entities
    title: "Temperature Monitoring"
    entities:
      - entity: sensor.printernizer_bambu_a1_main_bed_temp
        name: "Bed Temperature"
      - entity: sensor.printernizer_bambu_a1_main_nozzle_temp
        name: "Nozzle Temperature"
        
  # Print Information
  - type: entities  
    title: "Print Information"
    entities:
      - entity: sensor.printernizer_bambu_a1_main_current_job
        name: "Current Job"
      - entity: sensor.printernizer_bambu_a1_main_time_remaining
        name: "Time Remaining"
      - entity: sensor.printernizer_bambu_a1_main_material_used
        name: "Material Used"
      - entity: sensor.printernizer_bambu_a1_main_print_cost
        name: "Print Cost"
```

### Printer Status History Graph
```yaml
type: history-graph
title: "Printer Temperature History"
entities:
  - entity: sensor.printernizer_bambu_a1_main_bed_temp
    name: "Bed"
  - entity: sensor.printernizer_bambu_a1_main_nozzle_temp
    name: "Nozzle"
hours_to_show: 24
refresh_interval: 30
```

## Automation Examples

### Print Completion Notification
```yaml
automation:
  - alias: "3D Print Completed"
    description: "Notify when 3D print job completes"
    trigger:
      - platform: state
        entity_id: sensor.printernizer_bambu_a1_main_status
        to: "completed"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🎉 3D Print Completed"
          message: "{{ trigger.to_state.attributes.current_job }} finished printing!"
          data:
            push:
              sound: "success"
            actions:
              - action: "open_printernizer"
                title: "View Details"
```

### High Temperature Alert
```yaml
automation:
  - alias: "Printer High Temperature Alert" 
    description: "Alert if printer temperature exceeds safe limits"
    trigger:
      - platform: numeric_state
        entity_id: sensor.printernizer_bambu_a1_main_bed_temp
        above: 80
        for: "00:05:00"
    action:
      - service: notify.home_assistant
        data:
          title: "⚠️ High Printer Temperature"
          message: |
            Bed temperature is {{ states('sensor.printernizer_bambu_a1_main_bed_temp') }}°C
            This is above the 80°C safety threshold.
```

### Print Job Started Automation
```yaml
automation:
  - alias: "Print Job Started"
    description: "Actions when print job starts"
    trigger:
      - platform: state
        entity_id: sensor.printernizer_bambu_a1_main_status
        to: "printing"
    action:
      - service: light.turn_on
        target:
          entity_id: light.3d_printer_area
        data:
          brightness: 255
      - service: notify.family
        data:
          message: "🖨️ Started printing: {{ states('sensor.printernizer_bambu_a1_main_current_job') }}"
```

### Material Usage Tracking
```yaml
automation:
  - alias: "Track Material Usage"
    description: "Log material consumption for inventory"
    trigger:
      - platform: state
        entity_id: sensor.printernizer_bambu_a1_main_status
        to: "completed"
    action:
      - service: logbook.log
        data:
          name: "Material Usage"
          message: |
            Print job completed: {{ states('sensor.printernizer_bambu_a1_main_current_job') }}
            Material used: {{ states('sensor.printernizer_bambu_a1_main_material_used') }}g
            Cost: €{{ states('sensor.printernizer_bambu_a1_main_print_cost') }}
```

## API Endpoints

### Home Assistant Specific Endpoints

#### Get Integration Status
```http
GET /api/v1/homeassistant/status
```
Returns comprehensive integration status including MQTT connection, device count, and entity information.

#### Rediscover MQTT Devices
```http  
POST /api/v1/homeassistant/mqtt/rediscover
```
Forces rediscovery of all printer devices in Home Assistant. Useful after configuration changes.

#### Get Printer Entities
```http
GET /api/v1/homeassistant/entities/{printer_id}
```
Returns all Home Assistant entities for a specific printer.

#### Addon Health Check
```http
GET /api/v1/homeassistant/health
```
Health check endpoint for addon monitoring and diagnostics.

## Troubleshooting

### Common Issues

#### Entities Not Appearing in Home Assistant

**Symptom**: Printers configured but no entities in Home Assistant
**Solution**:
1. Verify MQTT broker is running and accessible
2. Check MQTT integration is enabled in Home Assistant
3. Review add-on logs for MQTT connection errors
4. Use rediscover endpoint: `POST /api/v1/homeassistant/mqtt/rediscover`

#### MQTT Connection Failed

**Symptom**: "MQTT integration not available" in logs
**Solution**:
1. Install and start Mosquitto broker add-on
2. Configure MQTT integration in Home Assistant  
3. Check network connectivity between add-on and broker
4. Verify MQTT credentials if using authentication

#### Printer Connection Issues

**Symptom**: Printer entities show "offline" or "unavailable"
**Solution**:
1. Verify printer IP address is correct and accessible
2. For Bambu Lab: Check access code is correct
3. For Prusa: Verify PrusaLink is enabled and API key is valid
4. Test network connectivity from Home Assistant host
5. Check firewall settings on printer and Home Assistant

#### Entities Show "Unknown" State

**Symptom**: Sensors created but showing "unknown" values
**Solution**:
1. Wait for next polling cycle (default 30 seconds)
2. Check printer is powered on and connected
3. Verify printer firmware supports required APIs
4. Review add-on logs for polling errors

### Debug Information

#### Enable Debug Logging
Set `log_level: debug` in add-on configuration for verbose logging.

#### Check MQTT Topics
Use MQTT Explorer or similar tool to monitor topics:
- Discovery: `homeassistant/sensor/printernizer_*/config`
- State: `printernizer/{printer_id}/*`
- Availability: `printernizer/{printer_id}/availability`

#### API Health Checks
Monitor addon health via API:
```bash
curl http://homeassistant.local:8000/api/v1/homeassistant/health
```

### Performance Optimization

#### Polling Intervals
- Default: 30 seconds (good for most uses)
- Active printing: Consider 15-20 seconds
- Idle printers: Can increase to 60+ seconds

#### MQTT Message Frequency
- Real-time updates during printing
- Reduced frequency when idle
- Automatic adjustment based on printer status

## Security Considerations

### Network Security
- Use dedicated VLAN for 3D printers
- Configure firewall rules appropriately
- Regular firmware updates on printers

### Data Privacy (GDPR Compliance)
- Print job data stored locally only
- No cloud transmission of printer data
- Automatic data retention management
- User consent tracking for business features

### Access Control
- Home Assistant user permissions
- API endpoint authentication
- Secure MQTT broker configuration

## Advanced Configuration

### Custom Entity Categories
```yaml
# Customize entity categories in Home Assistant
customize:
  sensor.printernizer_bambu_a1_main_status:
    entity_category: diagnostic
  sensor.printernizer_bambu_a1_main_print_cost:
    entity_category: diagnostic
    device_class: monetary
```

### Template Sensors
```yaml  
# Custom calculated sensors
template:
  - sensor:
      - name: "Print Efficiency"
        unit_of_measurement: "%"
        state: >
          {% set progress = states('sensor.printernizer_bambu_a1_main_progress') | float %}
          {% set time_remaining = states('sensor.printernizer_bambu_a1_main_time_remaining') | float %}
          {% if progress > 0 and time_remaining > 0 %}
            {{ ((progress / 100) / ((progress / 100) + (time_remaining / 60 / 100))) * 100) | round(1) }}
          {% else %}
            0
          {% endif %}
```

### Custom Automations
Create specialized automations for:
- Automatic print queue management  
- Material inventory tracking
- Cost center reporting
- Maintenance scheduling
- Quality control notifications

## Support and Community

### Getting Help
- **GitHub Issues**: https://github.com/porcus3d/printernizer/issues
- **Home Assistant Community**: Forum discussions and support
- **Email Support**: sebastian@porcus3d.de

### Contributing
- Feature requests and bug reports welcome
- Pull requests for improvements
- Documentation contributions
- Translation assistance

### Updates and Releases
- Automatic updates via Home Assistant
- Release notes in GitHub
- Breaking changes announced in advance

---

**Printernizer Home Assistant Integration**  
Professional 3D Print Management with German Business Features  
Made with ❤️ by [Porcus3D](https://porcus3d.de) in Kornwestheim, Germany 🇩🇪