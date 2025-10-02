
# Issues to work on

## Major Features (v1.2.0+)
- [ ] **[METADATA-001] Enhanced 3D Model Metadata Display** 📋
  - See detailed specification: `docs/features/ENHANCED_3D_MODEL_METADATA.md`
  - **Phase 1**: Backend metadata extraction enhancements
  - **Phase 2**: Frontend display improvements 
  - **Phase 3**: Advanced analysis and recommendations
  - Related tasks:
    - [ ] Files: Layer count and other statistics of the file
    - [ ] Printer tile: Layer count and other statistics of currently printed object

## Frontend Issues
- [ ] **Files: Add search bar to search for files by name**
- [x] **Files: 762 files in the statistics menu. Is that correct?**
- [ ] **Debug page: show the information in Anwendungsprotokolle with multiple columns instead of these blocks**
- [x] **Debug page: System-Status nicht verfügbar - Die Gesundheitsinformationen konnten nicht abgerufen werden**
- [ ] **Too many notifications piling up** - Not multiple of the same one at once. E.g. Only one message should appear that shows the connection status to the backend, currently we have multiple at once
- [ ] **Autodownload notification says ready even when the backend is offline**
- [ ] **Fix frontend error: POST /api/v1/errors/report returns 501 Unsupported method**
  ```
  ::ffff:192.168.176.159 - - [01/Oct/2025 10:06:48] code 501, message Unsupported method ('POST')
  ::ffff:192.168.176.159 - - [01/Oct/2025 10:06:48] "POST /api/v1/errors/report HTTP/1.1" 501 -
  ```
- [ ] **Grey out printer in dashboard when connection is in progress** - Show type of connection
- [ ] **Progress bar is gone**
- [ ] **Printer tile: Show preview image or placeholder if preview is not available**
- [ ] **Printer tile: Showing "Druckt" twice**

## Backend Issues
- [ ] **Cleanup .env or .env.sample** - Which of these values are actually used?
- [ ] **Watchdog Observer Thread Failure** - Windows threading compatibility fix (currently running in degraded fallback polling mode)
- [ ] **Bambu FTP Connection Timeouts** - Initial connection attempts fail (retry mechanism works but slow)
- [ ] **Bambu MQTT Connection Instability** - Multiple timeout/reconnect cycles before stable connection

## On Hold
- [ ] **Is the feature that identifies warmup procedure of the printers enabled?**

## Ideas for Later
- [ ] **Job History**
- [ ] **Auto Download System verification**
- [ ] **Timelapse cleaner**
- [ ] **Connect with porcus3d.de for print jobs**
- [ ] **Favorites from Makerworld and Printables**
- [ ] **Mailbox Integration**

---

# Completed (v1.1.0 - v1.1.7)

## v1.1.9 (Latest)
- [x] **Debug page: System-Status nicht verfügbar - Die Gesundheitsinformationen konnten nicht abgerufen werden** - Fixed hardcoded API URLs and service status display

## v1.1.8
- [x] **FIX: Static file paths in index.html** - Added /static/ prefix to all CSS, JS, and asset paths so files load correctly from backend

## v1.1.7
- [x] **Files: Parse file sizes from Bambu Lab FTP listings** - Files were showing "0 B" size

## v1.1.6
- [x] **Files: Add missing truncateText utility function** - Fixed discovered files display

## v1.1.5
- [x] **Add app footer with version display**
- [x] **Fix debug page initialization**

## v1.1.4
- [x] **Investigate and document Prusa BGCode download bug**

## v1.1.3
- [x] **Install Brotli library** - Fixed trending feature (MakerWorld/Printables)

## v1.1.2
- [x] **Fix NULL job IDs in database** - Job validation errors resolved

## v1.1.1
- [x] **Remove GZipMiddleware** - Resolved shutdown gzip errors

## v1.1.0
- [x] **Files: Can sort by printer** - A1BL and CoreOne now selectable (was only showing "Alle Drucker")
- [x] **Files: Fehlermeldung "Fehler beim Laden Entdeckte Dateien" fixed**

## v1.0.0 (Critical Security & Stability)
- [x] **Replace default secret key** with proper secret management
- [x] **Fix file watcher threading issue** for Windows compatibility
- [x] **Resolve EventService interface inconsistency**
- [x] **Clean up hardcoded credentials** in all files
- [x] **Fix trending service HTTP errors**



