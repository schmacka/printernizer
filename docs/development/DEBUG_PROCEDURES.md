# 🔧 Auto-Download System Debug Procedures

**Date**: September 2025
**Version**: 1.0
**For**: Error diagnosis and troubleshooting

## 📋 Overview

This document provides step-by-step debugging procedures for the Printernizer Auto-Download System, specifically for resolving download failures and backend communication issues.

> **Note**: For backend startup performance issues and slow server initialization, see [Startup Performance Analysis](development/STARTUP_PERFORMANCE_ANALYSIS.md).

## 🚨 Common Error Scenarios

### Error: "Unknown download status: error"
**Symptoms**:
- Downloads show as failed in management panel
- Error message displays "[object Object]" or "Unknown download status: error"
- Empty download folders in `C:\temp\printernizer-download\`
- Backend returns `status: "error"` instead of expected statuses

**Root Causes**:
- Backend API endpoint returning unhandled error statuses
- Printer connectivity issues
- Printer not in expected state (not printing, no active job)
- Backend service failures or timeouts

## 🛠️ Debug Tools Available

The system includes comprehensive debug utilities loaded automatically:

### Debug Commands
```javascript
// Full debug test of specific printer
debugDownload(printerId, printerName)

// Test API endpoint only (no queue processing)
testDownloadAPI(printerId)

// System health and component status check
checkDownloadHealth()

// Clear failed tasks for fresh testing
clearFailedDownloads()

// Start real-time queue monitoring (5-second intervals)
monitorDownloads(5)

// Stop monitoring
stopMonitoringDownloads()

// Export comprehensive debug report
exportDownloadDebug()
```

## 🔍 Step-by-Step Debugging Process

### Step 1: Initial System Check
1. **Reload the page** to ensure latest code is loaded
2. **Open browser DevTools** (F12) and go to Console tab
3. **Verify debug tools loaded**:
   ```
   🐛 Download Debug Tools Loaded! Available commands:
   - debugDownload(printerId, printerName) - Full debug test
   - testDownloadAPI(printerId) - Test API endpoint only
   [... more commands listed]
   ```

### Step 2: System Health Check
```javascript
checkDownloadHealth()
```

**Expected Output**:
```
🏥 Auto-Download System Health Check
🤖 System Status: {status: "active", stats: {...}, components: {...}}
📋 Download Queue Available: true
🖼️ Thumbnail Queue Available: true
📝 Logger Available: true
🖥️ UI Available: true
🤖 Manager Available: true
```

**If any component shows `false`**: System initialization failed - check console for startup errors.

### Step 3: Test Specific Failing Printer
Replace `"your-printer-id"` with the actual printer ID showing errors:

```javascript
testDownloadAPI("your-printer-id")
```

**Analyze the output**:

#### Success Response Example:
```
🔍 Testing Download Endpoint for Printer: bambu-a1-001
📡 Making API call to: /printers/bambu-a1-001/download-current-job
⏱️ API Response Time: 1250ms
📋 Full Response Object: {status: "success", file_id: "abc123", filename: "test.3mf", has_thumbnail: true}
📋 Status Field: success string
🧪 Testing Download Queue Response Handling...
✅ Would be processed as: SUCCESS
```

#### Error Response Example:
```
🔍 Testing Download Endpoint for Printer: bambu-a1-001
📡 Making API call to: /printers/bambu-a1-001/download-current-job
⏱️ API Response Time: 5000ms
📋 Full Response Object: {status: "error", message: "Printer not responding"}
📋 Status Field: error string
🧪 Testing Download Queue Response Handling...
❌ Would throw error: Download failed with error status
📋 Error message would be: Printer not responding
```

### Step 4: Interpret Backend Response

#### Valid Success Statuses:
- `"success"` - File downloaded successfully
- `"processed"` - File already processed
- `"exists_with_thumbnail"` - File exists with thumbnail
- `"exists_no_thumbnail"` - File exists without thumbnail

#### Valid Error Statuses (handled by system):
- `"error"` - Generic error (check message field)
- `"failed"` - Download operation failed
- `"not_printing"` - Printer not currently printing
- `"no_file"` - No file available for current job
- `"timeout"` - Request timed out
- `"connection_error"` - Cannot connect to printer
- `"file_not_found"` - File not found on printer
- `"access_denied"` - Permission denied

#### Response Fields to Check:
- `status` - Primary status indicator
- `message` - Human-readable error description
- `error` - Alternative error field
- `file_id` - Unique file identifier (for success)
- `filename` - Original filename (for success)
- `has_thumbnail` - Thumbnail availability boolean

### Step 5: Backend Investigation

Based on the API response, investigate backend issues:

#### If `status: "error"`:
1. **Check backend logs** for the specific endpoint
2. **Verify printer connectivity** from backend
3. **Check printer API credentials** (access codes, API keys)
4. **Test printer API directly** from backend

#### If `status: "not_printing"`:
1. **Verify printer is actually printing**
2. **Check printer status** from printer's web interface
3. **Confirm job is active** on printer

#### If `status: "connection_error"`:
1. **Check network connectivity** between backend and printer
2. **Verify printer IP address** is correct and reachable
3. **Test ping/telnet** to printer from backend server
4. **Check firewall rules** blocking printer communication

#### If API call throws exception:
1. **Check backend service** is running
2. **Verify endpoint URL** is correct
3. **Check authentication** requirements
4. **Review backend API logs** for errors

### Step 6: Clear Failed Tasks and Retry

After addressing backend issues:

```javascript
// Clear old failed attempts
clearFailedDownloads()

// Test with full system integration
debugDownload("your-printer-id", "Debug Test")
```

### Step 7: Monitor Real-time Processing

For ongoing issues, monitor the queue in real-time:

```javascript
// Start monitoring every 5 seconds
monitorDownloads(5)

// Trigger a download and watch processing
// ... trigger download via UI or debugDownload() ...

// Stop monitoring when done
stopMonitoringDownloads()
```

## 📊 Debug Report Export

For complex issues requiring support:

```javascript
exportDownloadDebug()
```

This exports a comprehensive JSON report containing:
- System status and component states
- Queue contents and statistics
- Recent log entries
- Error details
- Browser and system information

## 🔧 Common Solutions

### Solution 1: Printer Connectivity Issues
**Problem**: `status: "connection_error"` or API timeouts

**Steps**:
1. Verify printer IP address in system settings
2. Test ping from backend server to printer
3. Check printer web interface accessibility
4. Verify printer API settings (access codes, etc.)
5. Restart printer network connection if needed

### Solution 2: Printer State Issues
**Problem**: `status: "not_printing"` when printer appears to be printing

**Steps**:
1. Check printer's actual status via its web interface
2. Verify job is truly active (not paused, completed, or failed)
3. Check if printer is in correct mode for file access
4. Restart print job if needed

### Solution 3: Backend Service Issues
**Problem**: API call exceptions or `status: "error"` with generic messages

**Steps**:
1. Check backend service health and logs
2. Verify API endpoint implementation is correct
3. Test API authentication and permissions
4. Check database connectivity if backend uses DB
5. Restart backend service if necessary

### Solution 4: File Access Issues
**Problem**: `status: "file_not_found"` or `status: "access_denied"`

**Steps**:
1. Verify file actually exists on printer
2. Check printer file permissions and access rights
3. Confirm backend has proper credentials for file access
4. Check if file is locked or in use by printer
5. Verify file path and naming conventions

## 📈 Monitoring and Prevention

### Regular Health Checks
```javascript
// Daily health check
checkDownloadHealth()

// Weekly queue status
window.downloadQueue.getStats()
window.thumbnailQueue.getStats()

// Monthly log analysis
window.downloadLogger.getPerformanceMetrics(30)
```

### Proactive Monitoring Setup
```javascript
// Set up automatic monitoring alerts
setInterval(() => {
    const stats = window.downloadQueue.getStats();
    if (stats.failed > 10) {
        console.warn('🚨 High failure rate detected:', stats);
    }
}, 300000); // Check every 5 minutes
```

## 📝 Documentation Updates

When resolving issues:

1. **Document the specific error** encountered
2. **Record the backend response** details
3. **Note the solution** that worked
4. **Update this document** with new scenarios
5. **Share findings** with the development team

## 🆘 Escalation Procedures

If debugging doesn't resolve the issue:

1. **Export debug report** using `exportDownloadDebug()`
2. **Capture backend logs** for the timeframe of errors
3. **Document exact steps** that reproduce the issue
4. **Note system environment** details (OS, browser, network)
5. **Provide printer model** and firmware version information

## 🔄 Version History

- **v1.0** (Sept 2025): Initial debug procedures for "Unknown download status: error"

---

## Quick Reference

### Most Common Debug Commands
```javascript
// Quick system check
checkDownloadHealth()

// Test specific printer
testDownloadAPI("printer-id-here")

// Clear and retry
clearFailedDownloads()
debugDownload("printer-id-here", "Test Name")

// Export for support
exportDownloadDebug()
```

### Key Log Locations
- **Frontend Console**: Browser DevTools → Console
- **Backend Logs**: Check backend service logs for `/printers/{id}/download-current-job` endpoint
- **Printer Logs**: Check printer's web interface or log files
- **Download Logs**: Exported via `exportDownloadDebug()`