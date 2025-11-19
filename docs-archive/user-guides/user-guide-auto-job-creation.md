# Automated Job Creation - User Guide

## Overview

The **Automated Job Creation** feature automatically creates job entries in Printernizer when your 3D printers start printing. This ensures you never miss tracking a print job, even if you forget to create one manually or if Printernizer starts while a print is already in progress.

## Key Features

### ⚡ Automatic Detection
- Monitors all connected printers in real-time
- Creates job entries automatically when a print starts
- No manual intervention required

### 🚀 Startup Discovery
- Detects prints already in progress when Printernizer starts
- Creates job entries for ongoing prints automatically
- Marked with special "discovered on startup" flag

### 🎯 Smart Deduplication
- Prevents duplicate job creation
- Uses both in-memory cache and database checks
- Handles system restarts and reconnections gracefully

### ⏱️ Accurate Time Tracking
- Captures printer-reported start times when available
- Falls back to discovery time if printer doesn't provide start time
- Tracks elapsed time accurately

### 👁️ Visual Indicators
- Auto-created jobs display a distinctive **⚡ Auto** badge
- Hover over the badge to see creation details
- Easily distinguish automatic vs. manual jobs

### 🔔 Real-Time Notifications
- Toast notifications when jobs are auto-created
- Shows printer name and filename
- Indicates if discovered on startup

## Getting Started

### Enable/Disable Auto-Creation

1. Navigate to **Settings** page
2. Find **"Automatische Auftrags-Erstellung"** section
3. Toggle the checkbox to enable or disable
4. Settings are saved automatically

**Default**: Enabled

### Configuration

The feature works out-of-the-box with default settings:

```yaml
job_creation_auto_create: true  # Enable/disable auto-creation
```

To modify this setting:
- **Via UI**: Settings page (recommended)
- **Via Config**: Edit `config.yaml` if using standalone deployment
- **Via Environment**: Set `JOB_CREATION_AUTO_CREATE=false` in Docker/HA addon

## How It Works

### Normal Print Start Flow

1. **Monitoring**: Printernizer polls printer status every 30 seconds (default)
2. **Detection**: Status changes from `ONLINE` → `PRINTING`
3. **Auto-Creation**: Job entry is created automatically
4. **Notification**: Toast notification appears
5. **Badge**: Job displays ⚡ Auto badge in list

### Startup Discovery Flow

1. **System Start**: Printernizer starts or restarts
2. **Status Check**: Checks all printer statuses on startup
3. **Detection**: Finds printer(s) with status `PRINTING`
4. **Auto-Creation**: Creates job entries for ongoing prints
5. **Special Flag**: Marked as "discovered on startup"

### Deduplication Strategy

To prevent duplicate jobs, the system uses:

1. **Discovery Time Tracking**: Records when each print was first seen
2. **In-Memory Cache**: Fast lookup for recent prints (per session)
3. **Database Fallback**: Searches database for existing jobs (±2 minute window)
4. **Filename Normalization**: Handles cache/ prefix variations

## Understanding Auto-Created Jobs

### The ⚡ Auto Badge

Jobs with the ⚡ Auto badge were created automatically. Hover over the badge to see:
- Discovery time (when Printernizer first detected the print)
- Printer start time (if reported by printer)
- Startup flag (if discovered on system startup)

### Job Details

Auto-created jobs include:

| Field | Value |
|-------|-------|
| **Job Name** | Cleaned filename (without extension) |
| **Filename** | Original filename from printer |
| **Status** | `running` (initially) |
| **Start Time** | Printer-reported or discovery time |
| **Printer** | Auto-detected from printer status |
| **Metadata** | `customer_info` with auto-creation details |

### Editing Auto-Created Jobs

Auto-created jobs can be edited like any other job:
- Click the edit button (✏️) on the job
- Update business info, customer details, material costs, etc.
- The ⚡ Auto badge remains to show its origin

## Common Scenarios

### Scenario 1: Starting a Print Manually
**You**: Start a print on your Bambu Lab A1 using the printer's touchscreen
**Printernizer**: Detects the print within 30 seconds → Creates job automatically → Shows notification

### Scenario 2: System Restart During Print
**Situation**: You restart Printernizer while a 4-hour print is halfway done
**Printernizer**: Detects the ongoing print on startup → Creates job with "discovered on startup" flag → No duplicate created

### Scenario 3: Same File Printed Twice
**You**: Print the same model twice in a row
**Printernizer**: Creates two separate job entries → No duplicate within the same print → New job for second print

### Scenario 4: Pause and Resume
**You**: Pause a print, then resume it
**Printernizer**: Does NOT create a duplicate job → Recognizes it's the same print

### Scenario 5: Network Reconnection
**Situation**: Printer loses network connection temporarily
**Printernizer**: Checks database on reconnect → Finds existing job → No duplicate created

## Troubleshooting

### Jobs Not Being Created

**Check these settings:**
1. **Auto-creation enabled**: Settings → "Automatische Auftrags-Erstellung" is checked
2. **Monitoring active**: Dashboard shows printers are being monitored
3. **Printer status**: Printer reports status as `PRINTING`
4. **Filename available**: Printer provides current filename in status

**Debug steps:**
1. Check logs for "Auto-creating job" messages
2. Verify printer connection is stable
3. Ensure monitoring interval isn't too long

### Duplicate Jobs Created

This should rarely happen, but if it does:

**Possible causes:**
1. Manual job created at nearly same time as auto-creation
2. System restart within 2-minute window
3. Cache cleared during print

**Solutions:**
- Delete the duplicate manually
- Report as bug if reproducible

### Badge Not Showing

**Possible causes:**
1. Browser cache needs refresh (Ctrl+F5)
2. Job was created manually, not auto-created
3. Old job created before feature was added

**Solutions:**
- Refresh browser
- Check job's `customer_info` field for `auto_created: true`

### Start Time Inaccurate

**Understanding start times:**
- **Printer Start Time**: Most accurate, from printer's internal clock
- **Discovery Time**: When Printernizer first saw the print
- **Difference**: Can vary based on polling interval (30s default)

**For maximum accuracy:**
- Reduce monitoring interval (Settings → 5-10 seconds)
- Note: More frequent polling = higher network load

## Best Practices

### Recommended Settings
- ✅ Keep auto-creation **enabled** (default)
- ✅ Use default monitoring interval (30 seconds)
- ✅ Enable toast notifications for awareness

### When to Use Manual Jobs
You may still want to create jobs manually when:
- Setting up business information before print starts
- Entering detailed customer information upfront
- Planning jobs in advance
- Tracking virtual/test jobs

### Integration with Other Features
- **File Downloads**: Auto-created jobs link to files automatically if available
- **Business Mode**: Mark auto-created jobs as business after creation
- **Cost Tracking**: Add material costs and business info to auto-created jobs

## Performance

The automated job creation feature is highly optimized:

| Metric | Performance |
|--------|-------------|
| Detection Latency | < 30 seconds (polling interval) |
| Creation Time | < 50ms (typical) |
| Memory Usage | ~50 bytes per cached print |
| Database Queries | < 100ms with 100+ jobs |
| Lock Contention | < 1ms (50 concurrent updates) |

**Impact on system**: Negligible - feature adds minimal overhead to existing monitoring.

## Privacy & Data

### What Data is Stored?

Auto-created jobs store:
- Filename from printer
- Printer ID and type
- Discovery timestamp
- Printer-reported start time (if available)
- Startup detection flag

### Metadata Structure

```json
{
  "auto_created": true,
  "discovery_time": "2025-01-09T14:30:00",
  "printer_start_time": "2025-01-09T14:28:45",
  "discovered_on_startup": false
}
```

This metadata is stored in the `customer_info` field (JSON) in the database.

## Advanced Configuration

### Disable for Specific Printers

Currently, auto-creation is global (all printers). Per-printer settings are a future enhancement.

**Workaround**: Disable globally, create jobs manually for desired printers.

### Adjust Detection Window

The database deduplication window is set to ±2 minutes. This is not currently configurable but can be modified in code if needed.

**Location**: `src/services/printer_monitoring_service.py:722-763`

## FAQ

**Q: Will this create jobs for test prints or warmups?**
A: Yes, any print detected will create a job. You can delete unwanted jobs afterwards or mark them differently.

**Q: Can I disable auto-creation temporarily?**
A: Yes, toggle it off in Settings. No jobs will be auto-created while disabled.

**Q: What happens to auto-created jobs after prints complete?**
A: They remain in your job history like any other job. You can edit, export, or delete them.

**Q: Does this work with both Bambu Lab and Prusa printers?**
A: Yes! Fully supports both printer types with their respective APIs.

**Q: Can I convert a manual job to auto-created or vice versa?**
A: The badge is based on the `customer_info` field. You can manually edit this in the database if needed, but there's no UI for it.

**Q: What if two printers print the same file at once?**
A: Two separate jobs are created (one per printer). The system correctly differentiates by printer ID.

## Support

### Reporting Issues
If you encounter problems with automated job creation:

1. Check this guide first
2. Review logs for error messages
3. Submit detailed bug report with:
   - Printer type and model
   - Steps to reproduce
   - Expected vs. actual behavior
   - Relevant log excerpts

### Feature Requests
Ideas for improvements? Submit feature requests for:
- Per-printer auto-creation settings
- Custom metadata fields
- Notification customization
- Integration with other systems

## Related Features

- **Job Management**: Manual job creation and editing
- **Printer Monitoring**: Real-time status tracking
- **File Management**: Automatic file downloads and linking
- **Business Mode**: Cost tracking and customer information

---

**Version**: 2.3.0
**Last Updated**: 2025-01-09
**Feature Status**: Production Ready
**Documentation**: docs/design/automated-job-creation.md
