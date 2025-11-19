# Printernizer User Guide

**Complete guide to using Printernizer for 3D printer fleet management**

Version: 1.1.0
Last Updated: September 30, 2025

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Using the Dashboard](#using-the-dashboard)
5. [Managing Printers](#managing-printers)
6. [File Management (Drucker-Dateien)](#file-management-drucker-dateien)
7. [Job Monitoring](#job-monitoring)
8. [3D File Previews](#3d-file-previews)
9. [Business Analytics](#business-analytics)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Features](#advanced-features)

---

## Getting Started

### What is Printernizer?

Printernizer is a professional 3D printer management system designed for:
- **3D Printing Services**: Manage multiple printers for customer orders
- **Educational Institutions**: Monitor student print jobs across multiple printers
- **Production Environments**: Track manufacturing jobs and costs
- **Home Users**: Organize and manage personal 3D printing projects

### System Requirements

**Minimum Requirements:**
- Python 3.11 or higher
- 2GB RAM
- 500MB disk space
- Modern web browser (Chrome, Firefox, Edge, Safari)
- Network connectivity to your 3D printers

**Supported Printers:**
- Bambu Lab A1 (via MQTT)
- Prusa Core One (via PrusaLink HTTP API)

---

## Installation

### Quick Installation (Recommended)

**Windows:**
```cmd
# 1. Download Printernizer
git clone https://github.com/yourusername/printernizer.git
cd printernizer

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install fastapi uvicorn aiosqlite aiohttp websockets pydantic paho-mqtt python-dotenv aiofiles structlog trimesh numpy-stl matplotlib scipy

# 4. Start Printernizer
python -m src.main
```

**Linux/macOS:**
```bash
# 1. Download Printernizer
git clone https://github.com/yourusername/printernizer.git
cd printernizer

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install fastapi uvicorn aiosqlite aiohttp websockets pydantic paho-mqtt python-dotenv aiofiles structlog trimesh numpy-stl matplotlib scipy

# 4. Start Printernizer
./run.sh
```

### Accessing Printernizer

After starting, access Printernizer at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

---

## Configuration

### First-Time Setup

1. **Start Printernizer** using `python -m src.main` (Windows) or `./run.sh` (Linux/macOS)
2. **Open your browser** to http://localhost:8000
3. **Add your first printer** via the Dashboard

### Environment Configuration (.env)

The `.env` file in the project root contains system-wide settings:

```bash
# Application Settings
ENVIRONMENT=development
PORT=8000
LOG_LEVEL=info

# Database
DATABASE_PATH=./data/printernizer.db

# Printer Settings
PRINTER_POLLING_INTERVAL=30
MAX_CONCURRENT_DOWNLOADS=5

# Business Settings (Optional)
TIMEZONE=Europe/Berlin
CURRENCY=EUR
VAT_RATE=0.19
```

**Common Settings:**

| Setting | Description | Default |
|---------|-------------|---------|
| `PORT` | Web server port | 8000 |
| `PRINTER_POLLING_INTERVAL` | How often to check printer status (seconds) | 30 |
| `MAX_CONCURRENT_DOWNLOADS` | Maximum simultaneous file downloads | 5 |
| `TIMEZONE` | Your local timezone | Europe/Berlin |
| `LOG_LEVEL` | Logging verbosity (debug, info, warning, error) | info |

### Adding Printers

#### Bambu Lab A1 Configuration

You need three pieces of information:
1. **IP Address**: Find in printer network settings
2. **Access Code**: 8-digit code from printer display (Settings → Network → Access Code)
3. **Serial Number**: On the printer label (format: AC12345678)

**To add a Bambu Lab printer:**
1. Go to **Dashboard** → **Add Printer**
2. Select **Bambu Lab** as printer type
3. Enter:
   - Printer name (e.g., "Bambu Lab A1 #1")
   - IP address (e.g., 192.168.1.100)
   - Access code (8 digits)
   - Serial number
4. Click **Test Connection**
5. Click **Save**

#### Prusa Core One Configuration

You need:
1. **IP Address**: Find in printer network settings
2. **API Key**: Generate in PrusaLink settings on the printer

**To add a Prusa printer:**
1. Go to **Dashboard** → **Add Printer**
2. Select **Prusa** as printer type
3. Enter:
   - Printer name (e.g., "Prusa Core One #1")
   - IP address (e.g., 192.168.1.101)
   - API key (from PrusaLink)
4. Click **Test Connection**
5. Click **Save**

---

## Using the Dashboard

### Dashboard Overview

The Dashboard provides real-time monitoring of all your printers:

**Key Features:**
- **Printer Status Cards**: Live status for each printer
- **Temperature Monitoring**: Nozzle and bed temperatures
- **Job Progress**: Current print progress with estimated completion time
- **Connection Status**: Network connectivity indicators
- **Quick Actions**: Start/stop monitoring, view files, manage jobs

### Understanding Printer Status

| Status | Icon | Description |
|--------|------|-------------|
| **Idle** | 🟢 | Printer ready, no active job |
| **Printing** | 🔵 | Currently printing |
| **Paused** | 🟡 | Print paused |
| **Error** | 🔴 | Printer error or offline |
| **Offline** | ⚫ | Cannot connect to printer |

### Real-Time Updates

The dashboard updates automatically every 30 seconds via WebSocket connections. Look for:
- **Live temperature readings**
- **Progress percentage and layer count**
- **Time remaining estimates**
- **Connection quality indicators**

---

## Managing Printers

### Viewing Printer Details

Click on any printer card to see:
- **Status History**: Recent status changes
- **Current Job Details**: Layer progress, material usage, time estimates
- **Temperature Graphs**: Historical temperature data
- **Connection Health**: Response times, error rates

### Starting/Stopping Monitoring

**To start monitoring:**
1. Click **Start Monitoring** on a printer card
2. Printernizer begins polling the printer every 30 seconds
3. Real-time updates appear on the dashboard

**To stop monitoring:**
1. Click **Stop Monitoring** on a printer card
2. Polling stops, but printer configuration remains saved

### Editing Printer Configuration

1. Click printer card → **Settings** icon
2. Modify settings (name, IP, credentials)
3. Click **Test Connection** to verify changes
4. Click **Save**

### Removing a Printer

1. Click printer card → **Settings** icon
2. Scroll to bottom → **Delete Printer**
3. Confirm deletion
4. All associated jobs and files remain in the database

---

## File Management (Drucker-Dateien)

### Overview

The **Drucker-Dateien** (Printer Files) section provides unified file management across all printers.

### Viewing Files

Navigate to **Drucker-Dateien** to see:
- **Files on printer storage** (SD cards, internal storage)
- **Downloaded files** on your local system
- **File metadata**: size, type, upload date, thumbnails

### File Status Indicators

| Icon | Status | Description |
|------|--------|-------------|
| 📁 | **Available** | File on printer, not downloaded |
| ✓ | **Downloaded** | File successfully downloaded locally |
| 💾 | **Local** | File only exists locally |

### Downloading Files

**Single file download:**
1. Find file in Drucker-Dateien list
2. Click **Download** button
3. Watch progress bar
4. File saved to `data/downloads/{printer_name}/{date}/`

**Bulk download:**
1. Check boxes next to multiple files
2. Click **Download Selected** at top
3. All files download sequentially

### File Organization

Downloaded files are organized automatically:
```
data/
└── downloads/
    ├── bambu-lab-a1-1/
    │   └── 2025-09-30/
    │       ├── model1.3mf
    │       └── model2.stl
    └── prusa-core-one-1/
        └── 2025-09-30/
            └── prototype.gcode
```

### Filtering Files

Use filters to find files quickly:
- **By Printer**: Show files from specific printer
- **By Status**: Available, Downloaded, Local
- **By Type**: STL, 3MF, GCODE, BGCODE
- **Search**: Search by filename

### File Statistics

View storage statistics:
- **Total files**: Count across all printers
- **Downloaded files**: Number of local copies
- **Total size**: Storage usage
- **Available space**: Remaining disk space

---

## Job Monitoring

### Viewing Active Jobs

Navigate to **Jobs** to see:
- **Current prints**: In-progress jobs with real-time updates
- **Recent jobs**: Completed prints from last 7 days
- **Job history**: All past print jobs

### Job Information

Each job shows:
- **Job name**: Filename being printed
- **Printer**: Which printer is running the job
- **Progress**: Percentage complete and current layer
- **Time**: Elapsed time and estimated completion
- **Material**: Filament usage estimation
- **Status**: Printing, Paused, Completed, Failed

### Monitoring Print Progress

For active jobs:
- **Layer progress**: Current layer / Total layers
- **Print time**: Elapsed / Estimated total time
- **Temperature monitoring**: Nozzle and bed temps
- **Live preview**: Thumbnail of the model (if available)

### Job History

View completed jobs with:
- **Success rate**: Percentage of successful prints
- **Total print time**: Cumulative printing hours
- **Material usage**: Total filament consumed
- **Cost calculations**: Material + power costs (if configured)

---

## 3D File Previews

### Preview Support

Printernizer automatically generates thumbnails for:
- **STL files**: 3D mesh rendering
- **3MF files**: Embedded or generated thumbnails
- **GCODE files**: Toolpath visualization
- **BGCODE files**: Binary G-code with embedded previews

### Viewing Previews

**In File List:**
- Thumbnails appear automatically next to filenames
- Click thumbnail to view full-size preview

**Preview Features:**
- **Automatic generation**: First view generates thumbnail
- **Intelligent caching**: Thumbnails cached for 30 days
- **Multiple sizes**: 200x200, 256x256, 512x512 pixels
- **Fast loading**: Cached previews load in <50ms

### Preview Rendering

**STL/3MF Rendering:**
- Automatic mesh centering and scaling
- Professional gray color scheme
- 45° viewing angle for optimal visibility
- Edge highlighting for depth perception

**GCODE Toolpath Visualization:**
- Shows print path in 3D space
- Blue line rendering for clarity
- Limited to first 10,000 moves for performance
- Automatic viewport fitting

### Preview Configuration

Configure preview rendering in settings:
- **Cache duration**: How long to keep thumbnails (default: 30 days)
- **Render timeout**: Maximum time for preview generation (default: 10 seconds)
- **Camera angles**: Customize viewing angles for STL/3MF
- **Colors**: Customize face, edge, and background colors

---

## Business Analytics

### Analytics Dashboard

Navigate to **Analytics** to see:
- **Print statistics**: Total jobs, success rate, total hours
- **Material consumption**: Filament usage by printer and material type
- **Cost tracking**: Material costs, power consumption, labor hours
- **Performance metrics**: Average job time, failure rates

### Cost Calculations

**Material Costs:**
- Automatically calculated from filament usage
- Configurable material costs per kilogram
- Support for multiple material types (PLA, PETG, TPU, etc.)

**Power Costs:**
- Based on print time and printer power consumption
- Configurable electricity rates
- Per-job and cumulative calculations

**Business vs. Private:**
- Categorize jobs as business or private
- Separate cost tracking for accounting
- VAT calculations for business jobs

### Exporting Data

**Excel/CSV Export:**
1. Navigate to **Analytics** → **Export**
2. Select date range
3. Choose format (Excel or CSV)
4. Click **Export**
5. File downloads with detailed job data

**Export includes:**
- Job details (name, printer, dates, times)
- Material usage and costs
- Power consumption
- Success/failure status
- Business categorization

### German Business Compliance

For German business operations:
- **19% VAT calculations** automatic
- **EUR currency formatting** (1.234,56 €)
- **German date format** (DD.MM.YYYY)
- **GDPR-compliant data handling**
- **Export compatibility** with DATEV and German accounting software

---

## Troubleshooting

### Printer Connection Issues

**Problem: Printer shows "Offline"**

Solutions:
1. Verify printer is powered on
2. Check network connectivity: `ping <printer-ip>`
3. Verify IP address hasn't changed (DHCP lease)
4. Check credentials (Access Code for Bambu, API Key for Prusa)

**Problem: Connection keeps dropping**

Solutions:
1. Check WiFi signal strength on printer
2. Use wired Ethernet connection if possible
3. Reduce polling interval in settings
4. Check for network congestion

### File Download Issues

**Problem: Downloads fail or timeout**

Solutions:
1. Check available disk space
2. Verify network connection to printer
3. Reduce concurrent download limit
4. Try downloading smaller files first

**Problem: Downloaded files corrupted**

Solutions:
1. Re-download the file
2. Verify network stability
3. Check disk integrity
4. Update Printernizer to latest version

### Preview Generation Issues

**Problem: Thumbnails not appearing**

Solutions:
1. Verify preview libraries installed:
   ```bash
   pip install trimesh numpy-stl matplotlib scipy
   ```
2. Check preview cache directory permissions
3. View logs for rendering errors
4. Increase render timeout in settings

**Problem: Preview generation slow**

Solutions:
1. Reduce preview size in settings
2. Increase render timeout
3. Clear old cache files
4. For large files, disable GCODE toolpath rendering

### Performance Issues

**Problem: Dashboard slow or unresponsive**

Solutions:
1. Reduce number of monitored printers
2. Increase polling interval
3. Clear browser cache
4. Check system resources (CPU, RAM)

**Problem: Database errors**

Solutions:
1. Stop Printernizer
2. Backup database: `cp data/printernizer.db data/printernizer.db.backup`
3. Run database integrity check:
   ```bash
   sqlite3 data/printernizer.db "PRAGMA integrity_check;"
   ```
4. Restart Printernizer

### Logs and Debugging

**View logs:**
```bash
# Backend logs
tail -f logs/printernizer.log

# Python console output
# Check terminal where you ran the startup command
```

**Enable debug logging:**
1. Edit `.env` file
2. Change `LOG_LEVEL=info` to `LOG_LEVEL=debug`
3. Restart Printernizer
4. Debug logs show detailed operation information

---

## Advanced Features

### Watch Folders (Coming Soon)

Automatically detect new files in local folders and send to printers.

### Home Assistant Integration (Planned)

Connect Printernizer to Home Assistant for:
- Notifications when prints complete
- Automation based on printer status
- Integration with smart home devices

### Multi-User Support (Planned)

- User accounts with role-based permissions
- Team collaboration features
- Job assignment and tracking

### Advanced Analytics (Planned)

- Material inventory management
- Predictive maintenance alerts
- Custom reporting dashboards
- API access for external integrations

---

## Getting Help

### Documentation Resources

- **README.md**: Quick start and overview
- **API Documentation**: http://localhost:8000/docs
- **Development Plan**: `docs/development/development-plan.md`
- **Technical Documentation**: `docs/` directory

### Support Channels

- **GitHub Issues**: https://github.com/yourusername/printernizer/issues
- **GitHub Discussions**: https://github.com/yourusername/printernizer/discussions
- **Email Support**: sebastian@porcus3d.de (commercial license holders)

### Reporting Bugs

When reporting bugs, please include:
1. **Printernizer version**: Check bottom of dashboard
2. **Operating system**: Windows/Linux/macOS
3. **Python version**: `python --version`
4. **Printer type and model**: Bambu Lab A1, Prusa Core One, etc.
5. **Steps to reproduce**: Detailed instructions
6. **Logs**: Relevant log excerpts from `logs/printernizer.log`
7. **Screenshots**: If applicable

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Refresh dashboard |
| `Ctrl+P` | Go to Printers page |
| `Ctrl+F` | Go to Files page |
| `Ctrl+J` | Go to Jobs page |
| `Ctrl+A` | Go to Analytics page |
| `/` | Focus search box |
| `Esc` | Close modal/dialog |

---

## Best Practices

### Printer Management

1. **Use static IP addresses** for printers (configure in router DHCP settings)
2. **Test connections** before adding printers to fleet
3. **Monitor connection quality** regularly
4. **Update printer firmware** to latest stable versions

### File Management

1. **Download files regularly** to free up printer storage
2. **Organize files** by project or date
3. **Delete old files** from printer storage periodically
4. **Backup important files** outside of Printernizer

### Performance Optimization

1. **Start with fewer printers** and add more as needed
2. **Adjust polling interval** based on your needs (30-60 seconds recommended)
3. **Clear old jobs** from database periodically
4. **Monitor disk space** for downloaded files and logs

### Security

1. **Change default credentials** on printers
2. **Use strong WiFi passwords** for printer network
3. **Keep Printernizer updated** to latest version
4. **Backup database regularly**: `data/printernizer.db`
5. **Use firewall** to restrict access to Printernizer port

---

**Printernizer User Guide** - Version 1.1.0
*Making 3D printing fleet management simple and efficient*
