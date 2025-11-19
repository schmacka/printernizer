# Troubleshooting

Common issues and solutions for Printernizer. If you don't find your issue here, please [open a GitHub issue](https://github.com/schmacka/printernizer/issues).

## Quick Diagnostics

### Check System Health

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.7.0",
  "uptime": 3600,
  "database": "connected"
}
```

### Check Logs

**Python Standalone:**
```bash
# Logs are written to stdout
# Check terminal where Printernizer is running
```

**Docker:**
```bash
docker-compose logs -f printernizer
```

**Home Assistant:**
- Go to Add-on page → Printernizer → **Log** tab

## Printer Connection Issues

### Printer Won't Connect

**Symptoms:** Printer shows "Disconnected" or "Error" status

**Solutions:**

1. **Verify network connectivity:**
   ```bash
   ping <printer-ip-address>
   ```

2. **Check printer is powered on** and connected to network

3. **Verify same network/subnet** - Printer and Printernizer must be on same network

4. **For Bambu Lab:**
   - Enable "LAN Mode" in printer settings
   - Verify access code is correct
   - Check MQTT port 8883 is not blocked
   - Try rebooting the printer

5. **For Prusa:**
   - Verify PrusaLink is running (check printer screen)
   - Confirm API key is correct
   - Check HTTP port (usually 80 or 8080)
   - Access PrusaLink web interface to verify it's working

6. **Check firewall settings:**
   - Bambu Lab: Allow outbound MQTT (port 8883)
   - Prusa: Allow outbound HTTP (port 80/8080)

7. **Restart Printernizer** after fixing configuration

### Auto-Discovery Not Working

**Symptoms:** No printers found during discovery scan

**Solutions:**

1. **Ensure printers are on** and network-connected

2. **Check network settings:**
   - Disable VPN if active
   - Ensure multicast is enabled on network
   - Check router doesn't block mDNS/SSDP

3. **Try manual addition** instead (works more reliably)

4. **For Bambu Lab:**
   - Verify SSDP discovery is enabled on router
   - Check printer firmware is up to date

5. **For Prusa:**
   - Verify Bonjour/mDNS is working
   - Check printer hostname resolves: `ping prusa.local`

### Connection Drops Frequently

**Symptoms:** Printer connects then disconnects repeatedly

**Solutions:**

1. **Check network stability:**
   - Run continuous ping test
   - Check for network congestion
   - Verify WiFi signal strength (if printer is wireless)

2. **Increase retry intervals:**
   ```env
   BAMBU_RETRY_INTERVAL=60
   PRUSA_POLL_INTERVAL=10
   ```

3. **Check printer firmware:**
   - Update to latest version
   - Check manufacturer known issues

4. **Reduce polling frequency** if printer is slow to respond

## Application Issues

### Printernizer Won't Start

**Symptoms:** Application crashes on startup or won't start

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Verify dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check port availability:**
   ```bash
   # Linux/Mac
   lsof -i :8000

   # Windows
   netstat -ano | findstr :8000
   ```

4. **Check database permissions:**
   ```bash
   # Ensure data/ directory is writable
   chmod 755 data/
   ```

5. **Review logs** for specific error messages

6. **Try clean start:**
   ```bash
   # Backup database
   cp data/printernizer.db data/printernizer.db.bak

   # Remove database (creates new one)
   rm data/printernizer.db

   # Start application
   python src/main.py
   ```

### Port Already in Use

**Symptoms:** Error "Address already in use" or similar

**Solutions:**

1. **Change port:**
   ```env
   PORT=8001
   ```

2. **Kill existing process:**
   ```bash
   # Linux/Mac
   lsof -ti:8000 | xargs kill -9

   # Windows
   netstat -ano | findstr :8000
   # Note the PID, then:
   taskkill /PID <pid> /F
   ```

3. **Check for orphaned processes:**
   ```bash
   ps aux | grep python
   ```

### Web Interface Not Loading

**Symptoms:** Blank page, 404 errors, or connection refused

**Solutions:**

1. **Verify Printernizer is running:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **Check browser console** for JavaScript errors (F12)

3. **Clear browser cache** and reload

4. **Try different browser**

5. **Check firewall:**
   - Allow port 8000 inbound
   - Temporarily disable firewall to test

6. **Verify correct URL:**
   - `http://localhost:8000` (not https)
   - No trailing slash issues

## Job Monitoring Issues

### Jobs Not Appearing

**Symptoms:** Print jobs don't show up in Printernizer

**Solutions:**

1. **Verify printer connection** (must be "Connected" status)

2. **Check job is actually running** on the printer

3. **Refresh the page** or restart WebSocket connection

4. **For Bambu Lab:**
   - Verify MQTT connection is stable
   - Check printer is in LAN mode
   - Try restarting printer

5. **For Prusa:**
   - Verify PrusaLink is reporting job status
   - Check PrusaLink web interface shows job
   - Verify API polling is working

6. **Check database:**
   ```bash
   sqlite3 data/printernizer.db "SELECT * FROM jobs LIMIT 10;"
   ```

### Job Progress Not Updating

**Symptoms:** Job shows 0% or stale progress

**Solutions:**

1. **Check WebSocket connection:**
   - Open browser console (F12)
   - Look for WebSocket connection messages
   - Verify no errors

2. **Refresh the page**

3. **Verify printer is sending updates:**
   - Check printer display shows progress
   - For Prusa: Check PrusaLink shows progress

4. **Check polling interval** (for Prusa):
   ```env
   PRUSA_POLL_INTERVAL=5  # Check every 5 seconds
   ```

## File Management Issues

### Files Not Showing

**Symptoms:** File browser is empty or incomplete

**Solutions:**

1. **Verify printer connection** (must be connected)

2. **Check printer has files:**
   - For Bambu Lab: Check printer touchscreen
   - For Prusa: Check PrusaLink file browser

3. **Refresh file list:**
   - Click refresh button
   - Or reload page

4. **Check permissions:**
   - Verify API key/access code has file access

5. **Check logs** for file listing errors

### File Download Fails

**Symptoms:** Download starts but fails or gets stuck

**Solutions:**

1. **Check disk space:**
   ```bash
   df -h  # Linux/Mac
   ```

2. **Verify download path is writable:**
   ```bash
   chmod 755 ./downloads
   ```

3. **Check file exists on printer**

4. **Try smaller file** to test

5. **Check network stability:**
   - Large files may timeout on unstable connections
   - Increase timeout:
     ```env
     DOWNLOAD_TIMEOUT=600  # 10 minutes
     ```

6. **Check logs** for specific error

### 3D Preview Not Generating

**Symptoms:** File shows no preview thumbnail

**Solutions:**

1. **Check file format supported:**
   - Supported: STL, 3MF, GCODE, BGCODE
   - Others: No preview available

2. **Verify preview generation enabled:**
   ```env
   PREVIEW_ENABLED=true
   ```

3. **Check dependencies installed:**
   ```bash
   pip install trimesh numpy-stl matplotlib scipy
   ```

4. **File may be corrupted:**
   - Try downloading file manually
   - Test with different file

5. **Check logs** for generation errors

## Database Issues

### Database Locked

**Symptoms:** "Database is locked" errors

**Solutions:**

1. **Enable WAL mode:**
   ```env
   DATABASE_WAL_MODE=true
   ```

2. **Close other connections:**
   - Stop other Printernizer instances
   - Close database browser tools

3. **Check file permissions:**
   ```bash
   chmod 644 data/printernizer.db
   ```

4. **Increase timeout:**
   ```env
   DATABASE_TIMEOUT=30
   ```

### Database Corruption

**Symptoms:** "Database disk image is malformed" or similar

**Solutions:**

1. **Check database integrity:**
   ```bash
   sqlite3 data/printernizer.db "PRAGMA integrity_check;"
   ```

2. **Try to repair:**
   ```bash
   sqlite3 data/printernizer.db ".recover" | sqlite3 data/printernizer_recovered.db
   ```

3. **Restore from backup:**
   ```bash
   cp data/printernizer.db.bak data/printernizer.db
   ```

4. **If no backup, start fresh:**
   - Backup current: `cp data/printernizer.db data/printernizer.db.old`
   - Remove: `rm data/printernizer.db`
   - Restart Printernizer

## Performance Issues

### Slow Response Times

**Symptoms:** Web interface is slow or unresponsive

**Solutions:**

1. **Check system resources:**
   ```bash
   top  # Linux/Mac
   # or
   Task Manager  # Windows
   ```

2. **Reduce concurrent operations:**
   - Limit number of printers
   - Reduce polling frequency
   - Disable auto-download temporarily

3. **Increase worker processes:**
   ```env
   WORKERS=4
   ```

4. **Use SSD for database:**
   - Move database to SSD storage

5. **Clear old job history:**
   ```sql
   DELETE FROM jobs WHERE created_at < datetime('now', '-90 days');
   ```

6. **Restart Printernizer**

### High Memory Usage

**Symptoms:** Memory usage constantly increasing

**Solutions:**

1. **Restart Printernizer** (temporary fix)

2. **Check for memory leaks:**
   - Monitor memory over time
   - Report issue with details

3. **Reduce cache sizes:**
   ```env
   PREVIEW_CACHE_DAYS=7
   ```

4. **Limit concurrent downloads**

## Docker-Specific Issues

### Container Won't Start

See [Docker Deployment Guide](../deployment/docker.md#troubleshooting) for Docker-specific troubleshooting.

### Volume Permission Issues

```bash
# Fix permission issues
sudo chown -R 1000:1000 ./data
```

## Home Assistant Add-on Issues

### Add-on Won't Install

1. Check Home Assistant version (requires recent version)
2. Verify repository URL is correct
3. Check Home Assistant logs
4. Try refreshing add-on store

### Add-on Won't Start

1. Check add-on logs
2. Verify configuration is valid YAML
3. Check for port conflicts
4. Restart Home Assistant

## Getting Help

If you still have issues:

1. **Check logs** for detailed error messages
2. **Search existing issues:** [GitHub Issues](https://github.com/schmacka/printernizer/issues)
3. **Create new issue** with:
   - Printernizer version
   - Deployment method
   - Printer type
   - Steps to reproduce
   - Error logs
   - Screenshots (if applicable)

## Diagnostic Information

When reporting issues, include:

```bash
# System info
curl http://localhost:8000/api/v1/health

# Python version
python --version

# Printernizer version
cat src/main.py | grep "APP_VERSION"

# OS info
uname -a  # Linux/Mac
systeminfo  # Windows
```

## Additional Resources

- [User Guide](index.md) - General usage help
- [Settings Reference](SETTINGS_REFERENCE.md) - Configuration options
- [API Reference](../api-reference/index.md) - API documentation
- [GitHub Issues](https://github.com/schmacka/printernizer/issues) - Known issues and bug reports
