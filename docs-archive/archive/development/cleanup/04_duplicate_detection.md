# Phase 2: Duplicate Detection Report

**Generated**: Phase 2 Analysis

## Executive Summary

- **Exact Name Duplicates**: 117
- **Similar Name Groups**: 164
- **Identical Signature Groups**: 59
- **Structural Duplicates**: 9
- **Single-Use Functions**: 56
- **Potentially Unused Functions**: 120

## 🔴 Exact Name Duplicates (High Priority)

Functions with identical names in different files.

### `__init__` (52 occurrences)

**Severity**: MEDIUM

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| scripts\analyze_codebase.py | 23 | `(self, filepath: str)` | FunctionAnalyzer | dunder |
| scripts\bambu_credentials.py | 18 | `(self)` | BambuCredentials | dunder |
| scripts\download_bambu_files.py | 54 | `(self, download_base_dir: str)` | BambuDownloadManager | dunder |
| scripts\error_analysis_agent.py | 31 | `(self, log_file_path)` | ErrorAnalysisAgent | dunder |
| scripts\test_complete_bambu_ftp.py | 49 | `(self, ip_address: str, access_code: str)` | BambuFTPTester | dunder |
| scripts\working_bambu_ftp.py | 15 | `(self, host, port)` | BambuFTP | dunder |
| src\api\routers\errors.py | 48 | `(self)` | ErrorStoreService | dunder |
| src\api\routers\websocket.py | 21 | `(self)` | ConnectionManager | dunder |
| src\database\database.py | 22 | `(self, db_path: Optional[str])` | Database | dunder |
| src\printers\bambu_lab.py | 39 | `(self, printer_id: str, name: str, ip_address: str, access_code: str, serial_number: str, file_service)` | BambuLabPrinter | dunder |
| src\printers\base.py | 33 | `(self, filename: str, size: Optional[int], modified: Optional[datetime], path: Optional[str], file_type: Optional[str])` | PrinterFile | dunder |
| src\printers\base.py | 63 | `(self, job_id: str, name: str, status: JobStatus, progress: Optional[int], estimated_time: Optional[int], elapsed_time: Optional[int])` | JobInfo | dunder |
| src\printers\base.py | 146 | `(self, printer_id: str, name: str, ip_address: str)` | BasePrinter | dunder |
| src\printers\prusa.py | 23 | `(self, printer_id: str, name: str, ip_address: str, api_key: str, file_service)` | PrusaPrinter | dunder |
| src\services\analytics_service.py | 16 | `(self, database: Database)` | AnalyticsService | dunder |
| src\services\bambu_ftp_service.py | 32 | `(self, name: str, size: int, permissions: str, modified: Optional[datetime], raw_line: str)` | BambuFTPFile | dunder |
| src\services\bambu_ftp_service.py | 80 | `(self, ip_address: str, access_code: str, port: int)` | BambuFTPService | dunder |
| src\services\bambu_parser.py | 82 | `(self)` | BambuParser | dunder |
| src\services\config_service.py | 192 | `(self, config_path: Optional[str], database)` | ConfigService | dunder |
| src\services\event_service.py | 16 | `(self, printer_service, job_service, file_service, database)` | EventService | dunder |
| src\services\file_service.py | 24 | `(self, database: Database, event_service: EventService, file_watcher: Optional[FileWatcherService], printer_service, config_service, library_service)` | FileService | dunder |
| src\services\file_watcher_service.py | 54 | `(self, file_watcher: 'FileWatcherService')` | PrintFileHandler | dunder |
| src\services\file_watcher_service.py | 126 | `(self, config_service: ConfigService, event_service: EventService, library_service)` | FileWatcherService | dunder |
| src\services\idea_service.py | 20 | `(self, db: Database)` | IdeaService | dunder |
| src\services\job_service.py | 20 | `(self, database: Database, event_service: EventService)` | JobService | dunder |
| src\services\library_service.py | 24 | `(self, database, config_service, event_service)` | LibraryService | dunder |
| src\services\material_service.py | 39 | `(self, db: Database, event_service: EventService)` | MaterialService | dunder |
| src\services\migration_service.py | 19 | `(self, database: Database)` | MigrationService | dunder |
| src\services\monitoring_service.py | 21 | `(self)` | MonitoringService | dunder |
| src\services\preview_render_service.py | 37 | `(self, cache_dir: str)` | PreviewRenderService | dunder |
| src\services\printer_service.py | 24 | `(self, database: Database, event_service: EventService, config_service: ConfigService, file_service)` | PrinterService | dunder |
| src\services\threemf_analyzer.py | 18 | `(self)` | ThreeMFAnalyzer | dunder |
| src\services\thumbnail_service.py | 27 | `(self, event_service: EventService)` | ThumbnailService | dunder |
| src\services\trending_service.py | 34 | `(self, db: Database, event_service: EventService)` | TrendingService | dunder |
| src\services\url_parser_service.py | 19 | `(self)` | UrlParserService | dunder |
| src\services\watch_folder_db_service.py | 21 | `(self, database: Database)` | WatchFolderDbService | dunder |
| src\utils\error_handling.py | 45 | `(self)` | ErrorHandler | dunder |
| src\utils\exceptions.py | 12 | `(self, message: str, error_code: str, status_code: int, details: Optional[Dict[str, Any]])` | PrinternizerException | dunder |
| src\utils\exceptions.py | 31 | `(self, message: str, details: Optional[Dict[str, Any]])` | ConfigurationError | dunder |
| src\utils\exceptions.py | 43 | `(self, message: str, details: Optional[Dict[str, Any]])` | DatabaseError | dunder |
| src\utils\exceptions.py | 55 | `(self, printer_id: str, message: str, details: Optional[Dict[str, Any]])` | PrinterConnectionError | dunder |
| src\utils\exceptions.py | 67 | `(self, operation: str, filename: str, message: str, details: Optional[Dict[str, Any]])` | FileOperationError | dunder |
| src\utils\exceptions.py | 79 | `(self, field: str, message: str, details: Optional[Dict[str, Any]])` | ValidationError | dunder |
| src\utils\exceptions.py | 91 | `(self, message: str, details: Optional[Dict[str, Any]])` | AuthenticationError | dunder |
| src\utils\exceptions.py | 103 | `(self, message: str, details: Optional[Dict[str, Any]])` | AuthorizationError | dunder |
| src\utils\exceptions.py | 115 | `(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]])` | NotFoundError | dunder |
| src\utils\gcode_analyzer.py | 36 | `(self, optimize_enabled: bool)` | GcodeAnalyzer | dunder |
| tests\backend\test_error_handling.py | 788 | `(self)` | CircularReference | dunder |
| tests\backend\test_performance.py | 427 | `(self)` | WebSocketLoadTester | dunder |
| tests\backend\test_performance.py | 667 | `(self, max_connections)` | DatabaseConnectionPool | dunder |
| tests\run_milestone_1_2_tests.py | 28 | `(self)` | Milestone12TestRunner | dunder |
| tests\test_runner.py | 19 | `(self, project_root)` | PrinternizerTestRunner | dunder |

### `main` (13 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| scripts\analyze_codebase.py | 351 | `()` | None | public |
| scripts\download_bambu_files.py | 325 | `()` | None | public |
| scripts\error_analysis_agent.py | 460 | `()` | None | public |
| scripts\quick_bambu_check.py | 9 | `()` | None | public |
| scripts\simple_bambu_test.py | 109 | `()` | None | public |
| scripts\test_bambu_credentials.py | 226 | `()` | None | public |
| scripts\test_bambu_ftp_direct.py | 294 | `()` | None | public |
| scripts\test_complete_bambu_ftp.py | 361 | `()` | None | public |
| scripts\verify_bambu_download.py | 185 | `()` | None | public |
| tests\run_essential_tests.py | 13 | `()` | None | public |
| tests\run_milestone_1_2_tests.py | 222 | `()` | None | public |
| tests\test_runner.py | 650 | `()` | None | public |
| verify_phase2_integration.py | 35 | `()` | None | public |

### `download_file` (9 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| scripts\test_bambu_ftp_direct.py | 169 | `(ftp: ftplib.FTP_TLS, remote_filename: str, local_path: str)` | None | public |
| scripts\working_bambu_ftp.py | 127 | `(self, filename, local_path)` | BambuFTP | public |
| src\api\routers\files.py | 167 | `(file_id: str, file_service: FileService)` | None | public |
| src\printers\bambu_lab.py | 1299 | `(self, filename: str, local_path: str)` | BambuLabPrinter | public |
| src\printers\base.py | 108 | `(self, filename: str, local_path: str)` | PrinterInterface | public |
| src\printers\prusa.py | 477 | `(self, filename: str, local_path: str)` | PrusaPrinter | public |
| src\services\bambu_ftp_service.py | 296 | `(self, remote_filename: str, local_path: str, directory: str)` | BambuFTPService | public |
| src\services\file_service.py | 192 | `(self, printer_id: str, filename: str, destination_path: Optional[str])` | FileService | public |
| tests\backend\test_api_files.py | 496 | `(file_id)` | TestFileAPIPerformance | public |

### `list_files` (8 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| scripts\working_bambu_ftp.py | 69 | `(self)` | BambuFTP | public |
| src\api\routers\files.py | 61 | `(printer_id: Optional[str], status: Optional[FileStatus], source: Optional[FileSource], has_thumbnail: Optional[bool], search: Optional[str], limit: Optional[int], order_by: Optional[str], order_dir: Optional[str], page: Optional[int], file_service: FileService)` | None | public |
| src\database\database.py | 613 | `(self, printer_id: Optional[str], status: Optional[str], source: Optional[str])` | Database | public |
| src\printers\bambu_lab.py | 840 | `(self)` | BambuLabPrinter | public |
| src\printers\base.py | 103 | `(self)` | PrinterInterface | public |
| src\printers\prusa.py | 316 | `(self)` | PrusaPrinter | public |
| src\services\bambu_ftp_service.py | 194 | `(self, directory: str)` | BambuFTPService | public |
| src\services\library_service.py | 449 | `(self, filters: Dict[str, Any], page: int, limit: int)` | LibraryService | public |

### `connect` (5 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| scripts\working_bambu_ftp.py | 21 | `(self)` | BambuFTP | public |
| src\api\routers\websocket.py | 25 | `(self, websocket: WebSocket)` | ConnectionManager | public |
| src\printers\bambu_lab.py | 98 | `(self)` | BambuLabPrinter | public |
| src\printers\base.py | 83 | `(self)` | PrinterInterface | public |
| src\printers\prusa.py | 32 | `(self)` | PrusaPrinter | public |

### `initialize` (5 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\database\database.py | 31 | `(self)` | Database | public |
| src\services\library_service.py | 52 | `(self)` | LibraryService | public |
| src\services\material_service.py | 46 | `(self)` | MaterialService | public |
| src\services\printer_service.py | 35 | `(self)` | PrinterService | public |
| src\services\trending_service.py | 55 | `(self)` | TrendingService | public |

### `to_dict` (5 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\models\idea.py | 49 | `(self)` | Idea | public |
| src\models\idea.py | 138 | `(self)` | TrendingItem | public |
| src\models\watch_folder.py | 47 | `(self)` | WatchFolder | public |
| src\services\bambu_ftp_service.py | 64 | `(self)` | BambuFTPFile | public |
| src\services\config_service.py | 62 | `(self)` | PrinterConfig | public |

### `take_snapshot` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\camera.py | 119 | `(printer_id: UUID, snapshot_data: SnapshotCreate, printer_service: PrinterService)` | None | public |
| src\printers\bambu_lab.py | 1746 | `(self)` | BambuLabPrinter | public |
| src\printers\base.py | 138 | `(self)` | PrinterInterface | public |
| src\printers\prusa.py | 780 | `(self)` | PrusaPrinter | public |

### `health_check` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\health.py | 38 | `(request: Request, config: ConfigService, db: Database)` | None | public |
| src\database\database.py | 282 | `(self)` | Database | public |
| src\printers\base.py | 253 | `(self)` | BasePrinter | public |
| src\services\printer_service.py | 623 | `(self)` | PrinterService | public |

### `get_printer` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\printers.py | 177 | `(printer_id: UUID, printer_service: PrinterService)` | None | public |
| src\database\database.py | 325 | `(self, printer_id: str)` | Database | public |
| src\services\config_service.py | 311 | `(self, printer_id: str)` | ConfigService | public |
| src\services\printer_service.py | 305 | `(self, printer_id: str)` | PrinterService | public |

### `get_trending` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\trending.py | 52 | `(platform: Optional[str], category: Optional[str], limit: int, trending_service: TrendingService)` | None | public |
| src\database\database.py | 1023 | `(self, platform: Optional[str], category: Optional[str])` | Database | public |
| src\services\idea_service.py | 272 | `(self, platform: Optional[str], category: Optional[str])` | IdeaService | public |
| src\services\trending_service.py | 466 | `(self, platform: Optional[str], category: Optional[str], limit: int)` | TrendingService | public |

### `disconnect` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\websocket.py | 30 | `(self, websocket: WebSocket)` | ConnectionManager | public |
| src\printers\bambu_lab.py | 236 | `(self)` | BambuLabPrinter | public |
| src\printers\base.py | 88 | `(self)` | PrinterInterface | public |
| src\printers\prusa.py | 115 | `(self)` | PrusaPrinter | public |

### `from_dict` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\models\idea.py | 74 | `(cls, data: Dict[str, Any])` | Idea | public |
| src\models\idea.py | 157 | `(cls, data: Dict[str, Any])` | TrendingItem | public |
| src\models\watch_folder.py | 67 | `(cls, data: Dict[str, Any])` | WatchFolder | public |
| src\services\config_service.py | 49 | `(cls, printer_id: str, config: Dict[str, Any])` | PrinterConfig | public |

### `get_status` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\printers\bambu_lab.py | 262 | `(self)` | BambuLabPrinter | public |
| src\printers\base.py | 93 | `(self)` | PrinterInterface | public |
| src\printers\prusa.py | 133 | `(self)` | PrusaPrinter | public |
| src\services\event_service.py | 452 | `(self)` | EventService | public |

### `get_statistics` (4 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\services\idea_service.py | 197 | `(self)` | IdeaService | public |
| src\services\material_service.py | 304 | `(self)` | MaterialService | public |
| src\services\preview_render_service.py | 537 | `(self)` | PreviewRenderService | public |
| src\services\trending_service.py | 595 | `(self)` | TrendingService | public |

### `analyze_file` (3 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| scripts\analyze_codebase.py | 145 | `(filepath: str)` | None | public |
| src\api\routers\files.py | 661 | `(file_id: str, include_recommendations: bool, file_service: FileService)` | None | public |
| src\services\threemf_analyzer.py | 22 | `(self, file_path: Path)` | ThreeMFAnalyzer | public |

### `get_error_statistics` (3 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\errors.py | 111 | `(self, hours: int)` | ErrorStoreService | public |
| src\api\routers\errors.py | 238 | `(hours: int)` | None | public |
| src\utils\error_handling.py | 164 | `(self, hours: int)` | ErrorHandler | public |

### `get_file_statistics` (3 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\files.py | 124 | `(file_service: FileService)` | None | public |
| src\database\database.py | 790 | `(self)` | Database | public |
| src\services\file_service.py | 458 | `(self)` | FileService | public |

### `get_file_by_id` (3 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\files.py | 143 | `(file_id: str, file_service: FileService)` | None | public |
| src\services\file_service.py | 688 | `(self, file_id: str)` | FileService | public |
| src\services\library_service.py | 437 | `(self, file_id: str)` | LibraryService | public |

### `get_watch_folder_settings` (3 occurrences)

**Severity**: HIGH

| File | Line | Signature | Class | Access |
|------|------|-----------|-------|--------|
| src\api\routers\files.py | 363 | `(config_service: ConfigService)` | None | public |
| src\api\routers\settings.py | 234 | `(config_service: ConfigService)` | None | public |
| src\services\config_service.py | 441 | `(self)` | ConfigService | public |

## 🟡 Similar Name Patterns (Medium Priority)

Functions with similar names that may indicate duplicate functionality.

### Pattern: `_statistics` (16 functions)

| Function | File | Line |
|----------|------|------|
| `get_error_statistics` | src\api\routers\errors.py | 111 |
| `get_file_statistics` | src\api\routers\files.py | 124 |
| `get_idea_statistics` | src\api\routers\ideas.py | 301 |
| `get_library_statistics` | src\api\routers\library.py | 329 |
| `get_job_statistics` | src\database\database.py | 455 |
| `get_file_statistics` | src\database\database.py | 790 |
| `get_idea_statistics` | src\database\database.py | 1055 |
| `get_file_statistics` | src\services\file_service.py | 458 |
| `get_statistics` | src\services\idea_service.py | 197 |
| `get_job_statistics` | src\services\job_service.py | 339 |
| `get_library_statistics` | src\services\library_service.py | 560 |
| `get_statistics` | src\services\material_service.py | 304 |
| `get_statistics` | src\services\preview_render_service.py | 537 |
| `get_cache_statistics` | src\services\thumbnail_service.py | 233 |
| `get_statistics` | src\services\trending_service.py | 595 |
| `get_error_statistics` | src\utils\error_handling.py | 164 |

### Pattern: `[list_files, list_files, list_local_files...]` (13 functions)

| Function | File | Line |
|----------|------|------|
| `list_files` | scripts\working_bambu_ftp.py | 69 |
| `list_files` | src\api\routers\files.py | 61 |
| `list_local_files` | src\api\routers\files.py | 399 |
| `list_ideas` | src\api\routers\ideas.py | 99 |
| `list_files` | src\database\database.py | 613 |
| `list_local_files` | src\database\database.py | 763 |
| `list_ideas` | src\database\database.py | 862 |
| `list_files` | src\printers\bambu_lab.py | 840 |
| `list_files` | src\printers\base.py | 103 |
| `list_files` | src\printers\prusa.py | 316 |
| `list_files` | src\services\bambu_ftp_service.py | 194 |
| `list_ideas` | src\services\idea_service.py | 88 |
| `list_files` | src\services\library_service.py | 449 |

### Pattern: `download_` (11 functions)

| Function | File | Line |
|----------|------|------|
| `download_target_file` | scripts\download_target_file.py | 21 |
| `download_file` | scripts\test_bambu_ftp_direct.py | 169 |
| `download_file` | scripts\working_bambu_ftp.py | 127 |
| `download_printer_file` | src\api\routers\printers.py | 468 |
| `download_file` | src\printers\bambu_lab.py | 1299 |
| `download_file` | src\printers\base.py | 108 |
| `download_file` | src\printers\prusa.py | 477 |
| `download_file` | src\services\bambu_ftp_service.py | 296 |
| `download_file` | src\services\file_service.py | 192 |
| `download_printer_file` | src\services\printer_service.py | 526 |
| `download_file` | tests\backend\test_api_files.py | 496 |

### Pattern: `connect` (11 functions)

| Function | File | Line |
|----------|------|------|
| `connect` | scripts\working_bambu_ftp.py | 21 |
| `connect` | src\api\routers\websocket.py | 25 |
| `disconnect` | src\api\routers\websocket.py | 30 |
| `connection` | src\database\database.py | 276 |
| `connect` | src\printers\bambu_lab.py | 98 |
| `disconnect` | src\printers\bambu_lab.py | 236 |
| `connect` | src\printers\base.py | 83 |
| `disconnect` | src\printers\base.py | 88 |
| `connect` | src\printers\prusa.py | 32 |
| `disconnect` | src\printers\prusa.py | 115 |
| `mock_connect` | tests\backend\test_integration.py | 510 |

### Pattern: `_printer` (11 functions)

| Function | File | Line |
|----------|------|------|
| `create_printer` | src\api\routers\printers.py | 146 |
| `remove_printer` | src\api\routers\settings.py | 192 |
| `create_printer` | src\database\database.py | 304 |
| `get_printer` | src\database\database.py | 325 |
| `get_printer` | src\services\config_service.py | 311 |
| `remove_printer` | src\services\config_service.py | 338 |
| `get_printer` | src\services\printer_service.py | 305 |
| `create_printer` | src\services\printer_service.py | 671 |
| `update_printer` | src\services\printer_service.py | 723 |
| `delete_printer` | src\services\printer_service.py | 775 |
| `resume_printer` | src\services\printer_service.py | 803 |

### Pattern: `[get_camera_status, get_material_stats, get_status...]` (9 functions)

| Function | File | Line |
|----------|------|------|
| `get_camera_status` | src\api\routers\camera.py | 24 |
| `get_material_stats` | src\api\routers\materials.py | 114 |
| `get_status` | src\printers\bambu_lab.py | 262 |
| `get_camera_stream_url` | src\printers\bambu_lab.py | 1725 |
| `get_status` | src\printers\base.py | 93 |
| `get_camera_stream_url` | src\printers\base.py | 133 |
| `get_status` | src\printers\prusa.py | 133 |
| `get_camera_stream_url` | src\printers\prusa.py | 774 |
| `get_status` | src\services\event_service.py | 452 |

### Pattern: `delete_` (7 functions)

| Function | File | Line |
|----------|------|------|
| `delete_file` | src\api\routers\files.py | 574 |
| `delete_idea` | src\api\routers\ideas.py | 193 |
| `delete_local_file` | src\database\database.py | 782 |
| `delete_idea` | src\database\database.py | 926 |
| `delete_file` | src\services\file_service.py | 732 |
| `delete_idea` | src\services\idea_service.py | 165 |
| `delete_file` | src\services\library_service.py | 518 |

### Pattern: `get_job` (7 functions)

| Function | File | Line |
|----------|------|------|
| `get_job` | src\api\routers\jobs.py | 105 |
| `get_job` | src\database\database.py | 384 |
| `get_job_info` | src\printers\bambu_lab.py | 750 |
| `get_job_info` | src\printers\base.py | 98 |
| `get_job_info` | src\printers\prusa.py | 253 |
| `get_jobs` | src\services\job_service.py | 25 |
| `get_job` | src\services\job_service.py | 142 |

### Pattern: `_printer_files` (6 functions)

| Function | File | Line |
|----------|------|------|
| `sync_printer_files` | src\api\routers\files.py | 208 |
| `get_printer_files` | src\api\routers\printers.py | 398 |
| `get_printer_files` | src\services\file_service.py | 154 |
| `sync_printer_files` | src\services\file_service.py | 599 |
| `discover_printer_files` | src\services\file_service.py | 648 |
| `get_printer_files` | src\services\printer_service.py | 502 |

### Pattern: `_watch_folder` (6 functions)

| Function | File | Line |
|----------|------|------|
| `get_watch_folder_settings` | src\api\routers\files.py | 363 |
| `get_watch_folder_settings` | src\api\routers\settings.py | 234 |
| `get_watch_folders` | src\services\config_service.py | 407 |
| `get_watch_folder_settings` | src\services\config_service.py | 441 |
| `get_watch_folder_by_id` | src\services\watch_folder_db_service.py | 68 |
| `get_all_watch_folders` | src\services\watch_folder_db_service.py | 104 |

### Pattern: `_watch_folder` (6 functions)

| Function | File | Line |
|----------|------|------|
| `reload_watch_folders` | src\api\routers\files.py | 421 |
| `add_watch_folder` | src\services\config_service.py | 579 |
| `remove_watch_folder` | src\services\config_service.py | 613 |
| `reload_watch_folders` | src\services\file_service.py | 446 |
| `reload_watch_folders` | src\services\file_watcher_service.py | 520 |
| `create_watch_folder` | src\services\watch_folder_db_service.py | 25 |

### Pattern: `_folder` (6 functions)

| Function | File | Line |
|----------|------|------|
| `validate_watch_folder` | src\api\routers\files.py | 437 |
| `validate_watch_folder` | src\api\routers\settings.py | 250 |
| `validate_watch_folder` | src\services\config_service.py | 422 |
| `update_watch_folder` | src\services\watch_folder_db_service.py | 125 |
| `delete_watch_folder` | src\services\watch_folder_db_service.py | 173 |
| `validate_and_update_folder` | src\services\watch_folder_db_service.py | 253 |

### Pattern: `update_` (6 functions)

| Function | File | Line |
|----------|------|------|
| `update_idea` | src\api\routers\ideas.py | 156 |
| `update_file` | src\database\database.py | 654 |
| `update_idea` | src\database\database.py | 902 |
| `update_idea_status` | src\database\database.py | 937 |
| `update_idea` | src\services\idea_service.py | 134 |
| `update_idea_status` | src\services\idea_service.py | 177 |

### Pattern: `_material` (6 functions)

| Function | File | Line |
|----------|------|------|
| `get_materials` | src\api\routers\materials.py | 64 |
| `create_material` | src\services\material_service.py | 139 |
| `get_material` | src\services\material_service.py | 284 |
| `get_all_materials` | src\services\material_service.py | 288 |
| `get_materials_by_type` | src\services\material_service.py | 292 |
| `get_low_stock_materials` | src\services\material_service.py | 300 |

### Pattern: `_printer` (6 functions)

| Function | File | Line |
|----------|------|------|
| `list_printers` | src\api\routers\printers.py | 130 |
| `list_printers` | src\database\database.py | 334 |
| `get_printers` | src\services\config_service.py | 307 |
| `list_printers` | src\services\printer_service.py | 254 |
| `get_printers` | src\services\printer_service.py | 288 |
| `stop_printer` | src\services\printer_service.py | 817 |

## 🟠 Identical Signatures (Low Priority)

Functions with same signatures but different names.

### Signature: `()`

| Function | File | Line |
|----------|------|------|
| `main` | scripts\analyze_codebase.py | 351 |
| `main` | scripts\download_bambu_files.py | 325 |
| `main` | scripts\error_analysis_agent.py | 460 |
| `main` | scripts\quick_bambu_check.py | 9 |
| `main` | scripts\simple_bambu_test.py | 109 |
| `main` | scripts\test_bambu_credentials.py | 226 |
| `main` | scripts\test_bambu_ftp_direct.py | 294 |
| `main` | scripts\test_complete_bambu_ftp.py | 361 |
| `main` | scripts\verify_bambu_download.py | 185 |
| `main` | tests\run_essential_tests.py | 13 |
| `main` | tests\run_milestone_1_2_tests.py | 222 |
| `main` | tests\test_runner.py | 650 |
| `main` | verify_phase2_integration.py | 35 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `BambuCredentials.__init__` | scripts\bambu_credentials.py | 18 |
| `ErrorStoreService.__init__` | src\api\routers\errors.py | 48 |
| `ConnectionManager.__init__` | src\api\routers\websocket.py | 21 |
| `BambuParser.__init__` | src\services\bambu_parser.py | 82 |
| `MonitoringService.__init__` | src\services\monitoring_service.py | 21 |
| `ThreeMFAnalyzer.__init__` | src\services\threemf_analyzer.py | 18 |
| `UrlParserService.__init__` | src\services\url_parser_service.py | 19 |
| `ErrorHandler.__init__` | src\utils\error_handling.py | 45 |
| `CircularReference.__init__` | tests\backend\test_error_handling.py | 788 |
| `WebSocketLoadTester.__init__` | tests\backend\test_performance.py | 427 |
| `Milestone12TestRunner.__init__` | tests\run_milestone_1_2_tests.py | 28 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `Database.initialize` | src\database\database.py | 31 |
| `LibraryService.initialize` | src\services\library_service.py | 52 |
| `MaterialService.initialize` | src\services\material_service.py | 46 |
| `PrinterService.initialize` | src\services\printer_service.py | 35 |
| `TrendingService.initialize` | src\services\trending_service.py | 55 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `Idea.to_dict` | src\models\idea.py | 49 |
| `TrendingItem.to_dict` | src\models\idea.py | 138 |
| `WatchFolder.to_dict` | src\models\watch_folder.py | 47 |
| `BambuFTPFile.to_dict` | src\services\bambu_ftp_service.py | 64 |
| `PrinterConfig.to_dict` | src\services\config_service.py | 62 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `BambuFTP.connect` | scripts\working_bambu_ftp.py | 21 |
| `BambuLabPrinter.connect` | src\printers\bambu_lab.py | 98 |
| `PrinterInterface.connect` | src\printers\base.py | 83 |
| `PrusaPrinter.connect` | src\printers\prusa.py | 32 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `BambuFTP.list_files` | scripts\working_bambu_ftp.py | 69 |
| `BambuLabPrinter.list_files` | src\printers\bambu_lab.py | 840 |
| `PrinterInterface.list_files` | src\printers\base.py | 103 |
| `PrusaPrinter.list_files` | src\printers\prusa.py | 316 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `BambuLabPrinter.get_status` | src\printers\bambu_lab.py | 262 |
| `PrinterInterface.get_status` | src\printers\base.py | 93 |
| `PrusaPrinter.get_status` | src\printers\prusa.py | 133 |
| `EventService.get_status` | src\services\event_service.py | 452 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `IdeaService.get_statistics` | src\services\idea_service.py | 197 |
| `MaterialService.get_statistics` | src\services\material_service.py | 304 |
| `PreviewRenderService.get_statistics` | src\services\preview_render_service.py | 537 |
| `TrendingService.get_statistics` | src\services\trending_service.py | 595 |

### Signature: `(self, message: str, details: Optional[Dict[str, Any]])`

| Function | File | Line |
|----------|------|------|
| `ConfigurationError.__init__` | src\utils\exceptions.py | 31 |
| `DatabaseError.__init__` | src\utils\exceptions.py | 43 |
| `AuthenticationError.__init__` | src\utils\exceptions.py | 91 |
| `AuthorizationError.__init__` | src\utils\exceptions.py | 103 |

### Signature: `(self)`

| Function | File | Line |
|----------|------|------|
| `Database._create_tables` | src\database\database.py | 46 |
| `MaterialService._create_tables` | src\services\material_service.py | 56 |
| `TrendingService._create_tables` | src\services\trending_service.py | 65 |

## 🔴 Structural Duplicates (High Priority)

Functions with similar AST structures indicating duplicate logic.

### Structure Hash: `1cb36c9d` (6 functions)

| Function | File |
|----------|------|
| `test_get_files_filter_by_printer` | tests\backend\test_api_files.py |
| `test_get_files_filter_by_status` | tests\backend\test_api_files.py |
| `test_get_files_filter_by_type` | tests\backend\test_api_files.py |
| `test_get_jobs_filter_by_status` | tests\backend\test_api_jobs.py |
| `test_get_jobs_filter_by_printer` | tests\backend\test_api_jobs.py |
| `test_get_printers_filter_by_type` | tests\backend\test_api_printers.py |

### Structure Hash: `4e90f3f4` (2 functions)

| Function | File |
|----------|------|
| `ensure_log_directory` | src\api\routers\errors.py |
| `ensure_log_directory` | src\utils\error_handling.py |

### Structure Hash: `6371837b` (2 functions)

| Function | File |
|----------|------|
| `delete_job` | src\api\routers\jobs.py |
| `delete_printer` | src\api\routers\printers.py |

### Structure Hash: `ff7979d2` (2 functions)

| Function | File |
|----------|------|
| `initialize` | src\services\material_service.py |
| `initialize` | src\services\trending_service.py |

### Structure Hash: `2e60f678` (2 functions)

| Function | File |
|----------|------|
| `get_material` | src\services\material_service.py |
| `get_printer_driver` | src\services\printer_service.py |

### Structure Hash: `15961376` (2 functions)

| Function | File |
|----------|------|
| `_get_session` | src\services\thumbnail_service.py |
| `_get_session` | src\services\url_parser_service.py |

### Structure Hash: `f8f3ed1a` (2 functions)

| Function | File |
|----------|------|
| `test_file_naming_conventions` | tests\test_essential_config.py |
| `test_file_naming_german_support` | tests\test_working_core.py |

### Structure Hash: `d4188034` (2 functions)

| Function | File |
|----------|------|
| `async_client` | tests\test_essential_integration.py |
| `client` | tests\backend\test_api_health.py |

### Structure Hash: `1342a64a` (2 functions)

| Function | File |
|----------|------|
| `test_get_job_details_not_found` | tests\backend\test_api_jobs.py |
| `test_get_printer_status_not_found` | tests\backend\test_api_printers.py |

## 📊 Single-Use Functions

Functions called only once - candidates for inlining.

| Function | File | Line | Signature |
|----------|------|------|----------|
| `create_sample_gcode` | demo_gcode_optimization.py | 18 | `()` |
| `analyze_gcode_file_lines` | demo_gcode_optimization.py | 161 | `(self, lines)` |
| `find_python_files` | scripts\analyze_codebase.py | 172 | `(root_dir: str)` |
| `build_dependency_graph` | scripts\analyze_codebase.py | 186 | `(all_results: List[Dict])` |
| `find_entry_points` | scripts\analyze_codebase.py | 203 | `(all_results: List[Dict])` |
| `generate_function_inventory_report` | scripts\analyze_codebase.py | 247 | `(all_results: List[Dict], output_file: str)` |
| `generate_dependency_report` | scripts\analyze_codebase.py | 305 | `(dependency_graph: Dict, output_file: str)` |
| `generate_entry_points_report` | scripts\analyze_codebase.py | 323 | `(entry_points: List[Dict], output_file: str)` |
| `test_download_specific_file` | scripts\simple_bambu_test.py | 18 | `()` |
| `validate_credentials` | scripts\test_bambu_credentials.py | 28 | `(ip: str, access_code: str, serial: str)` |
| `test_bambu_connection` | scripts\test_bambu_credentials.py | 57 | `(ip: str, access_code: str, serial: str)` |
| `print_results` | scripts\test_bambu_credentials.py | 168 | `(result: dict)` |
| `get_interactive_input` | scripts\test_bambu_credentials.py | 201 | `()` |
| `create_secure_ftp_connection` | scripts\test_bambu_ftp_direct.py | 34 | `(host: str, username: str, password: str, port: int)` |
| `list_directory` | scripts\test_bambu_ftp_direct.py | 100 | `(ftp: ftplib.FTP_TLS, directory: str)` |
| `test_bambu_ftp` | scripts\test_bambu_ftp_direct.py | 217 | `(ip_address: str, access_code: str)` |
| `verify_download` | scripts\verify_bambu_download.py | 39 | `(ip_address: str, access_code: str, serial_number: str, target_file: str | None)` |
| `get_business_analytics` | src\api\routers\analytics.py | 66 | `(start_date: Optional[date], end_date: Optional[date], analytics_service: AnalyticsService)` |
| `take_snapshot` | src\api\routers\camera.py | 119 | `(printer_id: UUID, snapshot_data: SnapshotCreate, printer_service: PrinterService)` |
| `get_thumbnail_processing_log` | src\api\routers\debug.py | 98 | `(request: Request, limit: int)` |
| `sync_printer_files` | src\api\routers\files.py | 208 | `(printer_id: Optional[str], file_service: FileService)` |
| `add_watch_folder` | src\api\routers\files.py | 454 | `(folder_path: str, config_service: ConfigService, file_service: FileService)` |
| `remove_watch_folder` | src\api\routers\files.py | 492 | `(folder_path: str, config_service: ConfigService, file_service: FileService)` |
| `update_watch_folder` | src\api\routers\files.py | 522 | `(folder_path: str, is_active: bool, config_service: ConfigService, file_service: FileService)` |
| `get_idea_statistics` | src\api\routers\ideas.py | 301 | `(idea_service: IdeaService)` |
| `list_library_files` | src\api\routers\library.py | 91 | `(page: int, limit: int, source_type: Optional[str], file_type: Optional[str], status: Optional[str], search: Optional[str], has_thumbnail: Optional[bool], has_metadata: Optional[bool], manufacturer: Optional[str], printer_model: Optional[str], show_duplicates: Optional[bool], only_duplicates: Optional[bool], library_service)` |
| `delete_library_file` | src\api\routers\library.py | 268 | `(checksum: str, delete_physical: bool, library_service)` |
| `export_inventory` | src\api\routers\materials.py | 153 | `(format: str, material_service: MaterialService)` |
| `get_material` | src\api\routers\materials.py | 182 | `(material_id: str, material_service: MaterialService)` |
| `create_material` | src\api\routers\materials.py | 217 | `(material_data: MaterialCreate, material_service: MaterialService)` |

## 🗑️ Potentially Unused Functions

Functions that appear to have no callers in the codebase.

**Note**: May include entry points, API endpoints, or dynamically called functions.

| Function | File | Line | Async | Decorators |
|----------|------|------|-------|------------|
| `demo_optimization` | demo_gcode_optimization.py | 74 | No | - |
| `FunctionAnalyzer.visit_Import` | scripts\analyze_codebase.py | 31 | No | - |
| `FunctionAnalyzer.visit_ImportFrom` | scripts\analyze_codebase.py | 42 | No | - |
| `FunctionAnalyzer.visit_ClassDef` | scripts\analyze_codebase.py | 55 | No | - |
| `FunctionAnalyzer.visit_AsyncFunctionDef` | scripts\analyze_codebase.py | 117 | No | - |
| `FunctionAnalyzer.visit_Call` | scripts\analyze_codebase.py | 121 | No | - |
| `setup_example_env` | scripts\bambu_credentials.py | 103 | No | - |
| `test_direct_ftp` | scripts\debug_bambu_ftp.py | 12 | No | - |
| `test_alternative_ftp` | scripts\debug_bambu_ftp_v2.py | 12 | No | - |
| `download_target_file` | scripts\download_target_file.py | 21 | No | - |
| `test_working_ftp` | scripts\working_bambu_ftp.py | 212 | No | - |
| `Database.transaction` | src\database\database.py | 296 | Yes | asynccontextmanager |
| `Database.create_local_file` | src\database\database.py | 753 | Yes | - |
| `Database.list_local_files` | src\database\database.py | 763 | Yes | - |
| `Database.get_library_file_sources` | src\database\database.py | 1315 | Yes | - |
| `lifespan` | src\main.py | 88 | Yes | asynccontextmanager |
| `create_application` | src\main.py | 267 | No | - |
| `printernizer_exception_handler` | src\main.py | 350 | Yes | app.exception_handler(PrinternizerException) |
| `validation_exception_handler` | src\main.py | 365 | Yes | app.exception_handler(RequestValidationError) |
| `general_exception_handler` | src\main.py | 379 | Yes | app.exception_handler(Exception) |
| `setup_signal_handlers` | src\main.py | 395 | No | - |
| `signal_handler` | src\main.py | 397 | No | - |
| `Job.convert_progress_to_int` | src\models\job.py | 45 | No | field_validator('progress', mode='before') |
| `MaterialCreate.validate_remaining` | src\models\material.py | 116 | No | field_validator('remaining_weight') |
| `WatchFolder.get_display_name` | src\models\watch_folder.py | 106 | No | - |
| `WatchFolder.is_accessible` | src\models\watch_folder.py | 115 | No | - |
| `BambuLabPrinter.rank` | src\printers\bambu_lab.py | 1510 | No | - |
| `BasePrinter.remove_status_callback` | src\printers\base.py | 248 | No | - |
| `BasePrinter.get_connection_info` | src\printers\base.py | 261 | No | - |
| `BasePrinter.get_monitoring_metrics` | src\printers\base.py | 272 | No | - |
| `AnalyticsService.get_dashboard_stats` | src\services\analytics_service.py | 20 | Yes | - |
| `AnalyticsService.get_printer_usage` | src\services\analytics_service.py | 33 | Yes | - |
| `AnalyticsService.get_material_consumption` | src\services\analytics_service.py | 38 | Yes | - |
| `AnalyticsService.get_business_report` | src\services\analytics_service.py | 47 | Yes | - |
| `AnalyticsService.export_data` | src\services\analytics_service.py | 116 | Yes | - |
| `BambuFTPService.file_exists` | src\services\bambu_ftp_service.py | 368 | Yes | - |
| `create_bambu_ftp_service` | src\services\bambu_ftp_service.py | 433 | Yes | - |
| `BambuParser.get_largest_thumbnail` | src\services\bambu_parser.py | 832 | No | - |
| `ConfigService.get_business_settings` | src\services\config_service.py | 384 | No | - |
| `EventService.unsubscribe` | src\services\event_service.py | 89 | No | - |
| `EventService.set_services` | src\services\event_service.py | 476 | No | - |
| `EventService.force_discovery` | src\services\event_service.py | 493 | Yes | - |
| `EventService.reset_monitoring_state` | src\services\event_service.py | 543 | Yes | - |
| `FileService.get_download_status` | src\services\file_service.py | 367 | Yes | - |
| `FileService.cleanup_download_status` | src\services\file_service.py | 782 | Yes | - |
| `PrintFileHandler.on_created` | src\services\file_watcher_service.py | 92 | No | - |
| `PrintFileHandler.on_modified` | src\services\file_watcher_service.py | 99 | No | - |
| `PrintFileHandler.on_deleted` | src\services\file_watcher_service.py | 106 | No | - |
| `PrintFileHandler.on_moved` | src\services\file_watcher_service.py | 112 | No | - |
| `JobService.update_job_status` | src\services\job_service.py | 287 | Yes | - |

