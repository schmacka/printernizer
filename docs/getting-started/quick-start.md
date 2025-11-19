# Quick Start

Get started with Printernizer in 5 minutes! This guide covers the essentials to get you monitoring your 3D printers.

## Prerequisites

- Printernizer installed and running ([Installation Guide](installation.md))
- At least one Bambu Lab A1 or Prusa Core One printer on your network
- Printer IP address (or enable auto-discovery)

## Step 1: Access Printernizer

Open your web browser and navigate to:

```
http://localhost:8000
```

You should see the Printernizer dashboard with:
- Sidebar navigation
- Printer list (empty initially)
- Status overview

## Step 2: Add Your First Printer

### Option A: Auto-Discovery (Recommended)

Printernizer can automatically discover printers on your network:

1. Click **"Discover Printers"** button on the dashboard
2. Wait for the scan to complete (10-30 seconds)
3. Review discovered printers
4. Click **"Add"** for each printer you want to manage

**Supported discovery:**
- Bambu Lab A1: SSDP discovery
- Prusa Core One: mDNS (Bonjour) discovery

### Option B: Manual Addition

If auto-discovery doesn't work or you prefer manual setup:

1. Click **"Add Printer"** button
2. Fill in the form:
   - **Name:** Friendly name (e.g., "Main Bambu Lab")
   - **Type:** Select "Bambu Lab A1" or "Prusa Core One"
   - **IP Address:** Printer's IP address
   - **Serial Number:** (Bambu Lab only) Found in printer settings
   - **Access Code:** (Bambu Lab only) LAN access code from printer
   - **API Key:** (Prusa only) From PrusaLink settings
3. Click **"Add Printer"**

**Finding printer credentials:**

**Bambu Lab A1:**
- Go to printer touchscreen → Settings → Network
- Enable "LAN Mode"
- Note the "Access Code"
- Serial number is on the back of the printer

**Prusa Core One:**
- Access PrusaLink web interface
- Go to Settings → API
- Generate or copy API key

## Step 3: Verify Connection

After adding a printer:

1. Check the **Printers** page
2. Verify printer status shows "Connected" (green indicator)
3. Check that temperature readings appear
4. Confirm the printer name and details are correct

**Troubleshooting connection issues:**
- Verify printer is powered on and connected to network
- Check firewall settings
- Ensure Printernizer and printer are on same network/subnet
- For Bambu Lab: Verify LAN Mode is enabled
- For Prusa: Verify PrusaLink is running

## Step 4: Monitor a Print Job

Start a print job on your printer (from SD card, USB, or slicer):

1. Go to **Jobs** page in Printernizer
2. Watch as the job appears automatically
3. Monitor real-time progress:
   - Layer count
   - Progress percentage
   - Time remaining
   - Temperatures

**Job tracking features:**
- Live WebSocket updates (no page refresh needed)
- Historical job tracking
- Success/failure statistics
- Print time estimates

## Step 5: Explore File Management

### View Printer Files

1. Click **Files** in the sidebar
2. Browse files on your printer's storage
3. Filter by printer or file type

### Download Files

1. Find the file you want to download
2. Click the **Download** icon
3. File downloads to Printernizer's storage
4. View download status and progress

**File features:**
- Unified view of all printer files
- 3D preview thumbnails (STL, 3MF, GCODE, BGCODE)
- One-click downloads
- Status indicators

## Step 6: Configure Settings (Optional)

Customize Printernizer to your needs:

1. Click **Settings** in the sidebar
2. Explore available options:
   - **Auto-download:** Enable automatic file downloads after print completion
   - **Business tracking:** Mark jobs as business or private
   - **Notifications:** Configure alerts
   - **Thresholds:** Set temperature and progress alerts

See [Configuration Guide](configuration.md) for all settings.

## Next Steps

Now that you're up and running:

### Learn More Features

- **[File Management](../features/file-management.md)** - Advanced file operations
- **[Job Monitoring](../features/job-monitoring.md)** - Detailed job tracking
- **[Business Analytics](../features/business-analytics.md)** - Usage statistics
- **[Auto File Download](../features/auto-file-download.md)** - Automated downloads

### Customize Your Setup

- **[Settings Reference](../user-guide/SETTINGS_REFERENCE.md)** - Complete settings guide
- **[Configuration](configuration.md)** - Advanced configuration options

### Integrate with Other Tools

- **[API Reference](../api-reference/index.md)** - REST API documentation
- **[WebSocket API](../api-reference/websocket.md)** - Real-time updates
- **[API Automated Jobs](../user-guide/api-automated-job-creation.md)** - Automate job creation

## Common Tasks

### Check Printer Status

```bash
curl http://localhost:8000/api/v1/printers
```

### Get Active Jobs

```bash
curl http://localhost:8000/api/v1/jobs?status=in_progress
```

### Download a File

```bash
curl -X POST http://localhost:8000/api/v1/files/download \\
  -H "Content-Type: application/json" \\
  -d '{"printer_id": "abc123", "file_path": "/models/test.3mf"}'
```

See [API Reference](../api-reference/index.md) for all endpoints.

## Tips & Tricks

### Dashboard Customization

- Rearrange printer cards by dragging
- Click printer name to expand details
- Use filters to show specific printer types

### Keyboard Shortcuts

- `Ctrl/Cmd + K`: Quick search
- `Ctrl/Cmd + /`: Open command palette
- `R`: Refresh current page

### Mobile Access

Printernizer is fully responsive:
- Access from phone or tablet
- Same features as desktop
- Touch-friendly interface

### Multiple Printers

- Add as many printers as you need
- Mix Bambu Lab and Prusa printers
- View all printers in unified dashboard
- Filter and sort by various criteria

## Troubleshooting

### Printer won't connect

1. Verify printer IP address is correct
2. Check network connectivity: `ping <printer-ip>`
3. For Bambu Lab: Ensure LAN Mode is enabled
4. For Prusa: Verify PrusaLink is running
5. Check firewall settings

### Jobs not appearing

1. Ensure printer is connected (green status)
2. Verify job is actually running on printer
3. Check WebSocket connection (browser console)
4. Refresh the page

### Files not showing

1. Verify printer is connected
2. Check that printer has files on storage
3. Try manual refresh
4. Check browser console for errors

See [Troubleshooting Guide](../user-guide/troubleshooting.md) for more help.

## Getting Help

- **Documentation:** [User Guide](../user-guide/index.md)
- **Issues:** [GitHub Issues](https://github.com/schmacka/printernizer/issues)
- **API Help:** [API Reference](../api-reference/index.md)
- **Troubleshooting:** [Troubleshooting Guide](../user-guide/troubleshooting.md)

---

**Congratulations!** You're now ready to use Printernizer. Explore the documentation to learn about advanced features and customization options.
