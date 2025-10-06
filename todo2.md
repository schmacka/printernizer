
# Issues to work on

## Library
- [ ] **Tags** Ad custom tags to files

## Frontend Issues
- [ ] **Debug page: show the information in Anwendungsprotokolle with multiple columns instead of these blocks**

- [ ] **Too many notifications piling up** - Not multiple of the same one at once. E.g. Only one message should appear that shows the connection status to the backend, currently we have multiple at once
- [ ] **Autodownload notification says ready even when the backend is offline**
- [x] **Fix frontend error: POST /api/v1/errors/report returns 501 Unsupported method** - Endpoint verified working correctly, likely resolved by server restart
- [ ] **Grey out printer in dashboard when connection is in progress** - Show type of connection
- [ ] **Printer tile: Show preview image or placeholder if preview is not available**
- [x] **Printer tile: Showing "Druckt" twice** - Removed duplicate job status badge

## Backend Issues
### Prio 1
✅ All Prio 1 items completed
### Prio 2
- [ ] **Cleanup .env or .env.sample** - Which of these values are actually used?
- [ ] **Watchdog Observer Thread Failure** - Windows threading compatibility fix (currently running in degraded fallback polling mode)
- [ ] **Bambu FTP Connection Timeouts** - Initial connection attempts fail (retry mechanism works but slow)
- [ ] **Bambu MQTT Connection Instability** - Multiple timeout/reconnect cycles before stable connection

## On Hold
- [ ] **Is the feature that identifies warmup procedure of the printers enabled?**

## Ideas for Later
- [ ] **feature:Open in Slicer** open file in Slicer (Multple slicers possible)
- [ ] **Job History**
- [ ] **Timelapse cleaner**
- [ ] **Connect with porcus3d.de for print jobs**
- [ ] **Favorites from Makerworld and Printables**
- [ ] **Mailbox Integration**

---

# Completed (v1.1.0 - v1.1.7)

## to be sorted
- [x] **Files: 762 files in the statistics menu. Is that correct?**
- [x] **Debug page: System-Status nicht verfügbar - Die Gesundheitsinformationen konnten nicht abgerufen werden**
- [x] **Files: Add search bar to search for files by name**


## v1.5.2 (Latest)
- [x] **Printer tile: Showing "Druckt" twice** - Removed duplicate job status badge, replaced "gerade eben" with "Druckt" when printing
- [x] **Progress bar improvements** - Fixed progress bar to properly display current print progress

## v1.5.1
- [x] **Progress bar is gone** - Fixed progress bar visibility for printing jobs in printer cards

## v1.5.0
- [x] **Metadata and Thumbnail Extraction** - Complete support for STL, gcode, and bgcode files with comprehensive documentation
- [x] **Library Metadata Extraction** - Automatic metadata extraction for library files
- [x] **Bulk Re-analysis Functionality** - Ability to re-analyze all library files
- [x] **Automatic Versioning** - Implemented git tag-based versioning
- [x] **Duplicate Toast Messages Fixed** - File list updates when removing watch folders
- [x] **Watch Folder Modal Improvements** - Modal now closes properly after successful addition
- [x] **Code Quality Cleanup** - Priority 2 code cleanup completed (dead code removal)
- [x] **Comprehensive Logging** - Added detailed logging for watch folder operations

## v1.1.9
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



