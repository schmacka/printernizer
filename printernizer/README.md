# Printernizer - Home Assistant Add-on

Professional 3D Printer Management System for Bambu Lab A1 and Prusa Core One printers, running 24/7 in your Home Assistant instance.

## About

Printernizer provides enterprise-grade fleet management with real-time monitoring, automated file handling, and business analytics - all integrated directly into your Home Assistant environment.

## Features

- 🔄 **Real-time printer monitoring** - Live status, temperatures, and job progress
- 📁 **Unified file management** - One-click downloads from all printers
- 🎬 **Automated timelapse creation** - FlickerFree deflicker video processing with auto-detection
- 🏢 **Business analytics** - Professional reporting and cost tracking
- ⚡ **WebSocket updates** - Instant status updates without page refresh
- 🖼️ **3D preview** - Automatic thumbnail generation for print files
- 🔧 **Easy configuration** - Set up printers via Home Assistant UI

## Supported Printers

- **Bambu Lab A1** - Full MQTT integration with real-time updates
- **Prusa Core One** - HTTP API integration via PrusaLink

## Installation

1. Add this repository to Home Assistant:
   - Navigate to **Settings → Add-ons → Add-on Store**
   - Click the three dots menu → **Repositories**
   - Add: `https://github.com/schmacka/printernizer`

2. Install Printernizer:
   - Find "Printernizer" in the add-on store
   - Click **Install**
   - Wait for installation to complete

3. Configure your printers (see Configuration section)

4. Start the add-on:
   - Click **Start**
   - Enable **Start on boot** for 24/7 operation
   - Click **Open Web UI** to access the interface

## Configuration

### Basic Configuration

```yaml
log_level: info
timezone: Europe/Berlin
enable_3d_preview: true
enable_websockets: true
enable_business_reports: true
printers: []
```

### Adding Printers

Add printers in the add-on configuration:

**Bambu Lab A1:**
```yaml
printers:
  - name: "Bambu Lab A1 #1"
    type: bambu_lab
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "AC12345678"
    enabled: true
```

**Prusa Core One:**
```yaml
printers:
  - name: "Prusa Core One #1"
    type: prusa
    ip_address: "192.168.1.101"
    api_key: "your-prusalink-api-key"
    enabled: true
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_level` | list | `info` | Logging level: debug, info, warning, error |
| `timezone` | string | `Europe/Berlin` | Your timezone for timestamps |
| `library_folder` | string | `/data/printernizer/library` | Path where 3D model files are stored |
| `enable_3d_preview` | bool | `true` | Enable 3D file preview generation |
| `enable_websockets` | bool | `true` | Enable real-time WebSocket updates |
| `enable_business_reports` | bool | `true` | Enable business analytics features |
| `timelapse_enabled` | bool | `true` | Enable automated timelapse video creation |
| `timelapse_source_folder` | string | `/data/timelapse-images` | Folder to watch for timelapse image subfolders |
| `timelapse_output_folder` | string | `/data/timelapses` | Folder for completed timelapse videos |
| `timelapse_output_strategy` | list | `separate` | Video output location: same\|separate\|both |
| `timelapse_auto_process_timeout` | int | `300` | Seconds to wait after last image before auto-processing (60-3600) |
| `timelapse_cleanup_age_days` | int | `30` | Age threshold for cleanup recommendations in days (1-365) |

### Printer Configuration Fields

**Required for all printers:**
- `name` - Display name for your printer
- `type` - Either `bambu_lab` or `prusa`
- `ip_address` - Local network IP address
- `enabled` - Set to `true` to enable monitoring

**Bambu Lab specific:**
- `access_code` - 8-digit code from printer display
- `serial_number` - Printer serial number

**Prusa specific:**
- `api_key` - PrusaLink API key (generate in PrusaLink settings)

### Timelapse Configuration

Printernizer can automatically create timelapse videos from your 3D prints using the FlickerFree deflicker algorithm.

**Basic Setup:**
```yaml
timelapse_enabled: true
timelapse_source_folder: /data/timelapse-images
timelapse_output_folder: /data/timelapses
timelapse_output_strategy: separate
```

**Output Strategies:**
- `same` - Save videos in the same folder as source images
- `separate` - Save videos in the dedicated output folder (recommended)
- `both` - Save videos in both locations

**How it Works:**
1. Configure your printer to save timelapse images to `/data/timelapse-images/[job-name]/`
2. Printernizer automatically detects new image folders
3. After `timelapse_auto_process_timeout` seconds of no new images, processing begins
4. Videos are created with FlickerFree deflicker and saved to the configured location
5. Videos appear in the Zeitraffer (Timelapse) section of the web UI

**Folder Structure:**
```
/data/
├── timelapse-images/          ← Source (configure printer to save here)
│   ├── job_2025-01-07_12-30/  ← Auto-detected job folders
│   │   ├── img_0001.jpg
│   │   ├── img_0002.jpg
│   │   └── ...
│   └── job_2025-01-07_15-45/
└── timelapses/                ← Output (processed videos)
    ├── job_2025-01-07_12-30.mp4
    └── job_2025-01-07_15-45.mp4
```

**Bambu Lab Setup:**
1. In Bambu Studio, enable timelapse recording
2. Configure Bambu Lab to save timelapse images to a network share or mapped to `/data/timelapse-images`
3. Printernizer will auto-detect and process new jobs

**Storage Management:**
- Use `timelapse_cleanup_age_days` to get recommendations for old files
- Storage usage is tracked in the Zeitraffer section
- Cleanup is manual to prevent accidental deletion

## Usage

### Accessing the Interface

**Via Ingress (Recommended):**
- Click **Open Web UI** in the add-on page
- Access directly from Home Assistant sidebar

**Via Direct Port:**
- Enable port 8000 in Network settings if needed
- Access at `http://[your-ha-ip]:8000`

### Monitoring Printers

The dashboard shows:
- Real-time printer status and temperatures
- Current job progress with layer tracking
- Connection health monitoring
- File browser for all printers

### Downloading Files

1. Navigate to **Drucker-Dateien** (Printer Files)
2. Browse files from all connected printers
3. Click download button for desired files
4. Files are saved in persistent storage

### Business Features

- View today's statistics on dashboard
- Export job data for accounting
- Track material costs and consumption
- Generate business reports

## Networking

### Printer Discovery

Printers must be on the same network as Home Assistant or accessible via routing. Test connectivity:

```bash
ping [printer-ip-address]
```

### Firewall Considerations

Ensure these ports are accessible:
- **Bambu Lab:** MQTT port 1883
- **Prusa:** HTTP port 80 or custom PrusaLink port

## Troubleshooting

### Add-on Won't Start

1. Check the logs: **Configuration → Add-ons → Printernizer → Logs**
2. Verify printer configuration is valid
3. Ensure network connectivity to printers

### Printers Not Connecting

1. Verify printer IP addresses are correct
2. Check access codes/API keys
3. Test network connectivity to printers
4. Review add-on logs for error messages

### WebSocket Issues

1. Ensure `enable_websockets: true` in configuration
2. Clear browser cache and refresh
3. Check browser console for errors

### Database Issues

Data is stored in `/data/printernizer/` and persists across restarts. To reset:

1. Stop the add-on
2. Remove data via SSH or File Editor
3. Restart the add-on

## Data Persistence

All data is stored in Home Assistant's add-on data directory:

```
/data/
├── printernizer/
│   ├── printernizer.db      # SQLite database
│   ├── library/             # 3D model files (configurable)
│   ├── printer-files/       # Downloaded files
│   ├── preview-cache/       # 3D preview thumbnails
│   └── backups/             # Database backups
├── timelapse-images/        # Source images from printers (configurable)
│   └── [job-folders]/       # Auto-detected print job folders
└── timelapses/              # Processed timelapse videos (configurable)
    └── *.mp4                # Completed videos
```

This data persists across:
- Add-on restarts
- Add-on updates
- Home Assistant restarts

## Performance

**Resource Usage:**
- Memory: ~200-500MB depending on activity
- CPU: <5% idle, <20% during file downloads
- Storage: Minimal + downloaded printer files

**Recommended Hardware:**
- Raspberry Pi 4 (2GB+ RAM)
- Home Assistant Yellow
- Any x86_64 system

## Support

- **Documentation:** [Full Documentation](https://github.com/schmacka/printernizer)
- **Issues:** [GitHub Issues](https://github.com/schmacka/printernizer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/schmacka/printernizer/discussions)

## License

Printernizer is dual-licensed:
- **AGPL-3.0** for open source projects and personal use
- **Commercial License** available for commercial deployments

See [LICENSE](https://github.com/schmacka/printernizer/blob/master/LICENSE) for details.

---

**Printernizer** - Making 3D printing fleet management simple and efficient
