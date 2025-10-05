# Phase 3: Usage Analysis Report

**Generated**: Phase 3 Analysis

## Executive Summary

- **Dead Code Chains**: 0
- **Unused Functions**: 138
- **Single-Use Functions**: 226
- **Low-Use Functions** (2-3 calls): 113
- **Wrapper Functions**: 17
- **Legacy/Deprecated**: 1
- **Test-Only Functions**: 15
- **Files with Dynamic Calls**: 16
- **HTTP API Endpoints**: 0
- **WebSocket Endpoints**: 0

## 🔴 Dead Code Chains (High Priority)

Chains of unused functions that only call other unused functions.

No dead code chains detected.

## 📊 Usage Frequency Analysis

### Unused Functions

Total: 138

| Function | File | Line | Access |
|----------|------|------|--------|
| `demo_optimization` | demo_gcode_optimization.py | 74 | public |
| `FunctionAnalyzer.visit_Import` | scripts\analyze_codebase.py | 31 | public |
| `FunctionAnalyzer.visit_ImportFrom` | scripts\analyze_codebase.py | 42 | public |
| `FunctionAnalyzer.visit_ClassDef` | scripts\analyze_codebase.py | 55 | public |
| `FunctionAnalyzer.visit_AsyncFunctionDef` | scripts\analyze_codebase.py | 117 | public |
| `FunctionAnalyzer.visit_Call` | scripts\analyze_codebase.py | 121 | public |
| `setup_example_env` | scripts\bambu_credentials.py | 103 | public |
| `test_direct_ftp` | scripts\debug_bambu_ftp.py | 12 | public |
| `test_alternative_ftp` | scripts\debug_bambu_ftp_v2.py | 12 | public |
| `download_target_file` | scripts\download_target_file.py | 21 | public |
| `test_working_ftp` | scripts\working_bambu_ftp.py | 212 | public |
| `Database.list_local_files` | src\database\database.py | 763 | public |
| `Database.transaction` | src\database\database.py | 296 | public |
| `Database.create_local_file` | src\database\database.py | 753 | public |
| `Database.get_library_file_sources` | src\database\database.py | 1315 | public |
| `lifespan` | src\main.py | 88 | public |
| `_on_printer_status_update` | src\main.py | 144 | private |
| `create_application` | src\main.py | 267 | public |
| `printernizer_exception_handler` | src\main.py | 350 | public |
| `validation_exception_handler` | src\main.py | 365 | public |

### Single-Use Functions

Total: 226

Functions called exactly once - candidates for inlining.

| Function | File | Line | Type |
|----------|------|------|------|
| `create_sample_gcode` | demo_gcode_optimization.py | 18 | sync |
| `analyze_gcode_file_lines` | demo_gcode_optimization.py | 161 | sync |
| `FunctionAnalyzer.visit_FunctionDef` | scripts\analyze_codebase.py | 62 | sync |
| `find_python_files` | scripts\analyze_codebase.py | 172 | sync |
| `build_dependency_graph` | scripts\analyze_codebase.py | 186 | sync |
| `find_entry_points` | scripts\analyze_codebase.py | 203 | sync |
| `generate_function_inventory_report` | scripts\analyze_codebase.py | 247 | sync |
| `generate_dependency_report` | scripts\analyze_codebase.py | 305 | sync |
| `generate_entry_points_report` | scripts\analyze_codebase.py | 323 | sync |
| `BambuCredentials.get_printer_credentials` | scripts\bambu_credentials.py | 21 | sync |
| `BambuCredentials._validate_access_code` | scripts\bambu_credentials.py | 66 | sync |
| `BambuCredentials._is_development_environment` | scripts\bambu_credentials.py | 74 | sync |
| `BambuDownloadManager.download_from_bambulab_printers` | scripts\download_bambu_files.py | 75 | async |
| `BambuDownloadManager._process_single_printer` | scripts\download_bambu_files.py | 132 | async |
| `BambuDownloadManager._interactive_file_selection` | scripts\download_bambu_files.py | 230 | async |

### Low-Use Functions (2-3 calls)

Total: 113

| Function | File | Line | Calls |
|----------|------|------|-------|
| `analyze_file` | scripts\analyze_codebase.py | 145 | 2 |
| `ThreeMFAnalyzer.analyze_file` | src\services\threemf_analyzer.py | 22 | 2 |
| `BambuDownloadManager._print_summary` | scripts\download_bambu_files.py | 309 | 2 |
| `ErrorAnalysisAgent.analyze_root_cause` | scripts\error_analysis_agent.py | 108 | 2 |
| `ErrorAnalysisAgent.generate_report` | scripts\error_analysis_agent.py | 182 | 2 |
| `MaterialService.generate_report` | src\services\material_service.py | 402 | 2 |
| `ErrorHandler.ensure_log_directory` | src\utils\error_handling.py | 49 | 2 |
| `Database.get_file_statistics` | src\database\database.py | 790 | 2 |
| `FileService.get_file_statistics` | src\services\file_service.py | 458 | 2 |
| `FileService.process_file_thumbnails` | src\services\file_service.py | 803 | 3 |
| `ConfigService.get_watch_folder_settings` | src\services\config_service.py | 441 | 2 |
| `Database.health_check` | src\database\database.py | 282 | 2 |
| `BasePrinter.health_check` | src\printers\base.py | 253 | 2 |
| `PrinterService.health_check` | src\services\printer_service.py | 623 | 2 |
| `UrlParserService.validate_url` | src\services\url_parser_service.py | 243 | 2 |

## 🔄 Wrapper Functions

Simple functions that just delegate to other functions.

| Wrapper | Wraps | File | Line | Type |
|---------|-------|------|------|------|
| `__init__` | `__init__` | src\utils\exceptions.py | 31 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 43 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 55 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 67 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 79 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 91 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 103 | sync |
| `__init__` | `__init__` | src\utils\exceptions.py | 115 | sync |
| `mock_send` | `append` | tests\backend\test_integration.py | 274 | async |
| `mock_send` | `append` | tests\backend\test_integration.py | 305 | async |
| `mock_send` | `append` | tests\backend\test_integration.py | 336 | async |
| `mock_disconnect` | `append` | tests\backend\test_integration.py | 514 | async |
| `complex_query` | `fetchall` | tests\backend\test_performance.py | 172 | sync |
| `query_without_index` | `fetchall` | tests\backend\test_performance.py | 283 | sync |
| `serialize_response` | `dumps` | tests\backend\test_performance.py | 411 | sync |
| `__call__` | `__call__` | tests\conftest.py | 285 | async |
| `classify_customer` | `any` | tests\test_working_core.py | 130 | sync |

## ⚠️ Legacy/Deprecated Functions

Functions marked as deprecated, TODO, or legacy in docstrings.

### `PrinterService.get_printers`

**File**: src\services\printer_service.py:288

**Markers**: legacy

**Severity**: MEDIUM

**Docstring**: get list of all configured printers as dictionaries (legacy method).

## 🧪 Test-Only Functions

Functions in production code only called by tests.

| Function | File | Line | Used By |
|----------|------|------|----------|
| `BambuFTP.quit` | scripts\working_bambu_ftp.py | 182 | 4 tests |
| `BambuFTPService.get_file_info` | src\services\bambu_ftp_service.py | 389 | 1 tests |
| `TestUtils.berlin_timestamp` | tests\conftest.py | 380 | 5 tests |
| `TestUtils.calculate_vat` | tests\conftest.py | 393 | 1 tests |
| `TestUtils.format_currency` | tests\conftest.py | 398 | 1 tests |
| `JobService.get_jobs` | src\services\job_service.py | 25 | 2 tests |
| `BambuLabPrinter.get_job_info` | src\printers\bambu_lab.py | 750 | 2 tests |
| `PrinterInterface.get_job_info` | src\printers\base.py | 98 | 2 tests |
| `PrusaPrinter.get_job_info` | src\printers\prusa.py | 253 | 2 tests |
| `GcodeAnalyzer.analyze_gcode_file` | src\utils\gcode_analyzer.py | 178 | 3 tests |
| `IdeasTestFixtures.get_sample_ideas` | tests\fixtures\ideas_fixtures.py | 68 | 1 tests |
| `IdeasTestFixtures.get_sample_trending_items` | tests\fixtures\ideas_fixtures.py | 115 | 2 tests |
| `IdeaService.cache_trending` | src\services\idea_service.py | 242 | 1 tests |
| `Idea.get_formatted_time` | src\models\idea.py | 110 | 1 tests |
| `TrendingItem.is_expired` | src\models\idea.py | 175 | 2 tests |

## 🔮 Dynamic Function Calls

Files containing dynamic calls (getattr, eval, etc.) that may hide function usage.

### scripts\test_complete_bambu_ftp.py

- **getattr**: lines 202, 209, 210, 248

*May contain dynamic function calls not detected by static analysis*

### scripts\verify_bambu_download.py

- **getattr**: lines 108, 109, 124, 126, 128

*May contain dynamic function calls not detected by static analysis*

### src\api\routers\debug.py

- **getattr**: lines 27, 33, 83, 109

*May contain dynamic function calls not detected by static analysis*

### src\api\routers\health.py

- **getattr**: lines 52, 53, 54, 55, 136

*May contain dynamic function calls not detected by static analysis*

### src\api\routers\printers.py

- **getattr**: lines 114, 115, 116, 118, 119

*May contain dynamic function calls not detected by static analysis*

### src\api\routers\trending.py

- **locals()**: lines 143

*May contain dynamic function calls not detected by static analysis*

### src\printers\bambu_lab.py

- **getattr**: lines 329, 368, 369, 457, 458

*May contain dynamic function calls not detected by static analysis*

### src\services\config_service.py

- **getattr**: lines 461, 481, 510
- **setattr**: lines 513

*May contain dynamic function calls not detected by static analysis*

### src\services\library_service.py

- **getattr**: lines 38, 39, 40, 41, 42

*May contain dynamic function calls not detected by static analysis*

### src\services\material_service.py

- **setattr**: lines 198

*May contain dynamic function calls not detected by static analysis*

### src\services\printer_service.py

- **getattr**: lines 105, 107, 108, 109, 277

*May contain dynamic function calls not detected by static analysis*

### src\services\thumbnail_service.py

- **locals()**: lines 157

*May contain dynamic function calls not detected by static analysis*

### src\utils\error_handling.py

- **getattr**: lines 90

*May contain dynamic function calls not detected by static analysis*

### src\utils\logging_config.py

- **getattr**: lines 19, 40

*May contain dynamic function calls not detected by static analysis*

### tests\run_milestone_1_2_tests.py

- **__import__**: lines 75

*May contain dynamic function calls not detected by static analysis*

### tests\test_printer_interface_conformance.py

- **getattr**: lines 22, 32, 42

*May contain dynamic function calls not detected by static analysis*

## 🌐 API Endpoints Inventory

### HTTP Endpoints

Total: 0

### WebSocket Endpoints

Total: 0

## 📈 Usage Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| Unused | 138 | 23.0% |
| Single Use | 226 | 37.6% |
| Low Use | 113 | 18.8% |
| Moderate Use | 87 | 14.5% |
| High Use | 37 | 6.2% |

