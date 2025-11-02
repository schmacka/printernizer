# Printernizer Home Assistant Add-on - Detailed Documentation

Complete guide for installing, configuring, and using Printernizer as a Home Assistant Add-on.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Printer Setup](#printer-setup)
4. [Features](#features)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Topics](#advanced-topics)

---

## Installation

### Method 1: Via Repository (Recommended)

1. **Add Repository to Home Assistant:**
   - Navigate to **Settings → Add-ons → Add-on Store**
   - Click the **⋮** menu (three dots) in the top right
   - Select **Repositories**
   - Add: `https://github.com/schmacka/printernizer`
   - Click **Add**

2. **Install the Add-on:**
   - Refresh the add-on store page
   - Find **Printernizer** in the list
   - Click on it and select **Install**
   - Wait for the installation to complete (3-10 minutes depending on your hardware)

3. **Initial Configuration:**
   - Go to the **Configuration** tab
   - Set your timezone and preferences
   - Add at least one printer (see Printer Setup section)
   - Click **Save**

4. **Start the Add-on:**
   - Go to the **Info** tab
   - Click **Start**
   - Monitor the **Log** tab for startup messages
   - Once started, click **Open Web UI**

### Method 2: Local Installation

For development or testing:

1. Clone the repository to your Home Assistant addons folder:
   ```bash
   cd /addons
   git clone https://github.com/schmacka/printernizer
   ```

2. The add-on will appear in **Settings → Add-ons → Add-on Store** under "Local add-ons"

3. Follow steps 2-4 from Method 1

---

## Configuration

### Configuration Tab

The Configuration tab contains all add-on settings in YAML format.

### Basic Settings

```yaml
log_level: info
timezone: Europe/Berlin
library_folder: /data/printernizer/library
enable_3d_preview: true
enable_websockets: true
enable_business_reports: true
```

**log_level** (optional, default: `info`)
- Controls logging verbosity
- Options: `debug`, `info`, `warning`, `error`
- Use `debug` for troubleshooting, `info` for normal operation

**timezone** (optional, default: `Europe/Berlin`)
- Sets timezone for all timestamps
- Use IANA timezone format (e.g., `America/New_York`, `Asia/Tokyo`)
- Affects business reports and job timestamps

**library_folder** (optional, default: `/data/printernizer/library`)
- Path where downloaded 3D model files are stored
- Must be an absolute path
- Automatically created if it doesn't exist
- Examples:
  - `/data/printernizer/library` (default)
  - `/share/3d-models` (shared with other add-ons)
  - `/mnt/usb-drive/library` (external storage)
- **Note:** Ensure the path is accessible and has sufficient storage space

**enable_3d_preview** (optional, default: `true`)
- Enables automatic 3D preview generation for STL, 3MF, and G-code files
- Disable to reduce resource usage
- Previews are cached for 30 days

**enable_websockets** (optional, default: `true`)
- Enables real-time updates via WebSocket
- Provides live status without page refresh
- Recommended to keep enabled for best experience

**enable_business_reports** (optional, default: `true`)
- Enables business analytics and reporting features
- Includes cost calculations and statistics
- Disable if not needed for personal use

---

## Printer Setup

### Auto-Discovery (Recommended)

Printernizer can automatically discover printers on your local network using SSDP (for Bambu Lab) and mDNS/Bonjour (for Prusa).

**How to Use Auto-Discovery:**

1. **Enable Host Network (if needed):**
   - Go to **Add-on Configuration → Network** tab
   - Toggle **Show disabled ports**
   - If discovery doesn't work, you may need to enable **Host network** mode
   - This allows the add-on to access multicast traffic (SSDP/mDNS)

2. **Run Discovery:**
   - Open the Printernizer web interface
   - Go to **Drucker** (Printers) page
   - Click **"Drucker suchen"** (Discover Printers) button
   - Wait 5-10 seconds for the scan to complete

3. **Add Discovered Printer:**
   - Discovered printers will appear in the "Gefundene Drucker" (Discovered Printers) section
   - Click **"Hinzufügen"** (Add) on the printer you want to add
   - The add printer form will be pre-filled with IP address and type
   - Complete the configuration (add credentials for Bambu Lab, API key for Prusa)
   - Click **Save**

**Configuration Options:**
```yaml
discovery_enabled: true
discovery_timeout_seconds: 10
discovery_scan_interval_minutes: 60
```

**discovery_enabled** (optional, default: `true`)
- Enables/disables automatic printer discovery feature
- Set to `false` if you don't want discovery capability

**discovery_timeout_seconds** (optional, default: `10`)
- How long to wait for printer responses during discovery
- Range: 5-60 seconds
- Increase if your network is slow or printers aren't found

**discovery_scan_interval_minutes** (optional, default: `60`)
- Currently for future automatic background scanning
- Range: 10-1440 minutes (1 day)

**Troubleshooting Discovery:**
- **No printers found:** Make sure printers are powered on and connected to the network
- **Discovery errors:** Check if you're on the same network as the printers
- **SSDP/mDNS blocked:** Some networks block multicast traffic - enable **Host network** mode
- **Docker/HA networking:** Host network mode may be required for discovery to work

### Manual Printer Configuration

If auto-discovery doesn't work or you prefer manual configuration, you can add printers via the configuration file:

### Bambu Lab A1 Configuration

**Required Information:**
1. **IP Address:** Find in printer's network settings or your router
2. **Access Code:** 8-digit code displayed on printer (Settings → Network → MQTT)
3. **Serial Number:** Found on printer label or in settings

**Configuration Example:**
```yaml
printers:
  - name: "Bambu Lab A1 Workshop"
    type: bambu_lab
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "AC12345678901234"
    enabled: true
```

**Finding Access Code:**
1. On printer: **Settings → Network → MQTT**
2. Look for "Access Code" or "LAN Mode Password"
3. 8-digit numeric code

**Finding Serial Number:**
1. On printer label (starts with "AC")
2. Or in: **Settings → Device Info → Serial Number**

### Prusa Core One Configuration

**Required Information:**
1. **IP Address:** Find in printer's network settings
2. **API Key:** Generated in PrusaLink settings

**Configuration Example:**
```yaml
printers:
  - name: "Prusa Core One #1"
    type: prusa
    ip_address: "192.168.1.101"
    api_key: "A1B2C3D4E5F6G7H8"
    enabled: true
```

**Generating API Key:**
1. Access PrusaLink web interface: `http://[printer-ip]`
2. Navigate to **Settings**
3. Find **API Key** section
4. Click **Generate New Key** or copy existing key
5. Save the key securely

### Multiple Printers

Add multiple printers by repeating the configuration:

```yaml
printers:
  - name: "Bambu Lab A1 #1"
    type: bambu_lab
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "AC12345678901234"
    enabled: true

  - name: "Bambu Lab A1 #2"
    type: bambu_lab
    ip_address: "192.168.1.101"
    access_code: "87654321"
    serial_number: "AC98765432109876"
    enabled: true

  - name: "Prusa Core One #1"
    type: prusa
    ip_address: "192.168.1.102"
    api_key: "YOUR_API_KEY_HERE"
    enabled: true
```

### Temporarily Disabling Printers

Set `enabled: false` to stop monitoring a printer without removing configuration:

```yaml
printers:
  - name: "Bambu Lab A1 #1"
    type: bambu_lab
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "AC12345678901234"
    enabled: false  # Temporarily disabled
```

---

## Features

### Dashboard

Access via **Open Web UI** button or Home Assistant sidebar.

**Shows:**
- Real-time printer status cards
- Current job progress with layer tracking
- Temperature monitoring (bed, nozzle)
- Connection health indicators
- Today's business statistics
- Quick access to all features

### File Management (Drucker-Dateien)

**Capabilities:**
- Browse files on all connected printers
- One-click download from printers
- Upload files to printers (future)
- 3D preview for STL/3MF/G-code files
- Filter by printer, status, file type
- Bulk operations

**File Status Indicators:**
- 📁 **Available** - On printer, not downloaded
- ✓ **Downloaded** - Saved to Home Assistant storage
- 💾 **Local** - Only on Home Assistant

**Downloading Files:**
1. Navigate to **Drucker-Dateien**
2. Find desired file in list
3. Click download button
4. Monitor progress bar
5. File saved to `/data/printernizer/printer-files/`

### Job Monitoring

**Real-time Tracking:**
- Current job progress percentage
- Current layer / Total layers
- Elapsed time and estimated completion
- Material usage tracking
- Temperature monitoring

**Job History:**
- View all completed jobs
- Success/failure statistics
- Material consumption analysis
- Cost calculations

### Business Features

**Analytics Dashboard:**
- Today's statistics (jobs, material, time)
- Weekly/monthly summaries
- Success rate tracking
- Material cost analysis

**Cost Tracking:**
- Material costs per job
- Power consumption estimates
- Total operating costs
- Export for accounting software

**Reporting:**
- Export jobs to Excel/CSV
- German business format support
- VAT calculations (19%)
- Integration with accounting software

### 3D Previews

**Automatic Generation:**
- STL files - 3D model preview
- 3MF files - 3D model preview
- G-code files - Print path visualization
- BG-code files - Bambu Lab format support

**Performance:**
- Cached for 30 days
- Optimized for fast loading
- Background generation
- Low memory footprint

---

## Troubleshooting

### Add-on Won't Start

**Check Logs:**
1. Go to **Info** tab
2. Click **Refresh** on Log section
3. Look for error messages

**Common Issues:**

**"Database initialization failed"**
- Solution: Stop add-on, remove `/data/printernizer/`, restart

**"Port 8000 already in use"**
- Solution: Check for conflicting add-ons, change port in network settings

**"Invalid configuration"**
- Solution: Verify YAML syntax in Configuration tab, fix formatting errors

### Printers Not Connecting

**Bambu Lab Issues:**

1. **"Connection timeout"**
   - Check printer IP address is correct
   - Verify access code is correct (8 digits)
   - Ensure MQTT is enabled on printer
   - Check firewall allows port 1883

2. **"Authentication failed"**
   - Verify access code matches printer display
   - Try regenerating access code on printer
   - Check serial number is correct

**Prusa Issues:**

1. **"API authentication failed"**
   - Verify API key is correct
   - Regenerate API key if needed
   - Check PrusaLink is running

2. **"Connection refused"**
   - Verify printer IP address
   - Check PrusaLink is enabled
   - Test access to `http://[printer-ip]` in browser

**Network Diagnostics:**

Test from Home Assistant terminal:
```bash
# Test connectivity
ping [printer-ip]

# Test specific port (Bambu Lab MQTT)
nc -zv [printer-ip] 1883

# Test HTTP (Prusa)
curl http://[printer-ip]
```

### WebSocket Connection Issues

**Symptoms:**
- Dashboard doesn't update automatically
- Must refresh page to see changes
- "WebSocket disconnected" in browser console

**Solutions:**

1. **Enable WebSockets:**
   ```yaml
   enable_websockets: true
   ```

2. **Clear Browser Cache:**
   - Hard refresh: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
   - Clear all browser data
   - Try different browser

3. **Check Ingress:**
   - Use Ingress URL (recommended)
   - Avoid direct port access for WebSockets

### File Download Issues

**"Download failed"**
- Check network connectivity to printer
- Verify file still exists on printer
- Check available storage space
- Review logs for specific error

**"Preview generation failed"**
- Large files may timeout
- Try disabling 3D preview temporarily
- Check available memory

### Performance Issues

**Slow Dashboard:**
- Disable 3D preview: `enable_3d_preview: false`
- Reduce number of monitored printers
- Clear preview cache: Delete `/data/printernizer/preview-cache/`

**High Memory Usage:**
- Normal: 200-500MB depending on activity
- If higher: Restart add-on, check for memory leaks in logs

**High CPU Usage:**
- Normal during file downloads and preview generation
- If persistent: Check logs for errors, reduce polling interval

---

## Advanced Topics

### Data Storage

All persistent data stored in `/data/printernizer/`:

```
/data/printernizer/
├── printernizer.db          # SQLite database (jobs, printers, settings)
├── library/                 # Downloaded 3D model files (configurable)
│   ├── models/             # Organized 3D models
│   └── metadata/           # File metadata and checksums
├── printer-files/           # Temporary printer files
│   ├── bambu-lab-a1-1/     # Organized by printer
│   └── prusa-core-one-1/
├── preview-cache/           # 3D preview thumbnails
│   ├── thumbnails/
│   └── metadata/
└── backups/                 # Automatic database backups
```

**Note:** The library folder location is configurable via `library_folder` setting. By default it's `/data/printernizer/library`, but you can change it to any accessible path (e.g., external storage, shared folders).

### Backup and Restore

**Manual Backup:**

Via SSH or Terminal add-on:
```bash
# Backup database
cp /data/printernizer/printernizer.db /backup/printernizer-$(date +%Y%m%d).db

# Backup all data
tar czf /backup/printernizer-full-$(date +%Y%m%d).tar.gz /data/printernizer/
```

**Restore:**
```bash
# Restore database
cp /backup/printernizer-20250101.db /data/printernizer/printernizer.db

# Restore full backup
tar xzf /backup/printernizer-full-20250101.tar.gz -C /
```

**Automatic Backups:**

Add to Home Assistant automation:
```yaml
automation:
  - alias: "Printernizer Daily Backup"
    trigger:
      platform: time
      at: "03:00:00"
    action:
      service: hassio.addon_stdin
      data:
        addon: printernizer
        input: "backup"
```

### Integration with Home Assistant

**Future Capabilities:**
- MQTT discovery for printer sensors
- Binary sensors for job status
- Notifications via mobile app
- Automation triggers
- Dashboard cards

### Resource Management

**Recommended Hardware:**
- **Raspberry Pi 4:** 2GB+ RAM (4GB recommended)
- **Home Assistant Yellow:** Full support
- **x86_64 Systems:** Any modern CPU

**Resource Limits:**

Edit add-on configuration (advanced):
```yaml
# Not in normal config - requires manual edit
max_memory: 1024
max_cpu: 2.0
```

### Security Considerations

**Network Security:**
- Printers should be on trusted network
- Consider VLAN isolation for printers
- Use strong access codes/API keys
- Regular printer firmware updates

**Home Assistant Security:**
- Keep Home Assistant updated
- Use strong passwords
- Enable 2FA if possible
- Regular backups

### Updating the Add-on

**Automatic Updates:**
1. Go to **Info** tab
2. If update available, click **Update**
3. Wait for download and installation
4. Add-on restarts automatically

**Manual Update (Repository):**
```bash
cd /addons/printernizer
git pull
# Rebuild add-on via UI
```

### Logs and Debugging

**Enable Debug Logging:**
```yaml
log_level: debug
```

**View Logs:**
- Real-time: **Log** tab in add-on page
- Historical: `/data/printernizer/logs/` (if file logging enabled)

**Submit Bug Reports:**
1. Enable debug logging
2. Reproduce issue
3. Copy relevant log entries
4. Report at: https://github.com/schmacka/printernizer/issues

---

## Support

**Resources:**
- **Documentation:** https://github.com/schmacka/printernizer
- **Issue Tracker:** https://github.com/schmacka/printernizer/issues
- **Discussions:** https://github.com/schmacka/printernizer/discussions
- **Home Assistant Forum:** Tag @schmacka

**Before Reporting Issues:**
1. Check this documentation
2. Review troubleshooting section
3. Enable debug logging
4. Check existing GitHub issues
5. Provide complete information (logs, config, HA version)

---

**Printernizer** - Professional 3D Printer Management for Home Assistant
