# Printernizer Frontend Button and Interactive Element Mapping

## Overview
This document provides a comprehensive list of ALL buttons and interactive elements in the Printernizer frontend, along with their associated handlers and API calls.

---

## Navigation & Theme

### 1. Theme Toggle Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 106-108
- **HTML**: `<button id="themeToggle" class="theme-toggle">`
- **Handler**: `theme-switcher.js` - theme toggle functionality
- **Event**: `addEventListener('click')` - toggles between light/dark theme
- **API Call**: None (local state only)
- **Function**: `toggleTheme()`

### 2. Navigation Toggle (Hamburger Menu)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 28-29
- **HTML**: `<button class="nav-toggle" id="navToggle">`
- **Handler**: `main.js` - line 59
- **Event**: `addEventListener('click')` - toggles mobile navigation menu
- **API Call**: None
- **Function**: Navigation menu toggle

---

## Dashboard Page

### 3. Refresh Dashboard Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 122-125
- **HTML**: `<button class="btn btn-secondary" onclick="refreshDashboard()">`
- **Handler**: `dashboard.js` - line 957
- **Event**: `onclick`
- **API Calls**: 
  - `api.getStatisticsOverview('day')` - GET `/api/v1/analytics/statistics/overview?period=day`
  - `api.getPrinters({ active: true })` - GET `/api/v1/printers?active=true`
  - `api.getJobs({...})` - GET `/api/v1/jobs` with filters
  - `api.getFiles({...})` - GET `/api/v1/files` with filters
- **Function**: `refreshDashboard()` -> `dashboardManager.refreshDashboard()`

### 4. Add Printer Button (Dashboard)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 184-186
- **HTML**: `<button class="btn btn-primary" onclick="showAddPrinter()">`
- **Handler**: `dashboard.js` / `main.js` - line 964 / 390
- **Event**: `onclick`
- **API Call**: None (opens modal)
- **Function**: `showAddPrinter()` - opens `addPrinterModal`

### 5. Dashboard Cards (Printer, Jobs, Files, Today Stats)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 130-175
- **HTML**: `<div class="card overview-card">` (clickable cards)
- **Handler**: `dashboard.js` - line 474, 657
- **Event**: `addEventListener('click')`
- **API Call**: None (navigation)
- **Function**: Navigate to respective pages

---

## Printers Page

### 6. Discover Printers Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 235-238
- **HTML**: `<button class="btn btn-secondary" onclick="discoverPrinters()" id="discoverButton">`
- **Handler**: `printers.js` - line 854
- **Event**: `onclick`
- **API Call**: `api.discoverPrinters(params)` - GET `/api/v1/printers/discover`
- **Function**: `discoverPrinters()` - discovers printers on network
- **Additional**: Also calls `api.getNetworkInterfaces()` if interface selector present

### 7. Add Printer Button (Printers Page)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 239-241
- **HTML**: `<button class="btn btn-primary" onclick="showAddPrinter()">`
- **Handler**: `printers.js` - line 1026
- **Event**: `onclick`
- **API Call**: None (opens modal)
- **Function**: `showAddPrinter()` - opens `addPrinterModal`

### 8. Mini Discover Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 254
- **HTML**: `<button class="btn btn-secondary btn-sm" onclick="discoverPrinters()">`
- **Handler**: Same as #6
- **API Call**: Same as #6

### 9. Printer Card Actions (Components)
- **File**: `/home/user/printernizer/frontend/js/components.js`
- **Line**: 36-47 (PrinterCard render)

#### 9a. Show Printer Details Button
- **HTML**: `onclick="showPrinterDetails('${printer.id}')"`
- **API Call**: `api.getPrinter(printerId)` - GET `/api/v1/printers/{printerId}`
- **Function**: Shows printer details modal

#### 9b. Show Printer Files Button
- **HTML**: `onclick="showPrinterFiles('${printer.id}')"`
- **API Call**: `api.getPrinterFiles(printerId)` - GET `/api/v1/printers/{printerId}/files`
- **Function**: Shows printer files list

#### 9c. Edit Printer Button
- **HTML**: `onclick="editPrinter('${this.printer.id}')"`
- **API Call**: `api.getPrinter(printerId)` - GET `/api/v1/printers/{printerId}`
- **Function**: Opens edit printer modal

#### 9d. Download Current Job File Button (Thumbnail)
- **HTML**: `onclick="triggerCurrentJobDownload('${this.printer.id}')"`
- **API Call**: `api.downloadCurrentJobFile(printerId)` - POST `/api/v1/printers/{printerId}/download-current-job`
- **Function**: Downloads and extracts thumbnail from current job

#### 9e. Toggle Printer Monitoring Button
- **HTML**: `onclick="togglePrinterMonitoring('${this.printer.id}')"`
- **API Calls**:
  - `api.startPrinterMonitoring(printerId)` - POST `/api/v1/printers/{printerId}/monitoring/start`
  - `api.stopPrinterMonitoring(printerId)` - POST `/api/v1/printers/{printerId}/monitoring/stop`
  - `api.getPrinterStatus(printerId)` - GET `/api/v1/printers/{printerId}/status`
- **Function**: Toggles real-time monitoring with periodic status updates

### 10. Printer Control Buttons (PrinterManager class)
- **File**: `/home/user/printernizer/frontend/js/printers.js`

#### 10a. Pause Print Button
- **Line**: 648-669
- **API Call**: `api.pausePrinter(printerId)` - POST `/api/v1/printers/{printerId}/pause`
- **Function**: `pausePrint(printerId)` - pauses current print job

#### 10b. Resume Print Button
- **Line**: 674-695
- **API Call**: `api.resumePrinter(printerId)` - POST `/api/v1/printers/{printerId}/resume`
- **Function**: `resumePrint(printerId)` - resumes paused print job

#### 10c. Stop Print Button
- **Line**: 700-721
- **API Call**: `api.stopPrinter(printerId)` - POST `/api/v1/printers/{printerId}/stop`
- **Function**: `stopPrint(printerId)` - stops current print job (irreversible)

#### 10d. Test Connection Button
- **Line**: 619-636
- **API Call**: `api.getPrinter(printerId)` - GET `/api/v1/printers/{printerId}` (to get fresh status)
- **Function**: `testConnection(printerId)` - tests printer connectivity

#### 10e. Delete Printer Button
- **Line**: 600-614
- **API Call**: `api.deletePrinter(printerId)` - DELETE `/api/v1/printers/{printerId}`
- **Function**: `deletePrinter(printerId)` - deletes printer from system

---

## Jobs Page

### 11. Refresh Jobs Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 299-302
- **HTML**: `<button class="btn btn-secondary" onclick="refreshJobs()">`
- **Handler**: `jobs.js` - line 944-946
- **Event**: `onclick`
- **API Call**: `api.getJobs(filters)` - GET `/api/v1/jobs`
- **Function**: `refreshJobs()` -> `jobManager.loadJobs()`

### 12. Job Card Actions (Components)
- **File**: `/home/user/printernizer/frontend/js/components.js`
- **Line**: 722-738

#### 12a. Show Job Details Button
- **HTML**: `onclick="showJobDetails('${this.job.id}')"`
- **API Call**: `api.getJob(jobId)` - GET `/api/v1/jobs/{jobId}`
- **Function**: Shows job details modal

#### 12b. Cancel Job Button
- **HTML**: `onclick="cancelJob('${this.job.id}')"`
- **API Call**: `api.cancelJob(jobId)` - POST `/api/v1/jobs/{jobId}/cancel`
- **Function**: Cancels the job

#### 12c. Edit Job Button
- **HTML**: `onclick="editJob('${this.job.id}')"`
- **API Call**: `api.getJob(jobId)` - GET `/api/v1/jobs/{jobId}`
- **Function**: Opens job edit modal

---

## Files Page

### 13. Refresh Files Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 415-418
- **HTML**: `<button class="btn btn-secondary" onclick="refreshFiles()">`
- **Handler**: `files.js` - line 1525-1528
- **Event**: `onclick`
- **API Calls**:
  - `api.getFiles(filters)` - GET `/api/v1/files`
  - `api.getFileStatistics()` - GET `/api/v1/files/statistics`
- **Function**: `refreshFiles()` -> `fileManager.loadFiles()` and `fileManager.loadFileStatistics()`

### 14. Clear File Search Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 399-401
- **HTML**: `<button class="search-clear-btn" id="fileSearchClear" onclick="clearFileSearch()">`
- **Handler**: `files.js` - line 1533-1548
- **Event**: `onclick`
- **API Call**: `api.getFiles(filters)` - GET `/api/v1/files` (reload without search)
- **Function**: Clears file search and reloads list

### 15. Refresh Watch Folders Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 434-436
- **HTML**: `<button class="btn btn-secondary" onclick="refreshWatchFolders()">`
- **Handler**: `files.js` - line 1588-1590
- **Event**: `onclick`
- **API Calls**:
  - `api.getWatchFolderSettings()` - GET `/api/v1/files/watch-folders/settings`
  - `api.getWatchFolderStatus()` - GET `/api/v1/files/watch-folders/status`
- **Function**: `refreshWatchFolders()` -> `fileManager.loadWatchFolders()`

### 16. Add Watch Folder Dialog Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 438-441
- **HTML**: `<button class="btn btn-primary" onclick="showAddWatchFolderDialog()">`
- **Handler**: `files.js` - line 1595-1597
- **Event**: `onclick`
- **API Call**: None (opens modal)
- **Function**: `showAddWatchFolderDialog()` - opens `addWatchFolderModal`

### 17. Load Discovered Files Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 460-462
- **HTML**: `<button class="btn btn-secondary" onclick="loadDiscoveredFiles()">`
- **Handler**: Similar to Files load
- **API Call**: `api.getFiles({...})` with specific filters

### 18. File Card Actions (Components)
- **File**: `/home/user/printernizer/frontend/js/components.js`
- **Line**: 994-1030

#### 18a. Preview File Button
- **HTML**: `onclick="previewFile('${this.file.id}')"`
- **API Call**: `api.getFile(fileId)` - GET `/api/v1/files/{fileId}`
- **Function**: Shows file preview modal

#### 18b. Download File from Printer Button
- **HTML**: `onclick="downloadFileFromPrinter('${this.file.id}')"`
- **API Call**: `api.downloadFile(fileId)` - POST `/api/v1/files/{fileId}/download`
- **Function**: Starts download of file from printer

#### 18c. Open Local File Button
- **HTML**: `onclick="openLocalFile('${this.file.id}')"`
- **API Call**: None (opens file locally)
- **Function**: Opens file in local system

#### 18d. Upload to Printer Button
- **HTML**: `onclick="uploadToPrinter('${this.file.id}')"`
- **API Call**: Calls printer file upload
- **Function**: Uploads file to printer

#### 18e. Delete Local File Button
- **HTML**: `onclick="deleteLocalFile('${this.file.id}')"`
- **API Call**: `api.deleteFile(fileId)` - DELETE `/api/v1/files/{fileId}`
- **Function**: Deletes local file from system

### 19. Watch Folder Management Buttons (Files page)

#### 19a. Add Watch Folder (Form Submit)
- **Handler**: `settings.js` - line 512-543
- **API Calls**:
  - `api.validateWatchFolder(folderPath)` - POST `/api/v1/files/watch-folders/validate`
  - `api.addWatchFolder(folderPath)` - POST `/api/v1/files/watch-folders/add`
- **Function**: `addWatchFolder()`

#### 19b. Remove Watch Folder Button
- **Handler**: `files.js` - line 1602-1604 and `settings.js` - line 545-569
- **API Call**: `api.removeWatchFolder(folderPath)` - DELETE `/api/v1/files/watch-folders/remove`
- **Function**: `removeWatchFolder(folderPath)` and `removeWatchFolderFromSettings(folderPath)`

#### 19c. Activate Watch Folder Button
- **Handler**: `files.js` - line 1609-1622
- **API Call**: `api.updateWatchFolder(folderPath, true)` - PATCH `/api/v1/files/watch-folders/update`
- **Function**: `activateWatchFolder(folderPath)`

#### 19d. Deactivate Watch Folder Button
- **Handler**: `files.js` - line 1627-1645
- **API Call**: `api.updateWatchFolder(folderPath, false)` - PATCH `/api/v1/files/watch-folders/update`
- **Function**: `deactivateWatchFolder(folderPath)`

#### 19e. Validate Watch Folder Path Button
- **Handler**: `files.js` - line 1648-1684
- **API Call**: `api.validateWatchFolder(folderPath)` - POST `/api/v1/files/watch-folders/validate`
- **Function**: `validateWatchFolderPath()`

---

## Library Page

### 20. Refresh Library Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 503-506
- **HTML**: `<button class="btn btn-secondary" onclick="refreshLibrary()">`
- **Handler**: `library.js` - library manager
- **Event**: `onclick`
- **API Call**: Reloads library data
- **Function**: `refreshLibrary()`

### 21. Clear Library Search Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 498-500
- **HTML**: `<button class="search-clear-btn" id="librarySearchClear" onclick="clearLibrarySearch()">`
- **Handler**: `library.js`
- **Event**: `onclick`
- **API Call**: Reloads files without search filter

### 22. Pagination Buttons (Library)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 611-616
- **HTML**: 
  ```html
  <button id="prevPageBtn" disabled>
  <button id="nextPageBtn" disabled>
  ```
- **Handler**: `library.js` - line 88-90
- **Event**: `addEventListener('click')`
- **API Call**: `api.getFiles({...})` with page parameter

### 23. Library File Card Actions
- **Handler**: `library.js` - line 696-714
- **API Calls**:
  - Reprocess File: POST to reprocess file
  - Download File: `api.downloadFile(fileId)`
  - Delete File: `api.deleteFile(fileId)`

---

## Materials Page

### 24. Refresh Materials Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 629-631
- **HTML**: `<button class="btn btn-secondary" onclick="materialsManager.loadMaterials()">`
- **Handler**: `materials.js` - materials manager
- **Event**: `onclick`
- **API Call**: GET `/api/v1/materials`
- **Function**: `loadMaterials()`

### 25. Add Material Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 633-636
- **HTML**: `<button class="btn btn-primary" onclick="materialsManager.showAddMaterialModal()">`
- **Handler**: `materials.js`
- **Event**: `onclick`
- **API Call**: None (opens modal)
- **Function**: `showAddMaterialModal()`

### 26. Clear Material Search Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 699-701
- **HTML**: `<button class="search-clear-btn" id="materialSearchClear" onclick="materialsManager.clearSearch()">`
- **Handler**: `materials.js`
- **Event**: `onclick`
- **API Call**: Clears search filter

### 27. View Mode Buttons (Materials)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 709-715
- **HTML**:
  ```html
  <button class="btn btn-small" id="cardsViewBtn" onclick="materialsManager.setViewMode('cards')">
  <button class="btn btn-small" id="tableViewBtn" onclick="materialsManager.setViewMode('table')">
  ```
- **Handler**: `materials.js`
- **Event**: `onclick`
- **API Call**: None (view toggle only)
- **Function**: `setViewMode('cards')` or `setViewMode('table')`

### 28. Material CRUD Operations
- **Handler**: `materials.js`
- **API Calls**:
  - Create: POST `/api/v1/materials`
  - Update: PUT/PATCH `/api/v1/materials/{id}`
  - Delete: DELETE `/api/v1/materials/{id}`
  - List: GET `/api/v1/materials`
  - Stats: GET `/api/v1/materials/stats`

---

## Ideas Page

### 29. Refresh Ideas Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 806-808
- **HTML**: `<button class="btn btn-secondary" onclick="refreshIdeas()">`
- **Handler**: `ideas.js` - line 1151
- **Event**: `onclick`
- **API Call**: `fetch('${API_BASE_URL}/api/v1/ideas')`
- **Function**: `refreshIdeas()` -> `loadMyIdeas()`

### 30. Import Idea Dialog Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 810-812
- **HTML**: `<button class="btn btn-secondary" onclick="showImportDialog()">`
- **Handler**: `ideas.js` - line 625-642
- **Event**: `onclick`
- **API Call**: None (opens modal)
- **Function**: `showImportDialog()`

### 31. Add Idea Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 814-817
- **HTML**: `<button class="btn btn-primary" onclick="showAddIdeaDialog()">`
- **Handler**: `ideas.js` - line 605-623
- **Event**: `onclick`
- **API Call**: None (opens modal)
- **Function**: `showAddIdeaDialog()`

### 32. Idea Tab Buttons
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 824-833
- **HTML**:
  ```html
  <button class="tab-button active" data-tab="my-ideas" onclick="showIdeasTab('my-ideas')">
  <button class="tab-button" data-tab="bookmarks" onclick="showIdeasTab('bookmarks')">
  <button class="tab-button" data-tab="trending" onclick="showIdeasTab('trending')">
  ```
- **Handler**: `ideas.js` - line 170-198
- **Event**: `onclick`
- **API Calls**:
  - My Ideas: `fetch('${API_BASE_URL}/api/v1/ideas')`
  - Bookmarks: `fetch(url)` where url is built from filters
  - Trending: `fetch('${API_BASE_URL}/api/v1/ideas/trending/${platform}')`
- **Function**: `showIdeasTab(tabName)`

### 33. Ideas View Mode Buttons
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 855-860
- **HTML**:
  ```html
  <button class="btn btn-small" onclick="setIdeasView('grid')" id="gridViewBtn">
  <button class="btn btn-small" onclick="setIdeasView('list')" id="listViewBtn">
  ```
- **Handler**: `ideas.js` - line 1137-1150
- **Event**: `onclick`
- **API Call**: None (view toggle)
- **Function**: `setIdeasView('grid')` or `setIdeasView('list')`

### 34. Platform Filter Buttons (Bookmarks)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 890-897
- **HTML**:
  ```html
  <button class="platform-btn active" data-platform="all" onclick="filterBookmarksByPlatform('all')">
  <button class="platform-btn" data-platform="makerworld" onclick="filterBookmarksByPlatform('makerworld')">
  <button class="platform-btn" data-platform="printables" onclick="filterBookmarksByPlatform('printables')">
  ```
- **Handler**: `ideas.js` - line 1115-1125
- **Event**: `onclick`
- **API Call**: None (filters bookmarks)
- **Function**: `filterBookmarksByPlatform(platform)`

### 35. Platform Filter Buttons (Trending)
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 919-927
- **HTML**: Similar to bookmarks
- **Handler**: `ideas.js` - line 1126-1136
- **Event**: `onclick`
- **API Call**: `fetch('${API_BASE_URL}/api/v1/ideas/trending/${platform}')`
- **Function**: `filterTrendingByPlatform(platform)`

### 36. Refresh Trending Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 929-931
- **HTML**: `<button class="btn btn-secondary" onclick="refreshTrending()">`
- **Handler**: `ideas.js` - line 1166-1181
- **Event**: `onclick`
- **API Call**: `fetch('${API_BASE_URL}/api/v1/ideas/trending/refresh', { method: 'POST' })`
- **Function**: `refreshTrending()`

### 37. Idea Card Actions

#### 37a. Add Idea (Form Submit)
- **File**: `ideas.js` - line 744-810
- **API Call**: POST `${API_BASE_URL}/api/v1/ideas/`
- **Function**: `handleAddIdea(event)`
- **Body**: `{ title, description, category, priority, is_business, tags, estimated_print_time }`

#### 37b. Edit Idea Button
- **Handler**: `ideas.js` - line 644-658
- **API Call**: `fetch('${API_BASE_URL}/api/v1/ideas/${ideaId}')`
- **Function**: `editIdea(ideaId)`

#### 37c. Edit Idea (Form Submit)
- **File**: `ideas.js` - line 812-860
- **API Call**: PUT `${API_BASE_URL}/api/v1/ideas/${ideaId}`
- **Function**: `handleEditIdea(event)`

#### 37d. View Idea Details Button
- **Handler**: `ideas.js` - line 660-676
- **API Call**: `fetch('${API_BASE_URL}/api/v1/ideas/${ideaId}')`
- **Function**: `viewIdeaDetails(ideaId)`

#### 37e. Plan Idea Button
- **Handler**: `ideas.js` - line 678-696
- **API Call**: PATCH `${API_BASE_URL}/api/v1/ideas/${ideaId}/status` with `{ status: 'planned' }`
- **Function**: `planIdea(ideaId)`

#### 37f. Start Print Button
- **Handler**: `ideas.js` - line 698-716
- **API Call**: PATCH `${API_BASE_URL}/api/v1/ideas/${ideaId}/status` with `{ status: 'printing' }`
- **Function**: `startPrint(ideaId)`

#### 37g. Save Trending as Idea Button
- **Handler**: `ideas.js` - line 718-741
- **API Call**: POST `${API_BASE_URL}/api/v1/ideas/trending/${trendingId}/save`
- **Function**: `saveTrendingAsIdea(trendingId)`

#### 37h. Import Idea (Form Submit)
- **File**: `ideas.js` - line 863-910
- **API Call**: POST `${API_BASE_URL}/api/v1/ideas/import`
- **Function**: `handleImportIdea(event)`
- **Body**: `{ import_url, source_type }`

#### 37i. Preview Import URL Button
- **Handler**: `ideas.js` - line 1190-1218
- **API Call**: Fetches the URL to preview content
- **Function**: `previewImportUrl()`

---

## Settings Page

### 38. Load Settings Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 950-952
- **HTML**: `<button class="btn btn-secondary" onclick="loadSettings()">`
- **Handler**: `settings.js` - line 500-502
- **Event**: `onclick`
- **API Call**: `api.getApplicationSettings()` - GET `/api/v1/settings`
- **Function**: `loadSettings()` -> `settingsManager.loadSettings()`

### 39. Save Settings Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 954-956
- **HTML**: `<button class="btn btn-primary" onclick="saveSettings()">`
- **Handler**: `settings.js` - line 504-506
- **Event**: `onclick`
- **API Call**: `api.updateApplicationSettings(formData)` - PUT `/api/v1/settings`
- **Function**: `saveSettings()` -> `settingsManager.saveSettings()`

### 40. Validate Downloads Path Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1020
- **HTML**: `<button type="button" class="btn btn-secondary" onclick="validateDownloadsPath()">`
- **Handler**: `settings.js` - line 608-642
- **Event**: `onclick`
- **API Call**: `api.validateDownloadsPath(folderPath)` - POST `/api/v1/settings/downloads-path/validate`
- **Function**: `validateDownloadsPath()`

### 41. Validate Library Path Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1077
- **HTML**: `<button type="button" class="btn btn-secondary" onclick="validateLibraryPath()">`
- **Handler**: `settings.js` - line 644-681
- **Event**: `onclick`
- **API Call**: `api.validateLibraryPath(folderPath)` - POST `/api/v1/settings/library-path/validate`
- **Function**: `validateLibraryPath()`

### 42. Reset Navigation Preferences Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1141
- **HTML**: `<button class="btn btn-secondary" onclick="navigationPreferencesManager.resetNavigationPreferences()">`
- **Handler**: `navigation-preferences.js`
- **Event**: `onclick`
- **API Call**: None (local state)
- **Function**: `resetNavigationPreferences()`

### 43. Shutdown Server Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1163
- **HTML**: `<button class="btn btn-danger" onclick="shutdownServer()">`
- **Handler**: `settings.js` - line 571-606
- **Event**: `onclick`
- **API Call**: `api.shutdownServer()` - POST `/api/v1/system/shutdown`
- **Function**: `shutdownServer()` - shuts down the entire server

---

## Debug Page

### 44. Refresh Debug Info Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1242-1244
- **HTML**: `<button class="btn btn-secondary" onclick="refreshDebugInfo()">`
- **Handler**: `debug.js`
- **Event**: `onclick`
- **API Call**: `api.getHealth()` - GET `/api/v1/health`
- **Function**: `refreshDebugInfo()`

### 45. Clear Logs Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1246-1248
- **HTML**: `<button class="btn btn-secondary" onclick="clearLogs()">`
- **Handler**: `debug.js`
- **Event**: `onclick`
- **API Call**: None (clears local logs)
- **Function**: `clearLogs()`

### 46. Download Logs Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1250-1252
- **HTML**: `<button class="btn btn-primary" onclick="downloadLogs()">`
- **Handler**: `debug.js`
- **Event**: `onclick`
- **API Call**: None (downloads logs locally)
- **Function**: `downloadLogs()`

### 47. Refresh Thumbnail Log Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1328
- **HTML**: `<button onclick="debugManager.refreshThumbnailLog()" class="btn btn-sm">`
- **Handler**: `debug.js`
- **Event**: `onclick`
- **API Call**: None (refreshes local debug data)
- **Function**: `debugManager.refreshThumbnailLog()`

---

## Modal/Dialog Buttons

### 48. Modal Close Buttons
- **File**: `/home/user/printernizer/frontend/index.html`
- **Multiple locations**: 1371, 1461, 1553, 1569, 1585, 1627, 1722, 1831, 1917, 1933
- **HTML**: `<button class="modal-close" onclick="closeModal('modalName')">`
- **Handler**: `main.js` - `closeModal()` function
- **Event**: `onclick`
- **API Call**: None
- **Function**: `closeModal(modalName)` - closes the specified modal

### 49. Add Printer Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: ~1450
- **HTML**: `<button type="submit" form="addPrinterForm" class="btn btn-primary">`
- **Handler**: `printer-form.js` - form submit handler
- **Event**: `form.addEventListener('submit')`
- **API Call**: `api.addPrinter(printerData)` - POST `/api/v1/printers`
- **Function**: Form submit creates new printer

### 50. Edit Printer Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Handler**: Similar to Add Printer
- **API Call**: `api.updatePrinter(printerId, printerData)` - PUT `/api/v1/printers/{printerId}`

### 51. Add Watch Folder Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: ~1610
- **HTML**: `<button type="submit" form="addWatchFolderForm" class="btn btn-primary"`
- **Handler**: `files.js` - form submit handler
- **Event**: `form.addEventListener('submit')`
- **API Calls**:
  - `api.validateWatchFolder(folderPath)` - POST validation
  - `api.addWatchFolder(folderPath)` - POST to add folder
- **Function**: Adds new watch folder

### 52. Validate Watch Folder Path Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1604
- **HTML**: `<button type="button" class="btn btn-secondary" onclick="validateWatchFolderPath()">`
- **Handler**: `files.js` - line 1648-1684
- **Event**: `onclick`
- **API Call**: `api.validateWatchFolder(folderPath)` - POST validation
- **Function**: `validateWatchFolderPath()`

### 53. Add Idea Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: ~1710
- **Handler**: `ideas.js` - line 744-810
- **Event**: `form.addEventListener('submit')`
- **API Call**: POST `/api/v1/ideas/`
- **Function**: `handleAddIdea(event)`

### 54. Edit Idea Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: ~1820
- **Handler**: `ideas.js` - line 812-860
- **Event**: `form.addEventListener('submit')`
- **API Call**: PUT `/api/v1/ideas/{ideaId}`
- **Function**: `handleEditIdea(event)`

### 55. Import Idea Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: ~1905
- **Handler**: `ideas.js` - line 863-910
- **Event**: `form.addEventListener('submit')`
- **API Call**: POST `/api/v1/ideas/import`
- **Function**: `handleImportIdea(event)`

### 56. Preview Import URL Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1844
- **HTML**: `<button type="button" class="btn btn-secondary" onclick="previewImportUrl()">`
- **Handler**: `ideas.js` - line 1190-1218
- **Event**: `onclick`
- **API Call**: Fetches preview data
- **Function**: `previewImportUrl()`

### 57. Add Material Modal Submit
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: ~2032
- **Handler**: `materials.js`
- **Event**: `form.addEventListener('submit')`
- **API Call**: POST `/api/v1/materials/`
- **Function**: Form submit creates new material

---

## Timelapses Page

### 58. Refresh Timelapses Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 335-338
- **HTML**: `<button class="btn btn-secondary" onclick="refreshTimelapses()">`
- **Handler**: `timelapses.js` - timelapses manager
- **Event**: `onclick`
- **API Call**: `api.getTimelapses(filters)` - GET `/api/v1/timelapses`
- **Function**: `refreshTimelapses()` -> `timelapseManager.loadTimelapses()`

### 59. Timelapse Card Actions (Components)
- **File**: `components.js` - timelapses section
- **API Calls**:
  - Get Timelapses: GET `/api/v1/timelapses`
  - Process Timelapse: POST `/api/v1/timelapses/{timelapseId}/process`
  - Delete Timelapse: DELETE `/api/v1/timelapses/{timelapseId}`
  - Toggle Pin: PATCH `/api/v1/timelapses/{timelapseId}/pin`
  - Link to Job: PATCH `/api/v1/timelapses/{timelapseId}/link`
  - Get Stats: GET `/api/v1/timelapses/stats`

---

## Form Search and Filter Elements

### 60. File Search Input
- **File**: `/home/user/printernizer/frontend/index.html`
- **Handler**: `files.js` - line 262-283
- **Event**: `addEventListener('input')` and `addEventListener('keypress')`
- **API Call**: `api.getFiles(filters)` with search parameter
- **Function**: Filters files as you type

### 61. File Status Filter
- **File**: `/home/user/printernizer/frontend/index.html`
- **Handler**: `files.js` - line 300-310
- **Event**: `addEventListener('change')`
- **API Call**: `api.getFiles(filters)` with status filter
- **Function**: Filters files by status

### 62. File Printer Filter
- **File**: `/home/user/printernizer/frontend/index.html`
- **Handler**: `files.js` - line 310-320
- **Event**: `addEventListener('change')`
- **API Call**: `api.getFiles(filters)` with printer filter
- **Function**: Filters files by printer

### 63. Job Status Filter
- **File**: `/home/user/printernizer/frontend/js/jobs.js`
- **Line**: 175
- **Handler**: `addEventListener('change')`
- **API Call**: `api.getJobs(filters)` with status filter
- **Function**: Filters jobs by status

### 64. Job Printer Filter
- **File**: `/home/user/printernizer/frontend/js/jobs.js`
- **Line**: 184
- **Handler**: `addEventListener('change')`
- **API Call**: `api.getJobs(filters)` with printer filter
- **Function**: Filters jobs by printer

### 65. Timelapse Status Filter
- **File**: `timelapses.js` - line 151
- **Handler**: `addEventListener('change')`
- **API Call**: `api.getTimelapses(filters)` with status filter
- **Function**: Filters timelapses by status

### 66. Timelapse Linked Only Filter
- **File**: `timelapses.js` - line 160
- **Handler**: `addEventListener('change')`
- **API Call**: `api.getTimelapses(filters)` with linked_only filter
- **Function**: Shows only linked timelapses

### 67. Materials Search Input
- **File**: `/home/user/printernizer/frontend/index.html`
- **Handler**: `materials.js` - line 52
- **Event**: `addEventListener('input')`
- **API Call**: Filters materials locally or via API
- **Function**: Searches materials

---

## Bulk Actions

### 68. Select All Files Button
- **File**: `components.js` - line 1300
- **HTML**: `<button onclick="selectAllFiles()">`
- **Function**: `selectAllFiles()`

### 69. Select None Button
- **File**: `components.js` - line 1303
- **HTML**: `<button onclick="selectNone()">`
- **Function**: `selectNone()`

### 70. Select Available Button
- **File**: `components.js` - line 1306
- **HTML**: `<button onclick="selectAvailable()">`
- **Function**: `selectAvailable()`

### 71. Download All Available Button
- **File**: `/home/user/printernizer/frontend/index.html`
- **Line**: 1292
- **HTML**: `<button class="btn btn-success" onclick="downloadAllAvailable()">`
- **Handler**: `milestone-1-2-functions.js` - line 195-230
- **Event**: `onclick`
- **API Call**: `api.downloadFile(fileId)` for each file
- **Function**: `downloadAllAvailable()`

### 72. Download Selected Button
- **File**: `components.js` - line 1380
- **HTML**: `<button class="btn btn-primary" onclick="downloadSelected()">`
- **Handler**: `milestone-1-2-functions.js` - line 232
- **Event**: `onclick`
- **API Call**: `api.downloadFile(fileId)` for each selected file
- **Function**: `downloadSelected()`

### 73. Delete Selected Button
- **File**: `components.js` - line 1383
- **HTML**: `<button class="btn btn-error" onclick="deleteSelected()">`
- **Handler**: `milestone-1-2-functions.js`
- **Event**: `onclick`
- **API Call**: `api.deleteFile(fileId)` for each selected file
- **Function**: `deleteSelected()`

---

## Summary Statistics

- **Total Buttons Identified**: 73+
- **Buttons with API Calls**: ~50+
- **API Endpoints Covered**: ~30+ distinct endpoints
- **Main API Patterns**:
  - GET: Fetch data (printers, jobs, files, etc.)
  - POST: Create or trigger actions (add printer, discover, download, etc.)
  - PUT: Update complete resources (printer, job, idea, settings)
  - PATCH: Partial updates (watch folder status, idea status, timelapse pin)
  - DELETE: Remove resources (printer, file, timelapse)

---

## API Endpoint Summary

### Core Endpoints
- `/api/v1/printers` - GET/POST (list, add)
- `/api/v1/printers/{id}` - GET/PUT/DELETE (detail, update, delete)
- `/api/v1/printers/{id}/pause` - POST (pause print)
- `/api/v1/printers/{id}/resume` - POST (resume print)
- `/api/v1/printers/{id}/stop` - POST (stop print)
- `/api/v1/printers/{id}/discover` - GET (discover printers)
- `/api/v1/printers/{id}/files` - GET (get printer files)
- `/api/v1/printers/{id}/download-current-job` - POST (download thumbnail)
- `/api/v1/printers/{id}/monitoring/start` - POST (start monitoring)
- `/api/v1/printers/{id}/monitoring/stop` - POST (stop monitoring)
- `/api/v1/printers/{id}/status` - GET (get status)
- `/api/v1/jobs` - GET (list)
- `/api/v1/jobs/{id}` - GET/PUT (detail, update)
- `/api/v1/jobs/{id}/cancel` - POST (cancel)
- `/api/v1/files` - GET (list)
- `/api/v1/files/{id}` - GET/DELETE (detail, delete)
- `/api/v1/files/{id}/download` - POST (download)
- `/api/v1/files/watch-folders/*` - Various watch folder operations
- `/api/v1/ideas` - GET/POST (list, create)
- `/api/v1/ideas/{id}` - GET/PUT (detail, update)
- `/api/v1/ideas/{id}/status` - PATCH (update status)
- `/api/v1/materials` - GET/POST (list, create)
- `/api/v1/materials/{id}` - DELETE (delete)
- `/api/v1/timelapses` - GET (list)
- `/api/v1/timelapses/{id}` - GET/DELETE (detail, delete)
- `/api/v1/timelapses/{id}/process` - POST (process)
- `/api/v1/timelapses/{id}/pin` - PATCH (toggle pin)
- `/api/v1/settings` - GET/PUT (get, update)
- `/api/v1/system/shutdown` - POST (shutdown)
- `/api/v1/health` - GET (health check)

