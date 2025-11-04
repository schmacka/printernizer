# Function Inventory Report

Generated: 1759613260.4660633

## Summary

- Total Python files analyzed: 114
- Total functions found: 1327

## Functions by File

### demo_gcode_optimization.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `create_sample_gcode` | function | public | 18 | `()` | - |
| `demo_optimization` | function | public | 74 | `()` | - |
| `analyze_gcode_file_lines` | function | public | 161 | `(self, lines)` | - |

### scripts\analyze_codebase.py

Functions: 15

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `FunctionAnalyzer.__init__` | method | dunder | 23 | `(self, filepath: str)` | - |
| `FunctionAnalyzer.visit_Import` | method | public | 31 | `(self, node)` | - |
| `FunctionAnalyzer.visit_ImportFrom` | method | public | 42 | `(self, node)` | - |
| `FunctionAnalyzer.visit_ClassDef` | method | public | 55 | `(self, node)` | - |
| `FunctionAnalyzer.visit_FunctionDef` | method | public | 62 | `(self, node)` | - |
| `FunctionAnalyzer.visit_AsyncFunctionDef` | method | public | 117 | `(self, node)` | - |
| `FunctionAnalyzer.visit_Call` | method | public | 121 | `(self, node)` | - |
| `analyze_file` | function | public | 145 | `(filepath: str)` | - |
| `find_python_files` | function | public | 172 | `(root_dir: str)` | - |
| `build_dependency_graph` | function | public | 186 | `(all_results: List[Dict])` | - |
| `find_entry_points` | function | public | 203 | `(all_results: List[Dict])` | - |
| `generate_function_inventory_report` | function | public | 247 | `(all_results: List[Dict], output_file: str)` | - |
| `generate_dependency_report` | function | public | 305 | `(dependency_graph: Dict, output_file: str)` | - |
| `generate_entry_points_report` | function | public | 323 | `(entry_points: List[Dict], output_file: str)` | - |
| `main` | function | public | 351 | `()` | - |

### scripts\bambu_credentials.py

Functions: 6

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuCredentials.__init__` | method | dunder | 18 | `(self)` | - |
| `BambuCredentials.get_printer_credentials` | method | public | 21 | `(self, host: str)` | - |
| `BambuCredentials._validate_access_code` | method | private | 66 | `(self, access_code: str)` | - |
| `BambuCredentials._is_development_environment` | method | private | 74 | `(self)` | - |
| `get_bambu_credentials` | function | public | 87 | `(host: str)` | - |
| `setup_example_env` | function | public | 103 | `()` | - |

### scripts\debug_bambu_ftp.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `test_direct_ftp` | function | public | 12 | `()` | - |

### scripts\debug_bambu_ftp_v2.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `test_alternative_ftp` | function | public | 12 | `()` | - |

### scripts\download_bambu_files.py

Functions: 8

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuDownloadManager.__init__` | method | dunder | 54 | `(self, download_base_dir: str)` | - |
| `BambuDownloadManager.download_from_bambulab_printers` | async | public | 75 | `(self, printer_configs: List[Dict[str, str]], file_filter: Optional[str], download_all: bool)` | - |
| `BambuDownloadManager._process_single_printer` | async | private | 132 | `(self, config: Dict[str, str], file_filter: Optional[str], download_all: bool)` | - |
| `BambuDownloadManager._interactive_file_selection` | async | private | 230 | `(self, files: List[BambuFTPFile])` | - |
| `BambuDownloadManager._sanitize_name` | method | private | 275 | `(self, name: str)` | - |
| `BambuDownloadManager._generate_summary` | method | private | 285 | `(self, results: Dict[str, Any], duration)` | - |
| `BambuDownloadManager._print_summary` | method | private | 309 | `(self, summary: Dict[str, Any])` | - |
| `main` | async | public | 325 | `()` | - |

### scripts\download_target_file.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `download_target_file` | function | public | 21 | `()` | - |

### scripts\error_analysis_agent.py

Functions: 11

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `ErrorAnalysisAgent.__init__` | method | dunder | 31 | `(self, log_file_path)` | - |
| `ErrorAnalysisAgent.load_log` | method | public | 50 | `(self)` | - |
| `ErrorAnalysisAgent.parse_errors` | method | public | 60 | `(self)` | - |
| `ErrorAnalysisAgent.analyze_root_cause` | method | public | 108 | `(self)` | - |
| `ErrorAnalysisAgent.generate_report` | method | public | 182 | `(self, output_format)` | - |
| `ErrorAnalysisAgent._print_console_report` | method | private | 202 | `(self, analysis, total_import_errors, total_errors, total_warnings, total_tracebacks, total_info)` | - |
| `ErrorAnalysisAgent._generate_json_report` | method | private | 288 | `(self, analysis, total_import_errors, total_errors, total_warnings, total_tracebacks, total_info)` | - |
| `ErrorAnalysisAgent._generate_markdown_report` | method | private | 310 | `(self, analysis, total_import_errors, total_errors, total_warnings, total_tracebacks, total_info)` | - |
| `ErrorAnalysisAgent.apply_fixes` | method | public | 352 | `(self, analysis, dry_run)` | - |
| `ErrorAnalysisAgent.run` | method | public | 416 | `(self, output_format, plan_mode, apply_fixes)` | - |
| `main` | function | public | 460 | `()` | - |

### scripts\quick_bambu_check.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `main` | function | public | 9 | `()` | - |

### scripts\simple_bambu_test.py

Functions: 2

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `test_download_specific_file` | async | public | 18 | `()` | - |
| `main` | async | public | 109 | `()` | - |

### scripts\test_bambu_credentials.py

Functions: 5

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `validate_credentials` | function | public | 28 | `(ip: str, access_code: str, serial: str)` | - |
| `test_bambu_connection` | async | public | 57 | `(ip: str, access_code: str, serial: str)` | - |
| `print_results` | function | public | 168 | `(result: dict)` | - |
| `get_interactive_input` | function | public | 201 | `()` | - |
| `main` | async | public | 226 | `()` | - |

### scripts\test_bambu_ftp_direct.py

Functions: 6

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `create_secure_ftp_connection` | function | public | 34 | `(host: str, username: str, password: str, port: int)` | - |
| `list_directory` | function | public | 100 | `(ftp: ftplib.FTP_TLS, directory: str)` | - |
| `download_file` | function | public | 169 | `(ftp: ftplib.FTP_TLS, remote_filename: str, local_path: str)` | - |
| `progress_callback` | function | public | 190 | `(data)` | - |
| `test_bambu_ftp` | function | public | 217 | `(ip_address: str, access_code: str)` | - |
| `main` | function | public | 294 | `()` | - |

### scripts\test_complete_bambu_ftp.py

Functions: 10

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuFTPTester.__init__` | method | dunder | 49 | `(self, ip_address: str, access_code: str)` | - |
| `BambuFTPTester.run_all_tests` | async | public | 55 | `(self)` | - |
| `BambuFTPTester._test_ftp_service` | async | private | 101 | `(self)` | - |
| `BambuFTPTester._test_printer_class` | async | private | 137 | `(self)` | - |
| `BambuFTPTester._test_file_listing` | async | private | 182 | `(self)` | - |
| `BambuFTPTester._test_file_download` | async | private | 224 | `(self)` | - |
| `BambuFTPTester._test_error_handling` | async | private | 288 | `(self)` | - |
| `BambuFTPTester._generate_test_summary` | method | private | 321 | `(self, all_passed: bool)` | - |
| `BambuFTPTester._print_summary` | method | private | 333 | `(self, summary: Dict[str, Any])` | - |
| `main` | async | public | 361 | `()` | - |

### scripts\test_existing_bambu_api.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `test_bambu_api` | function | public | 22 | `()` | - |

### scripts\test_ssl_connection.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `test_ssl_connection` | function | public | 10 | `()` | - |

### scripts\verify_bambu_download.py

Functions: 2

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `verify_download` | async | public | 39 | `(ip_address: str, access_code: str, serial_number: str, target_file: str | None)` | - |
| `main` | function | public | 185 | `()` | - |

### scripts\working_bambu_ftp.py

Functions: 10

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuFTP.__init__` | method | dunder | 15 | `(self, host, port)` | - |
| `BambuFTP.connect` | method | public | 21 | `(self)` | - |
| `BambuFTP.login` | method | public | 42 | `(self, username, password)` | - |
| `BambuFTP.cwd` | method | public | 60 | `(self, directory)` | - |
| `BambuFTP.list_files` | method | public | 69 | `(self)` | - |
| `BambuFTP.download_file` | method | public | 127 | `(self, filename, local_path)` | - |
| `BambuFTP.quit` | method | public | 182 | `(self)` | - |
| `BambuFTP._send_command` | method | private | 193 | `(self, command)` | - |
| `BambuFTP._read_response` | method | private | 199 | `(self)` | - |
| `test_working_ftp` | function | public | 212 | `()` | - |

### src\api\routers\analytics.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_analytics_summary` | async | public | 48 | `(start_date: Optional[date], end_date: Optional[date], analytics_service: AnalyticsService)` | router.get('/summary', response_model=AnalyticsResponse) |
| `get_business_analytics` | async | public | 66 | `(start_date: Optional[date], end_date: Optional[date], analytics_service: AnalyticsService)` | router.get('/business', response_model=BusinessAnalyticsResponse) |
| `get_analytics_overview` | async | public | 84 | `(period: Optional[str], analytics_service: AnalyticsService)` | router.get('/overview', response_model=OverviewResponse) |

### src\api\routers\camera.py

Functions: 5

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_camera_status` | async | public | 24 | `(printer_id: UUID, printer_service: PrinterService)` | router.get('/{printer_id}/camera/status', response_model=CameraStatus) |
| `get_camera_stream` | async | public | 72 | `(printer_id: UUID, printer_service: PrinterService)` | router.get('/{printer_id}/camera/stream') |
| `take_snapshot` | async | public | 119 | `(printer_id: UUID, snapshot_data: SnapshotCreate, printer_service: PrinterService)` | router.post('/{printer_id}/camera/snapshot', response_model=SnapshotResponse) |
| `list_snapshots` | async | public | 198 | `(printer_id: UUID, limit: int, printer_service: PrinterService)` | router.get('/{printer_id}/snapshots', response_model=List[SnapshotResponse]) |
| `download_snapshot` | async | public | 220 | `(snapshot_id: int, printer_service: PrinterService)` | router.get('/snapshots/{snapshot_id}/download') |

### src\api\routers\debug.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `debug_printer_thumbnail` | async | public | 16 | `(request: Request, printer_id: str, include_file_record: bool, include_base64_lengths: bool)` | router.get('/printers/{printer_id}/thumbnail', tags=['Debug'], summary='Debug current printer thumbnail linkage') |
| `debug_file` | async | public | 78 | `(request: Request, file_id: str, include_base64_length: bool)` | router.get('/files/{file_id}', tags=['Debug'], summary='Debug file record & thumbnail flags') |
| `get_thumbnail_processing_log` | async | public | 98 | `(request: Request, limit: int)` | router.get('/thumbnail-processing-log', tags=['Debug'], summary='Get thumbnail processing status log') |

### src\api\routers\errors.py

Functions: 9

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `ErrorStoreService.__init__` | method | dunder | 48 | `(self)` | - |
| `ErrorStoreService.ensure_log_directory` | method | public | 53 | `(self)` | - |
| `ErrorStoreService.store_errors` | method | public | 57 | `(self, errors: List[ErrorReport], session: SessionInfo)` | - |
| `ErrorStoreService.get_recent_errors` | method | public | 87 | `(self, limit: int)` | - |
| `ErrorStoreService.get_error_statistics` | method | public | 111 | `(self, hours: int)` | - |
| `report_errors` | async | public | 170 | `(request: ErrorReportRequest, client_request: Request)` | router.post('/report') |
| `get_recent_errors` | async | public | 220 | `(limit: int)` | router.get('/recent') |
| `get_error_statistics` | async | public | 238 | `(hours: int)` | router.get('/statistics') |
| `error_system_health` | async | public | 255 | `()` | router.get('/health') |

### src\api\routers\files.py

Functions: 20

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `list_files` | async | public | 61 | `(printer_id: Optional[str], status: Optional[FileStatus], source: Optional[FileSource], has_thumbnail: Optional[bool], search: Optional[str], limit: Optional[int], order_by: Optional[str], order_dir: Optional[str], page: Optional[int], file_service: FileService)` | router.get('/', response_model=FileListResponse) |
| `get_file_statistics` | async | public | 124 | `(file_service: FileService)` | router.get('/statistics') |
| `get_file_by_id` | async | public | 143 | `(file_id: str, file_service: FileService)` | router.get('/{file_id}', response_model=FileResponse) |
| `download_file` | async | public | 167 | `(file_id: str, file_service: FileService)` | router.post('/{file_id}/download') |
| `sync_printer_files` | async | public | 208 | `(printer_id: Optional[str], file_service: FileService)` | router.post('/sync') |
| `get_file_thumbnail` | async | public | 225 | `(file_id: str, file_service: FileService)` | router.get('/{file_id}/thumbnail') |
| `get_file_metadata` | async | public | 280 | `(file_id: str, file_service: FileService)` | router.get('/{file_id}/metadata') |
| `process_file_thumbnails` | async | public | 321 | `(file_id: str, file_service: FileService)` | router.post('/{file_id}/process-thumbnails') |
| `get_watch_folder_settings` | async | public | 363 | `(config_service: ConfigService)` | router.get('/watch-folders/settings', response_model=WatchFolderSettings) |
| `get_watch_folder_status` | async | public | 382 | `(file_service: FileService, config_service: ConfigService)` | router.get('/watch-folders/status') |
| `list_local_files` | async | public | 399 | `(watch_folder_path: Optional[str], file_service: FileService)` | router.get('/local') |
| `reload_watch_folders` | async | public | 421 | `(file_service: FileService)` | router.post('/watch-folders/reload') |
| `validate_watch_folder` | async | public | 437 | `(folder_path: str, config_service: ConfigService)` | router.post('/watch-folders/validate') |
| `add_watch_folder` | async | public | 454 | `(folder_path: str, config_service: ConfigService, file_service: FileService)` | router.post('/watch-folders/add') |
| `remove_watch_folder` | async | public | 492 | `(folder_path: str, config_service: ConfigService, file_service: FileService)` | router.delete('/watch-folders/remove') |
| `update_watch_folder` | async | public | 522 | `(folder_path: str, is_active: bool, config_service: ConfigService, file_service: FileService)` | router.patch('/watch-folders/update') |
| `delete_file` | async | public | 574 | `(file_id: str, file_service: FileService)` | router.delete('/{file_id}') |
| `get_enhanced_metadata` | async | public | 603 | `(file_id: str, force_refresh: bool, file_service: FileService)` | router.get('/{file_id}/metadata/enhanced') |
| `analyze_file` | async | public | 661 | `(file_id: str, include_recommendations: bool, file_service: FileService)` | router.get('/{file_id}/analysis') |
| `check_printer_compatibility` | async | public | 764 | `(file_id: str, printer_id: str, file_service: FileService)` | router.get('/{file_id}/compatibility/{printer_id}') |

### src\api\routers\health.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `health_check` | async | public | 38 | `(request: Request, config: ConfigService, db: Database)` | router.get('/health', response_model=HealthResponse) |
| `readiness_check` | async | public | 162 | `()` | router.get('/readiness') |
| `liveness_check` | async | public | 171 | `()` | router.get('/liveness') |

### src\api\routers\idea_url.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `validate_url` | async | public | 20 | `(url: str, idea_service: IdeaService)` | router.get('/validate', response_model=Dict[str, Any]) |
| `preview_url` | async | public | 43 | `(url_data: UrlPreviewRequest, idea_service: IdeaService)` | router.post('/preview', response_model=Dict[str, Any]) |
| `get_supported_platforms` | async | public | 77 | `(idea_service: IdeaService)` | router.get('/platforms', response_model=List[Dict[str, Any]]) |

### src\api\routers\ideas.py

Functions: 13

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `create_idea` | async | public | 71 | `(idea_data: IdeaCreate, idea_service: IdeaService)` | router.post('/', response_model=Dict[str, str]) |
| `list_ideas` | async | public | 99 | `(status: Optional[str], is_business: Optional[bool], category: Optional[str], source_type: Optional[str], page: int, page_size: int, idea_service: IdeaService)` | router.get('/', response_model=Dict[str, Any]) |
| `get_idea` | async | public | 131 | `(idea_id: str, idea_service: IdeaService)` | router.get('/{idea_id}', response_model=Dict[str, Any]) |
| `update_idea` | async | public | 156 | `(idea_id: str, idea_data: IdeaUpdate, idea_service: IdeaService)` | router.put('/{idea_id}', response_model=Dict[str, str]) |
| `delete_idea` | async | public | 193 | `(idea_id: str, idea_service: IdeaService)` | router.delete('/{idea_id}', response_model=Dict[str, str]) |
| `update_idea_status` | async | public | 226 | `(idea_id: str, status_data: IdeaStatusUpdate, idea_service: IdeaService)` | router.patch('/{idea_id}/status', response_model=Dict[str, str]) |
| `import_idea_from_url` | async | public | 260 | `(import_data: IdeaImport, idea_service: IdeaService)` | router.post('/import', response_model=Dict[str, str]) |
| `get_all_tags` | async | public | 287 | `(idea_service: IdeaService)` | router.get('/tags/all', response_model=List[Dict[str, Any]]) |
| `get_idea_statistics` | async | public | 301 | `(idea_service: IdeaService)` | router.get('/stats/overview', response_model=Dict[str, Any]) |
| `search_ideas` | async | public | 315 | `(q: str, status: Optional[str], is_business: Optional[bool], category: Optional[str], idea_service: IdeaService)` | router.get('/search', response_model=List[Dict[str, Any]]) |
| `get_trending_models` | async | public | 342 | `(platform: str, category: Optional[str], idea_service: IdeaService)` | router.get('/trending/{platform}', response_model=List[Dict[str, Any]]) |
| `save_trending_as_idea` | async | public | 368 | `(trending_id: str, save_data: TrendingSave, idea_service: IdeaService)` | router.post('/trending/{trending_id}/save', response_model=Dict[str, str]) |
| `refresh_trending_cache` | async | public | 395 | `(idea_service: IdeaService)` | router.post('/trending/refresh', response_model=Dict[str, str]) |

### src\api\routers\jobs.py

Functions: 4

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `_transform_job_to_response` | function | private | 53 | `(job_data: dict)` | - |
| `list_jobs` | async | public | 78 | `(printer_id: Optional[str], job_status: Optional[str], is_business: Optional[bool], limit: int, offset: int, job_service: JobService)` | router.get('/', response_model=List[JobResponse]) |
| `get_job` | async | public | 105 | `(job_id: str, job_service: JobService)` | router.get('/{job_id}', response_model=JobResponse) |
| `delete_job` | async | public | 129 | `(job_id: UUID, job_service: JobService)` | router.delete('/{job_id}', status_code=status.HTTP_204_NO_CONTENT) |

### src\api\routers\library.py

Functions: 7

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_library_service` | async | public | 82 | `()` | - |
| `list_library_files` | async | public | 91 | `(page: int, limit: int, source_type: Optional[str], file_type: Optional[str], status: Optional[str], search: Optional[str], has_thumbnail: Optional[bool], has_metadata: Optional[bool], manufacturer: Optional[str], printer_model: Optional[str], show_duplicates: Optional[bool], only_duplicates: Optional[bool], library_service)` | router.get('/files', response_model=LibraryFileListResponse) |
| `get_library_file` | async | public | 168 | `(checksum: str, library_service)` | router.get('/files/{checksum}', response_model=LibraryFileResponse) |
| `reprocess_library_file` | async | public | 206 | `(checksum: str, library_service)` | router.post('/files/{checksum}/reprocess', response_model=ReprocessResponse) |
| `delete_library_file` | async | public | 268 | `(checksum: str, delete_physical: bool, library_service)` | router.delete('/files/{checksum}', response_model=DeleteResponse) |
| `get_library_statistics` | async | public | 329 | `(library_service)` | router.get('/statistics', response_model=LibraryStatsResponse) |
| `library_health_check` | async | public | 375 | `(library_service)` | router.get('/health') |

### src\api\routers\materials.py

Functions: 11

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_materials` | async | public | 64 | `(material_type: Optional[MaterialType], brand: Optional[MaterialBrand], color: Optional[MaterialColor], low_stock: bool, printer_id: Optional[str], material_service: MaterialService)` | router.get('/', response_model=List[MaterialResponse]) |
| `get_material_stats` | async | public | 114 | `(material_service: MaterialService)` | router.get('/stats', response_model=MaterialStats) |
| `get_material_types` | async | public | 125 | `()` | router.get('/types') |
| `get_consumption_report` | async | public | 135 | `(start_date: datetime, end_date: datetime, material_service: MaterialService)` | router.get('/report', response_model=MaterialReport) |
| `export_inventory` | async | public | 153 | `(format: str, material_service: MaterialService)` | router.get('/export') |
| `get_material` | async | public | 182 | `(material_id: str, material_service: MaterialService)` | router.get('/{material_id}', response_model=MaterialResponse) |
| `create_material` | async | public | 217 | `(material_data: MaterialCreate, material_service: MaterialService)` | router.post('/', response_model=MaterialResponse, status_code=201) |
| `update_material` | async | public | 250 | `(material_id: str, update_data: MaterialUpdate, material_service: MaterialService)` | router.patch('/{material_id}', response_model=MaterialResponse) |
| `record_consumption` | async | public | 286 | `(consumption_data: ConsumptionRequest, material_service: MaterialService)` | router.post('/consumption', response_model=dict, status_code=201) |
| `delete_material` | async | public | 319 | `(material_id: str, material_service: MaterialService)` | router.delete('/{material_id}', status_code=204) |
| `get_consumption_history` | async | public | 329 | `(material_id: Optional[str], job_id: Optional[str], printer_id: Optional[str], days: int, material_service: MaterialService)` | router.get('/consumption/history') |

### src\api\routers\printers.py

Functions: 17

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `_printer_to_response` | function | private | 70 | `(printer: Printer, printer_service: PrinterService)` | - |
| `list_printers` | async | public | 130 | `(printer_service: PrinterService)` | router.get('/', response_model=List[PrinterResponse]) |
| `create_printer` | async | public | 146 | `(printer_data: PrinterCreateRequest, printer_service: PrinterService)` | router.post('/', response_model=PrinterResponse, status_code=status.HTTP_201_CREATED) |
| `get_printer` | async | public | 177 | `(printer_id: UUID, printer_service: PrinterService)` | router.get('/{printer_id}', response_model=PrinterResponse) |
| `update_printer` | async | public | 201 | `(printer_id: UUID, printer_data: PrinterUpdateRequest, printer_service: PrinterService)` | router.put('/{printer_id}', response_model=PrinterResponse) |
| `delete_printer` | async | public | 231 | `(printer_id: UUID, printer_service: PrinterService)` | router.delete('/{printer_id}', status_code=status.HTTP_204_NO_CONTENT) |
| `connect_printer` | async | public | 254 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/connect') |
| `disconnect_printer` | async | public | 278 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/disconnect') |
| `pause_printer` | async | public | 295 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/pause') |
| `resume_printer` | async | public | 320 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/resume') |
| `stop_printer` | async | public | 345 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/stop') |
| `download_current_job_file` | async | public | 370 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/download-current-job') |
| `get_printer_files` | async | public | 398 | `(printer_id: UUID, printer_service: PrinterService)` | router.get('/{printer_id}/files') |
| `start_printer_monitoring` | async | public | 418 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/monitoring/start') |
| `stop_printer_monitoring` | async | public | 443 | `(printer_id: UUID, printer_service: PrinterService)` | router.post('/{printer_id}/monitoring/stop') |
| `download_printer_file` | async | public | 468 | `(printer_id: UUID, filename: str, printer_service: PrinterService)` | router.post('/{printer_id}/files/{filename}/download') |
| `get_printer_current_thumbnail` | async | public | 494 | `(printer_id: UUID, printer_service: PrinterService)` | router.get('/{printer_id}/thumbnail') |

### src\api\routers\settings.py

Functions: 11

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_application_settings` | async | public | 97 | `(config_service: ConfigService)` | router.get('/application', response_model=ApplicationSettingsResponse) |
| `update_application_settings` | async | public | 113 | `(settings: ApplicationSettingsUpdate, config_service: ConfigService)` | router.put('/application') |
| `get_printer_configurations` | async | public | 141 | `(config_service: ConfigService)` | router.get('/printers') |
| `add_or_update_printer` | async | public | 166 | `(printer_id: str, printer_config: PrinterConfigRequest, config_service: ConfigService)` | router.post('/printers/{printer_id}') |
| `remove_printer` | async | public | 192 | `(printer_id: str, config_service: ConfigService)` | router.delete('/printers/{printer_id}') |
| `validate_printer_connection` | async | public | 217 | `(printer_id: str, config_service: ConfigService)` | router.post('/printers/{printer_id}/validate') |
| `get_watch_folder_settings` | async | public | 234 | `(config_service: ConfigService)` | router.get('/watch-folders', response_model=WatchFolderSettings) |
| `validate_watch_folder` | async | public | 250 | `(folder_path: str, config_service: ConfigService)` | router.post('/watch-folders/validate') |
| `get_gcode_optimization_settings` | async | public | 274 | `(config_service: ConfigService)` | router.get('/gcode-optimization') |
| `update_gcode_optimization_settings` | async | public | 296 | `(settings: GcodeOptimizationSettings, config_service: ConfigService)` | router.put('/gcode-optimization') |
| `reload_configuration` | async | public | 322 | `(config_service: ConfigService)` | router.post('/reload') |

### src\api\routers\system.py

Functions: 2

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_system_info` | async | public | 25 | `(config_service: ConfigService)` | router.get('/info', response_model=SystemInfoResponse) |
| `create_backup` | async | public | 41 | `(config_service: ConfigService)` | router.post('/backup') |

### src\api\routers\trending.py

Functions: 8

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_trending` | async | public | 52 | `(platform: Optional[str], category: Optional[str], limit: int, trending_service: TrendingService)` | router.get('/', response_model=List[TrendingModel]) |
| `get_supported_platforms` | async | public | 91 | `()` | router.get('/platforms') |
| `get_trending_stats` | async | public | 112 | `(trending_service: TrendingService)` | router.get('/stats', response_model=TrendingStats) |
| `refresh_trending` | async | public | 124 | `(platform: Optional[str], trending_service: TrendingService)` | router.post('/refresh', status_code=202) |
| `save_trending_as_idea` | async | public | 157 | `(trending_id: str, request: SaveTrendingRequest, trending_service: TrendingService)` | router.post('/{trending_id}/save', response_model=dict, status_code=201) |
| `get_platform_trending` | async | public | 182 | `(platform: str, category: Optional[str], limit: int, trending_service: TrendingService)` | router.get('/{platform}') |
| `cleanup_expired` | async | public | 225 | `(trending_service: TrendingService)` | router.delete('/cleanup', status_code=204) |
| `get_trending_categories` | async | public | 236 | `(platform: Optional[str], trending_service: TrendingService)` | router.get('/categories/list') |

### src\api\routers\websocket.py

Functions: 15

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `ConnectionManager.__init__` | method | dunder | 21 | `(self)` | - |
| `ConnectionManager.connect` | async | public | 25 | `(self, websocket: WebSocket)` | - |
| `ConnectionManager.disconnect` | method | public | 30 | `(self, websocket: WebSocket)` | - |
| `ConnectionManager.broadcast` | async | public | 37 | `(self, message: dict)` | - |
| `ConnectionManager.send_to_printer_subscribers` | async | public | 55 | `(self, printer_id: str, message: dict)` | - |
| `ConnectionManager.subscribe_to_printer` | method | public | 74 | `(self, websocket: WebSocket, printer_id: str)` | - |
| `ConnectionManager.unsubscribe_from_printer` | method | public | 80 | `(self, websocket: WebSocket, printer_id: str)` | - |
| `websocket_endpoint` | async | public | 90 | `(websocket: WebSocket)` | router.websocket('/') |
| `websocket_endpoint_no_slash` | async | public | 96 | `(websocket: WebSocket)` | router.websocket('') |
| `_handle_websocket_connection` | async | private | 101 | `(websocket: WebSocket, event_service: EventService)` | - |
| `handle_client_message` | async | public | 128 | `(websocket: WebSocket, message: dict)` | - |
| `broadcast_printer_status` | async | public | 161 | `(printer_id: UUID, status_data: dict)` | - |
| `broadcast_job_update` | async | public | 170 | `(job_id: UUID, job_data: dict)` | - |
| `broadcast_system_event` | async | public | 179 | `(event_type: str, event_data: dict)` | - |
| `get_connection_manager` | function | public | 189 | `()` | - |

### src\database\database.py

Functions: 56

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `Database.__init__` | method | dunder | 22 | `(self, db_path: Optional[str])` | - |
| `Database.initialize` | async | public | 31 | `(self)` | - |
| `Database._create_tables` | async | private | 46 | `(self)` | - |
| `Database._execute_write` | async | private | 197 | `(self, sql: str, params: Optional[tuple])` | - |
| `Database._fetch_one` | async | private | 235 | `(self, sql: str, params: Optional[List[Any]])` | - |
| `Database._fetch_all` | async | private | 249 | `(self, sql: str, params: Optional[List[Any]])` | - |
| `Database.close` | async | public | 263 | `(self)` | - |
| `Database.get_connection` | method | public | 269 | `(self)` | - |
| `Database.connection` | async | public | 276 | `(self)` | asynccontextmanager |
| `Database.health_check` | async | public | 282 | `(self)` | - |
| `Database.transaction` | async | public | 296 | `(self)` | asynccontextmanager |
| `Database.create_printer` | async | public | 304 | `(self, printer_data: Dict[str, Any])` | - |
| `Database.get_printer` | async | public | 325 | `(self, printer_id: str)` | - |
| `Database.list_printers` | async | public | 334 | `(self, active_only: bool)` | - |
| `Database.update_printer_status` | async | public | 347 | `(self, printer_id: str, status: str, last_seen: Optional[datetime])` | - |
| `Database.create_job` | async | public | 361 | `(self, job_data: Dict[str, Any])` | - |
| `Database.get_job` | async | public | 384 | `(self, job_id: str)` | - |
| `Database.list_jobs` | async | public | 396 | `(self, printer_id: Optional[str], status: Optional[str], is_business: Optional[bool], limit: Optional[int], offset: Optional[int])` | - |
| `Database.get_jobs_by_date_range` | async | public | 435 | `(self, start_date: str, end_date: str, is_business: Optional[bool])` | - |
| `Database.get_job_statistics` | async | public | 455 | `(self)` | - |
| `Database.update_job` | async | public | 519 | `(self, job_id: str, updates: Dict[str, Any])` | - |
| `Database.delete_job` | async | public | 545 | `(self, job_id: str)` | - |
| `Database.create_file` | async | public | 557 | `(self, file_data: Dict[str, Any])` | - |
| `Database.list_files` | async | public | 613 | `(self, printer_id: Optional[str], status: Optional[str], source: Optional[str])` | - |
| `Database.update_file` | async | public | 654 | `(self, file_id: str, updates: Dict[str, Any])` | - |
| `Database.update_file_enhanced_metadata` | async | public | 681 | `(self, file_id: str, enhanced_metadata: Dict[str, Any], last_analyzed: datetime)` | - |
| `Database.create_local_file` | async | public | 753 | `(self, file_data: Dict[str, Any])` | - |
| `Database.list_local_files` | async | public | 763 | `(self, watch_folder_path: Optional[str])` | - |
| `Database.delete_local_file` | async | public | 782 | `(self, file_id: str)` | - |
| `Database.get_file_statistics` | async | public | 790 | `(self)` | - |
| `Database.create_idea` | async | public | 823 | `(self, idea_data: Dict[str, Any])` | - |
| `Database.get_idea` | async | public | 853 | `(self, idea_id: str)` | - |
| `Database.list_ideas` | async | public | 862 | `(self, status: Optional[str], is_business: Optional[bool], category: Optional[str], source_type: Optional[str], limit: Optional[int], offset: Optional[int])` | - |
| `Database.update_idea` | async | public | 902 | `(self, idea_id: str, updates: Dict[str, Any])` | - |
| `Database.delete_idea` | async | public | 926 | `(self, idea_id: str)` | - |
| `Database.update_idea_status` | async | public | 937 | `(self, idea_id: str, status: str)` | - |
| `Database.add_idea_tags` | async | public | 945 | `(self, idea_id: str, tags: List[str])` | - |
| `Database.remove_idea_tags` | async | public | 958 | `(self, idea_id: str, tags: List[str])` | - |
| `Database.get_idea_tags` | async | public | 971 | `(self, idea_id: str)` | - |
| `Database.get_all_tags` | async | public | 983 | `(self)` | - |
| `Database.upsert_trending` | async | public | 996 | `(self, trending_data: Dict[str, Any])` | - |
| `Database.get_trending` | async | public | 1023 | `(self, platform: Optional[str], category: Optional[str])` | - |
| `Database.clean_expired_trending` | async | public | 1044 | `(self)` | - |
| `Database.get_idea_statistics` | async | public | 1055 | `(self)` | - |
| `Database.create_library_file` | async | public | 1102 | `(self, file_data: Dict[str, Any])` | - |
| `Database.get_library_file` | async | public | 1133 | `(self, file_id: str)` | - |
| `Database.get_library_file_by_checksum` | async | public | 1141 | `(self, checksum: str)` | - |
| `Database.update_library_file` | async | public | 1149 | `(self, checksum: str, updates: Dict[str, Any])` | - |
| `Database.delete_library_file` | async | public | 1163 | `(self, checksum: str)` | - |
| `Database.list_library_files` | async | public | 1170 | `(self, filters: Optional[Dict[str, Any]], page: int, limit: int)` | - |
| `Database.create_library_file_source` | async | public | 1290 | `(self, source_data: Dict[str, Any])` | - |
| `Database.get_library_file_sources` | async | public | 1315 | `(self, checksum: str)` | - |
| `Database.delete_library_file_sources` | async | public | 1323 | `(self, checksum: str)` | - |
| `Database.get_library_stats` | async | public | 1330 | `(self)` | - |
| `Database.update_file_enhanced_metadata` | async | public | 1339 | `(self, file_id: str, enhanced_metadata: Dict[str, Any], last_analyzed: datetime)` | - |
| `Database._run_migrations` | async | private | 1401 | `(self)` | - |

### src\main.py

Functions: 12

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `lifespan` | async | public | 88 | `(app: FastAPI)` | asynccontextmanager |
| `_on_printer_status_update` | async | private | 144 | `(data)` | - |
| `shutdown_with_timeout` | async | public | 181 | `(coro, service_name: str, timeout: float)` | - |
| `create_application` | function | public | 267 | `()` | - |
| `read_index` | async | public | 333 | `()` | app.get('/') |
| `read_debug` | async | public | 338 | `()` | app.get('/debug') |
| `metrics` | async | public | 344 | `()` | app.get('/metrics') |
| `printernizer_exception_handler` | async | public | 350 | `(request: Request, exc: PrinternizerException)` | app.exception_handler(PrinternizerException) |
| `validation_exception_handler` | async | public | 365 | `(request: Request, exc: RequestValidationError)` | app.exception_handler(RequestValidationError) |
| `general_exception_handler` | async | public | 379 | `(request: Request, exc: Exception)` | app.exception_handler(Exception) |
| `setup_signal_handlers` | function | public | 395 | `()` | - |
| `signal_handler` | function | public | 397 | `(signum, frame)` | - |

### src\models\idea.py

Functions: 7

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `Idea.to_dict` | method | public | 49 | `(self)` | - |
| `Idea.from_dict` | method | public | 74 | `(cls, data: Dict[str, Any])` | classmethod |
| `Idea.validate` | method | public | 98 | `(self)` | - |
| `Idea.get_formatted_time` | method | public | 110 | `(self)` | - |
| `TrendingItem.to_dict` | method | public | 138 | `(self)` | - |
| `TrendingItem.from_dict` | method | public | 157 | `(cls, data: Dict[str, Any])` | classmethod |
| `TrendingItem.is_expired` | method | public | 175 | `(self)` | - |

### src\models\job.py

Functions: 1

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `Job.convert_progress_to_int` | method | public | 45 | `(cls, v)` | field_validator('progress', mode='before') |

### src\models\material.py

Functions: 6

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `MaterialSpool.used_weight` | method | public | 77 | `(self)` | property |
| `MaterialSpool.remaining_percentage` | method | public | 82 | `(self)` | property |
| `MaterialSpool.total_cost` | method | public | 89 | `(self)` | property |
| `MaterialSpool.remaining_value` | method | public | 94 | `(self)` | property |
| `MaterialCreate.validate_remaining` | method | public | 116 | `(cls, v, values)` | field_validator('remaining_weight') |
| `MaterialConsumption.weight_used_kg` | method | public | 147 | `(self)` | property |

### src\models\watch_folder.py

Functions: 5

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `WatchFolder.to_dict` | method | public | 47 | `(self)` | - |
| `WatchFolder.from_dict` | method | public | 67 | `(cls, data: Dict[str, Any])` | classmethod |
| `WatchFolder.from_db_row` | method | public | 87 | `(cls, row: tuple)` | classmethod |
| `WatchFolder.get_display_name` | method | public | 106 | `(self)` | - |
| `WatchFolder.is_accessible` | method | public | 115 | `(self)` | - |

### src\printers\bambu_lab.py

Functions: 38

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuLabPrinter.__init__` | method | dunder | 39 | `(self, printer_id: str, name: str, ip_address: str, access_code: str, serial_number: str, file_service)` | - |
| `BambuLabPrinter._on_connect` | method | private | 74 | `(self, client, userdata, flags, rc)` | - |
| `BambuLabPrinter._on_message` | method | private | 85 | `(self, client, userdata, msg)` | - |
| `BambuLabPrinter._on_disconnect` | method | private | 94 | `(self, client, userdata, rc)` | - |
| `BambuLabPrinter.connect` | async | public | 98 | `(self)` | - |
| `BambuLabPrinter._connect_bambu_api` | async | private | 133 | `(self)` | - |
| `BambuLabPrinter._connect_mqtt` | async | private | 165 | `(self)` | - |
| `BambuLabPrinter._on_bambu_status_update` | async | private | 202 | `(self, status: Dict[str, Any])` | - |
| `BambuLabPrinter._on_bambu_file_list_update` | async | private | 207 | `(self, file_list_data: Dict[str, Any])` | - |
| `BambuLabPrinter.disconnect` | async | public | 236 | `(self)` | - |
| `BambuLabPrinter.get_status` | async | public | 262 | `(self)` | - |
| `BambuLabPrinter._get_status_bambu_api` | async | private | 283 | `(self)` | - |
| `BambuLabPrinter._get_status_mqtt` | async | private | 571 | `(self)` | - |
| `BambuLabPrinter._map_bambu_status` | method | private | 700 | `(self, bambu_status)` | - |
| `BambuLabPrinter.get_job_info` | async | public | 750 | `(self)` | - |
| `BambuLabPrinter._map_job_status` | method | private | 791 | `(self, bambu_status)` | - |
| `BambuLabPrinter.list_files` | async | public | 840 | `(self)` | - |
| `BambuLabPrinter._list_files_bambu_api` | async | private | 859 | `(self)` | - |
| `BambuLabPrinter._discover_files_via_ftp` | async | private | 946 | `(self)` | - |
| `BambuLabPrinter._discover_files_via_mqtt_dump` | async | private | 1020 | `(self)` | - |
| `BambuLabPrinter._list_files_mqtt` | async | private | 1088 | `(self)` | - |
| `BambuLabPrinter._list_files_mqtt_from_bambu_api` | async | private | 1170 | `(self)` | - |
| `BambuLabPrinter._list_files_direct_ftp` | async | private | 1220 | `(self)` | - |
| `BambuLabPrinter._download_file_direct_ftp` | async | private | 1255 | `(self, filename: str, local_path: str)` | - |
| `BambuLabPrinter._get_file_type_from_name` | method | private | 1285 | `(self, filename: str)` | - |
| `BambuLabPrinter.download_file` | async | public | 1299 | `(self, filename: str, local_path: str)` | - |
| `BambuLabPrinter._download_file_bambu_api` | async | private | 1318 | `(self, filename: str, local_path: str)` | - |
| `BambuLabPrinter._download_file_mqtt` | async | private | 1379 | `(self, filename: str, local_path: str)` | - |
| `BambuLabPrinter._download_via_ftp` | async | private | 1386 | `(self, filename: str, local_path: str)` | - |
| `BambuLabPrinter._safe_list` | method | private | 1445 | `(dir_path: str)` | - |
| `BambuLabPrinter.rank` | method | public | 1510 | `(item)` | - |
| `BambuLabPrinter._download_via_http` | async | private | 1554 | `(self, filename: str, local_path: str)` | - |
| `BambuLabPrinter.pause_print` | async | public | 1642 | `(self)` | - |
| `BambuLabPrinter.resume_print` | async | public | 1665 | `(self)` | - |
| `BambuLabPrinter.stop_print` | async | public | 1688 | `(self)` | - |
| `BambuLabPrinter.has_camera` | async | public | 1711 | `(self)` | - |
| `BambuLabPrinter.get_camera_stream_url` | async | public | 1725 | `(self)` | - |
| `BambuLabPrinter.take_snapshot` | async | public | 1746 | `(self)` | - |

### src\printers\base.py

Functions: 28

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrinterFile.__init__` | method | dunder | 33 | `(self, filename: str, size: Optional[int], modified: Optional[datetime], path: Optional[str], file_type: Optional[str])` | - |
| `PrinterFile._guess_file_type` | method | private | 42 | `(self, filename: str)` | - |
| `PrinterFile.__repr__` | method | dunder | 57 | `(self)` | - |
| `JobInfo.__init__` | method | dunder | 63 | `(self, job_id: str, name: str, status: JobStatus, progress: Optional[int], estimated_time: Optional[int], elapsed_time: Optional[int])` | - |
| `JobInfo.__repr__` | method | dunder | 75 | `(self)` | - |
| `PrinterInterface.connect` | async | public | 83 | `(self)` | abstractmethod |
| `PrinterInterface.disconnect` | async | public | 88 | `(self)` | abstractmethod |
| `PrinterInterface.get_status` | async | public | 93 | `(self)` | abstractmethod |
| `PrinterInterface.get_job_info` | async | public | 98 | `(self)` | abstractmethod |
| `PrinterInterface.list_files` | async | public | 103 | `(self)` | abstractmethod |
| `PrinterInterface.download_file` | async | public | 108 | `(self, filename: str, local_path: str)` | abstractmethod |
| `PrinterInterface.pause_print` | async | public | 113 | `(self)` | abstractmethod |
| `PrinterInterface.resume_print` | async | public | 118 | `(self)` | abstractmethod |
| `PrinterInterface.stop_print` | async | public | 123 | `(self)` | abstractmethod |
| `PrinterInterface.has_camera` | async | public | 128 | `(self)` | abstractmethod |
| `PrinterInterface.get_camera_stream_url` | async | public | 133 | `(self)` | abstractmethod |
| `PrinterInterface.take_snapshot` | async | public | 138 | `(self)` | abstractmethod |
| `BasePrinter.__init__` | method | dunder | 146 | `(self, printer_id: str, name: str, ip_address: str)` | - |
| `BasePrinter.start_monitoring` | async | public | 168 | `(self, interval: int)` | - |
| `BasePrinter.stop_monitoring` | async | public | 185 | `(self)` | - |
| `BasePrinter._monitor_loop` | async | private | 203 | `(self, interval: int)` | - |
| `BasePrinter.add_status_callback` | method | public | 244 | `(self, callback: Callable[[PrinterStatusUpdate], None])` | - |
| `BasePrinter.remove_status_callback` | method | public | 248 | `(self, callback: Callable[[PrinterStatusUpdate], None])` | - |
| `BasePrinter.health_check` | async | public | 253 | `(self)` | - |
| `BasePrinter.get_connection_info` | method | public | 261 | `(self)` | - |
| `BasePrinter.get_monitoring_metrics` | method | public | 272 | `(self)` | - |
| `BasePrinter.__aenter__` | async | dunder | 285 | `(self)` | - |
| `BasePrinter.__aexit__` | async | dunder | 290 | `(self, exc_type, exc_val, exc_tb)` | - |

### src\printers\prusa.py

Functions: 20

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrusaPrinter.__init__` | method | dunder | 23 | `(self, printer_id: str, name: str, ip_address: str, api_key: str, file_service)` | - |
| `PrusaPrinter.connect` | async | public | 32 | `(self)` | - |
| `PrusaPrinter.disconnect` | async | public | 115 | `(self)` | - |
| `PrusaPrinter.get_status` | async | public | 133 | `(self)` | - |
| `PrusaPrinter._map_prusa_status` | method | private | 238 | `(self, prusa_state: str)` | - |
| `PrusaPrinter.get_job_info` | async | public | 253 | `(self)` | - |
| `PrusaPrinter._map_job_status` | method | private | 299 | `(self, prusa_state: str)` | - |
| `PrusaPrinter.list_files` | async | public | 316 | `(self)` | - |
| `PrusaPrinter.extract_files_from_structure` | method | public | 339 | `(items, prefix)` | - |
| `PrusaPrinter.get_files` | async | public | 399 | `(self)` | - |
| `PrusaPrinter.extract_raw_files_from_structure` | method | public | 421 | `(items, prefix)` | - |
| `PrusaPrinter.download_file` | async | public | 477 | `(self, filename: str, local_path: str)` | - |
| `PrusaPrinter._find_file_by_display_name` | async | private | 577 | `(self, display_name: str)` | - |
| `PrusaPrinter.download_thumbnail` | async | public | 628 | `(self, filename: str, size: str)` | - |
| `PrusaPrinter.pause_print` | async | public | 696 | `(self)` | - |
| `PrusaPrinter.resume_print` | async | public | 720 | `(self)` | - |
| `PrusaPrinter.stop_print` | async | public | 744 | `(self)` | - |
| `PrusaPrinter.has_camera` | async | public | 768 | `(self)` | - |
| `PrusaPrinter.get_camera_stream_url` | async | public | 774 | `(self)` | - |
| `PrusaPrinter.take_snapshot` | async | public | 780 | `(self)` | - |

### src\services\analytics_service.py

Functions: 12

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `AnalyticsService.__init__` | method | dunder | 16 | `(self, database: Database)` | - |
| `AnalyticsService.get_dashboard_stats` | async | public | 20 | `(self)` | - |
| `AnalyticsService.get_printer_usage` | async | public | 33 | `(self, days: int)` | - |
| `AnalyticsService.get_material_consumption` | async | public | 38 | `(self, days: int)` | - |
| `AnalyticsService.get_business_report` | async | public | 47 | `(self, start_date: datetime, end_date: datetime)` | - |
| `AnalyticsService.export_data` | async | public | 116 | `(self, format_type: str, filters: Dict[str, Any])` | - |
| `AnalyticsService.get_summary` | async | public | 128 | `(self, start_date: Optional[datetime], end_date: Optional[datetime])` | - |
| `AnalyticsService.get_business_analytics` | async | public | 168 | `(self, start_date: Optional[datetime], end_date: Optional[datetime])` | - |
| `AnalyticsService.get_dashboard_overview` | async | public | 223 | `(self, period: str)` | - |
| `AnalyticsService._get_job_statistics` | async | private | 260 | `(self, period: str)` | - |
| `AnalyticsService._get_file_statistics` | async | private | 282 | `(self)` | - |
| `AnalyticsService._get_printer_statistics` | async | private | 310 | `(self)` | - |

### src\services\bambu_ftp_service.py

Functions: 18

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuFTPFile.__init__` | method | dunder | 32 | `(self, name: str, size: int, permissions: str, modified: Optional[datetime], raw_line: str)` | - |
| `BambuFTPFile._determine_file_type` | method | private | 41 | `(self)` | - |
| `BambuFTPFile.is_3d_file` | method | public | 60 | `(self)` | property |
| `BambuFTPFile.to_dict` | method | public | 64 | `(self)` | - |
| `BambuFTPService.__init__` | method | dunder | 80 | `(self, ip_address: str, access_code: str, port: int)` | - |
| `BambuFTPService._create_ssl_context` | method | private | 102 | `(self)` | - |
| `BambuFTPService._connect_ftp` | async | private | 110 | `(self)` | - |
| `BambuFTPService._sync_connect` | method | private | 124 | `()` | - |
| `BambuFTPService.ftp_connection` | async | public | 154 | `(self)` | asynccontextmanager |
| `BambuFTPService.list_files` | async | public | 194 | `(self, directory: str)` | - |
| `BambuFTPService._sync_list` | method | private | 212 | `()` | - |
| `BambuFTPService._parse_ftp_line` | method | private | 247 | `(self, line: str)` | - |
| `BambuFTPService.download_file` | async | public | 296 | `(self, remote_filename: str, local_path: str, directory: str)` | - |
| `BambuFTPService._sync_download` | method | private | 320 | `()` | - |
| `BambuFTPService.file_exists` | async | public | 368 | `(self, filename: str, directory: str)` | - |
| `BambuFTPService.get_file_info` | async | public | 389 | `(self, filename: str, directory: str)` | - |
| `BambuFTPService.test_connection` | async | public | 410 | `(self)` | - |
| `create_bambu_ftp_service` | async | public | 433 | `(ip_address: str, access_code: str)` | - |

### src\services\bambu_parser.py

Functions: 20

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `BambuParser.__init__` | method | dunder | 82 | `(self)` | - |
| `BambuParser.parse_file` | async | public | 86 | `(self, file_path: str)` | - |
| `BambuParser._parse_gcode_file` | async | private | 141 | `(self, file_path: Path)` | - |
| `BambuParser._parse_3mf_file` | async | private | 176 | `(self, file_path: Path)` | - |
| `BambuParser._extract_gcode_thumbnails` | method | private | 255 | `(self, content: str)` | - |
| `BambuParser._extract_gcode_metadata` | method | private | 314 | `(self, content: str)` | - |
| `BambuParser._extract_advanced_metadata` | method | private | 375 | `(self, content: str)` | - |
| `BambuParser._convert_metadata_value` | method | private | 387 | `(self, key: str, value: str)` | - |
| `BambuParser._calculate_derived_metrics` | method | private | 438 | `(self, metadata: Dict[str, Any])` | - |
| `BambuParser._calculate_complexity_score` | method | private | 511 | `(self, metadata: Dict[str, Any])` | - |
| `BambuParser._calculate_difficulty_level` | method | private | 561 | `(self, metadata: Dict[str, Any])` | - |
| `BambuParser._extract_3mf_metadata` | method | private | 574 | `(self, xml_content: str)` | - |
| `BambuParser._parse_bgcode_file` | async | private | 606 | `(self, file_path: Path)` | - |
| `BambuParser._parse_stl_file` | async | private | 720 | `(self, file_path: Path)` | - |
| `BambuParser._extract_png_dimensions` | method | private | 763 | `(self, png_data: bytes)` | - |
| `BambuParser._parse_thumbnail_dimensions` | method | private | 775 | `(self, filename: str)` | - |
| `BambuParser._parse_time_duration` | method | private | 785 | `(self, time_str: str)` | - |
| `BambuParser._is_valid_base64` | method | private | 820 | `(self, s: str)` | - |
| `BambuParser.get_largest_thumbnail` | method | public | 832 | `(self, thumbnails: List[Dict[str, Any]])` | - |
| `BambuParser.get_thumbnail_by_size` | method | public | 841 | `(self, thumbnails: List[Dict[str, Any]], preferred_size: Tuple[int, int])` | - |

### src\services\config_service.py

Functions: 32

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrinterConfig.__post_init__` | method | dunder | 33 | `(self)` | - |
| `PrinterConfig._validate_config` | method | private | 37 | `(self)` | - |
| `PrinterConfig.from_dict` | method | public | 49 | `(cls, printer_id: str, config: Dict[str, Any])` | classmethod |
| `PrinterConfig.to_dict` | method | public | 62 | `(self)` | - |
| `Settings.get_cors_origins` | method | public | 115 | `(self)` | - |
| `Settings.normalize_downloads_path` | method | public | 124 | `(cls, v: str)` | field_validator('downloads_path'), classmethod |
| `Settings.normalize_library_path` | method | public | 159 | `(cls, v: str)` | field_validator('library_path'), classmethod |
| `ConfigService.__init__` | method | dunder | 192 | `(self, config_path: Optional[str], database)` | - |
| `ConfigService._load_printer_configs` | method | private | 205 | `(self)` | - |
| `ConfigService._load_from_environment` | method | private | 234 | `(self)` | - |
| `ConfigService._create_default_config` | method | private | 276 | `(self)` | - |
| `ConfigService.get_printers` | method | public | 307 | `(self)` | - |
| `ConfigService.get_printer` | method | public | 311 | `(self, printer_id: str)` | - |
| `ConfigService.get_active_printers` | method | public | 315 | `(self)` | - |
| `ConfigService.add_printer` | method | public | 322 | `(self, printer_id: str, config: Dict[str, Any])` | - |
| `ConfigService.remove_printer` | method | public | 338 | `(self, printer_id: str)` | - |
| `ConfigService._save_config` | method | private | 347 | `(self)` | - |
| `ConfigService.validate_printer_connection` | method | public | 372 | `(self, printer_id: str)` | - |
| `ConfigService.get_business_settings` | method | public | 384 | `(self)` | - |
| `ConfigService.reload_config` | method | public | 393 | `(self)` | - |
| `ConfigService.get_watch_folders` | async | public | 407 | `(self)` | - |
| `ConfigService.is_watch_folders_enabled` | method | public | 412 | `(self)` | - |
| `ConfigService.is_recursive_watching_enabled` | method | public | 417 | `(self)` | - |
| `ConfigService.validate_watch_folder` | method | public | 422 | `(self, folder_path: str)` | - |
| `ConfigService.get_watch_folder_settings` | async | public | 441 | `(self)` | - |
| `ConfigService.get_application_settings` | method | public | 454 | `(self)` | - |
| `ConfigService._get_cors_origins_list` | method | private | 484 | `(self, cors_origins_str: str)` | - |
| `ConfigService.update_application_settings` | method | public | 490 | `(self, settings_dict: Dict[str, Any])` | - |
| `ConfigService._persist_settings_to_env` | method | private | 533 | `(self, settings_dict: Dict[str, Any])` | - |
| `ConfigService.add_watch_folder` | async | public | 579 | `(self, folder_path: str)` | - |
| `ConfigService.remove_watch_folder` | async | public | 613 | `(self, folder_path: str)` | - |
| `ConfigService._ensure_env_migration` | async | private | 635 | `(self)` | - |

### src\services\event_service.py

Functions: 13

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `EventService.__init__` | method | dunder | 16 | `(self, printer_service, job_service, file_service, database)` | - |
| `EventService.start` | async | public | 45 | `(self)` | - |
| `EventService.stop` | async | public | 63 | `(self)` | - |
| `EventService.subscribe` | method | public | 83 | `(self, event_type: str, handler: Callable)` | - |
| `EventService.unsubscribe` | method | public | 89 | `(self, event_type: str, handler: Callable)` | - |
| `EventService.emit_event` | async | public | 95 | `(self, event_type: str, data: Dict[str, Any])` | - |
| `EventService._printer_monitoring_task` | async | private | 111 | `(self)` | - |
| `EventService._job_status_task` | async | private | 222 | `(self)` | - |
| `EventService._file_discovery_task` | async | private | 333 | `(self)` | - |
| `EventService.get_status` | method | public | 452 | `(self)` | - |
| `EventService.set_services` | method | public | 476 | `(self, printer_service, job_service, file_service, database)` | - |
| `EventService.force_discovery` | async | public | 493 | `(self)` | - |
| `EventService.reset_monitoring_state` | async | public | 543 | `(self)` | - |

### src\services\file_service.py

Functions: 22

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `FileService.__init__` | method | dunder | 24 | `(self, database: Database, event_service: EventService, file_watcher: Optional[FileWatcherService], printer_service, config_service, library_service)` | - |
| `FileService.get_files` | async | public | 43 | `(self, printer_id: Optional[str], include_local: bool, status: Optional[str], source: Optional[str], has_thumbnail: Optional[bool], search: Optional[str], limit: Optional[int], order_by: Optional[str], order_dir: Optional[str], page: Optional[int])` | - |
| `FileService.get_printer_files` | async | public | 154 | `(self, printer_id: str)` | - |
| `FileService.download_file` | async | public | 192 | `(self, printer_id: str, filename: str, destination_path: Optional[str])` | - |
| `FileService.get_download_status` | async | public | 367 | `(self, file_id: str)` | - |
| `FileService.get_local_files` | async | public | 406 | `(self)` | - |
| `FileService.scan_local_files` | async | public | 417 | `(self)` | - |
| `FileService.get_watch_status` | async | public | 435 | `(self)` | - |
| `FileService.reload_watch_folders` | async | public | 446 | `(self)` | - |
| `FileService.get_file_statistics` | async | public | 458 | `(self)` | - |
| `FileService._get_file_type` | method | private | 538 | `(self, filename: str)` | - |
| `FileService._extract_printer_info` | method | private | 551 | `(self, printer: Dict[str, Any])` | - |
| `FileService.sync_printer_files` | async | public | 599 | `(self, printer_id: str)` | - |
| `FileService.discover_printer_files` | async | public | 648 | `(self, printer_id: str)` | - |
| `FileService.get_file_by_id` | async | public | 688 | `(self, file_id: str)` | - |
| `FileService.find_file_by_name` | async | public | 709 | `(self, filename: str, printer_id: Optional[str])` | - |
| `FileService.delete_file` | async | public | 732 | `(self, file_id: str)` | - |
| `FileService.cleanup_download_status` | async | public | 782 | `(self, max_age_hours: int)` | - |
| `FileService.process_file_thumbnails` | async | public | 803 | `(self, file_path: str, file_id: str)` | - |
| `FileService._log_thumbnail_processing` | method | private | 982 | `(self, file_path: str, file_id: str, status: str, details: Optional[str])` | - |
| `FileService.get_thumbnail_processing_log` | method | public | 1001 | `(self, limit: Optional[int])` | - |
| `FileService.extract_enhanced_metadata` | async | public | 1007 | `(self, file_id: str)` | - |

### src\services\file_watcher_service.py

Functions: 23

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrintFileHandler.__init__` | method | dunder | 54 | `(self, file_watcher: 'FileWatcherService')` | - |
| `PrintFileHandler.should_process_file` | method | public | 61 | `(self, file_path: str)` | - |
| `PrintFileHandler._debounce_event` | method | private | 80 | `(self, file_path: str)` | - |
| `PrintFileHandler.on_created` | method | public | 92 | `(self, event: FileSystemEvent)` | - |
| `PrintFileHandler.on_modified` | method | public | 99 | `(self, event: FileSystemEvent)` | - |
| `PrintFileHandler.on_deleted` | method | public | 106 | `(self, event: FileSystemEvent)` | - |
| `PrintFileHandler.on_moved` | method | public | 112 | `(self, event: FileSystemEvent)` | - |
| `FileWatcherService.__init__` | method | dunder | 126 | `(self, config_service: ConfigService, event_service: EventService, library_service)` | - |
| `FileWatcherService.start` | async | public | 141 | `(self)` | - |
| `FileWatcherService.stop` | async | public | 203 | `(self)` | - |
| `FileWatcherService._add_watch_folder` | async | private | 241 | `(self, folder_path: str, recursive: bool)` | - |
| `FileWatcherService._initial_scan` | async | private | 280 | `(self)` | - |
| `FileWatcherService._scan_folder` | async | private | 294 | `(self, folder_path: Path, recursive: bool)` | - |
| `FileWatcherService._process_discovered_file` | async | private | 310 | `(self, file_path: str)` | - |
| `FileWatcherService._find_watch_folder_for_file` | method | private | 388 | `(self, file_path: str)` | - |
| `FileWatcherService._handle_file_created` | async | private | 403 | `(self, file_path: str)` | - |
| `FileWatcherService._handle_file_modified` | async | private | 407 | `(self, file_path: str)` | - |
| `FileWatcherService._handle_file_deleted` | async | private | 429 | `(self, file_path: str)` | - |
| `FileWatcherService._handle_file_moved` | async | private | 442 | `(self, old_path: str, new_path: str)` | - |
| `FileWatcherService._emit_file_event` | async | private | 469 | `(self, event_type: str, local_file: LocalFile)` | - |
| `FileWatcherService.get_local_files` | method | public | 491 | `(self)` | - |
| `FileWatcherService.get_watch_status` | method | public | 511 | `(self)` | - |
| `FileWatcherService.reload_watch_folders` | async | public | 520 | `(self)` | - |

### src\services\idea_service.py

Functions: 16

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `IdeaService.__init__` | method | dunder | 20 | `(self, db: Database)` | - |
| `IdeaService.create_idea` | async | public | 24 | `(self, idea_data: Dict[str, Any])` | - |
| `IdeaService.get_idea` | async | public | 63 | `(self, idea_id: str)` | - |
| `IdeaService.list_ideas` | async | public | 88 | `(self, filters: Optional[Dict[str, Any]], page: int, page_size: int)` | - |
| `IdeaService.update_idea` | async | public | 134 | `(self, idea_id: str, updates: Dict[str, Any])` | - |
| `IdeaService.delete_idea` | async | public | 165 | `(self, idea_id: str)` | - |
| `IdeaService.update_idea_status` | async | public | 177 | `(self, idea_id: str, status: str)` | - |
| `IdeaService.get_all_tags` | async | public | 189 | `(self)` | - |
| `IdeaService.get_statistics` | async | public | 197 | `(self)` | - |
| `IdeaService.import_from_url` | async | public | 205 | `(self, url: str, additional_data: Optional[Dict[str, Any]])` | - |
| `IdeaService._extract_url_metadata` | async | private | 233 | `(self, url: str)` | - |
| `IdeaService.cache_trending` | async | public | 242 | `(self, platform: str, models: List[Dict[str, Any]], cache_duration_hours: int)` | - |
| `IdeaService.get_trending` | async | public | 272 | `(self, platform: Optional[str], category: Optional[str])` | - |
| `IdeaService.save_trending_as_idea` | async | public | 283 | `(self, trending_id: str, additional_data: Optional[Dict[str, Any]])` | - |
| `IdeaService.cleanup_expired_trending` | async | public | 320 | `(self)` | - |
| `IdeaService.search_ideas` | async | public | 332 | `(self, query: str, filters: Optional[Dict[str, Any]])` | - |

### src\services\job_service.py

Functions: 15

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `JobService.__init__` | method | dunder | 20 | `(self, database: Database, event_service: EventService)` | - |
| `JobService.get_jobs` | async | public | 25 | `(self, limit: int, offset: int)` | - |
| `JobService.list_jobs` | async | public | 80 | `(self, printer_id, status, is_business, limit: int, offset: int)` | - |
| `JobService.get_job` | async | public | 142 | `(self, job_id)` | - |
| `JobService.delete_job` | async | public | 167 | `(self, job_id)` | - |
| `JobService.get_active_jobs` | async | public | 193 | `(self)` | - |
| `JobService.create_job` | async | public | 230 | `(self, job_data: Dict[str, Any])` | - |
| `JobService.update_job_status` | async | public | 287 | `(self, job_id: str, status: str, data: Dict[str, Any])` | - |
| `JobService.get_job_statistics` | async | public | 339 | `(self)` | - |
| `JobService.get_jobs_by_date_range` | async | public | 391 | `(self, start_date: str, end_date: str, is_business: Optional[bool])` | - |
| `JobService.get_business_jobs` | async | public | 426 | `(self, limit: int, offset: int)` | - |
| `JobService.get_private_jobs` | async | public | 430 | `(self, limit: int, offset: int)` | - |
| `JobService.calculate_material_costs` | async | public | 434 | `(self, job_id: str, material_cost_per_gram: float, power_cost_per_hour: float)` | - |
| `JobService.get_printer_jobs` | async | public | 467 | `(self, printer_id: str, limit: int, offset: int)` | - |
| `JobService.update_job_progress` | async | public | 471 | `(self, job_id: str, progress: int, material_used: Optional[float])` | - |

### src\services\library_service.py

Functions: 16

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `LibraryService.__init__` | method | dunder | 24 | `(self, database, config_service, event_service)` | - |
| `LibraryService.initialize` | async | public | 52 | `(self)` | - |
| `LibraryService.calculate_checksum` | async | public | 89 | `(self, file_path: Path, algorithm: str)` | - |
| `LibraryService._calculate_checksum_sync` | method | private | 106 | `(self, file_path: Path, algorithm: str)` | - |
| `LibraryService.get_library_path_for_file` | method | public | 134 | `(self, checksum: str, source_type: str, original_filename: str, printer_name: str)` | - |
| `LibraryService._resolve_filename_conflict` | method | private | 169 | `(self, target_path: Path)` | - |
| `LibraryService._check_duplicate` | async | private | 202 | `(self, checksum: str)` | - |
| `LibraryService.add_file_to_library` | async | public | 215 | `(self, source_path: Path, source_info: Dict[str, Any], copy_file: bool, calculate_hash: bool)` | - |
| `LibraryService.get_file_by_checksum` | async | public | 425 | `(self, checksum: str)` | - |
| `LibraryService.get_file_by_id` | async | public | 437 | `(self, file_id: str)` | - |
| `LibraryService.list_files` | async | public | 449 | `(self, filters: Dict[str, Any], page: int, limit: int)` | - |
| `LibraryService.add_file_source` | async | public | 470 | `(self, checksum: str, source_info: Dict[str, Any])` | - |
| `LibraryService.delete_file` | async | public | 518 | `(self, checksum: str, delete_physical: bool)` | - |
| `LibraryService.get_library_statistics` | async | public | 560 | `(self)` | - |
| `LibraryService._extract_metadata_async` | async | private | 569 | `(self, file_id: str, checksum: str)` | - |
| `LibraryService.reprocess_file` | async | public | 625 | `(self, checksum: str)` | - |

### src\services\material_service.py

Functions: 18

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `MaterialService.__init__` | method | dunder | 39 | `(self, db: Database, event_service: EventService)` | - |
| `MaterialService.initialize` | async | public | 46 | `(self)` | - |
| `MaterialService._create_tables` | async | private | 56 | `(self)` | - |
| `MaterialService._load_materials` | async | private | 108 | `(self)` | - |
| `MaterialService._row_to_material` | method | private | 119 | `(self, row)` | - |
| `MaterialService.create_material` | async | public | 139 | `(self, material_data: MaterialCreate)` | - |
| `MaterialService.update_material` | async | public | 184 | `(self, material_id: str, update_data: MaterialUpdate)` | - |
| `MaterialService.record_consumption` | async | public | 224 | `(self, job_id: str, material_id: str, weight_grams: float, printer_id: str, file_name: Optional[str], print_time_hours: Optional[float])` | - |
| `MaterialService.get_material` | async | public | 284 | `(self, material_id: str)` | - |
| `MaterialService.get_all_materials` | async | public | 288 | `(self)` | - |
| `MaterialService.get_materials_by_type` | async | public | 292 | `(self, material_type: MaterialType)` | - |
| `MaterialService.get_materials_by_printer` | async | public | 296 | `(self, printer_id: str)` | - |
| `MaterialService.get_low_stock_materials` | async | public | 300 | `(self, threshold: float)` | - |
| `MaterialService.get_statistics` | async | public | 304 | `(self)` | - |
| `MaterialService._calculate_consumption_period` | async | private | 386 | `(self, days: int)` | - |
| `MaterialService.generate_report` | async | public | 402 | `(self, start_date: datetime, end_date: datetime)` | - |
| `MaterialService.export_inventory` | async | public | 513 | `(self, file_path: Path)` | - |
| `MaterialService.cleanup` | async | public | 539 | `(self)` | - |

### src\services\migration_service.py

Functions: 8

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `MigrationService.__init__` | method | dunder | 19 | `(self, database: Database)` | - |
| `MigrationService.run_migrations` | async | public | 25 | `(self)` | - |
| `MigrationService._ensure_migrations_table` | async | private | 60 | `(self)` | - |
| `MigrationService._get_completed_migrations` | async | private | 81 | `(self)` | - |
| `MigrationService._get_migration_files` | method | private | 102 | `(self)` | - |
| `MigrationService._run_migration_file` | async | private | 118 | `(self, migration_file: Path, migration_name: str)` | - |
| `MigrationService.get_migration_status` | async | public | 152 | `(self)` | - |
| `MigrationService.force_run_migration` | async | public | 177 | `(self, migration_name: str)` | - |

### src\services\monitoring_service.py

Functions: 14

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `MonitoringService.__init__` | method | dunder | 21 | `(self)` | - |
| `MonitoringService.start_monitoring` | async | public | 40 | `(self)` | - |
| `MonitoringService._error_monitoring_loop` | async | private | 51 | `(self)` | - |
| `MonitoringService._health_check_loop` | async | private | 61 | `(self)` | - |
| `MonitoringService._cleanup_old_logs_loop` | async | private | 71 | `(self)` | - |
| `MonitoringService._check_error_rates` | async | private | 81 | `(self)` | - |
| `MonitoringService._check_error_patterns` | async | private | 120 | `(self, stats: Dict[str, Any])` | - |
| `MonitoringService._perform_health_checks` | async | private | 146 | `(self)` | - |
| `MonitoringService._check_database_health` | async | private | 173 | `(self)` | - |
| `MonitoringService._check_file_system_health` | async | private | 207 | `(self)` | - |
| `MonitoringService._trigger_alert` | async | private | 238 | `(self, alert_type: str, message: str, context: Dict[str, Any])` | - |
| `MonitoringService._store_alert` | async | private | 272 | `(self, alert_type: str, message: str, context: Dict[str, Any])` | - |
| `MonitoringService._cleanup_old_logs` | async | private | 291 | `(self)` | - |
| `MonitoringService.get_monitoring_status` | async | public | 317 | `(self)` | - |

### src\services\preview_render_service.py

Functions: 11

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PreviewRenderService.__init__` | method | dunder | 37 | `(self, cache_dir: str)` | - |
| `PreviewRenderService.get_or_generate_preview` | async | public | 86 | `(self, file_path: str, file_type: str, size: Tuple[int, int])` | - |
| `PreviewRenderService._render_file` | method | private | 152 | `(self, file_path: str, file_type: str, size: Tuple[int, int])` | - |
| `PreviewRenderService._render_stl` | method | private | 181 | `(self, file_path: str, size: Tuple[int, int])` | - |
| `PreviewRenderService._render_3mf` | method | private | 264 | `(self, file_path: str, size: Tuple[int, int])` | - |
| `PreviewRenderService._render_mesh_common` | method | private | 298 | `(self, mesh: 'trimesh.Trimesh', size: Tuple[int, int])` | - |
| `PreviewRenderService._render_gcode_toolpath` | method | private | 372 | `(self, file_path: str, size: Tuple[int, int])` | - |
| `PreviewRenderService._get_cache_key` | method | private | 479 | `(self, file_path: str, size: Tuple[int, int])` | - |
| `PreviewRenderService.clear_cache` | async | public | 499 | `(self, older_than_days: Optional[int])` | - |
| `PreviewRenderService.get_statistics` | method | public | 537 | `(self)` | - |
| `PreviewRenderService.update_config` | method | public | 551 | `(self, config: Dict[str, Any])` | - |

### src\services\printer_service.py

Functions: 33

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrinterService.__init__` | method | dunder | 24 | `(self, database: Database, event_service: EventService, config_service: ConfigService, file_service)` | - |
| `PrinterService.initialize` | async | public | 35 | `(self)` | - |
| `PrinterService._load_printers` | async | private | 42 | `(self)` | - |
| `PrinterService._create_printer_instance` | method | private | 70 | `(self, printer_id: str, config)` | - |
| `PrinterService._sync_database_printers` | async | private | 93 | `(self)` | - |
| `PrinterService._handle_status_update` | async | private | 116 | `(self, status: PrinterStatusUpdate)` | - |
| `PrinterService._is_print_file` | method | private | 165 | `(self, filename: str)` | - |
| `PrinterService._attempt_download_current_job` | async | private | 172 | `(self, printer_id: str, filename: str)` | - |
| `PrinterService._attempt` | async | private | 178 | `(name: str)` | - |
| `PrinterService._store_status_update` | async | private | 245 | `(self, status: PrinterStatusUpdate)` | - |
| `PrinterService.list_printers` | async | public | 254 | `(self)` | - |
| `PrinterService.get_printers` | async | public | 288 | `(self)` | - |
| `PrinterService.get_printer` | async | public | 305 | `(self, printer_id: str)` | - |
| `PrinterService.get_printer_driver` | async | public | 333 | `(self, printer_id: str)` | - |
| `PrinterService.get_printer_status` | async | public | 337 | `(self, printer_id: str)` | - |
| `PrinterService.connect_printer` | async | public | 370 | `(self, printer_id: str)` | - |
| `PrinterService.disconnect_printer` | async | public | 391 | `(self, printer_id: str)` | - |
| `PrinterService._connect_and_monitor_printer` | async | private | 404 | `(self, printer_id: str, instance: BasePrinter)` | - |
| `PrinterService.start_monitoring` | async | public | 430 | `(self, printer_id: Optional[str])` | - |
| `PrinterService.stop_monitoring` | async | public | 475 | `(self, printer_id: Optional[str])` | - |
| `PrinterService.get_printer_files` | async | public | 502 | `(self, printer_id: str)` | - |
| `PrinterService.download_printer_file` | async | public | 526 | `(self, printer_id: str, filename: str, local_path: str)` | - |
| `PrinterService.download_current_job_file` | async | public | 552 | `(self, printer_id: str)` | - |
| `PrinterService.health_check` | async | public | 623 | `(self)` | - |
| `PrinterService.shutdown` | async | public | 653 | `(self)` | - |
| `PrinterService.create_printer` | async | public | 671 | `(self, name: str, printer_type: PrinterType, connection_config: Dict[str, Any], location: Optional[str], description: Optional[str])` | - |
| `PrinterService.update_printer` | async | public | 723 | `(self, printer_id: UUID)` | - |
| `PrinterService.delete_printer` | async | public | 775 | `(self, printer_id: UUID)` | - |
| `PrinterService.pause_printer` | async | public | 789 | `(self, printer_id: str)` | - |
| `PrinterService.resume_printer` | async | public | 803 | `(self, printer_id: str)` | - |
| `PrinterService.stop_printer` | async | public | 817 | `(self, printer_id: str)` | - |
| `PrinterService.start_printer_monitoring` | async | public | 831 | `(self, printer_id: str)` | - |
| `PrinterService.stop_printer_monitoring` | async | public | 849 | `(self, printer_id: str)` | - |

### src\services\threemf_analyzer.py

Functions: 9

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `ThreeMFAnalyzer.__init__` | method | dunder | 18 | `(self)` | - |
| `ThreeMFAnalyzer.analyze_file` | async | public | 22 | `(self, file_path: Path)` | - |
| `ThreeMFAnalyzer._analyze_model_geometry` | async | private | 73 | `(self, zip_file: zipfile.ZipFile)` | - |
| `ThreeMFAnalyzer._analyze_print_settings` | async | private | 122 | `(self, zip_file: zipfile.ZipFile)` | - |
| `ThreeMFAnalyzer._analyze_material_usage` | async | private | 177 | `(self, zip_file: zipfile.ZipFile)` | - |
| `ThreeMFAnalyzer._analyze_compatibility` | async | private | 230 | `(self, zip_file: zipfile.ZipFile)` | - |
| `ThreeMFAnalyzer._calculate_costs` | async | private | 264 | `(self, metadata: Dict[str, Any])` | - |
| `ThreeMFAnalyzer._assess_quality` | async | private | 321 | `(self, metadata: Dict[str, Any])` | - |
| `ThreeMFAnalyzer._safe_extract` | method | private | 392 | `(self, data: dict, key: str, default: Any, as_int: bool)` | - |

### src\services\thumbnail_service.py

Functions: 12

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `ThumbnailService.__init__` | method | dunder | 27 | `(self, event_service: EventService)` | - |
| `ThumbnailService._get_session` | async | private | 37 | `(self)` | - |
| `ThumbnailService._get_cache_path` | method | private | 47 | `(self, url: str, source_type: str)` | - |
| `ThumbnailService.download_thumbnail` | async | public | 66 | `(self, url: str, source_type: str, force_refresh: bool)` | - |
| `ThumbnailService._process_and_save_image` | async | private | 110 | `(self, image_data: bytes, cache_path: Path, original_url: str)` | - |
| `ThumbnailService.get_thumbnail` | async | public | 161 | `(self, url: str, source_type: str, auto_download: bool)` | - |
| `ThumbnailService.cache_multiple_thumbnails` | async | public | 181 | `(self, url_list: list[Dict[str, str]], max_concurrent: int)` | - |
| `ThumbnailService.download_single` | async | public | 187 | `(item: Dict[str, str])` | - |
| `ThumbnailService.cleanup_expired` | async | public | 210 | `(self)` | - |
| `ThumbnailService.get_cache_statistics` | async | public | 233 | `(self)` | - |
| `ThumbnailService.clear_cache` | async | public | 287 | `(self, source_type: Optional[str])` | - |
| `ThumbnailService.cleanup` | async | public | 315 | `(self)` | - |

### src\services\trending_service.py

Functions: 22

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TrendingService.__init__` | method | dunder | 34 | `(self, db: Database, event_service: EventService)` | - |
| `TrendingService.initialize` | async | public | 55 | `(self)` | - |
| `TrendingService._create_tables` | async | private | 65 | `(self)` | - |
| `TrendingService._retry_with_backoff` | async | private | 95 | `(self, func)` | - |
| `TrendingService._get_session` | async | private | 150 | `(self)` | - |
| `TrendingService._close_session` | async | private | 187 | `(self)` | - |
| `TrendingService._start_refresh_task` | async | private | 197 | `(self)` | - |
| `TrendingService._refresh_loop` | async | private | 202 | `(self)` | - |
| `TrendingService._needs_refresh` | async | private | 219 | `(self)` | - |
| `TrendingService._fetch_url` | async | private | 239 | `(self, url: str)` | - |
| `TrendingService._fetch` | async | private | 243 | `()` | - |
| `TrendingService.fetch_makerworld_trending` | async | public | 285 | `(self)` | - |
| `TrendingService.fetch_printables_trending` | async | public | 330 | `(self)` | - |
| `TrendingService._extract_id_from_url` | method | private | 376 | `(self, url: str, platform: str)` | - |
| `TrendingService._parse_count` | method | private | 389 | `(self, text: str)` | - |
| `TrendingService.save_trending_items` | async | public | 409 | `(self, items: List[Dict[str, Any]], platform: str)` | - |
| `TrendingService.get_trending` | async | public | 466 | `(self, platform: Optional[str], category: Optional[str], limit: int)` | - |
| `TrendingService.refresh_all_platforms` | async | public | 494 | `(self)` | - |
| `TrendingService.cleanup_expired` | async | public | 524 | `(self)` | - |
| `TrendingService.save_as_idea` | async | public | 548 | `(self, trending_id: str, user_notes: Optional[str])` | - |
| `TrendingService.get_statistics` | async | public | 595 | `(self)` | - |
| `TrendingService.cleanup` | async | public | 652 | `(self)` | - |

### src\services\url_parser_service.py

Functions: 12

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `UrlParserService.__init__` | method | dunder | 19 | `(self)` | - |
| `UrlParserService._get_session` | async | private | 22 | `(self)` | - |
| `UrlParserService.close` | async | public | 32 | `(self)` | - |
| `UrlParserService.detect_platform` | method | public | 38 | `(self, url: str)` | - |
| `UrlParserService.extract_model_id` | method | public | 55 | `(self, url: str, platform: str)` | - |
| `UrlParserService.fetch_page_title` | async | public | 89 | `(self, url: str)` | - |
| `UrlParserService._clean_title` | method | private | 110 | `(self, title: str)` | - |
| `UrlParserService.extract_creator_from_title` | method | public | 129 | `(self, title: str, platform: str)` | - |
| `UrlParserService.parse_url` | async | public | 144 | `(self, url: str)` | - |
| `UrlParserService.get_platform_info` | method | public | 198 | `(self, platform: str)` | - |
| `UrlParserService.validate_url` | method | public | 243 | `(self, url: str)` | - |
| `UrlParserService.get_supported_platforms` | method | public | 256 | `(self)` | - |

### src\services\watch_folder_db_service.py

Functions: 12

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `WatchFolderDbService.__init__` | method | dunder | 21 | `(self, database: Database)` | - |
| `WatchFolderDbService.create_watch_folder` | async | public | 25 | `(self, watch_folder: WatchFolder)` | - |
| `WatchFolderDbService.get_watch_folder_by_id` | async | public | 68 | `(self, folder_id: int)` | - |
| `WatchFolderDbService.get_watch_folder_by_path` | async | public | 86 | `(self, folder_path: str)` | - |
| `WatchFolderDbService.get_all_watch_folders` | async | public | 104 | `(self, active_only: bool)` | - |
| `WatchFolderDbService.update_watch_folder` | async | public | 125 | `(self, folder_id: int, updates: Dict[str, Any])` | - |
| `WatchFolderDbService.delete_watch_folder` | async | public | 173 | `(self, folder_id: int)` | - |
| `WatchFolderDbService.delete_watch_folder_by_path` | async | public | 194 | `(self, folder_path: str)` | - |
| `WatchFolderDbService.get_active_folder_paths` | async | public | 215 | `(self)` | - |
| `WatchFolderDbService.update_folder_statistics` | async | public | 230 | `(self, folder_path: str, file_count: int)` | - |
| `WatchFolderDbService.validate_and_update_folder` | async | public | 253 | `(self, folder_path: str, is_valid: bool, error_message: Optional[str])` | - |
| `WatchFolderDbService.migrate_env_folders` | async | public | 277 | `(self, folder_paths: List[str])` | - |

### src\utils\config.py

Functions: 8

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrinternizerSettings.validate_secret_key` | method | public | 90 | `(cls, v)` | validator('secret_key') |
| `PrinternizerSettings.validate_library_path` | method | public | 105 | `(cls, v)` | validator('library_path') |
| `PrinternizerSettings.cors_origins_list` | method | public | 124 | `(self)` | property |
| `PrinternizerSettings.watch_folders_list` | method | public | 131 | `(self)` | property |
| `PrinternizerSettings.is_homeassistant_addon` | method | public | 138 | `(self)` | property |
| `PrinternizerSettings.mqtt_available` | method | public | 143 | `(self)` | property |
| `get_settings` | function | public | 157 | `()` | - |
| `reload_settings` | function | public | 165 | `()` | - |

### src\utils\dependencies.py

Functions: 11

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `get_database` | async | public | 19 | `(request: Request)` | - |
| `get_config_service` | async | public | 24 | `(request: Request)` | - |
| `get_event_service` | async | public | 29 | `(request: Request)` | - |
| `get_printer_service` | async | public | 34 | `(request: Request)` | - |
| `get_job_service` | async | public | 39 | `(database: Database, event_service: EventService)` | - |
| `get_file_service` | async | public | 47 | `(request: Request)` | - |
| `get_analytics_service` | async | public | 52 | `(database: Database)` | - |
| `get_idea_service` | async | public | 59 | `(database: Database)` | - |
| `get_trending_service` | async | public | 66 | `(request: Request)` | - |
| `get_thumbnail_service` | async | public | 71 | `(request: Request)` | - |
| `get_url_parser_service` | async | public | 76 | `(request: Request)` | - |

### src\utils\error_handling.py

Functions: 21

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `ErrorHandler.__init__` | method | dunder | 45 | `(self)` | - |
| `ErrorHandler.ensure_log_directory` | method | public | 49 | `(self)` | - |
| `ErrorHandler.handle_error` | method | public | 53 | `(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity, context: Optional[Dict[str, Any]], user_message: Optional[str], should_log_to_file: bool)` | - |
| `ErrorHandler._generate_error_id` | method | private | 109 | `(self)` | - |
| `ErrorHandler._get_log_level` | method | private | 113 | `(self, severity: ErrorSeverity)` | - |
| `ErrorHandler._generate_user_message` | method | private | 123 | `(self, category: ErrorCategory, error: Exception)` | - |
| `ErrorHandler._log_to_file` | method | private | 140 | `(self, error_info: Dict[str, Any])` | - |
| `ErrorHandler._handle_critical_error` | method | private | 148 | `(self, error_info: Dict[str, Any])` | - |
| `ErrorHandler.get_error_statistics` | method | public | 164 | `(self, hours: int)` | - |
| `ErrorHandler._empty_stats` | method | private | 189 | `(self, hours: int)` | - |
| `ErrorHandler._calculate_statistics` | method | private | 200 | `(self, errors: list, hours: int)` | - |
| `handle_exceptions` | function | public | 233 | `(category: ErrorCategory, severity: ErrorSeverity, user_message: Optional[str], reraise: bool)` | - |
| `decorator` | function | public | 248 | `(func: Callable)` | - |
| `sync_wrapper` | function | public | 250 | `()` | functools.wraps(func) |
| `async_wrapper` | async | public | 270 | `()` | functools.wraps(func) |
| `ErrorReportingMixin.report_error` | method | public | 297 | `(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity, context: Optional[Dict[str, Any]], user_message: Optional[str])` | - |
| `handle_database_error` | function | public | 316 | `(error: Exception, context: Optional[Dict[str, Any]])` | - |
| `handle_api_error` | function | public | 326 | `(error: Exception, context: Optional[Dict[str, Any]])` | - |
| `handle_printer_error` | function | public | 336 | `(error: Exception, context: Optional[Dict[str, Any]])` | - |
| `handle_file_error` | function | public | 346 | `(error: Exception, context: Optional[Dict[str, Any]])` | - |
| `handle_validation_error` | function | public | 356 | `(error: Exception, context: Optional[Dict[str, Any]])` | - |

### src\utils\exceptions.py

Functions: 9

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrinternizerException.__init__` | method | dunder | 12 | `(self, message: str, error_code: str, status_code: int, details: Optional[Dict[str, Any]])` | - |
| `ConfigurationError.__init__` | method | dunder | 31 | `(self, message: str, details: Optional[Dict[str, Any]])` | - |
| `DatabaseError.__init__` | method | dunder | 43 | `(self, message: str, details: Optional[Dict[str, Any]])` | - |
| `PrinterConnectionError.__init__` | method | dunder | 55 | `(self, printer_id: str, message: str, details: Optional[Dict[str, Any]])` | - |
| `FileOperationError.__init__` | method | dunder | 67 | `(self, operation: str, filename: str, message: str, details: Optional[Dict[str, Any]])` | - |
| `ValidationError.__init__` | method | dunder | 79 | `(self, field: str, message: str, details: Optional[Dict[str, Any]])` | - |
| `AuthenticationError.__init__` | method | dunder | 91 | `(self, message: str, details: Optional[Dict[str, Any]])` | - |
| `AuthorizationError.__init__` | method | dunder | 103 | `(self, message: str, details: Optional[Dict[str, Any]])` | - |
| `NotFoundError.__init__` | method | dunder | 115 | `(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]])` | - |

### src\utils\gcode_analyzer.py

Functions: 5

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `GcodeAnalyzer.__init__` | method | dunder | 36 | `(self, optimize_enabled: bool)` | - |
| `GcodeAnalyzer.find_print_start_line` | method | public | 45 | `(self, gcode_lines: List[str])` | - |
| `GcodeAnalyzer._is_likely_print_move` | method | private | 109 | `(self, gcode_line: str)` | - |
| `GcodeAnalyzer.get_optimized_gcode_lines` | method | public | 153 | `(self, gcode_lines: List[str])` | - |
| `GcodeAnalyzer.analyze_gcode_file` | method | public | 178 | `(self, file_path: str, max_lines: int)` | - |

### src\utils\logging_config.py

Functions: 2

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `setup_logging` | function | public | 12 | `(log_level: str, log_file: str)` | - |
| `get_logger` | function | public | 66 | `(name: str)` | - |

### src\utils\middleware.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `RequestTimingMiddleware.dispatch` | async | public | 17 | `(self, request: Request, call_next: Callable)` | - |
| `SecurityHeadersMiddleware.dispatch` | async | public | 46 | `(self, request: Request, call_next: Callable)` | - |
| `GermanComplianceMiddleware.dispatch` | async | public | 79 | `(self, request: Request, call_next: Callable)` | - |

### tests\backend\test_api_files.py

Functions: 31

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestFileAPI.test_get_files_unified_empty` | method | public | 17 | `(self, api_client, temp_database, test_config)` | - |
| `TestFileAPI.test_get_files_unified_with_data` | method | public | 32 | `(self, api_client, populated_database, test_config, sample_file_data)` | - |
| `TestFileAPI.test_get_files_filter_by_printer` | method | public | 63 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_get_files_filter_by_status` | method | public | 75 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_get_files_filter_by_type` | method | public | 87 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_post_file_download_bambu_lab` | method | public | 99 | `(self, api_client, populated_database, test_config, mock_bambu_api, temp_download_directory, sample_3mf_file)` | - |
| `TestFileAPI.test_post_file_download_prusa` | method | public | 127 | `(self, api_client, populated_database, test_config, mock_prusa_api, temp_download_directory)` | - |
| `TestFileAPI.test_post_file_download_already_downloaded` | method | public | 152 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_post_file_download_printer_offline` | method | public | 167 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_post_file_download_disk_space_error` | method | public | 186 | `(self, api_client, populated_database, test_config, mock_bambu_api)` | - |
| `TestFileAPI.test_post_file_download_with_progress_tracking` | method | public | 208 | `(self, api_client, populated_database, test_config, mock_bambu_api, temp_download_directory)` | - |
| `TestFileAPI.test_delete_file_local` | method | public | 235 | `(self, api_client, populated_database, test_config, temp_download_directory)` | - |
| `TestFileAPI.test_delete_file_available_only` | method | public | 257 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_get_file_download_progress` | method | public | 269 | `(self, api_client, test_config)` | - |
| `TestFileAPI.test_get_file_download_history` | method | public | 294 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPI.test_post_file_cleanup` | method | public | 307 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileBusinessLogic.test_german_file_naming_sanitization` | method | public | 340 | `(self)` | - |
| `TestFileBusinessLogic.test_file_download_path_organization` | method | public | 367 | `(self, temp_download_directory, test_utils)` | - |
| `TestFileBusinessLogic.test_file_checksum_verification` | method | public | 394 | `(self, sample_3mf_file)` | - |
| `TestFileBusinessLogic.test_file_size_validation_german_limits` | method | public | 407 | `(self)` | - |
| `TestFileBusinessLogic.test_file_metadata_extraction_3mf` | method | public | 423 | `(self, sample_3mf_file)` | - |
| `TestFileBusinessLogic.test_disk_space_monitoring` | method | public | 433 | `(self, temp_download_directory)` | - |
| `TestFileAPIPerformance.test_large_file_list_performance` | method | public | 452 | `(self, api_client, db_connection, test_config)` | - |
| `TestFileAPIPerformance.test_concurrent_file_downloads` | method | public | 490 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileAPIPerformance.download_file` | method | public | 496 | `(file_id)` | - |
| `sanitize_german_filename` | function | public | 526 | `(filename)` | - |
| `generate_download_path` | function | public | 552 | `(base_dir, printer_id, filename)` | - |
| `calculate_file_checksum` | function | public | 562 | `(file_content, algorithm)` | - |
| `validate_file_size` | function | public | 572 | `(file_size_bytes, max_size_mb)` | - |
| `extract_3mf_metadata` | function | public | 578 | `(file_content)` | - |
| `check_disk_space` | function | public | 598 | `(directory, required_bytes)` | - |

### tests\backend\test_api_health.py

Functions: 6

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `client` | function | public | 12 | `()` | pytest.fixture |
| `TestHealthEndpoint.test_health_check_success` | method | public | 20 | `(self, client)` | - |
| `TestHealthEndpoint.test_health_check_includes_system_info` | method | public | 31 | `(self, client)` | - |
| `TestHealthEndpoint.test_health_check_response_format` | method | public | 43 | `(self, client)` | - |
| `TestHealthEndpoint.test_health_check_german_timezone` | method | public | 56 | `(self, client)` | - |
| `TestHealthEndpoint.test_health_check_performance` | async | public | 68 | `(self, client)` | pytest.mark.asyncio |

### tests\backend\test_api_jobs.py

Functions: 30

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestJobAPI.test_get_jobs_empty_database` | method | public | 16 | `(self, api_client, temp_database, test_config)` | - |
| `TestJobAPI.test_get_jobs_with_data` | method | public | 30 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_get_jobs_filter_by_status` | method | public | 54 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_get_jobs_filter_by_printer` | method | public | 66 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_get_jobs_filter_by_business_type` | method | public | 78 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_get_jobs_date_range_filter` | method | public | 91 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_get_jobs_pagination` | method | public | 108 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_post_jobs_create_new_job` | method | public | 122 | `(self, api_client, db_connection, test_config)` | - |
| `TestJobAPI.test_post_jobs_validation_errors` | method | public | 162 | `(self, api_client, test_config)` | - |
| `TestJobAPI.test_get_job_details` | method | public | 207 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_get_job_details_not_found` | method | public | 239 | `(self, api_client, test_config)` | - |
| `TestJobAPI.test_put_job_status_update` | method | public | 246 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_put_job_completion_with_quality_assessment` | method | public | 271 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_put_job_failure_handling` | method | public | 305 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_put_job_status_invalid_transitions` | method | public | 332 | `(self, api_client, test_config)` | - |
| `TestJobAPI.test_delete_job` | method | public | 359 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPI.test_delete_active_job_forbidden` | method | public | 370 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobBusinessLogic.test_german_cost_calculations` | method | public | 386 | `(self, sample_cost_calculations, german_business_config)` | - |
| `TestJobBusinessLogic.test_business_vs_private_job_classification` | method | public | 419 | `(self, populated_database)` | - |
| `TestJobBusinessLogic.test_job_timezone_handling` | method | public | 436 | `(self, populated_database, test_utils)` | - |
| `TestJobBusinessLogic.test_material_usage_tracking` | method | public | 446 | `(self, sample_job_data)` | - |
| `TestJobBusinessLogic.test_print_quality_assessment_german_standards` | method | public | 464 | `(self, sample_job_data)` | - |
| `TestJobAPIPerformance.test_large_job_list_performance` | method | public | 487 | `(self, api_client, db_connection, test_config)` | - |
| `TestJobAPIPerformance.test_job_filtering_performance` | method | public | 524 | `(self, api_client, db_connection, test_config)` | - |
| `TestJobAPIPerformance.test_concurrent_job_updates` | method | public | 546 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPIPerformance.update_job_status` | method | public | 553 | `(job_id, status)` | - |
| `TestJobAPIErrorHandling.test_job_api_database_connection_error` | method | public | 585 | `(self, api_client, test_config)` | - |
| `TestJobAPIErrorHandling.test_job_creation_with_invalid_printer` | method | public | 596 | `(self, api_client, test_config)` | - |
| `TestJobAPIErrorHandling.test_job_update_race_condition_handling` | method | public | 611 | `(self, api_client, populated_database, test_config)` | - |
| `TestJobAPIErrorHandling.test_job_deletion_safety_checks` | method | public | 635 | `(self, api_client, populated_database, test_config)` | - |

### tests\backend\test_api_printers.py

Functions: 28

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestPrinterAPI.test_get_printers_empty_database` | method | public | 16 | `(self, api_client, temp_database, test_config)` | - |
| `TestPrinterAPI.test_get_printers_with_data` | method | public | 30 | `(self, api_client, populated_database, test_config, sample_printer_data)` | - |
| `TestPrinterAPI.test_get_printers_filter_by_type` | method | public | 53 | `(self, api_client, populated_database, test_config)` | - |
| `TestPrinterAPI.test_get_printers_filter_by_active_status` | method | public | 65 | `(self, api_client, populated_database, test_config)` | - |
| `TestPrinterAPI.test_post_printers_bambu_lab` | method | public | 77 | `(self, api_client, db_connection, test_config)` | - |
| `TestPrinterAPI.test_post_printers_prusa` | method | public | 106 | `(self, api_client, db_connection, test_config)` | - |
| `TestPrinterAPI.test_post_printers_validation_errors` | method | public | 130 | `(self, api_client, test_config)` | - |
| `TestPrinterAPI.test_get_printer_status_bambu_lab` | method | public | 177 | `(self, api_client, populated_database, test_config, mock_bambu_api)` | - |
| `TestPrinterAPI.test_get_printer_status_prusa` | method | public | 209 | `(self, api_client, populated_database, test_config, mock_prusa_api)` | - |
| `TestPrinterAPI.test_get_printer_status_offline` | method | public | 233 | `(self, api_client, test_config)` | - |
| `TestPrinterAPI.test_get_printer_status_not_found` | method | public | 249 | `(self, api_client, test_config)` | - |
| `TestPrinterAPI.test_put_printers_update_config` | method | public | 258 | `(self, api_client, populated_database, test_config)` | - |
| `TestPrinterAPI.test_put_printers_invalid_update` | method | public | 281 | `(self, api_client, test_config)` | - |
| `TestPrinterAPI.test_delete_printers` | method | public | 305 | `(self, api_client, populated_database, test_config)` | - |
| `TestPrinterAPI.test_delete_printer_with_active_jobs` | method | public | 325 | `(self, api_client, populated_database, test_config)` | - |
| `TestPrinterAPI.test_printer_connection_test` | method | public | 340 | `(self, api_client, test_config, mock_bambu_api)` | - |
| `TestPrinterAPI.test_printer_connection_test_failed` | method | public | 357 | `(self, api_client, test_config)` | - |
| `TestPrinterBusinessLogic.test_printer_timezone_handling` | method | public | 377 | `(self, populated_database, german_business_config, test_utils)` | - |
| `TestPrinterBusinessLogic.test_printer_cost_calculations_euro` | method | public | 392 | `(self, sample_cost_calculations, test_utils)` | - |
| `TestPrinterBusinessLogic.test_printer_business_hours_validation` | method | public | 415 | `(self, german_business_config)` | - |
| `TestPrinterBusinessLogic.test_printer_id_generation_german_locale` | method | public | 435 | `(self)` | - |
| `generate_printer_id` | function | public | 449 | `(name, printer_type)` | - |
| `TestPrinterAPIEdgeCases.test_concurrent_printer_requests` | method | public | 465 | `(self, api_client, test_config, populated_database)` | - |
| `TestPrinterAPIEdgeCases.make_request` | method | public | 472 | `()` | - |
| `TestPrinterAPIEdgeCases.test_large_printer_list_performance` | method | public | 494 | `(self, api_client, test_config, db_connection)` | - |
| `TestPrinterAPIEdgeCases.test_printer_api_rate_limiting` | method | public | 532 | `(self, api_client, test_config)` | - |
| `TestPrinterAPIEdgeCases.test_invalid_json_handling` | method | public | 546 | `(self, api_client, test_config)` | - |
| `TestPrinterAPIEdgeCases.test_oversized_request_handling` | method | public | 560 | `(self, api_client, test_config)` | - |

### tests\backend\test_database.py

Functions: 18

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestDatabaseSchema.test_database_creation` | method | public | 14 | `(self, temp_database)` | - |
| `TestDatabaseSchema.test_printer_table_constraints` | method | public | 37 | `(self, db_connection)` | - |
| `TestDatabaseSchema.test_job_table_constraints` | method | public | 64 | `(self, populated_database)` | - |
| `TestDatabaseSchema.test_file_table_generated_columns` | method | public | 106 | `(self, db_connection)` | - |
| `TestDatabaseSchema.test_database_indexes` | method | public | 135 | `(self, temp_database)` | - |
| `TestDatabaseSchema.test_database_triggers` | method | public | 163 | `(self, populated_database)` | - |
| `TestDatabaseSchema.test_job_status_change_trigger` | method | public | 185 | `(self, populated_database)` | - |
| `TestDatabaseSchema.test_foreign_key_constraints` | method | public | 217 | `(self, populated_database)` | - |
| `TestDatabaseSchema.test_database_views` | method | public | 237 | `(self, populated_database)` | - |
| `TestGermanBusinessLogic.test_european_timezone_handling` | method | public | 269 | `(self, populated_database, test_utils)` | - |
| `TestGermanBusinessLogic.test_euro_currency_calculations` | method | public | 296 | `(self, populated_database)` | - |
| `TestGermanBusinessLogic.test_german_business_hours_config` | method | public | 333 | `(self, populated_database)` | - |
| `TestGermanBusinessLogic.test_material_cost_per_gram_tracking` | method | public | 350 | `(self, populated_database)` | - |
| `TestGermanBusinessLogic.test_power_cost_calculation_german_rates` | method | public | 373 | `(self, populated_database)` | - |
| `TestGermanBusinessLogic.test_business_vs_private_job_tracking` | method | public | 395 | `(self, populated_database)` | - |
| `TestGermanBusinessLogic.test_german_file_retention_policies` | method | public | 435 | `(self, populated_database)` | - |
| `TestDatabasePerformance.test_job_query_performance_with_indexes` | method | public | 478 | `(self, db_connection)` | - |
| `TestDatabasePerformance.test_database_size_estimates` | method | public | 518 | `(self, db_connection)` | - |

### tests\backend\test_end_to_end.py

Functions: 10

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestE2EPrinterSetupWorkflow.test_complete_bambu_lab_setup` | async | public | 25 | `(self, api_client, temp_database, test_config, mock_bambu_api)` | pytest.mark.asyncio |
| `TestE2EPrinterSetupWorkflow.test_complete_prusa_setup` | async | public | 116 | `(self, api_client, temp_database, test_config, mock_prusa_api)` | pytest.mark.asyncio |
| `TestE2EJobManagementWorkflow.test_complete_print_job_lifecycle` | async | public | 172 | `(self, api_client, populated_database, test_config, german_business_config, mock_bambu_api)` | pytest.mark.asyncio |
| `TestE2EJobManagementWorkflow.test_job_failure_and_recovery` | async | public | 290 | `(self, api_client, populated_database, test_config)` | pytest.mark.asyncio |
| `TestE2EFileManagementWorkflow.test_complete_file_download_workflow` | async | public | 354 | `(self, api_client, populated_database, test_config, temp_download_directory)` | pytest.mark.asyncio |
| `TestE2EFileManagementWorkflow.test_file_cleanup_workflow` | async | public | 465 | `(self, api_client, populated_database, test_config)` | pytest.mark.asyncio |
| `TestE2EDashboardWorkflow.test_complete_dashboard_monitoring` | async | public | 517 | `(self, api_client, populated_database, test_config, german_business_config)` | pytest.mark.asyncio |
| `TestE2EDashboardWorkflow.test_real_time_dashboard_updates` | async | public | 607 | `(self, api_client, populated_database, test_config, mock_websocket)` | pytest.mark.asyncio |
| `TestE2EDashboardWorkflow.mock_websocket_handler` | async | public | 620 | `()` | - |
| `TestE2EGermanBusinessCompliance.test_complete_vat_compliance_workflow` | async | public | 686 | `(self, api_client, temp_database, test_config, german_business_config)` | pytest.mark.asyncio |

### tests\backend\test_error_handling.py

Functions: 32

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestNetworkErrorHandling.test_printer_connection_timeout` | method | public | 31 | `(self, api_client, test_config)` | - |
| `TestNetworkErrorHandling.test_network_interruption_during_operation` | method | public | 54 | `(self, api_client, populated_database, test_config)` | - |
| `TestNetworkErrorHandling.test_dns_resolution_failure` | method | public | 73 | `(self, api_client, test_config)` | - |
| `TestNetworkErrorHandling.test_ssl_certificate_errors` | method | public | 94 | `(self, api_client, test_config)` | - |
| `TestDataValidationErrors.test_malformed_json_requests` | method | public | 121 | `(self, api_client, test_config)` | - |
| `TestDataValidationErrors.test_invalid_data_types` | method | public | 155 | `(self, api_client, test_config)` | - |
| `TestDataValidationErrors.test_out_of_range_values` | method | public | 191 | `(self, api_client, test_config)` | - |
| `TestDataValidationErrors.test_string_length_validation` | method | public | 221 | `(self, api_client, test_config)` | - |
| `TestDatabaseErrorHandling.test_database_connection_failure` | method | public | 258 | `(self, api_client, test_config)` | - |
| `TestDatabaseErrorHandling.test_database_corruption` | method | public | 273 | `(self, temp_database, api_client, test_config)` | - |
| `TestDatabaseErrorHandling.test_constraint_violations` | method | public | 289 | `(self, api_client, populated_database, test_config)` | - |
| `TestDatabaseErrorHandling.test_transaction_rollback_on_error` | method | public | 313 | `(self, api_client, populated_database, test_config)` | - |
| `TestFileSystemErrorHandling.test_insufficient_disk_space` | method | public | 347 | `(self, api_client, test_config, temp_download_directory)` | - |
| `TestFileSystemErrorHandling.test_permission_denied_errors` | method | public | 367 | `(self, api_client, test_config)` | - |
| `TestFileSystemErrorHandling.test_file_corruption_during_download` | method | public | 382 | `(self, api_client, test_config)` | - |
| `TestFileSystemErrorHandling.test_missing_file_errors` | method | public | 409 | `(self, api_client, test_config)` | - |
| `TestConcurrencyErrorHandling.test_concurrent_resource_access` | method | public | 435 | `(self, api_client, populated_database, test_config)` | - |
| `TestConcurrencyErrorHandling.make_update` | method | public | 458 | `(update_data, result_list)` | - |
| `TestConcurrencyErrorHandling.test_race_condition_in_job_creation` | method | public | 481 | `(self, api_client, populated_database, test_config)` | - |
| `TestConcurrencyErrorHandling.create_job` | method | public | 509 | `(result_list)` | - |
| `TestSecurityErrorHandling.test_sql_injection_attempts` | method | public | 532 | `(self, api_client, test_config)` | - |
| `TestSecurityErrorHandling.test_path_traversal_attempts` | method | public | 566 | `(self, api_client, test_config)` | - |
| `TestSecurityErrorHandling.test_xss_prevention` | method | public | 600 | `(self, api_client, test_config)` | - |
| `TestResourceExhaustionHandling.test_memory_exhaustion_handling` | method | public | 643 | `(self, api_client, test_config)` | - |
| `TestResourceExhaustionHandling.test_too_many_concurrent_requests` | method | public | 659 | `(self, api_client, test_config)` | - |
| `TestResourceExhaustionHandling.test_disk_space_exhaustion` | method | public | 682 | `(self, api_client, test_config)` | - |
| `TestEdgeCaseScenarios.test_unicode_and_special_characters` | method | public | 700 | `(self, api_client, test_config)` | - |
| `TestEdgeCaseScenarios.test_extreme_numeric_values` | method | public | 731 | `(self, api_client, test_config)` | - |
| `TestEdgeCaseScenarios.test_very_long_operations` | method | public | 759 | `(self, api_client, test_config)` | - |
| `TestEdgeCaseScenarios.slow_download` | method | public | 767 | `()` | - |
| `TestEdgeCaseScenarios.test_circular_references_in_data` | method | public | 782 | `(self, api_client, test_config)` | - |
| `CircularReference.__init__` | method | dunder | 788 | `(self)` | - |

### tests\backend\test_german_business.py

Functions: 21

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestGermanCurrencyHandling.test_eur_currency_formatting` | method | public | 23 | `(self, german_business_config)` | - |
| `TestGermanCurrencyHandling.test_currency_precision` | method | public | 46 | `(self)` | - |
| `TestGermanCurrencyHandling.test_currency_conversion_edge_cases` | method | public | 66 | `(self)` | - |
| `TestGermanVATCalculations.test_standard_vat_rate_19_percent` | method | public | 90 | `(self, german_business_config)` | - |
| `TestGermanVATCalculations.test_reverse_vat_calculation` | method | public | 120 | `(self)` | - |
| `TestGermanVATCalculations.test_vat_exemption_cases` | method | public | 146 | `(self)` | - |
| `TestGermanVATCalculations.test_complex_invoice_vat_calculation` | method | public | 165 | `(self)` | - |
| `TestGermanTimezoneHandling.test_berlin_timezone_conversion` | method | public | 200 | `(self)` | - |
| `TestGermanTimezoneHandling.test_daylight_saving_time_transitions` | method | public | 223 | `(self)` | - |
| `TestGermanTimezoneHandling.test_business_hours_calculation` | method | public | 256 | `(self, german_business_config)` | - |
| `TestGermanDateTimeFormatting.test_german_date_formatting` | method | public | 293 | `(self)` | - |
| `TestGermanDateTimeFormatting.test_german_time_formatting` | method | public | 310 | `(self)` | - |
| `TestGermanDateTimeFormatting.test_german_datetime_formatting` | method | public | 327 | `(self)` | - |
| `TestGermanAccountingStandards.test_hgb_compliance` | method | public | 348 | `(self)` | - |
| `TestGermanAccountingStandards.test_gob_electronic_records` | method | public | 381 | `(self)` | - |
| `TestGermanAccountingStandards.test_invoice_numbering_sequence` | method | public | 412 | `(self)` | - |
| `TestGermanTaxReporting.test_ustva_vat_return_format` | method | public | 443 | `(self)` | - |
| `TestGermanTaxReporting.test_annual_tax_declaration` | method | public | 481 | `(self)` | - |
| `TestGermanTaxReporting.test_elster_xml_export` | method | public | 512 | `(self)` | - |
| `TestGermanBusinessWorkflows.test_b2b_invoice_workflow` | method | public | 564 | `(self, german_business_config)` | - |
| `TestGermanBusinessWorkflows.test_kleinunternehmer_exemption` | method | public | 636 | `(self)` | - |

### tests\backend\test_integration.py

Functions: 21

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestAPIIntegration.test_complete_printer_lifecycle` | method | public | 21 | `(self, api_client, temp_database, test_config)` | - |
| `TestAPIIntegration.test_complete_job_workflow` | method | public | 84 | `(self, api_client, populated_database, test_config, mock_bambu_api)` | - |
| `TestAPIIntegration.test_file_management_workflow` | method | public | 170 | `(self, api_client, populated_database, test_config, temp_download_directory)` | - |
| `TestAPIIntegration.test_dashboard_real_time_updates` | method | public | 231 | `(self, api_client, populated_database, test_config)` | - |
| `TestWebSocketIntegration.test_real_time_job_updates` | async | public | 268 | `(self, mock_websocket, populated_database)` | pytest.mark.asyncio |
| `TestWebSocketIntegration.mock_send` | async | public | 274 | `(message)` | - |
| `TestWebSocketIntegration.test_printer_status_broadcast` | async | public | 300 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketIntegration.mock_send` | async | public | 305 | `(message)` | - |
| `TestWebSocketIntegration.test_file_download_progress` | async | public | 331 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketIntegration.mock_send` | async | public | 336 | `(message)` | - |
| `TestGermanBusinessLogic.test_vat_calculations` | method | public | 360 | `(self, german_business_config, sample_cost_calculations)` | - |
| `TestGermanBusinessLogic.test_berlin_timezone_handling` | method | public | 392 | `(self, test_utils)` | - |
| `TestGermanBusinessLogic.test_currency_formatting` | method | public | 408 | `(self, test_utils)` | - |
| `TestGermanBusinessLogic.test_business_hours_validation` | method | public | 415 | `(self, german_business_config)` | - |
| `TestGermanBusinessLogic.test_export_data_format` | method | public | 435 | `(self, api_client, populated_database, test_config)` | - |
| `TestErrorHandlingIntegration.test_printer_connection_failure_recovery` | method | public | 461 | `(self, api_client, test_config)` | - |
| `TestErrorHandlingIntegration.test_database_transaction_rollback` | method | public | 481 | `(self, api_client, temp_database, test_config)` | - |
| `TestErrorHandlingIntegration.test_websocket_reconnection` | method | public | 504 | `(self, mock_websocket)` | - |
| `TestErrorHandlingIntegration.mock_connect` | async | public | 510 | `()` | - |
| `TestErrorHandlingIntegration.mock_disconnect` | async | public | 514 | `()` | - |
| `TestErrorHandlingIntegration.test_file_download_interruption_recovery` | method | public | 526 | `(self, api_client, test_config, temp_download_directory)` | - |

### tests\backend\test_job_null_fix.py

Functions: 5

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestNullJobIDFix.test_job_model_rejects_null_id` | async | public | 21 | `(self)` | pytest.mark.asyncio |
| `TestNullJobIDFix.test_database_prevents_null_job_ids` | async | public | 47 | `(self)` | pytest.mark.asyncio |
| `TestNullJobIDFix.test_job_service_creates_valid_ids` | async | public | 83 | `(self)` | pytest.mark.asyncio |
| `TestNullJobIDFix.test_migration_005_applied` | async | public | 129 | `(self)` | pytest.mark.asyncio |
| `TestNullJobIDFix.test_job_service_error_logging` | async | public | 163 | `(self)` | pytest.mark.asyncio |

### tests\backend\test_job_validation.py

Functions: 13

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `create_test_db` | async | public | 18 | `()` | - |
| `TestJobIDValidation.test_database_schema_prevents_null_ids` | async | public | 33 | `(self)` | pytest.mark.asyncio |
| `TestJobIDValidation.test_database_schema_prevents_empty_ids` | async | public | 50 | `(self)` | pytest.mark.asyncio |
| `TestJobIDValidation.test_job_service_creates_valid_id` | async | public | 67 | `(self)` | pytest.mark.asyncio |
| `TestJobIDValidation.test_job_model_validates_id_field` | async | public | 98 | `(self)` | pytest.mark.asyncio |
| `TestJobIDValidation.test_get_jobs_skips_invalid_jobs` | async | public | 125 | `(self, job_service, test_db)` | pytest.mark.asyncio |
| `TestJobIDValidation.test_list_jobs_skips_invalid_jobs` | async | public | 140 | `(self, job_service)` | pytest.mark.asyncio |
| `TestMigration005.test_migration_tracking_table_created` | async | public | 169 | `(self, test_db)` | pytest.mark.asyncio |
| `TestMigration005.test_migration_005_recorded` | async | public | 179 | `(self, test_db)` | pytest.mark.asyncio |
| `TestMigration005.test_jobs_table_has_not_null_constraint` | async | public | 191 | `(self, test_db)` | pytest.mark.asyncio |
| `TestJobCreationValidation.test_create_job_validates_required_fields` | async | public | 208 | `(self, job_service)` | pytest.mark.asyncio |
| `TestJobCreationValidation.test_create_job_generates_unique_ids` | async | public | 223 | `(self, job_service)` | pytest.mark.asyncio |
| `TestJobCreationValidation.test_create_job_with_business_info` | async | public | 243 | `(self, job_service)` | pytest.mark.asyncio |

### tests\backend\test_library_service.py

Functions: 36

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `temp_library_path` | function | public | 21 | `()` | pytest.fixture |
| `mock_database` | function | public | 29 | `()` | pytest.fixture |
| `mock_config_service` | function | public | 44 | `(temp_library_path)` | pytest.fixture |
| `mock_event_service` | function | public | 58 | `()` | pytest.fixture |
| `library_service` | async | public | 66 | `(mock_database, mock_config_service, mock_event_service)` | pytest.fixture |
| `sample_test_file` | function | public | 75 | `(temp_library_path)` | pytest.fixture |
| `TestLibraryServiceInitialization.test_initialize_creates_folders` | async | public | 86 | `(self, library_service, temp_library_path)` | pytest.mark.asyncio |
| `TestLibraryServiceInitialization.test_initialize_validates_write_permissions` | async | public | 95 | `(self, library_service, temp_library_path)` | pytest.mark.asyncio |
| `TestLibraryServiceInitialization.test_disabled_library_skips_initialization` | async | public | 101 | `(self, mock_database, mock_config_service, mock_event_service)` | pytest.mark.asyncio |
| `TestChecksumCalculation.test_calculate_checksum_sha256` | async | public | 114 | `(self, library_service, sample_test_file)` | pytest.mark.asyncio |
| `TestChecksumCalculation.test_calculate_checksum_consistent` | async | public | 121 | `(self, library_service, sample_test_file)` | pytest.mark.asyncio |
| `TestChecksumCalculation.test_calculate_checksum_different_files` | async | public | 128 | `(self, library_service, temp_library_path)` | pytest.mark.asyncio |
| `TestLibraryPathGeneration.test_watch_folder_path_generation` | method | public | 143 | `(self, library_service)` | - |
| `TestLibraryPathGeneration.test_printer_path_generation` | method | public | 155 | `(self, library_service)` | - |
| `TestLibraryPathGeneration.test_upload_path_generation` | method | public | 168 | `(self, library_service)` | - |
| `TestLibraryPathGeneration.test_path_sharding_distribution` | method | public | 180 | `(self, library_service)` | - |
| `TestFileAddition.test_add_new_file_to_library` | async | public | 203 | `(self, library_service, sample_test_file, mock_database)` | pytest.mark.asyncio |
| `TestFileAddition.test_add_duplicate_file_adds_source` | async | public | 221 | `(self, library_service, sample_test_file, mock_database)` | pytest.mark.asyncio |
| `TestFileAddition.test_disk_space_check` | async | public | 245 | `(self, library_service, temp_library_path, mock_database)` | pytest.mark.asyncio |
| `TestFileAddition.test_file_copy_preserves_original` | async | public | 262 | `(self, library_service, sample_test_file, mock_database, temp_library_path)` | pytest.mark.asyncio |
| `TestFileAddition.test_checksum_verification_after_copy` | async | public | 275 | `(self, library_service, sample_test_file, mock_database)` | pytest.mark.asyncio |
| `TestSourceTracking.test_add_multiple_sources` | async | public | 291 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestSourceTracking.test_duplicate_source_not_added` | async | public | 324 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestFileDeletion.test_delete_file_with_physical` | async | public | 349 | `(self, library_service, mock_database, temp_library_path)` | pytest.mark.asyncio |
| `TestFileDeletion.test_delete_file_database_only` | async | public | 371 | `(self, library_service, mock_database, temp_library_path)` | pytest.mark.asyncio |
| `TestListFiles.test_list_files_with_pagination` | async | public | 396 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestListFiles.test_list_files_with_filters` | async | public | 412 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestReprocessing.test_reprocess_file` | async | public | 430 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestReprocessing.test_reprocess_nonexistent_file` | async | public | 444 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestStatistics.test_get_statistics` | async | public | 457 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestErrorHandling.test_add_file_missing_source` | async | public | 476 | `(self, library_service, sample_test_file)` | pytest.mark.asyncio |
| `TestErrorHandling.test_add_file_invalid_source_type` | async | public | 485 | `(self, library_service, sample_test_file)` | pytest.mark.asyncio |
| `TestErrorHandling.test_database_error_cleanup` | async | public | 493 | `(self, library_service, sample_test_file, mock_database, temp_library_path)` | pytest.mark.asyncio |
| `TestConcurrency.test_concurrent_file_additions` | async | public | 512 | `(self, library_service, mock_database)` | pytest.mark.asyncio |
| `TestConcurrency.side_effect` | async | public | 518 | `()` | - |
| `TestIntegration.test_full_file_lifecycle` | async | public | 533 | `(self, library_service, sample_test_file, mock_database)` | pytest.mark.asyncio |

### tests\backend\test_performance.py

Functions: 33

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PerformanceTestBase.measure_performance` | method | public | 44 | `(self, func)` | - |
| `PerformanceTestBase.load_test` | async | public | 81 | `(self, async_func, concurrent_requests: int, total_requests: int)` | - |
| `PerformanceTestBase.bounded_request` | async | public | 85 | `()` | - |
| `TestDatabasePerformance.test_large_dataset_queries` | method | public | 117 | `(self, temp_database, performance_test_data)` | - |
| `TestDatabasePerformance.insert_large_dataset` | method | public | 126 | `()` | - |
| `TestDatabasePerformance.complex_query` | method | public | 172 | `()` | - |
| `TestDatabasePerformance.test_concurrent_database_access` | method | public | 195 | `(self, temp_database)` | - |
| `TestDatabasePerformance.database_worker` | method | public | 197 | `(worker_id: int, operations: int)` | - |
| `TestDatabasePerformance.test_database_indexing_performance` | method | public | 265 | `(self, temp_database)` | pytest.mark.benchmark |
| `TestDatabasePerformance.query_without_index` | method | public | 283 | `()` | - |
| `TestAPIPerformance.test_concurrent_api_requests` | async | public | 313 | `(self, api_client, populated_database, test_config)` | pytest.mark.asyncio |
| `TestAPIPerformance.api_request` | async | public | 316 | `()` | - |
| `TestAPIPerformance.test_large_response_performance` | method | public | 358 | `(self, api_client, test_config)` | - |
| `TestAPIPerformance.create_large_dataset_response` | method | public | 361 | `()` | - |
| `TestAPIPerformance.serialize_response` | method | public | 411 | `()` | - |
| `TestAPIPerformance.test_websocket_performance` | async | public | 423 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `WebSocketLoadTester.__init__` | method | dunder | 427 | `(self)` | - |
| `WebSocketLoadTester.send_high_frequency_updates` | async | public | 433 | `(self, messages_per_second: int, duration_seconds: int)` | - |
| `WebSocketLoadTester.get_performance_metrics` | method | public | 458 | `(self)` | - |
| `TestFileDownloadPerformance.test_large_file_download_performance` | method | public | 493 | `(self, temp_download_directory)` | - |
| `TestFileDownloadPerformance.simulate_large_file_download` | method | public | 496 | `(file_size_mb: int)` | - |
| `TestFileDownloadPerformance.test_concurrent_file_downloads` | method | public | 541 | `(self, temp_download_directory)` | - |
| `TestFileDownloadPerformance.download_worker` | method | public | 544 | `(worker_id: int, file_count: int)` | - |
| `TestMemoryAndResourceUsage.test_memory_usage_under_load` | method | public | 606 | `(self, populated_database)` | memory_profiler.profile |
| `TestMemoryAndResourceUsage.simulate_heavy_workload` | method | public | 609 | `()` | - |
| `TestMemoryAndResourceUsage.test_database_connection_pooling_performance` | method | public | 663 | `(self, temp_database)` | - |
| `DatabaseConnectionPool.__init__` | method | dunder | 667 | `(self, max_connections)` | - |
| `DatabaseConnectionPool.get_connection` | method | public | 679 | `(self)` | - |
| `DatabaseConnectionPool.return_connection` | method | public | 687 | `(self, conn)` | - |
| `DatabaseConnectionPool.close_all` | method | public | 692 | `(self)` | - |
| `TestMemoryAndResourceUsage.database_operation_with_pool` | method | public | 699 | `()` | - |
| `TestMemoryAndResourceUsage.test_cpu_usage_optimization` | method | public | 755 | `(self)` | - |
| `TestMemoryAndResourceUsage.cpu_intensive_task` | method | public | 758 | `(complexity_level: int)` | - |

### tests\backend\test_watch_folders.py

Functions: 9

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestWatchFolderConfiguration.test_config_settings` | method | public | 20 | `(self)` | - |
| `TestWatchFolderConfiguration.test_config_service_watch_folders` | method | public | 40 | `(self)` | - |
| `TestFileWatcherService.file_watcher` | async | public | 59 | `(self)` | pytest.fixture |
| `TestFileWatcherService.test_local_file_creation` | method | public | 74 | `(self)` | - |
| `TestFileWatcherService.test_file_watcher_status` | async | public | 92 | `(self, file_watcher)` | - |
| `TestFileWatcherService.test_print_file_handler_extension_filtering` | method | public | 104 | `(self)` | - |
| `TestFileWatcherService.test_local_files_list` | async | public | 129 | `(self, file_watcher)` | - |
| `TestWatchFolderIntegration.test_database_local_file_support` | method | public | 141 | `(self)` | - |
| `TestWatchFolderIntegration.test_file_service_local_integration` | method | public | 162 | `(self)` | - |

### tests\backend\test_websocket.py

Functions: 22

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestWebSocketConnection.test_websocket_connection_establishment` | async | public | 17 | `(self, mock_websocket, test_config)` | pytest.mark.asyncio |
| `TestWebSocketConnection.test_websocket_authentication` | async | public | 31 | `(self, mock_websocket, test_config)` | pytest.mark.asyncio |
| `TestWebSocketConnection.test_websocket_subscription_management` | async | public | 59 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketConnection.test_websocket_connection_error_handling` | async | public | 83 | `(self, test_config)` | pytest.mark.asyncio |
| `TestWebSocketConnection.test_websocket_reconnection_logic` | async | public | 96 | `(self, mock_websocket, test_config)` | pytest.mark.asyncio |
| `TestWebSocketRealTimeUpdates.test_printer_status_updates` | async | public | 126 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketRealTimeUpdates.test_job_progress_updates` | async | public | 160 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketRealTimeUpdates.test_file_download_progress_updates` | async | public | 188 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketRealTimeUpdates.test_system_event_notifications` | async | public | 216 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketRealTimeUpdates.test_batch_update_processing` | async | public | 241 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketErrorHandling.test_message_parsing_errors` | async | public | 284 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketErrorHandling.test_connection_timeout_handling` | async | public | 309 | `(self, test_config)` | pytest.mark.asyncio |
| `TestWebSocketErrorHandling.test_heartbeat_mechanism` | async | public | 321 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketErrorHandling.test_connection_recovery_after_network_error` | async | public | 351 | `(self, mock_websocket, test_config)` | pytest.mark.asyncio |
| `TestWebSocketErrorHandling.test_message_queue_overflow_handling` | async | public | 381 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketPerformance.test_high_frequency_updates_performance` | async | public | 421 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketPerformance.test_concurrent_websocket_connections` | async | public | 461 | `(self)` | pytest.mark.asyncio |
| `TestWebSocketPerformance.receive_messages` | async | public | 477 | `(connection, connection_id)` | - |
| `TestWebSocketPerformance.test_memory_usage_with_long_running_connection` | async | public | 495 | `(self, mock_websocket)` | pytest.mark.asyncio |
| `TestWebSocketGermanBusinessIntegration.test_german_timezone_in_websocket_messages` | async | public | 537 | `(self, mock_websocket, test_utils)` | pytest.mark.asyncio |
| `TestWebSocketGermanBusinessIntegration.test_business_cost_updates_via_websocket` | async | public | 559 | `(self, mock_websocket, test_utils)` | pytest.mark.asyncio |
| `TestWebSocketGermanBusinessIntegration.test_german_quality_assessment_updates` | async | public | 589 | `(self, mock_websocket)` | pytest.mark.asyncio |

### tests\conftest.py

Functions: 24

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `temp_database` | function | public | 20 | `()` | pytest.fixture |
| `db_connection` | function | public | 41 | `(temp_database)` | pytest.fixture |
| `sample_printer_data` | function | public | 50 | `()` | pytest.fixture |
| `sample_job_data` | function | public | 84 | `()` | pytest.fixture |
| `sample_file_data` | function | public | 126 | `()` | pytest.fixture |
| `populated_database` | function | public | 158 | `(db_connection, sample_printer_data, sample_job_data, sample_file_data)` | pytest.fixture |
| `mock_bambu_api` | function | public | 192 | `()` | pytest.fixture |
| `mock_prusa_api` | function | public | 234 | `()` | pytest.fixture |
| `mock_websocket` | function | public | 274 | `()` | pytest.fixture |
| `AsyncMock.__call__` | async | dunder | 285 | `(self)` | - |
| `german_business_config` | function | public | 294 | `()` | pytest.fixture |
| `sample_cost_calculations` | function | public | 311 | `()` | pytest.fixture |
| `temp_download_directory` | function | public | 330 | `()` | pytest.fixture |
| `sample_3mf_file` | function | public | 339 | `()` | pytest.fixture |
| `test_utils` | function | public | 376 | `()` | pytest.fixture |
| `TestUtils.berlin_timestamp` | method | public | 380 | `(date_str)` | staticmethod |
| `TestUtils.calculate_vat` | method | public | 393 | `(amount, rate)` | staticmethod |
| `TestUtils.format_currency` | method | public | 398 | `(amount)` | staticmethod |
| `TestUtils.generate_test_file_id` | method | public | 403 | `()` | staticmethod |
| `event_loop` | function | public | 416 | `()` | pytest.fixture(scope='session') |
| `api_client` | function | public | 428 | `()` | pytest.fixture |
| `network_error_scenarios` | function | public | 444 | `()` | pytest.fixture |
| `performance_test_data` | function | public | 461 | `()` | pytest.fixture |
| `test_config` | function | public | 476 | `()` | pytest.fixture |

### tests\fixtures\ideas_fixtures.py

Functions: 9

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `create_sample_idea` | function | public | 9 | `(title: str, status: str, priority: int, is_business: bool)` | - |
| `create_sample_trending_item` | function | public | 37 | `(platform: str)` | - |
| `IdeasTestFixtures.get_sample_ideas` | method | public | 68 | `()` | staticmethod |
| `IdeasTestFixtures.get_sample_trending_items` | method | public | 115 | `()` | staticmethod |
| `IdeasTestFixtures.get_sample_tags` | method | public | 153 | `()` | staticmethod |
| `IdeasTestFixtures.get_sample_categories` | method | public | 162 | `()` | staticmethod |
| `create_idea_with_tags` | function | public | 171 | `(title: str, tags: List[str])` | - |
| `create_business_idea` | function | public | 182 | `(title: str, customer_name: str)` | - |
| `create_external_idea` | function | public | 197 | `(title: str, platform: str, url: str)` | - |

### tests\run_essential_tests.py

Functions: 2

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `main` | function | public | 13 | `()` | - |
| `run_frontend_tests` | function | public | 131 | `()` | - |

### tests\run_milestone_1_2_tests.py

Functions: 8

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `Milestone12TestRunner.__init__` | method | dunder | 28 | `(self)` | - |
| `Milestone12TestRunner.print_header` | method | public | 47 | `(self)` | - |
| `Milestone12TestRunner.check_dependencies` | method | public | 61 | `(self)` | - |
| `Milestone12TestRunner.run_backend_tests` | method | public | 87 | `(self, verbose, coverage)` | - |
| `Milestone12TestRunner.run_frontend_tests` | method | public | 134 | `(self, verbose)` | - |
| `Milestone12TestRunner.print_summary` | method | public | 171 | `(self, backend_success, frontend_success, start_time)` | - |
| `Milestone12TestRunner.run_tests` | method | public | 200 | `(self, verbose, coverage)` | - |
| `main` | function | public | 222 | `()` | - |

### tests\test_essential_config.py

Functions: 16

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestGermanBusinessConfig.test_german_timezone_configuration` | method | public | 20 | `(self)` | - |
| `TestGermanBusinessConfig.test_currency_configuration` | method | public | 29 | `(self)` | - |
| `TestGermanBusinessConfig.test_vat_rate_configuration` | method | public | 37 | `(self)` | - |
| `TestGermanBusinessConfig.test_material_cost_calculation` | method | public | 47 | `(self)` | - |
| `TestGermanBusinessConfig.test_power_cost_calculation` | method | public | 58 | `(self)` | - |
| `TestSystemConfiguration.test_environment_variables` | method | public | 73 | `(self)` | - |
| `TestSystemConfiguration.test_database_path_configuration` | method | public | 89 | `(self)` | - |
| `TestSystemConfiguration.test_api_base_configuration` | method | public | 97 | `(self)` | - |
| `TestSystemConfiguration.test_printer_default_configuration` | method | public | 111 | `(self)` | - |
| `TestConfigService.test_config_service_initialization` | method | public | 140 | `(self)` | - |
| `TestConfigService.test_config_service_german_settings` | method | public | 145 | `(self)` | - |
| `TestBusinessLogic.test_business_hours_validation` | method | public | 156 | `(self)` | - |
| `TestBusinessLogic.test_customer_data_validation` | method | public | 171 | `(self)` | - |
| `TestBusinessLogic.test_job_classification` | method | public | 186 | `(self)` | - |
| `TestBusinessLogic.is_business_job` | method | public | 200 | `(customer_name)` | - |
| `TestBusinessLogic.test_file_naming_conventions` | method | public | 210 | `(self)` | - |

### tests\test_essential_integration.py

Functions: 20

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `async_client` | function | public | 16 | `()` | pytest.fixture |
| `TestCoreWorkflowIntegration.test_complete_printer_setup_workflow` | method | public | 24 | `(self, async_client)` | - |
| `TestCoreWorkflowIntegration.test_health_check_system_integration` | method | public | 61 | `(self, async_client)` | - |
| `TestCoreWorkflowIntegration.test_files_discovery_workflow` | method | public | 77 | `(self, async_client)` | - |
| `TestCoreWorkflowIntegration.test_jobs_monitoring_workflow` | method | public | 88 | `(self, async_client)` | - |
| `TestCoreWorkflowIntegration.test_analytics_basic_functionality` | method | public | 99 | `(self, async_client)` | - |
| `TestCoreWorkflowIntegration.test_system_configuration_workflow` | method | public | 108 | `(self, async_client)` | - |
| `TestCoreWorkflowIntegration.test_websocket_connection_basic` | async | public | 118 | `(self)` | pytest.mark.asyncio |
| `TestCoreWorkflowIntegration.test_german_business_integration` | method | public | 136 | `(self, async_client)` | - |
| `TestErrorHandlingIntegration.test_invalid_printer_data_handling` | method | public | 164 | `(self, async_client)` | - |
| `TestErrorHandlingIntegration.test_nonexistent_resource_handling` | method | public | 180 | `(self, async_client)` | - |
| `TestErrorHandlingIntegration.test_duplicate_printer_handling` | method | public | 190 | `(self, async_client)` | - |
| `TestGermanBusinessIntegration.test_timezone_integration` | method | public | 212 | `(self)` | - |
| `TestGermanBusinessIntegration.test_currency_formatting_integration` | method | public | 223 | `(self)` | - |
| `TestGermanBusinessIntegration.calculate_job_cost` | method | public | 226 | `(material_grams, cost_per_gram, vat_rate)` | - |
| `TestGermanBusinessIntegration.test_business_vs_private_classification` | method | public | 239 | `(self)` | - |
| `TestGermanBusinessIntegration.classify_customer` | method | public | 242 | `(customer_name)` | - |
| `TestGermanBusinessIntegration.test_file_naming_german_support` | method | public | 252 | `(self)` | - |
| `TestHardwareIntegration.test_bambu_lab_real_connection` | method | public | 275 | `(self)` | - |
| `TestHardwareIntegration.test_prusa_real_connection` | method | public | 279 | `(self)` | - |

### tests\test_essential_models.py

Functions: 16

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestPrinterModel.test_valid_bambu_printer_creation` | method | public | 17 | `(self)` | - |
| `TestPrinterModel.test_valid_prusa_printer_creation` | method | public | 35 | `(self)` | - |
| `TestPrinterModel.test_printer_required_fields` | method | public | 50 | `(self)` | - |
| `TestPrinterModel.test_printer_config_optional_fields` | method | public | 62 | `(self)` | - |
| `TestJobModel.test_valid_job_creation` | method | public | 74 | `(self)` | - |
| `TestJobModel.test_job_business_logic_fields` | method | public | 90 | `(self)` | - |
| `TestJobModel.test_job_create_minimal` | method | public | 107 | `(self)` | - |
| `TestJobModel.test_job_update_fields` | method | public | 117 | `(self)` | - |
| `TestFileModel.test_valid_file_creation` | method | public | 132 | `(self)` | - |
| `TestFileModel.test_file_download_status_progression` | method | public | 147 | `(self)` | - |
| `TestEnumValidation.test_printer_type_enum_values` | method | public | 175 | `(self)` | - |
| `TestEnumValidation.test_printer_status_enum_values` | method | public | 181 | `(self)` | - |
| `TestEnumValidation.test_job_status_enum_values` | method | public | 188 | `(self)` | - |
| `TestEnumValidation.test_file_download_status_enum` | method | public | 195 | `(self)` | - |
| `TestModelSerialization.test_printer_json_serialization` | method | public | 206 | `(self)` | - |
| `TestModelSerialization.test_job_json_serialization` | method | public | 221 | `(self)` | - |

### tests\test_essential_printer_api.py

Functions: 14

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestEssentialPrinterAPIEndpoints.mock_printer_id` | method | public | 25 | `(self)` | pytest.fixture |
| `TestEssentialPrinterAPIEndpoints.mock_bambu_printer` | method | public | 30 | `(self, mock_printer_id)` | pytest.fixture |
| `TestEssentialPrinterAPIEndpoints.mock_prusa_printer` | method | public | 43 | `(self, mock_printer_id)` | pytest.fixture |
| `TestEssentialPrinterAPIEndpoints.test_printer_status_endpoint_real_time` | async | public | 54 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterAPIEndpoints.test_printer_monitoring_start_stop` | async | public | 93 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterAPIEndpoints.test_drucker_dateien_file_listing` | async | public | 113 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterAPIEndpoints.test_one_click_file_download` | async | public | 167 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterAPIEndpoints.test_current_job_real_time_progress` | async | public | 197 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterAPIEndpoints.test_job_sync_history_integration` | async | public | 240 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterConnectionRecovery.test_bambu_mqtt_connection_recovery` | async | public | 304 | `(self)` | pytest.mark.asyncio |
| `TestEssentialPrinterConnectionRecovery.test_prusa_http_connection_recovery` | async | public | 336 | `(self)` | pytest.mark.asyncio |
| `TestEssentialGermanBusinessIntegration.test_german_material_cost_calculation` | method | public | 367 | `(self)` | - |
| `TestEssentialGermanBusinessIntegration.test_german_business_customer_classification` | method | public | 387 | `(self)` | - |
| `TestEssentialGermanBusinessIntegration.test_german_timezone_handling` | method | public | 405 | `(self)` | - |

### tests\test_essential_printer_drivers.py

Functions: 17

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestEssentialBambuLabDriverIntegration.mock_bambu_printer` | method | public | 26 | `(self)` | pytest.fixture |
| `TestEssentialBambuLabDriverIntegration.test_bambu_mqtt_connection_initialization` | async | public | 46 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialBambuLabDriverIntegration.test_bambu_real_time_status_via_mqtt` | async | public | 69 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialBambuLabDriverIntegration.test_bambu_file_listing_via_mqtt` | async | public | 120 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialBambuLabDriverIntegration.test_bambu_mqtt_error_recovery` | async | public | 168 | `(self, mock_bambu_printer)` | pytest.mark.asyncio |
| `TestEssentialBambuLabDriverIntegration.mock_connect_with_retry` | async | public | 173 | `()` | - |
| `TestEssentialPrusaDriverIntegration.mock_prusa_printer` | method | public | 197 | `(self)` | pytest.fixture |
| `TestEssentialPrusaDriverIntegration.test_prusa_http_api_connection` | async | public | 207 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrusaDriverIntegration.test_prusa_30_second_polling_status` | async | public | 247 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrusaDriverIntegration.mock_poll_status` | async | public | 281 | `()` | - |
| `TestEssentialPrusaDriverIntegration.test_prusa_file_download_http` | async | public | 321 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrusaDriverIntegration.test_prusa_job_history_sync` | async | public | 357 | `(self, mock_prusa_printer)` | pytest.mark.asyncio |
| `TestEssentialPrinterDriverComparison.test_unified_status_interface` | async | public | 426 | `(self)` | pytest.mark.asyncio |
| `TestEssentialPrinterDriverComparison.test_connection_recovery_consistency` | async | public | 481 | `(self)` | pytest.mark.asyncio |
| `TestEssentialPrinterDriverComparison.test_german_business_data_integration` | method | public | 505 | `(self)` | - |
| `TestEssentialPrinterDriverComparison.classify_customer_type` | method | public | 518 | `(customer_name)` | - |
| `TestEssentialPrinterDriverComparison.calculate_total_cost` | method | public | 523 | `(base_cost, vat_rate)` | - |

### tests\test_gcode_analyzer.py

Functions: 19

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestGcodeAnalyzer.test_init_enabled` | method | public | 15 | `(self)` | - |
| `TestGcodeAnalyzer.test_init_disabled` | method | public | 20 | `(self)` | - |
| `TestGcodeAnalyzer.test_find_print_start_disabled` | method | public | 25 | `(self)` | - |
| `TestGcodeAnalyzer.test_find_print_start_layer_marker` | method | public | 38 | `(self)` | - |
| `TestGcodeAnalyzer.test_find_print_start_type_marker` | method | public | 52 | `(self)` | - |
| `TestGcodeAnalyzer.test_find_print_start_extrusion_based` | method | public | 66 | `(self)` | - |
| `TestGcodeAnalyzer.test_find_print_start_no_markers` | method | public | 79 | `(self)` | - |
| `TestGcodeAnalyzer.test_is_likely_print_move_small_extrusion` | method | public | 92 | `(self)` | - |
| `TestGcodeAnalyzer.test_is_likely_print_move_edge_position` | method | public | 100 | `(self)` | - |
| `TestGcodeAnalyzer.test_is_likely_print_move_normal_print` | method | public | 112 | `(self)` | - |
| `TestGcodeAnalyzer.test_get_optimized_gcode_lines_with_optimization` | method | public | 120 | `(self)` | - |
| `TestGcodeAnalyzer.test_get_optimized_gcode_lines_disabled` | method | public | 141 | `(self)` | - |
| `TestGcodeAnalyzer.test_get_optimized_gcode_lines_no_optimization_possible` | method | public | 155 | `(self)` | - |
| `TestGcodeAnalyzer.test_analyze_gcode_file_success` | method | public | 167 | `(self)` | - |
| `TestGcodeAnalyzer.test_analyze_gcode_file_not_found` | method | public | 197 | `(self)` | - |
| `TestGcodeAnalyzer.test_analyze_gcode_file_disabled` | method | public | 209 | `(self)` | - |
| `TestGcodeAnalyzer.test_multiple_slicer_markers` | method | public | 232 | `(self)` | - |
| `TestGcodeAnalyzer.test_warmup_end_pattern_detection` | method | public | 256 | `(self)` | - |
| `TestGcodeAnalyzer.test_heating_detection` | method | public | 277 | `(self, heating_command, expected_heated)` | pytest.mark.parametrize('heating_command,expected_heated', [('M104 S200', True), ('M109 S200', True), ('M140 S60', False), ('M190 S60', False), ('G28', False)]) |

### tests\test_ideas_service.py

Functions: 29

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `mock_database` | function | public | 19 | `()` | pytest.fixture |
| `idea_service` | function | public | 40 | `(mock_database)` | pytest.fixture |
| `TestIdeaService.test_create_idea_success` | async | public | 49 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_create_idea_with_tags` | async | public | 60 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_create_idea_missing_title` | async | public | 74 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_get_idea_success` | async | public | 85 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_get_idea_not_found` | async | public | 99 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_list_ideas_with_filters` | async | public | 108 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_update_idea_success` | async | public | 131 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_update_idea_with_tags` | async | public | 142 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_delete_idea_success` | async | public | 155 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_update_idea_status` | async | public | 165 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_get_statistics` | async | public | 176 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_cache_trending_success` | async | public | 194 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_get_trending` | async | public | 205 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_save_trending_as_idea` | async | public | 216 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_search_ideas` | async | public | 227 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaService.test_cleanup_expired_trending` | async | public | 273 | `(self, idea_service, mock_database)` | pytest.mark.asyncio |
| `TestIdeaModel.test_idea_creation_from_dict` | method | public | 284 | `(self)` | - |
| `TestIdeaModel.test_idea_to_dict` | method | public | 294 | `(self)` | - |
| `TestIdeaModel.test_idea_validation_success` | method | public | 304 | `(self)` | - |
| `TestIdeaModel.test_idea_validation_missing_title` | method | public | 311 | `(self)` | - |
| `TestIdeaModel.test_idea_validation_invalid_priority` | method | public | 319 | `(self)` | - |
| `TestIdeaModel.test_idea_validation_invalid_status` | method | public | 326 | `(self)` | - |
| `TestIdeaModel.test_get_formatted_time` | method | public | 333 | `(self)` | - |
| `TestTrendingItemModel.test_trending_item_creation` | method | public | 351 | `(self)` | - |
| `TestTrendingItemModel.test_trending_item_to_dict` | method | public | 360 | `(self)` | - |
| `TestTrendingItemModel.test_is_expired_false` | method | public | 370 | `(self)` | - |
| `TestTrendingItemModel.test_is_expired_true` | method | public | 377 | `(self)` | - |

### tests\test_printer_interface_conformance.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `test_printer_interface_methods_signature` | async | public | 18 | `()` | pytest.mark.asyncio |
| `test_prusa_printer_implements_interface` | async | public | 27 | `(monkeypatch)` | pytest.mark.asyncio |
| `test_bambu_printer_implements_interface` | async | public | 36 | `(monkeypatch)` | pytest.mark.asyncio |

### tests\test_runner.py

Functions: 13

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `PrinternizerTestRunner.__init__` | method | dunder | 19 | `(self, project_root)` | - |
| `PrinternizerTestRunner.run_backend_tests` | method | public | 29 | `(self, test_type, coverage, verbose)` | - |
| `PrinternizerTestRunner.run_frontend_tests` | method | public | 80 | `(self, test_type, coverage, verbose)` | - |
| `PrinternizerTestRunner.run_performance_benchmarks` | method | public | 126 | `(self, duration, concurrent_users)` | - |
| `PrinternizerTestRunner.generate_coverage_report` | method | public | 149 | `(self)` | - |
| `PrinternizerTestRunner.generate_test_documentation` | method | public | 223 | `(self)` | - |
| `PrinternizerTestRunner.run_full_test_suite` | method | public | 237 | `(self, skip_performance, skip_frontend)` | - |
| `PrinternizerTestRunner._process_backend_results` | method | private | 301 | `(self, result, duration)` | - |
| `PrinternizerTestRunner._process_frontend_results` | method | private | 312 | `(self, result, duration)` | - |
| `PrinternizerTestRunner._process_benchmark_results` | method | private | 323 | `(self, result, duration)` | - |
| `PrinternizerTestRunner._create_test_documentation` | method | private | 344 | `(self)` | - |
| `PrinternizerTestRunner._print_final_summary` | method | private | 615 | `(self, results)` | - |
| `main` | function | public | 650 | `()` | - |

### tests\test_url_parser_service.py

Functions: 19

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `url_parser` | function | public | 11 | `()` | pytest.fixture |
| `TestUrlParserService.test_detect_platform_makerworld` | method | public | 19 | `(self, url_parser)` | - |
| `TestUrlParserService.test_detect_platform_printables` | method | public | 31 | `(self, url_parser)` | - |
| `TestUrlParserService.test_detect_platform_thingiverse` | method | public | 43 | `(self, url_parser)` | - |
| `TestUrlParserService.test_detect_platform_unknown` | method | public | 55 | `(self, url_parser)` | - |
| `TestUrlParserService.test_extract_model_id_makerworld` | method | public | 67 | `(self, url_parser)` | - |
| `TestUrlParserService.test_extract_model_id_printables` | method | public | 80 | `(self, url_parser)` | - |
| `TestUrlParserService.test_extract_model_id_thingiverse` | method | public | 93 | `(self, url_parser)` | - |
| `TestUrlParserService.test_clean_title` | method | public | 106 | `(self, url_parser)` | - |
| `TestUrlParserService.test_extract_creator_from_title` | method | public | 120 | `(self, url_parser)` | - |
| `TestUrlParserService.test_validate_url` | method | public | 133 | `(self, url_parser)` | - |
| `TestUrlParserService.test_get_supported_platforms` | method | public | 154 | `(self, url_parser)` | - |
| `TestUrlParserService.test_get_platform_info` | method | public | 163 | `(self, url_parser)` | - |
| `TestUrlParserService.test_parse_url_success` | async | public | 178 | `(self, url_parser)` | pytest.mark.asyncio |
| `TestUrlParserService.test_parse_url_http_error` | async | public | 201 | `(self, url_parser)` | pytest.mark.asyncio |
| `TestUrlParserService.test_parse_url_invalid_url` | async | public | 221 | `(self, url_parser)` | pytest.mark.asyncio |
| `TestUrlParserService.test_fetch_page_title_success` | async | public | 233 | `(self, url_parser)` | pytest.mark.asyncio |
| `TestUrlParserService.test_fetch_page_title_no_title_tag` | async | public | 250 | `(self, url_parser)` | pytest.mark.asyncio |
| `TestUrlParserService.test_close_session` | async | public | 267 | `(self, url_parser)` | pytest.mark.asyncio |

### tests\test_working_core.py

Functions: 12

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `TestCoreModels.test_printer_model_creation` | method | public | 21 | `(self)` | - |
| `TestCoreModels.test_job_model_business_logic` | method | public | 47 | `(self)` | - |
| `TestCoreModels.test_file_model_statuses` | method | public | 77 | `(self)` | - |
| `TestGermanBusinessLogic.test_vat_calculations` | method | public | 109 | `(self)` | - |
| `TestGermanBusinessLogic.test_business_classification` | method | public | 126 | `(self)` | - |
| `TestGermanBusinessLogic.classify_customer` | method | public | 130 | `(name)` | - |
| `TestGermanBusinessLogic.test_file_naming_german_support` | method | public | 143 | `(self)` | - |
| `TestConfigurationValidation.test_printer_config_updates` | method | public | 166 | `(self)` | - |
| `TestConfigurationValidation.test_job_creation_and_updates` | method | public | 179 | `(self)` | - |
| `TestEnumConsistency.test_printer_enums` | method | public | 206 | `(self)` | - |
| `TestEnumConsistency.test_job_enums` | method | public | 219 | `(self)` | - |
| `TestEnumConsistency.test_file_enums` | method | public | 227 | `(self)` | - |

### verify_phase2_integration.py

Functions: 3

| Function | Type | Access | Line | Signature | Decorators |
|----------|------|--------|------|-----------|------------|
| `check_file_exists` | function | public | 11 | `(filepath, description)` | - |
| `check_file_contains` | function | public | 21 | `(filepath, search_string, description)` | - |
| `main` | function | public | 35 | `()` | - |

## Statistics

- Public functions: 1086
- Private functions: 183
- Dunder methods: 58

- Async functions: 645
- Properties: 10
- Static methods: 8
