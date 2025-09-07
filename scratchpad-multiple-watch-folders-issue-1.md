# Scratchpad: Multiple Watch Folders - Issue #1

**Issue Link**: https://github.com/schmacka/printernizer/issues/1

## Problem Analysis

The issue requests the ability to "add multiple folders to watch them for new 3d print files". Based on my analysis of the codebase:

**Current State:**
- System downloads files from printers via API calls (Bambu Lab MQTT & Prusa HTTP)
- File service (`file_service.py`) is mostly placeholder with TODOs
- Configuration service is well-established for printer configs
- Frontend shows files from printers, not local folders

**Requirement:**
Add local folder monitoring capability to detect new 3D print files (.stl, .3mf, .gcode, etc.) in addition to existing printer file discovery.

## Implementation Plan

### Phase 1: Configuration Infrastructure
1. **Extend Settings Configuration** (`src/utils/config.py`)
   - Add `watch_folders: List[str]` to `PrinternizerSettings`
   - Add validation for folder paths
   - Support environment variable: `WATCH_FOLDERS="path1,path2,path3"`

2. **Update Configuration Service** (`src/services/config_service.py`)
   - Add methods for managing watch folders
   - `get_watch_folders()`, `add_watch_folder()`, `remove_watch_folder()`
   - Persist watch folders in configuration

### Phase 2: File Watching Service
3. **Implement FileWatcher Service** (new: `src/services/file_watcher_service.py`)
   - Use Python's `watchdog` library for cross-platform file monitoring
   - Monitor multiple folders for 3D file types (.stl, .3mf, .gcode, .obj)
   - Generate events for new/modified files
   - Handle recursive subdirectory watching

4. **Enhanced File Service** (`src/services/file_service.py`)
   - Integrate local file discovery with existing printer file discovery
   - Unified file listing (printer files + local watched files)
   - File metadata extraction (size, modification date, type)

### Phase 3: Database Integration
5. **Database Schema Updates**
   - Extend file tracking to include local files
   - Add `source` field: 'printer' | 'local_watch'
   - Add `watch_folder_id` for tracking source folder

### Phase 4: API & Frontend Integration  
6. **API Endpoints** (`src/api/routers/files.py`)
   - Extend existing file endpoints to include local files
   - Add endpoints for managing watch folders
   - `/api/watch-folders` CRUD operations

7. **Frontend Updates** (`frontend/js/files.js`)
   - Show files from both printers and watched folders
   - Add watch folder management interface
   - File source indicators (📁 Printer, 💾 Local)

### Phase 5: Configuration UI
8. **Settings Interface**
   - Add watch folder management to web interface
   - Browse/select folder dialog
   - Enable/disable watching per folder

## Technical Considerations

### File Types to Monitor
- `.stl` - STL files
- `.3mf` - 3MF manufacturing format  
- `.gcode` - G-code files
- `.obj` - Wavefront OBJ files
- `.ply` - PLY files

### Performance Considerations
- Debounce file events to avoid duplicate processing
- Limit recursive depth for subdirectories
- File size limits (existing: 500MB max)
- Exclude temporary/lock files

### Error Handling
- Handle inaccessible folders gracefully
- Network drive monitoring considerations
- Permission errors

## Dependencies
- `watchdog` - Cross-platform file system monitoring
- Existing `structlog` for logging
- Existing configuration infrastructure

## Testing Strategy
- Unit tests for file watcher service
- Integration tests with mock file system events
- End-to-end tests with actual file operations

## Implementation Steps (Small Commits)
1. Add watch_folders to configuration settings
2. Implement basic FileWatcher service
3. Integrate file watcher with file service  
4. Update database schema for local files
5. Extend API endpoints for watch folders
6. Update frontend file listing
7. Add watch folder management UI
8. Add comprehensive tests

## Future Enhancements
- File pattern filtering (e.g., ignore .tmp files)
- Real-time file preview for local files
- Automatic file organization
- Import/export of watch folder configurations