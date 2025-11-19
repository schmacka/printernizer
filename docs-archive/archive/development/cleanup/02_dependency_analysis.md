# Function Dependency Analysis

## Summary

- Total functions with dependencies: 1239
- Total dependency relationships: 10376

## Dependency Graph

### demo_gcode_optimization.py:analyze_gcode_file_lines

Calls:
- `find_print_start_line` (line 163, type: attribute)
- `len` (line 166, type: direct)

### demo_gcode_optimization.py:demo_optimization

Calls:
- `print` (line 76, type: direct)
- `print` (line 77, type: direct)
- `create_sample_gcode` (line 80, type: direct)
- `split` (line 81, type: attribute)
- `strip` (line 81, type: attribute)
- `print` (line 83, type: direct)
- `len` (line 83, type: direct)
- `print` (line 84, type: direct)
- `print` (line 87, type: direct)
- `print` (line 88, type: direct)
- `GcodeAnalyzer` (line 90, type: direct)
- `analyze_gcode_file_lines` (line 93, type: attribute)
- `print` (line 95, type: direct)
- `print` (line 96, type: direct)
- `print` (line 97, type: direct)
- `print` (line 98, type: direct)
- `print` (line 99, type: direct)
- `get_optimized_gcode_lines` (line 102, type: attribute)
- `print` (line 103, type: direct)
- `len` (line 103, type: direct)
- `len` (line 103, type: direct)
- `len` (line 103, type: direct)
- `len` (line 103, type: direct)
- `print` (line 107, type: direct)
- `enumerate` (line 108, type: direct)
- `strip` (line 109, type: attribute)
- `startswith` (line 109, type: attribute)
- `print` (line 110, type: direct)
- `print` (line 112, type: direct)
- `enumerate` (line 113, type: direct)
- `strip` (line 114, type: attribute)
- `print` (line 115, type: direct)
- `print` (line 117, type: direct)
- `print` (line 120, type: direct)
- `print` (line 121, type: direct)
- `GcodeAnalyzer` (line 123, type: direct)
- `get_optimized_gcode_lines` (line 124, type: attribute)
- `print` (line 126, type: direct)
- `len` (line 126, type: direct)
- `print` (line 127, type: direct)
- `print` (line 129, type: direct)
- `print` (line 132, type: direct)
- `print` (line 133, type: direct)
- `len` (line 135, type: direct)
- `len` (line 135, type: direct)
- `len` (line 135, type: direct)
- `print` (line 136, type: direct)
- `print` (line 137, type: direct)
- `print` (line 138, type: direct)
- `print` (line 140, type: direct)
- `print` (line 143, type: direct)
- `print` (line 144, type: direct)
- `NamedTemporaryFile` (line 146, type: attribute)
- `write` (line 147, type: attribute)
- `join` (line 147, type: attribute)
- `NamedTemporaryFile` (line 150, type: attribute)
- `write` (line 151, type: attribute)
- `join` (line 151, type: attribute)
- `print` (line 154, type: direct)
- `print` (line 155, type: direct)
- `print` (line 156, type: direct)

### scripts\analyze_codebase.py:FunctionAnalyzer.visit_AsyncFunctionDef

Calls:
- `visit_FunctionDef` (line 119, type: attribute)

### scripts\analyze_codebase.py:FunctionAnalyzer.visit_Call

Calls:
- `isinstance` (line 125, type: direct)
- `append` (line 127, type: attribute)
- `isinstance` (line 133, type: direct)
- `append` (line 136, type: attribute)
- `generic_visit` (line 142, type: attribute)

### scripts\analyze_codebase.py:FunctionAnalyzer.visit_ClassDef

Calls:
- `generic_visit` (line 59, type: attribute)

### scripts\analyze_codebase.py:FunctionAnalyzer.visit_FunctionDef

Calls:
- `unparse` (line 69, type: attribute)
- `append` (line 70, type: attribute)
- `unparse` (line 73, type: attribute)
- `get_docstring` (line 76, type: attribute)
- `unparse` (line 81, type: attribute)
- `startswith` (line 84, type: attribute)
- `startswith` (line 84, type: attribute)
- `startswith` (line 85, type: attribute)
- `endswith` (line 85, type: attribute)
- `join` (line 95, type: attribute)
- `isinstance` (line 103, type: direct)
- `append` (line 109, type: attribute)
- `generic_visit` (line 114, type: attribute)

### scripts\analyze_codebase.py:FunctionAnalyzer.visit_Import

Calls:
- `append` (line 34, type: attribute)
- `generic_visit` (line 40, type: attribute)

### scripts\analyze_codebase.py:FunctionAnalyzer.visit_ImportFrom

Calls:
- `append` (line 46, type: attribute)
- `generic_visit` (line 53, type: attribute)

### scripts\analyze_codebase.py:analyze_file

Calls:
- `open` (line 148, type: direct)
- `read` (line 149, type: attribute)
- `parse` (line 151, type: attribute)
- `FunctionAnalyzer` (line 152, type: direct)
- `visit` (line 153, type: attribute)
- `str` (line 168, type: direct)

### scripts\analyze_codebase.py:build_dependency_graph

Calls:
- `defaultdict` (line 188, type: direct)
- `append` (line 194, type: attribute)
- `dict` (line 200, type: direct)

### scripts\analyze_codebase.py:find_entry_points

Calls:
- `open` (line 212, type: direct)
- `read` (line 213, type: attribute)
- `append` (line 218, type: attribute)
- `join` (line 226, type: attribute)
- `any` (line 227, type: direct)
- `append` (line 228, type: attribute)
- `join` (line 237, type: attribute)
- `str` (line 237, type: direct)
- `append` (line 238, type: attribute)

### scripts\analyze_codebase.py:find_python_files

Calls:
- `Path` (line 175, type: direct)
- `rglob` (line 177, type: attribute)
- `any` (line 179, type: direct)
- `append` (line 181, type: attribute)
- `str` (line 181, type: direct)
- `sorted` (line 183, type: direct)

### scripts\analyze_codebase.py:generate_dependency_report

Calls:
- `open` (line 307, type: direct)
- `write` (line 308, type: attribute)
- `write` (line 310, type: attribute)
- `write` (line 311, type: attribute)
- `len` (line 311, type: direct)
- `write` (line 312, type: attribute)
- `sum` (line 312, type: direct)
- `len` (line 312, type: direct)
- `values` (line 312, type: attribute)
- `write` (line 314, type: attribute)
- `sorted` (line 315, type: direct)
- `items` (line 315, type: attribute)
- `write` (line 316, type: attribute)
- `write` (line 317, type: attribute)
- `write` (line 319, type: attribute)
- `write` (line 320, type: attribute)

### scripts\analyze_codebase.py:generate_entry_points_report

Calls:
- `open` (line 325, type: direct)
- `write` (line 326, type: attribute)
- `write` (line 328, type: attribute)
- `write` (line 329, type: attribute)
- `len` (line 329, type: direct)
- `defaultdict` (line 332, type: direct)
- `append` (line 334, type: attribute)
- `sorted` (line 336, type: direct)
- `items` (line 336, type: attribute)
- `write` (line 337, type: attribute)
- `upper` (line 337, type: attribute)
- `write` (line 338, type: attribute)
- `len` (line 338, type: direct)
- `write` (line 341, type: attribute)
- `write` (line 343, type: attribute)
- `write` (line 345, type: attribute)
- `join` (line 345, type: attribute)
- `write` (line 347, type: attribute)
- `write` (line 348, type: attribute)

### scripts\analyze_codebase.py:generate_function_inventory_report

Calls:
- `open` (line 249, type: direct)
- `write` (line 250, type: attribute)
- `write` (line 251, type: attribute)
- `stat` (line 251, type: attribute)
- `Path` (line 251, type: direct)
- `sum` (line 254, type: direct)
- `len` (line 254, type: direct)
- `len` (line 255, type: direct)
- `write` (line 256, type: attribute)
- `write` (line 257, type: attribute)
- `write` (line 258, type: attribute)
- `write` (line 261, type: attribute)
- `write` (line 264, type: attribute)
- `write` (line 265, type: attribute)
- `write` (line 271, type: attribute)
- `write` (line 272, type: attribute)
- `len` (line 272, type: direct)
- `write` (line 274, type: attribute)
- `write` (line 275, type: attribute)
- `join` (line 279, type: attribute)
- `write` (line 280, type: attribute)
- `write` (line 283, type: attribute)
- `write` (line 286, type: attribute)
- `sum` (line 288, type: direct)
- `sum` (line 289, type: direct)
- `sum` (line 290, type: direct)
- `write` (line 292, type: attribute)
- `write` (line 293, type: attribute)
- `write` (line 294, type: attribute)
- `sum` (line 296, type: direct)
- `sum` (line 297, type: direct)
- `sum` (line 298, type: direct)
- `write` (line 300, type: attribute)
- `write` (line 301, type: attribute)
- `write` (line 302, type: attribute)

### scripts\analyze_codebase.py:main

Calls:
- `print` (line 353, type: direct)
- `find_python_files` (line 357, type: direct)
- `print` (line 358, type: direct)
- `len` (line 358, type: direct)
- `enumerate` (line 362, type: direct)
- `print` (line 363, type: direct)
- `len` (line 363, type: direct)
- `analyze_file` (line 364, type: direct)
- `append` (line 365, type: attribute)
- `print` (line 368, type: direct)
- `build_dependency_graph` (line 369, type: direct)
- `print` (line 372, type: direct)
- `find_entry_points` (line 373, type: direct)
- `Path` (line 376, type: direct)
- `mkdir` (line 377, type: attribute)
- `print` (line 379, type: direct)
- `open` (line 380, type: direct)
- `dump` (line 381, type: attribute)
- `print` (line 388, type: direct)
- `generate_function_inventory_report` (line 389, type: direct)
- `generate_dependency_report` (line 390, type: direct)
- `generate_entry_points_report` (line 391, type: direct)
- `print` (line 393, type: direct)
- `print` (line 394, type: direct)
- `print` (line 395, type: direct)
- `print` (line 396, type: direct)
- `print` (line 397, type: direct)
- `print` (line 398, type: direct)

### scripts\bambu_credentials.py:BambuCredentials._is_development_environment

Calls:
- `lower` (line 77, type: attribute)
- `getenv` (line 77, type: attribute)
- `lower` (line 78, type: attribute)
- `getenv` (line 78, type: attribute)
- `isatty` (line 79, type: attribute)

### scripts\bambu_credentials.py:BambuCredentials._validate_access_code

Calls:
- `isinstance` (line 69, type: direct)
- `isdigit` (line 70, type: attribute)
- `len` (line 71, type: direct)

### scripts\bambu_credentials.py:BambuCredentials.get_printer_credentials

Calls:
- `getenv` (line 35, type: attribute)
- `getenv` (line 36, type: attribute)
- `_validate_access_code` (line 39, type: attribute)
- `ValueError` (line 42, type: direct)
- `_is_development_environment` (line 50, type: attribute)
- `print` (line 51, type: direct)
- `print` (line 52, type: direct)
- `getpass` (line 54, type: attribute)
- `_validate_access_code` (line 55, type: attribute)
- `ValueError` (line 59, type: direct)
- `ValueError` (line 61, type: direct)

### scripts\bambu_credentials.py:get_bambu_credentials

Calls:
- `get_printer_credentials` (line 100, type: attribute)

### scripts\bambu_credentials.py:setup_example_env

Calls:
- `print` (line 105, type: direct)
- `print` (line 106, type: direct)
- `print` (line 107, type: direct)
- `print` (line 108, type: direct)
- `print` (line 109, type: direct)
- `print` (line 110, type: direct)
- `print` (line 111, type: direct)
- `print` (line 112, type: direct)
- `print` (line 113, type: direct)
- `print` (line 114, type: direct)
- `print` (line 115, type: direct)
- `print` (line 116, type: direct)
- `print` (line 117, type: direct)
- `print` (line 118, type: direct)
- `print` (line 119, type: direct)
- `print` (line 120, type: direct)
- `print` (line 121, type: direct)
- `print` (line 122, type: direct)
- `print` (line 123, type: direct)
- `print` (line 124, type: direct)
- `print` (line 125, type: direct)

### scripts\debug_bambu_ftp.py:test_direct_ftp

Calls:
- `print` (line 19, type: direct)
- `print` (line 20, type: direct)
- `print` (line 21, type: direct)
- `print` (line 22, type: direct)
- `print` (line 23, type: direct)
- `get_bambu_credentials` (line 26, type: direct)
- `print` (line 27, type: direct)
- `print` (line 28, type: direct)
- `len` (line 28, type: direct)
- `print` (line 30, type: direct)
- `print` (line 32, type: direct)
- `print` (line 36, type: direct)
- `socket` (line 37, type: attribute)
- `settimeout` (line 38, type: attribute)
- `connect_ex` (line 39, type: attribute)
- `close` (line 40, type: attribute)
- `print` (line 43, type: direct)
- `print` (line 45, type: direct)
- `print` (line 49, type: direct)
- `create_default_context` (line 50, type: attribute)
- `print` (line 53, type: direct)
- `print` (line 56, type: direct)
- `FTP_TLS` (line 57, type: attribute)
- `set_debuglevel` (line 58, type: attribute)
- `set_pasv` (line 59, type: attribute)
- `print` (line 60, type: direct)
- `print` (line 63, type: direct)
- `connect` (line 64, type: attribute)
- `print` (line 65, type: direct)
- `print` (line 68, type: direct)
- `login` (line 69, type: attribute)
- `print` (line 70, type: direct)
- `print` (line 73, type: direct)
- `prot_p` (line 74, type: attribute)
- `print` (line 75, type: direct)
- `print` (line 78, type: direct)
- `cwd` (line 79, type: attribute)
- `pwd` (line 80, type: attribute)
- `print` (line 81, type: direct)
- `retrlines` (line 84, type: attribute)
- `print` (line 85, type: direct)
- `len` (line 85, type: direct)
- `print` (line 87, type: direct)
- `print` (line 90, type: direct)
- `quit` (line 91, type: attribute)
- `print` (line 92, type: direct)
- `print` (line 97, type: direct)
- `print` (line 100, type: direct)
- `print` (line 103, type: direct)
- `print` (line 106, type: direct)

### scripts\debug_bambu_ftp_v2.py:test_alternative_ftp

Calls:
- `print` (line 19, type: direct)
- `print` (line 20, type: direct)
- `print` (line 21, type: direct)
- `print` (line 22, type: direct)
- `print` (line 23, type: direct)
- `get_bambu_credentials` (line 26, type: direct)
- `print` (line 27, type: direct)
- `print` (line 29, type: direct)
- `print` (line 34, type: direct)
- `create_default_context` (line 36, type: attribute)
- `FTP_TLS` (line 40, type: attribute)
- `set_pasv` (line 41, type: attribute)
- `print` (line 42, type: direct)
- `connect` (line 43, type: attribute)
- `print` (line 44, type: direct)
- `login` (line 45, type: attribute)
- `print` (line 46, type: direct)
- `prot_p` (line 47, type: attribute)
- `print` (line 48, type: direct)
- `cwd` (line 51, type: attribute)
- `retrlines` (line 53, type: attribute)
- `print` (line 54, type: direct)
- `len` (line 54, type: direct)
- `quit` (line 56, type: attribute)
- `print` (line 60, type: direct)
- `print` (line 63, type: direct)
- `create_default_context` (line 65, type: attribute)
- `FTP_TLS` (line 69, type: attribute)
- `set_pasv` (line 70, type: attribute)
- `print` (line 71, type: direct)
- `connect` (line 72, type: attribute)
- `print` (line 73, type: direct)
- `login` (line 74, type: attribute)
- `print` (line 75, type: direct)
- `prot_p` (line 76, type: attribute)
- `print` (line 77, type: direct)
- `cwd` (line 80, type: attribute)
- `retrlines` (line 82, type: attribute)
- `print` (line 83, type: direct)
- `len` (line 83, type: direct)
- `quit` (line 85, type: attribute)
- `print` (line 89, type: direct)
- `print` (line 92, type: direct)
- `socket` (line 95, type: attribute)
- `settimeout` (line 96, type: attribute)
- `print` (line 98, type: direct)
- `connect` (line 99, type: attribute)
- `print` (line 101, type: direct)
- `create_default_context` (line 102, type: attribute)
- `wrap_socket` (line 106, type: attribute)
- `print` (line 108, type: direct)
- `FTP` (line 109, type: attribute)
- `makefile` (line 111, type: attribute)
- `getresp` (line 114, type: attribute)
- `print` (line 115, type: direct)
- `print` (line 117, type: direct)
- `login` (line 118, type: attribute)
- `print` (line 119, type: direct)
- `cwd` (line 122, type: attribute)
- `retrlines` (line 124, type: attribute)
- `print` (line 125, type: direct)
- `len` (line 125, type: direct)
- `quit` (line 127, type: attribute)
- `print` (line 131, type: direct)
- `print` (line 136, type: direct)

### scripts\download_bambu_files.py:BambuDownloadManager.__init__

Calls:
- `Path` (line 61, type: direct)
- `mkdir` (line 62, type: attribute)

### scripts\download_bambu_files.py:BambuDownloadManager._generate_summary

Calls:
- `total_seconds` (line 288, type: attribute)
- `split` (line 289, type: attribute)
- `str` (line 289, type: direct)
- `str` (line 306, type: direct)
- `absolute` (line 306, type: attribute)

### scripts\download_bambu_files.py:BambuDownloadManager._interactive_file_selection

Calls:
- `print` (line 235, type: direct)
- `print` (line 236, type: direct)
- `enumerate` (line 237, type: direct)
- `print` (line 239, type: direct)
- `print` (line 241, type: direct)
- `print` (line 242, type: direct)
- `print` (line 243, type: direct)
- `print` (line 244, type: direct)
- `lower` (line 247, type: attribute)
- `strip` (line 247, type: attribute)
- `input` (line 247, type: direct)
- `split` (line 257, type: attribute)
- `int` (line 259, type: direct)
- `strip` (line 259, type: attribute)
- `len` (line 260, type: direct)
- `append` (line 261, type: attribute)
- `print` (line 263, type: direct)
- `print` (line 265, type: direct)
- `print` (line 268, type: direct)
- `len` (line 268, type: direct)
- `print` (line 272, type: direct)

### scripts\download_bambu_files.py:BambuDownloadManager._print_summary

Calls:
- `print` (line 311, type: direct)
- `print` (line 312, type: direct)
- `print` (line 313, type: direct)
- `print` (line 314, type: direct)
- `print` (line 315, type: direct)
- `print` (line 316, type: direct)
- `print` (line 317, type: direct)
- `print` (line 319, type: direct)
- `print` (line 320, type: direct)
- `print` (line 321, type: direct)
- `print` (line 322, type: direct)

### scripts\download_bambu_files.py:BambuDownloadManager._process_single_printer

Calls:
- `get` (line 136, type: attribute)
- `BambuFTPService` (line 139, type: direct)
- `test_connection` (line 142, type: attribute)
- `ConnectionError` (line 144, type: direct)
- `print` (line 146, type: direct)
- `print` (line 149, type: direct)
- `list_files` (line 150, type: attribute)
- `len` (line 155, type: direct)
- `print` (line 156, type: direct)
- `len` (line 156, type: direct)
- `len` (line 156, type: direct)
- `print` (line 171, type: direct)
- `len` (line 171, type: direct)
- `lower` (line 175, type: attribute)
- `lower` (line 175, type: attribute)
- `print` (line 176, type: direct)
- `len` (line 176, type: direct)
- `_interactive_file_selection` (line 180, type: attribute)
- `_sanitize_name` (line 191, type: attribute)
- `strftime` (line 192, type: attribute)
- `now` (line 192, type: attribute)
- `mkdir` (line 193, type: attribute)
- `print` (line 200, type: direct)
- `download_file` (line 205, type: attribute)
- `str` (line 205, type: direct)
- `exists` (line 207, type: attribute)
- `stat` (line 208, type: attribute)
- `print` (line 213, type: direct)
- `print` (line 215, type: direct)
- `print` (line 219, type: direct)
- `str` (line 226, type: direct)
- `len` (line 227, type: direct)

### scripts\download_bambu_files.py:BambuDownloadManager._sanitize_name

Calls:
- `sub` (line 279, type: attribute)
- `sub` (line 281, type: attribute)
- `strip` (line 283, type: attribute)

### scripts\download_bambu_files.py:BambuDownloadManager.download_from_bambulab_printers

Calls:
- `now` (line 90, type: attribute)
- `print` (line 92, type: direct)
- `print` (line 93, type: direct)
- `print` (line 94, type: direct)
- `absolute` (line 94, type: attribute)
- `print` (line 95, type: direct)
- `len` (line 95, type: direct)
- `print` (line 96, type: direct)
- `strftime` (line 96, type: attribute)
- `print` (line 97, type: direct)
- `enumerate` (line 101, type: direct)
- `get` (line 102, type: attribute)
- `print` (line 103, type: direct)
- `len` (line 103, type: direct)
- `print` (line 104, type: direct)
- `_process_single_printer` (line 107, type: attribute)
- `print` (line 112, type: direct)
- `str` (line 115, type: direct)
- `print` (line 121, type: direct)
- `now` (line 123, type: attribute)
- `_generate_summary` (line 127, type: attribute)
- `_print_summary` (line 128, type: attribute)

### scripts\download_bambu_files.py:main

Calls:
- `ArgumentParser` (line 327, type: attribute)
- `add_argument` (line 328, type: attribute)
- `add_argument` (line 329, type: attribute)
- `add_argument` (line 330, type: attribute)
- `add_argument` (line 331, type: attribute)
- `add_argument` (line 332, type: attribute)
- `add_argument` (line 333, type: attribute)
- `add_argument` (line 334, type: attribute)
- `add_argument` (line 335, type: attribute)
- `parse_args` (line 337, type: attribute)
- `open` (line 348, type: direct)
- `load` (line 349, type: attribute)
- `get` (line 350, type: attribute)
- `print` (line 352, type: direct)
- `getenv` (line 365, type: attribute)
- `getenv` (line 366, type: attribute)
- `print` (line 375, type: direct)
- `print` (line 376, type: direct)
- `print` (line 377, type: direct)
- `print` (line 378, type: direct)
- `print` (line 379, type: direct)
- `print` (line 383, type: direct)
- `BambuDownloadManager` (line 388, type: direct)
- `download_from_bambulab_printers` (line 399, type: attribute)
- `print` (line 407, type: direct)
- `print` (line 410, type: direct)
- `print` (line 413, type: direct)
- `print` (line 417, type: direct)
- `print` (line 420, type: direct)

### scripts\download_target_file.py:download_target_file

Calls:
- `print` (line 29, type: direct)
- `print` (line 30, type: direct)
- `print` (line 31, type: direct)
- `print` (line 32, type: direct)
- `get_bambu_credentials` (line 35, type: direct)
- `print` (line 36, type: direct)
- `print` (line 38, type: direct)
- `print` (line 43, type: direct)
- `BambuClient` (line 44, type: direct)
- `connect` (line 49, type: attribute)
- `print` (line 50, type: direct)
- `print` (line 53, type: direct)
- `list_cache_dir` (line 54, type: attribute)
- `print` (line 55, type: direct)
- `len` (line 55, type: direct)
- `isinstance` (line 62, type: direct)
- `split` (line 64, type: attribute)
- `strip` (line 64, type: attribute)
- `len` (line 65, type: direct)
- `join` (line 66, type: attribute)
- `lower` (line 71, type: attribute)
- `lower` (line 71, type: attribute)
- `print` (line 77, type: direct)
- `print` (line 78, type: direct)
- `print` (line 81, type: direct)
- `download_file` (line 83, type: attribute)
- `getvalue` (line 85, type: attribute)
- `len` (line 86, type: direct)
- `Path` (line 88, type: direct)
- `mkdir` (line 89, type: attribute)
- `open` (line 92, type: direct)
- `write` (line 93, type: attribute)
- `print` (line 95, type: direct)
- `print` (line 96, type: direct)
- `len` (line 96, type: direct)
- `print` (line 97, type: direct)
- `absolute` (line 97, type: attribute)
- `disconnect` (line 99, type: attribute)
- `print` (line 102, type: direct)
- `print` (line 104, type: direct)
- `print` (line 106, type: direct)
- `print` (line 109, type: direct)
- `print` (line 110, type: direct)
- `isinstance` (line 114, type: direct)
- `split` (line 115, type: attribute)
- `strip` (line 115, type: attribute)
- `len` (line 116, type: direct)
- `join` (line 117, type: attribute)
- `any` (line 121, type: direct)
- `lower` (line 121, type: attribute)
- `append` (line 122, type: attribute)
- `enumerate` (line 125, type: direct)
- `print` (line 126, type: direct)
- `print` (line 127, type: direct)
- `print` (line 129, type: direct)
- `print` (line 130, type: direct)
- `enumerate` (line 131, type: direct)
- `split` (line 132, type: attribute)
- `strip` (line 132, type: attribute)
- `len` (line 133, type: direct)
- `join` (line 134, type: attribute)
- `print` (line 137, type: direct)
- `disconnect` (line 139, type: attribute)
- `print` (line 143, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.__init__

Calls:
- `Path` (line 32, type: direct)
- `defaultdict` (line 35, type: direct)
- `defaultdict` (line 36, type: direct)
- `defaultdict` (line 37, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent._generate_json_report

Calls:
- `dumps` (line 293, type: attribute)
- `isoformat` (line 294, type: attribute)
- `now` (line 294, type: attribute)
- `str` (line 295, type: direct)
- `len` (line 299, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent._generate_markdown_report

Calls:
- `strftime` (line 321, type: attribute)
- `now` (line 321, type: attribute)
- `get` (line 323, type: attribute)
- `len` (line 327, type: direct)
- `title` (line 339, type: attribute)
- `replace` (line 339, type: attribute)
- `enumerate` (line 347, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent._print_console_report

Calls:
- `print` (line 205, type: direct)
- `print` (line 206, type: direct)
- `center` (line 206, type: attribute)
- `print` (line 207, type: direct)
- `print` (line 210, type: direct)
- `strftime` (line 210, type: attribute)
- `now` (line 210, type: attribute)
- `print` (line 211, type: direct)
- `print` (line 219, type: direct)
- `get` (line 219, type: attribute)
- `print` (line 223, type: direct)
- `print` (line 224, type: direct)
- `items` (line 225, type: attribute)
- `print` (line 226, type: direct)
- `print` (line 227, type: direct)
- `len` (line 227, type: direct)
- `join` (line 227, type: attribute)
- `map` (line 227, type: direct)
- `print` (line 228, type: direct)
- `print` (line 232, type: direct)
- `print` (line 233, type: direct)
- `items` (line 234, type: attribute)
- `print` (line 235, type: direct)
- `print` (line 236, type: direct)
- `len` (line 236, type: direct)
- `join` (line 236, type: attribute)
- `map` (line 236, type: direct)
- `print` (line 237, type: direct)
- `print` (line 241, type: direct)
- `print` (line 242, type: direct)
- `items` (line 243, type: attribute)
- `print` (line 244, type: direct)
- `print` (line 245, type: direct)
- `len` (line 245, type: direct)
- `join` (line 245, type: attribute)
- `map` (line 245, type: direct)
- `print` (line 246, type: direct)
- `print` (line 250, type: direct)
- `print` (line 251, type: direct)
- `print` (line 252, type: direct)
- `len` (line 252, type: direct)
- `print` (line 253, type: direct)
- `print` (line 254, type: direct)
- `print` (line 255, type: direct)
- `print` (line 258, type: direct)
- `print` (line 259, type: direct)
- `print` (line 260, type: direct)
- `len` (line 260, type: direct)
- `print` (line 261, type: direct)
- `print` (line 262, type: direct)
- `print` (line 263, type: direct)
- `print` (line 264, type: direct)
- `print` (line 265, type: direct)
- `print` (line 266, type: direct)
- `print` (line 269, type: direct)
- `print` (line 270, type: direct)
- `print` (line 273, type: direct)
- `upper` (line 273, type: attribute)
- `print` (line 274, type: direct)
- `print` (line 275, type: direct)
- `print` (line 277, type: direct)
- `print` (line 278, type: direct)
- `print` (line 279, type: direct)
- `print` (line 282, type: direct)
- `print` (line 283, type: direct)
- `enumerate` (line 284, type: direct)
- `print` (line 285, type: direct)
- `print` (line 286, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.analyze_root_cause

Calls:
- `sum` (line 110, type: direct)
- `len` (line 110, type: direct)
- `values` (line 110, type: attribute)
- `sum` (line 111, type: direct)
- `len` (line 111, type: direct)
- `values` (line 111, type: attribute)
- `sum` (line 112, type: direct)
- `len` (line 112, type: direct)
- `values` (line 112, type: attribute)
- `append` (line 125, type: attribute)
- `extend` (line 131, type: attribute)
- `append` (line 138, type: attribute)
- `append` (line 145, type: attribute)
- `items` (line 157, type: attribute)
- `append` (line 158, type: attribute)
- `len` (line 161, type: direct)
- `append` (line 164, type: attribute)
- `items` (line 167, type: attribute)
- `append` (line 168, type: attribute)
- `len` (line 171, type: direct)
- `append` (line 174, type: attribute)
- `append` (line 178, type: attribute)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.apply_fixes

Calls:
- `print` (line 355, type: direct)
- `print` (line 358, type: direct)
- `print` (line 359, type: direct)
- `enumerate` (line 361, type: direct)
- `print` (line 362, type: direct)
- `print` (line 363, type: direct)
- `print` (line 364, type: direct)
- `print` (line 367, type: direct)
- `print` (line 368, type: direct)
- `repr` (line 368, type: direct)
- `print` (line 369, type: direct)
- `print` (line 370, type: direct)
- `repr` (line 370, type: direct)
- `print` (line 373, type: direct)
- `print` (line 374, type: direct)
- `print` (line 375, type: direct)
- `print` (line 379, type: direct)
- `lower` (line 380, type: attribute)
- `strip` (line 380, type: attribute)
- `input` (line 380, type: direct)
- `print` (line 383, type: direct)
- `print` (line 387, type: direct)
- `Path` (line 392, type: direct)
- `exists` (line 393, type: attribute)
- `print` (line 394, type: direct)
- `read_text` (line 398, type: attribute)
- `replace` (line 403, type: attribute)
- `write_text` (line 404, type: attribute)
- `print` (line 405, type: direct)
- `print` (line 408, type: direct)
- `print` (line 411, type: direct)
- `print` (line 413, type: direct)
- `len` (line 413, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.generate_report

Calls:
- `analyze_root_cause` (line 184, type: attribute)
- `sum` (line 186, type: direct)
- `len` (line 186, type: direct)
- `values` (line 186, type: attribute)
- `sum` (line 187, type: direct)
- `len` (line 187, type: direct)
- `values` (line 187, type: attribute)
- `sum` (line 188, type: direct)
- `len` (line 188, type: direct)
- `values` (line 188, type: attribute)
- `len` (line 189, type: direct)
- `len` (line 190, type: direct)
- `_print_console_report` (line 193, type: attribute)
- `_generate_json_report` (line 196, type: attribute)
- `_generate_markdown_report` (line 199, type: attribute)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.load_log

Calls:
- `exists` (line 52, type: attribute)
- `FileNotFoundError` (line 53, type: direct)
- `open` (line 55, type: direct)
- `readlines` (line 56, type: attribute)
- `print` (line 58, type: direct)
- `len` (line 58, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.parse_errors

Calls:
- `enumerate` (line 65, type: direct)
- `strip` (line 69, type: attribute)
- `append` (line 71, type: attribute)
- `strip` (line 71, type: attribute)
- `strip` (line 73, type: attribute)
- `startswith` (line 73, type: attribute)
- `append` (line 74, type: attribute)
- `search` (line 79, type: attribute)
- `group` (line 81, type: attribute)
- `append` (line 82, type: attribute)
- `search` (line 85, type: attribute)
- `group` (line 87, type: attribute)
- `append` (line 88, type: attribute)
- `search` (line 91, type: attribute)
- `group` (line 93, type: attribute)
- `append` (line 94, type: attribute)
- `search` (line 97, type: attribute)
- `group` (line 99, type: attribute)
- `append` (line 100, type: attribute)
- `append` (line 104, type: attribute)
- `strip` (line 104, type: attribute)
- `print` (line 106, type: direct)

### scripts\error_analysis_agent.py:ErrorAnalysisAgent.run

Calls:
- `print` (line 426, type: direct)
- `print` (line 429, type: direct)
- `print` (line 431, type: direct)
- `load_log` (line 434, type: attribute)
- `parse_errors` (line 437, type: attribute)
- `analyze_root_cause` (line 440, type: attribute)
- `generate_report` (line 443, type: attribute)
- `apply_fixes` (line 450, type: attribute)
- `print` (line 452, type: direct)
- `print` (line 456, type: direct)

### scripts\error_analysis_agent.py:main

Calls:
- `ArgumentParser` (line 462, type: attribute)
- `add_argument` (line 473, type: attribute)
- `add_argument` (line 474, type: attribute)
- `add_argument` (line 476, type: attribute)
- `parse_args` (line 478, type: attribute)
- `ErrorAnalysisAgent` (line 481, type: direct)
- `run` (line 482, type: attribute)
- `Path` (line 486, type: direct)
- `write_text` (line 487, type: attribute)
- `print` (line 488, type: direct)

### scripts\quick_bambu_check.py:main

Calls:
- `print` (line 10, type: direct)
- `print` (line 11, type: direct)
- `print` (line 16, type: direct)
- `print` (line 17, type: direct)
- `print` (line 19, type: direct)
- `print` (line 20, type: direct)
- `Printer` (line 26, type: direct)
- `print` (line 31, type: direct)
- `print` (line 33, type: direct)
- `str` (line 33, type: direct)
- `print` (line 34, type: direct)
- `print` (line 39, type: direct)
- `print` (line 41, type: direct)
- `print` (line 42, type: direct)
- `print` (line 44, type: direct)
- `print` (line 45, type: direct)
- `print` (line 46, type: direct)
- `print` (line 47, type: direct)
- `print` (line 48, type: direct)
- `print` (line 49, type: direct)

### scripts\simple_bambu_test.py:main

Calls:
- `test_download_specific_file` (line 110, type: direct)

### scripts\simple_bambu_test.py:test_download_specific_file

Calls:
- `print` (line 25, type: direct)
- `print` (line 26, type: direct)
- `print` (line 27, type: direct)
- `print` (line 28, type: direct)
- `print` (line 29, type: direct)
- `get_bambu_credentials` (line 32, type: direct)
- `print` (line 33, type: direct)
- `print` (line 35, type: direct)
- `print` (line 40, type: direct)
- `BambuFTPService` (line 41, type: direct)
- `print` (line 44, type: direct)
- `test_connection` (line 45, type: attribute)
- `print` (line 47, type: direct)
- `print` (line 49, type: direct)
- `print` (line 52, type: direct)
- `list_files` (line 53, type: attribute)
- `print` (line 54, type: direct)
- `len` (line 54, type: direct)
- `print` (line 57, type: direct)
- `print` (line 61, type: direct)
- `enumerate` (line 62, type: direct)
- `print` (line 63, type: direct)
- `lower` (line 68, type: attribute)
- `lower` (line 68, type: attribute)
- `print` (line 73, type: direct)
- `print` (line 74, type: direct)
- `print` (line 77, type: direct)
- `print` (line 78, type: direct)
- `NamedTemporaryFile` (line 81, type: attribute)
- `print` (line 84, type: direct)
- `download_file` (line 85, type: attribute)
- `exists` (line 87, type: attribute)
- `Path` (line 87, type: direct)
- `stat` (line 88, type: attribute)
- `Path` (line 88, type: direct)
- `print` (line 89, type: direct)
- `Path` (line 92, type: direct)
- `mkdir` (line 93, type: attribute)
- `rename` (line 96, type: attribute)
- `Path` (line 96, type: direct)
- `print` (line 97, type: direct)
- `absolute` (line 97, type: attribute)
- `print` (line 101, type: direct)
- `print` (line 105, type: direct)

### scripts\test_bambu_credentials.py:get_interactive_input

Calls:
- `print` (line 203, type: direct)
- `print` (line 204, type: direct)
- `strip` (line 207, type: attribute)
- `input` (line 207, type: direct)
- `print` (line 210, type: direct)
- `strip` (line 213, type: attribute)
- `input` (line 213, type: direct)
- `print` (line 216, type: direct)
- `strip` (line 219, type: attribute)
- `input` (line 219, type: direct)
- `print` (line 222, type: direct)

### scripts\test_bambu_credentials.py:main

Calls:
- `print` (line 227, type: direct)
- `print` (line 228, type: direct)
- `print` (line 231, type: direct)
- `print` (line 232, type: direct)
- `exit` (line 233, type: attribute)
- `ArgumentParser` (line 235, type: attribute)
- `add_argument` (line 236, type: attribute)
- `add_argument` (line 237, type: attribute)
- `add_argument` (line 238, type: attribute)
- `add_argument` (line 239, type: attribute)
- `parse_args` (line 241, type: attribute)
- `print` (line 248, type: direct)
- `exit` (line 249, type: attribute)
- `get_interactive_input` (line 250, type: direct)
- `validate_credentials` (line 253, type: direct)
- `print` (line 256, type: direct)
- `print` (line 258, type: direct)
- `print` (line 261, type: direct)
- `print` (line 262, type: direct)
- `print` (line 263, type: direct)
- `print` (line 264, type: direct)
- `exit` (line 266, type: attribute)
- `print` (line 269, type: direct)
- `print` (line 270, type: direct)
- `test_bambu_connection` (line 273, type: direct)
- `print` (line 277, type: direct)
- `dumps` (line 277, type: attribute)
- `print_results` (line 279, type: direct)
- `print` (line 283, type: direct)
- `print` (line 284, type: direct)
- `print` (line 285, type: direct)
- `print` (line 286, type: direct)
- `print` (line 288, type: direct)
- `print` (line 289, type: direct)
- `print` (line 290, type: direct)
- `print` (line 291, type: direct)
- `print` (line 292, type: direct)
- `exit` (line 294, type: attribute)

### scripts\test_bambu_credentials.py:print_results

Calls:
- `print` (line 170, type: direct)
- `print` (line 171, type: direct)
- `print` (line 172, type: direct)
- `print` (line 175, type: direct)
- `print` (line 177, type: direct)
- `print` (line 179, type: direct)
- `print` (line 180, type: direct)
- `print` (line 181, type: direct)
- `print` (line 182, type: direct)
- `print` (line 185, type: direct)
- `items` (line 186, type: attribute)
- `isinstance` (line 187, type: direct)
- `print` (line 188, type: direct)
- `title` (line 188, type: attribute)
- `items` (line 189, type: attribute)
- `print` (line 190, type: direct)
- `print` (line 192, type: direct)
- `title` (line 192, type: attribute)
- `print` (line 195, type: direct)
- `print` (line 197, type: direct)
- `print` (line 199, type: direct)

### scripts\test_bambu_credentials.py:test_bambu_connection

Calls:
- `print` (line 60, type: direct)
- `print` (line 61, type: direct)
- `print` (line 62, type: direct)
- `len` (line 62, type: direct)
- `print` (line 63, type: direct)
- `print` (line 64, type: direct)
- `print` (line 77, type: direct)
- `Printer` (line 78, type: direct)
- `print` (line 85, type: direct)
- `print` (line 88, type: direct)
- `get_current_state` (line 90, type: attribute)
- `str` (line 93, type: direct)
- `print` (line 94, type: direct)
- `append` (line 96, type: attribute)
- `str` (line 96, type: direct)
- `print` (line 97, type: direct)
- `str` (line 97, type: direct)
- `get_bed_temperature` (line 101, type: attribute)
- `get_nozzle_temperature` (line 102, type: attribute)
- `float` (line 105, type: direct)
- `float` (line 106, type: direct)
- `print` (line 108, type: direct)
- `print` (line 110, type: direct)
- `str` (line 110, type: direct)
- `hasattr` (line 114, type: direct)
- `callable` (line 117, type: direct)
- `subtask_name` (line 117, type: attribute)
- `get_percentage` (line 121, type: attribute)
- `str` (line 124, type: direct)
- `print` (line 127, type: direct)
- `print` (line 129, type: direct)
- `print` (line 131, type: direct)
- `str` (line 131, type: direct)
- `print` (line 134, type: direct)
- `append` (line 139, type: attribute)
- `print` (line 140, type: direct)
- `ClientSession` (line 145, type: attribute)
- `ClientTimeout` (line 145, type: attribute)
- `get` (line 146, type: attribute)
- `print` (line 150, type: direct)
- `print` (line 153, type: direct)
- `append` (line 155, type: attribute)
- `str` (line 155, type: direct)
- `print` (line 156, type: direct)
- `str` (line 156, type: direct)
- `append` (line 163, type: attribute)
- `str` (line 163, type: direct)
- `print` (line 164, type: direct)
- `str` (line 164, type: direct)

### scripts\test_bambu_credentials.py:validate_credentials

Calls:
- `split` (line 33, type: attribute)
- `len` (line 34, type: direct)
- `append` (line 35, type: attribute)
- `int` (line 39, type: direct)
- `append` (line 41, type: attribute)
- `append` (line 44, type: attribute)
- `isdigit` (line 48, type: attribute)
- `len` (line 48, type: direct)
- `append` (line 49, type: attribute)
- `isalnum` (line 52, type: attribute)
- `len` (line 52, type: direct)
- `append` (line 53, type: attribute)
- `len` (line 55, type: direct)

### scripts\test_bambu_ftp_direct.py:create_secure_ftp_connection

Calls:
- `print` (line 50, type: direct)
- `print` (line 51, type: direct)
- `print` (line 52, type: direct)
- `len` (line 52, type: direct)
- `create_default_context` (line 55, type: attribute)
- `FTP_TLS` (line 61, type: attribute)
- `set_pasv` (line 64, type: attribute)
- `print` (line 68, type: direct)
- `connect` (line 69, type: attribute)
- `print` (line 72, type: direct)
- `login` (line 73, type: attribute)
- `prot_p` (line 76, type: attribute)
- `print` (line 78, type: direct)
- `print` (line 82, type: direct)
- `print` (line 85, type: direct)
- `print` (line 88, type: direct)
- `print` (line 89, type: direct)
- `print` (line 92, type: direct)
- `print` (line 93, type: direct)
- `print` (line 96, type: direct)

### scripts\test_bambu_ftp_direct.py:download_file

Calls:
- `print` (line 181, type: direct)
- `print` (line 182, type: direct)
- `mkdir` (line 186, type: attribute)
- `Path` (line 186, type: direct)
- `open` (line 189, type: direct)
- `print` (line 196, type: direct)
- `retrbinary` (line 197, type: attribute)
- `print` (line 198, type: direct)
- `exists` (line 201, type: attribute)
- `Path` (line 201, type: direct)
- `stat` (line 202, type: attribute)
- `Path` (line 202, type: direct)
- `print` (line 203, type: direct)
- `print` (line 206, type: direct)
- `print` (line 210, type: direct)
- `print` (line 213, type: direct)

### scripts\test_bambu_ftp_direct.py:list_directory

Calls:
- `print` (line 111, type: direct)
- `cwd` (line 115, type: attribute)
- `pwd` (line 116, type: attribute)
- `print` (line 117, type: direct)
- `retrlines` (line 124, type: attribute)
- `print` (line 126, type: direct)
- `len` (line 126, type: direct)
- `print` (line 128, type: direct)
- `split` (line 132, type: attribute)
- `len` (line 133, type: direct)
- `isdigit` (line 136, type: attribute)
- `join` (line 138, type: attribute)
- `startswith` (line 141, type: attribute)
- `isdigit` (line 144, type: attribute)
- `str` (line 144, type: direct)
- `int` (line 144, type: direct)
- `append` (line 148, type: attribute)
- `print` (line 150, type: direct)
- `len` (line 150, type: direct)
- `enumerate` (line 151, type: direct)
- `print` (line 153, type: direct)
- `str` (line 158, type: direct)
- `print` (line 159, type: direct)
- `print` (line 160, type: direct)
- `print` (line 162, type: direct)
- `print` (line 165, type: direct)

### scripts\test_bambu_ftp_direct.py:main

Calls:
- `ArgumentParser` (line 296, type: attribute)
- `add_argument` (line 297, type: attribute)
- `getenv` (line 297, type: attribute)
- `add_argument` (line 298, type: attribute)
- `getenv` (line 298, type: attribute)
- `parse_args` (line 300, type: attribute)
- `print` (line 303, type: direct)
- `print` (line 304, type: direct)
- `print` (line 305, type: direct)
- `print` (line 306, type: direct)
- `print` (line 307, type: direct)
- `print` (line 308, type: direct)
- `print` (line 309, type: direct)
- `print` (line 310, type: direct)
- `test_bambu_ftp` (line 314, type: direct)
- `print` (line 316, type: direct)
- `print` (line 317, type: direct)
- `print` (line 319, type: direct)
- `print` (line 320, type: direct)
- `print` (line 321, type: direct)
- `print` (line 323, type: direct)
- `print` (line 324, type: direct)
- `print` (line 325, type: direct)
- `print` (line 330, type: direct)
- `print` (line 333, type: direct)

### scripts\test_bambu_ftp_direct.py:progress_callback

Calls:
- `write` (line 191, type: attribute)
- `len` (line 193, type: direct)
- `print` (line 194, type: direct)

### scripts\test_bambu_ftp_direct.py:test_bambu_ftp

Calls:
- `print` (line 228, type: direct)
- `print` (line 229, type: direct)
- `print` (line 230, type: direct)
- `print` (line 231, type: direct)
- `len` (line 231, type: direct)
- `print` (line 232, type: direct)
- `strftime` (line 232, type: attribute)
- `now` (line 232, type: attribute)
- `print` (line 233, type: direct)
- `create_secure_ftp_connection` (line 238, type: direct)
- `print` (line 239, type: direct)
- `list_directory` (line 242, type: direct)
- `print` (line 243, type: direct)
- `NamedTemporaryFile` (line 252, type: attribute)
- `download_file` (line 255, type: direct)
- `print` (line 258, type: direct)
- `unlink` (line 261, type: attribute)
- `Path` (line 261, type: direct)
- `print` (line 262, type: direct)
- `print` (line 264, type: direct)
- `print` (line 266, type: direct)
- `print` (line 269, type: direct)
- `print` (line 270, type: direct)
- `print` (line 272, type: direct)
- `print` (line 273, type: direct)
- `print` (line 274, type: direct)
- `print` (line 278, type: direct)
- `quit` (line 285, type: attribute)
- `print` (line 286, type: direct)
- `close` (line 289, type: attribute)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._generate_test_summary

Calls:
- `len` (line 325, type: direct)
- `sum` (line 326, type: direct)
- `values` (line 326, type: attribute)
- `get` (line 326, type: attribute)
- `sum` (line 327, type: direct)
- `values` (line 327, type: attribute)
- `get` (line 327, type: attribute)
- `isoformat` (line 329, type: attribute)
- `now` (line 329, type: attribute)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._print_summary

Calls:
- `print` (line 335, type: direct)
- `print` (line 336, type: direct)
- `print` (line 337, type: direct)
- `print` (line 338, type: direct)
- `print` (line 339, type: direct)
- `print` (line 340, type: direct)
- `print` (line 343, type: direct)
- `print` (line 344, type: direct)
- `print` (line 345, type: direct)
- `print` (line 347, type: direct)
- `print` (line 348, type: direct)
- `print` (line 349, type: direct)
- `print` (line 351, type: direct)
- `print` (line 352, type: direct)
- `print` (line 353, type: direct)
- `print` (line 354, type: direct)
- `print` (line 355, type: direct)
- `print` (line 356, type: direct)
- `print` (line 357, type: direct)
- `print` (line 358, type: direct)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._test_error_handling

Calls:
- `print` (line 292, type: direct)
- `BambuFTPService` (line 293, type: direct)
- `test_connection` (line 294, type: attribute)
- `print` (line 297, type: direct)
- `print` (line 300, type: direct)
- `BambuFTPService` (line 301, type: direct)
- `test_connection` (line 302, type: attribute)
- `print` (line 305, type: direct)
- `print` (line 308, type: direct)
- `BambuFTPService` (line 309, type: direct)
- `list_files` (line 310, type: attribute)
- `print` (line 311, type: direct)
- `len` (line 311, type: direct)
- `str` (line 319, type: direct)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._test_file_download

Calls:
- `BambuLabPrinter` (line 227, type: direct)
- `connect` (line 235, type: attribute)
- `list_files` (line 238, type: attribute)
- `disconnect` (line 240, type: attribute)
- `getattr` (line 248, type: direct)
- `str` (line 248, type: direct)
- `print` (line 250, type: direct)
- `NamedTemporaryFile` (line 253, type: attribute)
- `download_file` (line 258, type: attribute)
- `exists` (line 260, type: attribute)
- `Path` (line 260, type: direct)
- `stat` (line 261, type: attribute)
- `Path` (line 261, type: direct)
- `print` (line 262, type: direct)
- `unlink` (line 265, type: attribute)
- `Path` (line 265, type: direct)
- `disconnect` (line 267, type: attribute)
- `print` (line 274, type: direct)
- `disconnect` (line 275, type: attribute)
- `unlink` (line 281, type: attribute)
- `Path` (line 281, type: direct)
- `str` (line 286, type: direct)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._test_file_listing

Calls:
- `BambuLabPrinter` (line 185, type: direct)
- `connect` (line 193, type: attribute)
- `list_files` (line 196, type: attribute)
- `print` (line 197, type: direct)
- `len` (line 197, type: direct)
- `getattr` (line 202, type: direct)
- `get` (line 203, type: attribute)
- `print` (line 205, type: direct)
- `dict` (line 205, type: direct)
- `enumerate` (line 208, type: direct)
- `getattr` (line 209, type: direct)
- `str` (line 209, type: direct)
- `getattr` (line 210, type: direct)
- `print` (line 211, type: direct)
- `disconnect` (line 213, type: attribute)
- `len` (line 217, type: direct)
- `str` (line 222, type: direct)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._test_ftp_service

Calls:
- `BambuFTPService` (line 105, type: direct)
- `print` (line 106, type: direct)
- `test_connection` (line 109, type: attribute)
- `print` (line 113, type: direct)
- `list_files` (line 116, type: attribute)
- `print` (line 117, type: direct)
- `len` (line 117, type: direct)
- `get_file_info` (line 122, type: attribute)
- `print` (line 124, type: direct)
- `print` (line 126, type: direct)
- `len` (line 130, type: direct)
- `str` (line 135, type: direct)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester._test_printer_class

Calls:
- `BambuLabPrinter` (line 141, type: direct)
- `print` (line 149, type: direct)
- `connect` (line 152, type: attribute)
- `print` (line 156, type: direct)
- `print` (line 160, type: direct)
- `get_status` (line 164, type: attribute)
- `print` (line 165, type: direct)
- `print` (line 167, type: direct)
- `disconnect` (line 170, type: attribute)
- `print` (line 171, type: direct)
- `str` (line 180, type: direct)

### scripts\test_complete_bambu_ftp.py:BambuFTPTester.run_all_tests

Calls:
- `print` (line 57, type: direct)
- `print` (line 58, type: direct)
- `print` (line 59, type: direct)
- `print` (line 60, type: direct)
- `len` (line 60, type: direct)
- `print` (line 61, type: direct)
- `strftime` (line 61, type: attribute)
- `now` (line 61, type: attribute)
- `print` (line 62, type: direct)
- `print` (line 75, type: direct)
- `print` (line 76, type: direct)
- `test_func` (line 79, type: direct)
- `print` (line 83, type: direct)
- `print` (line 85, type: direct)
- `get` (line 85, type: attribute)
- `print` (line 89, type: direct)
- `str` (line 90, type: direct)
- `print` (line 93, type: direct)
- `_generate_test_summary` (line 96, type: attribute)
- `_print_summary` (line 97, type: attribute)

### scripts\test_complete_bambu_ftp.py:main

Calls:
- `ArgumentParser` (line 363, type: attribute)
- `add_argument` (line 364, type: attribute)
- `getenv` (line 364, type: attribute)
- `add_argument` (line 365, type: attribute)
- `getenv` (line 365, type: attribute)
- `parse_args` (line 367, type: attribute)
- `print` (line 373, type: direct)
- `print` (line 374, type: direct)
- `print` (line 375, type: direct)
- `print` (line 376, type: direct)
- `print` (line 377, type: direct)
- `print` (line 378, type: direct)
- `print` (line 379, type: direct)
- `print` (line 380, type: direct)
- `BambuFTPTester` (line 384, type: direct)
- `run_all_tests` (line 385, type: attribute)
- `print` (line 390, type: direct)
- `print` (line 393, type: direct)

### scripts\test_existing_bambu_api.py:test_bambu_api

Calls:
- `print` (line 32, type: direct)
- `print` (line 33, type: direct)
- `print` (line 34, type: direct)
- `print` (line 35, type: direct)
- `get_bambu_credentials` (line 38, type: direct)
- `print` (line 39, type: direct)
- `len` (line 39, type: direct)
- `print` (line 41, type: direct)
- `print` (line 46, type: direct)
- `BambuClient` (line 47, type: direct)
- `print` (line 54, type: direct)
- `connect` (line 55, type: attribute)
- `print` (line 56, type: direct)
- `print` (line 59, type: direct)
- `get_current_state` (line 61, type: attribute)
- `print` (line 63, type: direct)
- `print` (line 65, type: direct)
- `print` (line 67, type: direct)
- `hasattr` (line 70, type: direct)
- `print` (line 71, type: direct)
- `print` (line 75, type: direct)
- `list_cache_dir` (line 76, type: attribute)
- `print` (line 77, type: direct)
- `print` (line 78, type: direct)
- `len` (line 78, type: direct)
- `enumerate` (line 81, type: direct)
- `print` (line 82, type: direct)
- `print` (line 87, type: direct)
- `isinstance` (line 90, type: direct)
- `split` (line 92, type: attribute)
- `strip` (line 92, type: attribute)
- `len` (line 93, type: direct)
- `join` (line 94, type: attribute)
- `str` (line 98, type: direct)
- `print` (line 100, type: direct)
- `download_file` (line 104, type: attribute)
- `getvalue` (line 106, type: attribute)
- `len` (line 107, type: direct)
- `Path` (line 109, type: direct)
- `mkdir` (line 110, type: attribute)
- `open` (line 113, type: direct)
- `write` (line 114, type: attribute)
- `print` (line 116, type: direct)
- `len` (line 116, type: direct)
- `print` (line 119, type: direct)
- `print` (line 121, type: direct)
- `print` (line 123, type: direct)
- `print` (line 126, type: direct)
- `print` (line 129, type: direct)
- `disconnect` (line 132, type: attribute)
- `print` (line 135, type: direct)

### scripts\test_ssl_connection.py:test_ssl_connection

Calls:
- `print` (line 15, type: direct)
- `print` (line 16, type: direct)
- `print` (line 17, type: direct)
- `print` (line 18, type: direct)
- `print` (line 19, type: direct)
- `print` (line 23, type: direct)
- `socket` (line 24, type: attribute)
- `settimeout` (line 25, type: attribute)
- `connect` (line 26, type: attribute)
- `print` (line 27, type: direct)
- `close` (line 28, type: attribute)
- `print` (line 31, type: direct)
- `socket` (line 32, type: attribute)
- `settimeout` (line 33, type: attribute)
- `connect` (line 34, type: attribute)
- `create_default_context` (line 37, type: attribute)
- `wrap_socket` (line 42, type: attribute)
- `print` (line 43, type: direct)
- `getpeercert` (line 46, type: attribute)
- `cipher` (line 47, type: attribute)
- `print` (line 48, type: direct)
- `print` (line 49, type: direct)
- `version` (line 49, type: attribute)
- `print` (line 52, type: direct)
- `settimeout` (line 53, type: attribute)
- `decode` (line 55, type: attribute)
- `recv` (line 55, type: attribute)
- `print` (line 56, type: direct)
- `strip` (line 56, type: attribute)
- `print` (line 58, type: direct)
- `close` (line 60, type: attribute)
- `print` (line 64, type: direct)

### scripts\verify_bambu_download.py:main

Calls:
- `ArgumentParser` (line 187, type: attribute)
- `add_argument` (line 188, type: attribute)
- `getenv` (line 188, type: attribute)
- `add_argument` (line 189, type: attribute)
- `getenv` (line 189, type: attribute)
- `add_argument` (line 190, type: attribute)
- `getenv` (line 190, type: attribute)
- `add_argument` (line 191, type: attribute)
- `parse_args` (line 193, type: attribute)
- `all` (line 195, type: direct)
- `print` (line 196, type: direct)
- `print` (line 197, type: direct)
- `print` (line 198, type: direct)
- `print` (line 199, type: direct)
- `print` (line 200, type: direct)
- `print` (line 201, type: direct)
- `print` (line 202, type: direct)
- `print` (line 203, type: direct)
- `print` (line 204, type: direct)
- `print` (line 205, type: direct)
- `run` (line 209, type: attribute)
- `verify_download` (line 209, type: direct)
- `print` (line 211, type: direct)
- `print` (line 213, type: direct)
- `print` (line 214, type: direct)
- `print` (line 216, type: direct)
- `print` (line 217, type: direct)
- `print` (line 218, type: direct)
- `print` (line 223, type: direct)
- `print` (line 226, type: direct)

### scripts\verify_bambu_download.py:verify_download

Calls:
- `print` (line 41, type: direct)
- `print` (line 42, type: direct)
- `print` (line 43, type: direct)
- `print` (line 44, type: direct)
- `print` (line 45, type: direct)
- `len` (line 45, type: direct)
- `print` (line 46, type: direct)
- `BambuLabPrinter` (line 52, type: direct)
- `print` (line 62, type: direct)
- `connect` (line 63, type: attribute)
- `print` (line 66, type: direct)
- `print` (line 67, type: direct)
- `print` (line 70, type: direct)
- `print` (line 73, type: direct)
- `BambuFTPService` (line 75, type: direct)
- `test_connection` (line 76, type: attribute)
- `print` (line 78, type: direct)
- `list_files` (line 81, type: attribute)
- `print` (line 82, type: direct)
- `len` (line 82, type: direct)
- `print` (line 84, type: direct)
- `print` (line 86, type: direct)
- `print` (line 89, type: direct)
- `get_status` (line 91, type: attribute)
- `print` (line 92, type: direct)
- `hasattr` (line 92, type: direct)
- `print` (line 94, type: direct)
- `print` (line 97, type: direct)
- `list_files` (line 99, type: attribute)
- `print` (line 102, type: direct)
- `print` (line 103, type: direct)
- `print` (line 106, type: direct)
- `len` (line 106, type: direct)
- `enumerate` (line 107, type: direct)
- `getattr` (line 108, type: direct)
- `str` (line 108, type: direct)
- `getattr` (line 109, type: direct)
- `print` (line 110, type: direct)
- `len` (line 112, type: direct)
- `print` (line 113, type: direct)
- `len` (line 113, type: direct)
- `print` (line 116, type: direct)
- `lower` (line 123, type: attribute)
- `next` (line 124, type: direct)
- `lower` (line 124, type: attribute)
- `getattr` (line 124, type: direct)
- `str` (line 124, type: direct)
- `getattr` (line 126, type: direct)
- `str` (line 126, type: direct)
- `split` (line 128, type: attribute)
- `lower` (line 128, type: attribute)
- `getattr` (line 128, type: direct)
- `str` (line 128, type: direct)
- `getattr` (line 130, type: direct)
- `str` (line 130, type: direct)
- `print` (line 131, type: direct)
- `print` (line 133, type: direct)
- `getattr` (line 136, type: direct)
- `str` (line 136, type: direct)
- `print` (line 140, type: direct)
- `NamedTemporaryFile` (line 142, type: attribute)
- `download_file` (line 146, type: attribute)
- `exists` (line 148, type: attribute)
- `Path` (line 148, type: direct)
- `stat` (line 149, type: attribute)
- `Path` (line 149, type: direct)
- `print` (line 150, type: direct)
- `print` (line 151, type: direct)
- `print` (line 152, type: direct)
- `unlink` (line 155, type: attribute)
- `Path` (line 155, type: direct)
- `print` (line 158, type: direct)
- `print` (line 162, type: direct)
- `unlink` (line 167, type: attribute)
- `Path` (line 167, type: direct)
- `print` (line 174, type: direct)
- `disconnect` (line 180, type: attribute)

### scripts\working_bambu_ftp.py:BambuFTP._read_response

Calls:
- `recv` (line 203, type: attribute)
- `strip` (line 210, type: attribute)
- `decode` (line 210, type: attribute)

### scripts\working_bambu_ftp.py:BambuFTP._send_command

Calls:
- `encode` (line 195, type: attribute)
- `send` (line 196, type: attribute)
- `print` (line 197, type: direct)

### scripts\working_bambu_ftp.py:BambuFTP.connect

Calls:
- `socket` (line 24, type: attribute)
- `settimeout` (line 25, type: attribute)
- `connect` (line 26, type: attribute)
- `create_default_context` (line 29, type: attribute)
- `wrap_socket` (line 33, type: attribute)
- `_read_response` (line 36, type: attribute)
- `print` (line 37, type: direct)
- `startswith` (line 39, type: attribute)
- `Exception` (line 40, type: direct)

### scripts\working_bambu_ftp.py:BambuFTP.cwd

Calls:
- `_send_command` (line 62, type: attribute)
- `_read_response` (line 63, type: attribute)
- `print` (line 64, type: direct)
- `startswith` (line 66, type: attribute)
- `Exception` (line 67, type: direct)

### scripts\working_bambu_ftp.py:BambuFTP.download_file

Calls:
- `_send_command` (line 130, type: attribute)
- `_read_response` (line 131, type: attribute)
- `startswith` (line 133, type: attribute)
- `Exception` (line 134, type: direct)
- `search` (line 138, type: attribute)
- `Exception` (line 140, type: direct)
- `split` (line 142, type: attribute)
- `group` (line 142, type: attribute)
- `join` (line 143, type: attribute)
- `int` (line 144, type: direct)
- `int` (line 144, type: direct)
- `socket` (line 147, type: attribute)
- `settimeout` (line 148, type: attribute)
- `connect` (line 149, type: attribute)
- `create_default_context` (line 152, type: attribute)
- `wrap_socket` (line 155, type: attribute)
- `_send_command` (line 158, type: attribute)
- `_read_response` (line 159, type: attribute)
- `print` (line 160, type: direct)
- `startswith` (line 162, type: attribute)
- `close` (line 163, type: attribute)
- `Exception` (line 164, type: direct)
- `open` (line 167, type: direct)
- `recv` (line 169, type: attribute)
- `write` (line 172, type: attribute)
- `close` (line 174, type: attribute)
- `_read_response` (line 177, type: attribute)
- `print` (line 178, type: direct)

### scripts\working_bambu_ftp.py:BambuFTP.list_files

Calls:
- `_send_command` (line 72, type: attribute)
- `_read_response` (line 73, type: attribute)
- `print` (line 74, type: direct)
- `startswith` (line 76, type: attribute)
- `Exception` (line 77, type: direct)
- `search` (line 82, type: attribute)
- `Exception` (line 84, type: direct)
- `split` (line 86, type: attribute)
- `group` (line 86, type: attribute)
- `join` (line 87, type: attribute)
- `int` (line 88, type: direct)
- `int` (line 88, type: direct)
- `print` (line 90, type: direct)
- `socket` (line 93, type: attribute)
- `settimeout` (line 94, type: attribute)
- `connect` (line 95, type: attribute)
- `create_default_context` (line 98, type: attribute)
- `wrap_socket` (line 101, type: attribute)
- `_send_command` (line 104, type: attribute)
- `_read_response` (line 105, type: attribute)
- `print` (line 106, type: direct)
- `recv` (line 112, type: attribute)
- `append` (line 115, type: attribute)
- `decode` (line 115, type: attribute)
- `close` (line 119, type: attribute)
- `_read_response` (line 122, type: attribute)
- `print` (line 123, type: direct)
- `split` (line 125, type: attribute)
- `join` (line 125, type: attribute)

### scripts\working_bambu_ftp.py:BambuFTP.login

Calls:
- `_send_command` (line 45, type: attribute)
- `_read_response` (line 46, type: attribute)
- `print` (line 47, type: direct)
- `startswith` (line 49, type: attribute)
- `_send_command` (line 51, type: attribute)
- `_read_response` (line 52, type: attribute)
- `print` (line 53, type: direct)
- `startswith` (line 55, type: attribute)
- `Exception` (line 56, type: direct)
- `startswith` (line 57, type: attribute)
- `Exception` (line 58, type: direct)

### scripts\working_bambu_ftp.py:BambuFTP.quit

Calls:
- `_send_command` (line 184, type: attribute)
- `_read_response` (line 185, type: attribute)
- `print` (line 186, type: direct)
- `close` (line 189, type: attribute)
- `close` (line 191, type: attribute)

### scripts\working_bambu_ftp.py:test_working_ftp

Calls:
- `print` (line 219, type: direct)
- `print` (line 220, type: direct)
- `print` (line 221, type: direct)
- `print` (line 222, type: direct)
- `print` (line 223, type: direct)
- `get_bambu_credentials` (line 226, type: direct)
- `print` (line 227, type: direct)
- `print` (line 229, type: direct)
- `BambuFTP` (line 234, type: direct)
- `print` (line 235, type: direct)
- `connect` (line 236, type: attribute)
- `print` (line 239, type: direct)
- `login` (line 240, type: attribute)
- `print` (line 243, type: direct)
- `cwd` (line 244, type: attribute)
- `print` (line 247, type: direct)
- `list_files` (line 248, type: attribute)
- `print` (line 250, type: direct)
- `len` (line 250, type: direct)
- `strip` (line 250, type: attribute)
- `strip` (line 251, type: attribute)
- `startswith` (line 251, type: attribute)
- `enumerate` (line 252, type: direct)
- `print` (line 253, type: direct)
- `strip` (line 253, type: attribute)
- `lower` (line 258, type: attribute)
- `lower` (line 258, type: attribute)
- `strip` (line 259, type: attribute)
- `print` (line 263, type: direct)
- `split` (line 266, type: attribute)
- `Path` (line 269, type: direct)
- `mkdir` (line 270, type: attribute)
- `print` (line 273, type: direct)
- `download_file` (line 274, type: attribute)
- `str` (line 274, type: direct)
- `exists` (line 276, type: attribute)
- `stat` (line 277, type: attribute)
- `print` (line 278, type: direct)
- `print` (line 281, type: direct)
- `print` (line 284, type: direct)
- `quit` (line 288, type: attribute)
- `print` (line 291, type: direct)

### src\api\routers\analytics.py:get_analytics_overview

Calls:
- `Query` (line 85, type: direct)
- `Depends` (line 86, type: direct)
- `get_dashboard_overview` (line 90, type: attribute)
- `error` (line 93, type: attribute)
- `str` (line 93, type: direct)
- `HTTPException` (line 94, type: direct)
- `get` (line 83, type: attribute)

### src\api\routers\analytics.py:get_analytics_summary

Calls:
- `Query` (line 49, type: direct)
- `Query` (line 50, type: direct)
- `Depends` (line 51, type: direct)
- `get_summary` (line 55, type: attribute)
- `error` (line 58, type: attribute)
- `str` (line 58, type: direct)
- `HTTPException` (line 59, type: direct)
- `get` (line 47, type: attribute)

### src\api\routers\analytics.py:get_business_analytics

Calls:
- `Query` (line 67, type: direct)
- `Query` (line 68, type: direct)
- `Depends` (line 69, type: direct)
- `get_business_analytics` (line 73, type: attribute)
- `error` (line 76, type: attribute)
- `str` (line 76, type: direct)
- `HTTPException` (line 77, type: direct)
- `get` (line 65, type: attribute)

### src\api\routers\camera.py:download_snapshot

Calls:
- `Depends` (line 222, type: direct)
- `HTTPException` (line 227, type: direct)
- `error` (line 235, type: attribute)
- `str` (line 236, type: direct)
- `HTTPException` (line 237, type: direct)
- `get` (line 219, type: attribute)

### src\api\routers\camera.py:get_camera_status

Calls:
- `Depends` (line 26, type: direct)
- `str` (line 30, type: direct)
- `get_printer_driver` (line 31, type: attribute)
- `HTTPException` (line 34, type: direct)
- `has_camera` (line 39, type: attribute)
- `get_camera_stream_url` (line 45, type: attribute)
- `str` (line 49, type: direct)
- `CameraStatus` (line 53, type: direct)
- `error` (line 63, type: attribute)
- `str` (line 64, type: direct)
- `str` (line 64, type: direct)
- `HTTPException` (line 65, type: direct)
- `get` (line 23, type: attribute)

### src\api\routers\camera.py:get_camera_stream

Calls:
- `Depends` (line 74, type: direct)
- `str` (line 78, type: direct)
- `get_printer_driver` (line 79, type: attribute)
- `HTTPException` (line 82, type: direct)
- `has_camera` (line 87, type: attribute)
- `HTTPException` (line 88, type: direct)
- `get_camera_stream_url` (line 93, type: attribute)
- `HTTPException` (line 95, type: direct)
- `Response` (line 102, type: direct)
- `error` (line 110, type: attribute)
- `str` (line 111, type: direct)
- `str` (line 111, type: direct)
- `HTTPException` (line 112, type: direct)
- `get` (line 71, type: attribute)

### src\api\routers\camera.py:list_snapshots

Calls:
- `Depends` (line 201, type: direct)
- `str` (line 205, type: direct)
- `error` (line 211, type: attribute)
- `str` (line 212, type: direct)
- `str` (line 212, type: direct)
- `HTTPException` (line 213, type: direct)
- `get` (line 197, type: attribute)

### src\api\routers\camera.py:take_snapshot

Calls:
- `Depends` (line 122, type: direct)
- `str` (line 126, type: direct)
- `get_printer_driver` (line 127, type: attribute)
- `HTTPException` (line 130, type: direct)
- `has_camera` (line 135, type: attribute)
- `HTTPException` (line 136, type: direct)
- `take_snapshot` (line 142, type: attribute)
- `HTTPException` (line 144, type: direct)
- `strftime` (line 150, type: attribute)
- `now` (line 150, type: attribute)
- `makedirs` (line 155, type: attribute)
- `join` (line 157, type: attribute)
- `open` (line 160, type: attribute)
- `write` (line 161, type: attribute)
- `SnapshotResponse` (line 164, type: direct)
- `len` (line 169, type: direct)
- `isoformat` (line 171, type: attribute)
- `now` (line 171, type: attribute)
- `info` (line 179, type: attribute)
- `len` (line 182, type: direct)
- `error` (line 189, type: attribute)
- `str` (line 190, type: direct)
- `str` (line 190, type: direct)
- `HTTPException` (line 191, type: direct)
- `post` (line 118, type: attribute)

### src\api\routers\debug.py:debug_file

Calls:
- `Query` (line 81, type: direct)
- `getattr` (line 83, type: direct)
- `HTTPException` (line 85, type: direct)
- `get_file_by_id` (line 87, type: attribute)
- `HTTPException` (line 89, type: direct)
- `items` (line 91, type: attribute)
- `get` (line 92, type: attribute)
- `len` (line 93, type: direct)
- `get` (line 77, type: attribute)

### src\api\routers\debug.py:debug_printer_thumbnail

Calls:
- `Query` (line 19, type: direct)
- `Query` (line 20, type: direct)
- `getattr` (line 27, type: direct)
- `get` (line 29, type: attribute)
- `HTTPException` (line 31, type: direct)
- `getattr` (line 33, type: direct)
- `bool` (line 37, type: direct)
- `hasattr` (line 43, type: direct)
- `model_dump` (line 43, type: attribute)
- `get` (line 45, type: attribute)
- `get` (line 47, type: attribute)
- `get` (line 48, type: attribute)
- `get_file_by_id` (line 51, type: attribute)
- `append` (line 53, type: attribute)
- `get` (line 55, type: attribute)
- `get` (line 56, type: attribute)
- `append` (line 57, type: attribute)
- `get` (line 58, type: attribute)
- `len` (line 60, type: direct)
- `append` (line 63, type: attribute)
- `get` (line 64, type: attribute)
- `append` (line 65, type: attribute)
- `append` (line 67, type: attribute)
- `items` (line 71, type: attribute)
- `get` (line 15, type: attribute)

### src\api\routers\debug.py:get_thumbnail_processing_log

Calls:
- `Query` (line 100, type: direct)
- `getattr` (line 109, type: direct)
- `HTTPException` (line 111, type: direct)
- `get_thumbnail_processing_log` (line 113, type: attribute)
- `get` (line 118, type: attribute)
- `get` (line 120, type: attribute)
- `Path` (line 122, type: direct)
- `get` (line 122, type: attribute)
- `get` (line 123, type: attribute)
- `get` (line 124, type: attribute)
- `get` (line 128, type: attribute)
- `get` (line 129, type: attribute)
- `append` (line 131, type: attribute)
- `len` (line 134, type: direct)
- `sum` (line 135, type: direct)
- `get` (line 135, type: attribute)
- `sum` (line 136, type: direct)
- `get` (line 136, type: attribute)
- `round` (line 137, type: direct)
- `get` (line 142, type: attribute)
- `get` (line 143, type: attribute)
- `get` (line 97, type: attribute)

### src\api\routers\errors.py:ErrorStoreService.__init__

Calls:
- `Path` (line 49, type: direct)
- `ensure_log_directory` (line 51, type: attribute)

### src\api\routers\errors.py:ErrorStoreService.ensure_log_directory

Calls:
- `mkdir` (line 55, type: attribute)

### src\api\routers\errors.py:ErrorStoreService.get_error_statistics

Calls:
- `timestamp` (line 114, type: attribute)
- `now` (line 114, type: attribute)
- `get_recent_errors` (line 115, type: attribute)
- `timestamp` (line 120, type: attribute)
- `fromisoformat` (line 120, type: attribute)
- `extend` (line 122, type: attribute)
- `len` (line 125, type: direct)
- `set` (line 128, type: direct)
- `get` (line 132, type: attribute)
- `get` (line 133, type: attribute)
- `get` (line 136, type: attribute)
- `get` (line 137, type: attribute)
- `timestamp` (line 141, type: attribute)
- `fromisoformat` (line 141, type: attribute)
- `add` (line 142, type: attribute)
- `len` (line 147, type: direct)
- `max` (line 150, type: direct)
- `len` (line 150, type: direct)
- `error` (line 154, type: attribute)
- `str` (line 154, type: direct)

### src\api\routers\errors.py:ErrorStoreService.get_recent_errors

Calls:
- `exists` (line 90, type: attribute)
- `open` (line 94, type: direct)
- `readlines` (line 95, type: attribute)
- `loads` (line 100, type: attribute)
- `strip` (line 100, type: attribute)
- `append` (line 101, type: attribute)
- `list` (line 105, type: direct)
- `reversed` (line 105, type: direct)
- `error` (line 108, type: attribute)
- `str` (line 108, type: direct)

### src\api\routers\errors.py:ErrorStoreService.store_errors

Calls:
- `isoformat` (line 62, type: attribute)
- `now` (line 62, type: attribute)
- `dict` (line 63, type: attribute)
- `dict` (line 64, type: attribute)
- `len` (line 65, type: direct)
- `open` (line 69, type: direct)
- `write` (line 70, type: attribute)
- `dumps` (line 70, type: attribute)
- `info` (line 73, type: attribute)
- `len` (line 76, type: direct)
- `error` (line 84, type: attribute)
- `str` (line 84, type: direct)

### src\api\routers\errors.py:error_system_health

Calls:
- `write_text` (line 260, type: attribute)
- `unlink` (line 261, type: attribute)
- `get_error_statistics` (line 264, type: attribute)
- `str` (line 268, type: direct)
- `isoformat` (line 270, type: attribute)
- `now` (line 270, type: attribute)
- `error` (line 274, type: attribute)
- `str` (line 274, type: direct)
- `str` (line 277, type: direct)
- `isoformat` (line 278, type: attribute)
- `now` (line 278, type: attribute)
- `get` (line 254, type: attribute)

### src\api\routers\errors.py:get_error_statistics

Calls:
- `get_error_statistics` (line 241, type: attribute)
- `isoformat` (line 244, type: attribute)
- `now` (line 244, type: attribute)
- `error` (line 247, type: attribute)
- `str` (line 247, type: direct)
- `HTTPException` (line 248, type: direct)
- `get` (line 237, type: attribute)

### src\api\routers\errors.py:get_recent_errors

Calls:
- `get_recent_errors` (line 223, type: attribute)
- `len` (line 226, type: direct)
- `isoformat` (line 227, type: attribute)
- `now` (line 227, type: attribute)
- `error` (line 230, type: attribute)
- `str` (line 230, type: direct)
- `HTTPException` (line 231, type: direct)
- `get` (line 219, type: attribute)

### src\api\routers\errors.py:report_errors

Calls:
- `store_errors` (line 180, type: attribute)
- `HTTPException` (line 183, type: direct)
- `warning` (line 191, type: attribute)
- `len` (line 195, type: direct)
- `len` (line 205, type: direct)
- `isoformat` (line 206, type: attribute)
- `now` (line 206, type: attribute)
- `error` (line 212, type: attribute)
- `str` (line 212, type: direct)
- `HTTPException` (line 213, type: direct)
- `post` (line 169, type: attribute)

### src\api\routers\files.py:add_watch_folder

Calls:
- `Query` (line 455, type: direct)
- `Depends` (line 456, type: direct)
- `Depends` (line 457, type: direct)
- `validate_watch_folder` (line 462, type: attribute)
- `HTTPException` (line 464, type: direct)
- `add_watch_folder` (line 470, type: attribute)
- `HTTPException` (line 472, type: direct)
- `reload_watch_folders` (line 478, type: attribute)
- `error` (line 484, type: attribute)
- `str` (line 484, type: direct)
- `HTTPException` (line 485, type: direct)
- `post` (line 453, type: attribute)

### src\api\routers\files.py:analyze_file

Calls:
- `Query` (line 663, type: direct)
- `Depends` (line 664, type: direct)
- `info` (line 676, type: attribute)
- `get_enhanced_metadata` (line 679, type: direct)
- `append` (line 703, type: attribute)
- `append` (line 710, type: attribute)
- `append` (line 719, type: attribute)
- `append` (line 727, type: attribute)
- `append` (line 735, type: attribute)
- `append` (line 742, type: attribute)
- `error` (line 756, type: attribute)
- `str` (line 756, type: direct)
- `HTTPException` (line 757, type: direct)
- `str` (line 759, type: direct)
- `get` (line 660, type: attribute)

### src\api\routers\files.py:check_printer_compatibility

Calls:
- `Depends` (line 767, type: direct)
- `info` (line 779, type: attribute)
- `get_enhanced_metadata` (line 782, type: direct)
- `append` (line 804, type: attribute)
- `append` (line 811, type: attribute)
- `lower` (line 818, type: attribute)
- `any` (line 820, type: direct)
- `lower` (line 820, type: attribute)
- `append` (line 821, type: attribute)
- `error` (line 831, type: attribute)
- `str` (line 831, type: direct)
- `HTTPException` (line 832, type: direct)
- `str` (line 834, type: direct)
- `get` (line 763, type: attribute)

### src\api\routers\files.py:delete_file

Calls:
- `Depends` (line 576, type: direct)
- `delete_file` (line 580, type: attribute)
- `HTTPException` (line 583, type: direct)
- `error` (line 593, type: attribute)
- `str` (line 593, type: direct)
- `HTTPException` (line 594, type: direct)
- `str` (line 596, type: direct)
- `delete` (line 573, type: attribute)

### src\api\routers\files.py:download_file

Calls:
- `Depends` (line 169, type: direct)
- `HTTPException` (line 176, type: direct)
- `split` (line 182, type: attribute)
- `info` (line 186, type: attribute)
- `download_file` (line 189, type: attribute)
- `get` (line 191, type: attribute)
- `HTTPException` (line 192, type: direct)
- `error` (line 200, type: attribute)
- `str` (line 200, type: direct)
- `str` (line 200, type: direct)
- `HTTPException` (line 201, type: direct)
- `post` (line 166, type: attribute)

### src\api\routers\files.py:get_enhanced_metadata

Calls:
- `Query` (line 605, type: direct)
- `Depends` (line 606, type: direct)
- `info` (line 622, type: attribute)
- `get_file` (line 625, type: attribute)
- `HTTPException` (line 627, type: direct)
- `extract_enhanced_metadata` (line 637, type: attribute)
- `warning` (line 639, type: attribute)
- `EnhancedFileMetadata` (line 641, type: direct)
- `EnhancedFileMetadata` (line 648, type: direct)
- `error` (line 653, type: attribute)
- `str` (line 653, type: direct)
- `HTTPException` (line 654, type: direct)
- `str` (line 656, type: direct)
- `get` (line 602, type: attribute)

### src\api\routers\files.py:get_file_by_id

Calls:
- `Depends` (line 145, type: direct)
- `get_file_by_id` (line 149, type: attribute)
- `HTTPException` (line 151, type: direct)
- `model_validate` (line 155, type: attribute)
- `error` (line 159, type: attribute)
- `str` (line 159, type: direct)
- `HTTPException` (line 160, type: direct)
- `get` (line 142, type: attribute)

### src\api\routers\files.py:get_file_metadata

Calls:
- `Depends` (line 282, type: direct)
- `get_file_by_id` (line 286, type: attribute)
- `HTTPException` (line 289, type: direct)
- `get` (line 295, type: attribute)
- `get` (line 300, type: attribute)
- `get` (line 301, type: attribute)
- `get` (line 302, type: attribute)
- `get` (line 303, type: attribute)
- `get` (line 304, type: attribute)
- `error` (line 313, type: attribute)
- `str` (line 313, type: direct)
- `HTTPException` (line 314, type: direct)
- `get` (line 279, type: attribute)

### src\api\routers\files.py:get_file_statistics

Calls:
- `Depends` (line 125, type: direct)
- `get_file_statistics` (line 129, type: attribute)
- `error` (line 135, type: attribute)
- `str` (line 135, type: direct)
- `HTTPException` (line 136, type: direct)
- `get` (line 123, type: attribute)

### src\api\routers\files.py:get_file_thumbnail

Calls:
- `Depends` (line 227, type: direct)
- `get_file_by_id` (line 231, type: attribute)
- `HTTPException` (line 234, type: direct)
- `get` (line 239, type: attribute)
- `get` (line 239, type: attribute)
- `HTTPException` (line 240, type: direct)
- `b64decode` (line 247, type: attribute)
- `error` (line 249, type: attribute)
- `str` (line 249, type: direct)
- `HTTPException` (line 250, type: direct)
- `get` (line 256, type: attribute)
- `Response` (line 260, type: direct)
- `error` (line 272, type: attribute)
- `str` (line 272, type: direct)
- `HTTPException` (line 273, type: direct)
- `get` (line 224, type: attribute)

### src\api\routers\files.py:get_watch_folder_settings

Calls:
- `Depends` (line 364, type: direct)
- `get_watch_folder_settings` (line 368, type: attribute)
- `get_all_watch_folders` (line 370, type: attribute)
- `to_dict` (line 371, type: attribute)
- `WatchFolderSettings` (line 372, type: direct)
- `error` (line 374, type: attribute)
- `str` (line 374, type: direct)
- `HTTPException` (line 375, type: direct)
- `get` (line 362, type: attribute)

### src\api\routers\files.py:get_watch_folder_status

Calls:
- `Depends` (line 383, type: direct)
- `Depends` (line 384, type: direct)
- `get_watch_status` (line 388, type: attribute)
- `error` (line 391, type: attribute)
- `str` (line 391, type: direct)
- `HTTPException` (line 392, type: direct)
- `get` (line 381, type: attribute)

### src\api\routers\files.py:list_files

Calls:
- `Query` (line 62, type: direct)
- `Query` (line 63, type: direct)
- `Query` (line 64, type: direct)
- `Query` (line 65, type: direct)
- `Query` (line 66, type: direct)
- `Query` (line 67, type: direct)
- `Query` (line 68, type: direct)
- `Query` (line 69, type: direct)
- `Query` (line 70, type: direct)
- `Depends` (line 71, type: direct)
- `info` (line 75, type: attribute)
- `get_files` (line 79, type: attribute)
- `len` (line 91, type: direct)
- `max` (line 92, type: direct)
- `info` (line 99, type: attribute)
- `len` (line 99, type: direct)
- `model_validate` (line 101, type: attribute)
- `info` (line 103, type: attribute)
- `len` (line 103, type: direct)
- `error` (line 116, type: attribute)
- `str` (line 116, type: direct)
- `HTTPException` (line 117, type: direct)
- `str` (line 119, type: direct)
- `get` (line 60, type: attribute)

### src\api\routers\files.py:list_local_files

Calls:
- `Query` (line 400, type: direct)
- `Depends` (line 401, type: direct)
- `get_local_files` (line 405, type: attribute)
- `get` (line 409, type: attribute)
- `error` (line 413, type: attribute)
- `str` (line 413, type: direct)
- `HTTPException` (line 414, type: direct)
- `get` (line 398, type: attribute)

### src\api\routers\files.py:process_file_thumbnails

Calls:
- `Depends` (line 323, type: direct)
- `get_file_by_id` (line 327, type: attribute)
- `HTTPException` (line 330, type: direct)
- `get` (line 335, type: attribute)
- `HTTPException` (line 337, type: direct)
- `process_file_thumbnails` (line 342, type: attribute)
- `error` (line 352, type: attribute)
- `str` (line 352, type: direct)
- `HTTPException` (line 353, type: direct)
- `post` (line 320, type: attribute)

### src\api\routers\files.py:reload_watch_folders

Calls:
- `Depends` (line 422, type: direct)
- `reload_watch_folders` (line 426, type: attribute)
- `error` (line 429, type: attribute)
- `str` (line 429, type: direct)
- `HTTPException` (line 430, type: direct)
- `post` (line 420, type: attribute)

### src\api\routers\files.py:remove_watch_folder

Calls:
- `Query` (line 493, type: direct)
- `Depends` (line 494, type: direct)
- `Depends` (line 495, type: direct)
- `remove_watch_folder` (line 500, type: attribute)
- `HTTPException` (line 502, type: direct)
- `reload_watch_folders` (line 508, type: attribute)
- `error` (line 514, type: attribute)
- `str` (line 514, type: direct)
- `HTTPException` (line 515, type: direct)
- `delete` (line 491, type: attribute)

### src\api\routers\files.py:sync_printer_files

Calls:
- `Query` (line 209, type: direct)
- `Depends` (line 210, type: direct)
- `sync_printer_files` (line 214, type: attribute)
- `error` (line 217, type: attribute)
- `str` (line 217, type: direct)
- `str` (line 217, type: direct)
- `HTTPException` (line 218, type: direct)
- `post` (line 207, type: attribute)

### src\api\routers\files.py:update_watch_folder

Calls:
- `Query` (line 523, type: direct)
- `Query` (line 524, type: direct)
- `Depends` (line 525, type: direct)
- `Depends` (line 526, type: direct)
- `_ensure_env_migration` (line 531, type: attribute)
- `get_watch_folder_by_path` (line 532, type: attribute)
- `HTTPException` (line 535, type: direct)
- `update_watch_folder` (line 541, type: attribute)
- `HTTPException` (line 547, type: direct)
- `reload_watch_folders` (line 553, type: attribute)
- `error` (line 566, type: attribute)
- `str` (line 566, type: direct)
- `HTTPException` (line 567, type: direct)
- `patch` (line 521, type: attribute)

### src\api\routers\files.py:validate_watch_folder

Calls:
- `Query` (line 438, type: direct)
- `Depends` (line 439, type: direct)
- `validate_watch_folder` (line 443, type: attribute)
- `error` (line 446, type: attribute)
- `str` (line 446, type: direct)
- `HTTPException` (line 447, type: direct)
- `post` (line 436, type: attribute)

### src\api\routers\health.py:health_check

Calls:
- `Depends` (line 40, type: direct)
- `Depends` (line 41, type: direct)
- `health_check` (line 49, type: attribute)
- `getattr` (line 52, type: direct)
- `getattr` (line 53, type: direct)
- `getattr` (line 54, type: direct)
- `getattr` (line 55, type: direct)
- `hasattr` (line 70, type: direct)
- `len` (line 70, type: direct)
- `hasattr` (line 75, type: direct)
- `str` (line 81, type: direct)
- `str` (line 106, type: direct)
- `values` (line 121, type: attribute)
- `all` (line 122, type: direct)
- `any` (line 124, type: direct)
- `HealthResponse` (line 132, type: direct)
- `now` (line 134, type: attribute)
- `getattr` (line 136, type: direct)
- `error` (line 147, type: attribute)
- `str` (line 147, type: direct)
- `HealthResponse` (line 151, type: direct)
- `now` (line 153, type: attribute)
- `getattr` (line 155, type: direct)
- `str` (line 157, type: direct)
- `get` (line 37, type: attribute)

### src\api\routers\health.py:liveness_check

Calls:
- `get` (line 170, type: attribute)

### src\api\routers\health.py:readiness_check

Calls:
- `get` (line 161, type: attribute)

### src\api\routers\idea_url.py:get_supported_platforms

Calls:
- `Depends` (line 78, type: direct)
- `get_supported_platforms` (line 82, type: attribute)
- `get_platform_info` (line 86, type: attribute)
- `append` (line 87, type: attribute)
- `HTTPException` (line 95, type: direct)
- `get` (line 76, type: attribute)

### src\api\routers\idea_url.py:preview_url

Calls:
- `Depends` (line 45, type: direct)
- `_extract_url_metadata` (line 49, type: attribute)
- `HTTPException` (line 51, type: direct)
- `get` (line 60, type: attribute)
- `get` (line 61, type: attribute)
- `get` (line 62, type: attribute)
- `get` (line 63, type: attribute)
- `HTTPException` (line 70, type: direct)
- `post` (line 42, type: attribute)

### src\api\routers\idea_url.py:validate_url

Calls:
- `Depends` (line 22, type: direct)
- `validate_url` (line 26, type: attribute)
- `detect_platform` (line 27, type: attribute)
- `get_supported_platforms` (line 32, type: attribute)
- `HTTPException` (line 36, type: direct)
- `get` (line 19, type: attribute)

### src\api\routers\ideas.py:create_idea

Calls:
- `Depends` (line 73, type: direct)
- `create_idea` (line 77, type: attribute)
- `dict` (line 77, type: attribute)
- `HTTPException` (line 79, type: direct)
- `HTTPException` (line 87, type: direct)
- `str` (line 89, type: direct)
- `HTTPException` (line 92, type: direct)
- `post` (line 70, type: attribute)

### src\api\routers\ideas.py:delete_idea

Calls:
- `Depends` (line 195, type: direct)
- `get_idea` (line 200, type: attribute)
- `HTTPException` (line 202, type: direct)
- `delete_idea` (line 207, type: attribute)
- `HTTPException` (line 209, type: direct)
- `HTTPException` (line 219, type: direct)
- `delete` (line 192, type: attribute)

### src\api\routers\ideas.py:get_all_tags

Calls:
- `Depends` (line 288, type: direct)
- `get_all_tags` (line 292, type: attribute)
- `HTTPException` (line 294, type: direct)
- `get` (line 286, type: attribute)

### src\api\routers\ideas.py:get_idea

Calls:
- `Depends` (line 133, type: direct)
- `get_idea` (line 137, type: attribute)
- `HTTPException` (line 139, type: direct)
- `to_dict` (line 144, type: attribute)
- `HTTPException` (line 149, type: direct)
- `get` (line 130, type: attribute)

### src\api\routers\ideas.py:get_idea_statistics

Calls:
- `Depends` (line 302, type: direct)
- `get_statistics` (line 306, type: attribute)
- `HTTPException` (line 308, type: direct)
- `get` (line 300, type: attribute)

### src\api\routers\ideas.py:get_trending_models

Calls:
- `Query` (line 344, type: direct)
- `Depends` (line 345, type: direct)
- `HTTPException` (line 350, type: direct)
- `get_trending` (line 356, type: attribute)
- `HTTPException` (line 361, type: direct)
- `get` (line 341, type: attribute)

### src\api\routers\ideas.py:import_idea_from_url

Calls:
- `Depends` (line 262, type: direct)
- `dict` (line 266, type: attribute)
- `import_from_url` (line 267, type: attribute)
- `str` (line 267, type: direct)
- `HTTPException` (line 270, type: direct)
- `HTTPException` (line 280, type: direct)
- `post` (line 259, type: attribute)

### src\api\routers\ideas.py:list_ideas

Calls:
- `Query` (line 100, type: direct)
- `Query` (line 101, type: direct)
- `Query` (line 102, type: direct)
- `Query` (line 103, type: direct)
- `Query` (line 104, type: direct)
- `Query` (line 105, type: direct)
- `Depends` (line 106, type: direct)
- `list_ideas` (line 120, type: attribute)
- `HTTPException` (line 124, type: direct)
- `get` (line 98, type: attribute)

### src\api\routers\ideas.py:refresh_trending_cache

Calls:
- `Depends` (line 396, type: direct)
- `cleanup_expired_trending` (line 402, type: attribute)
- `HTTPException` (line 407, type: direct)
- `HTTPException` (line 415, type: direct)
- `post` (line 394, type: attribute)

### src\api\routers\ideas.py:save_trending_as_idea

Calls:
- `Depends` (line 371, type: direct)
- `save_trending_as_idea` (line 375, type: attribute)
- `dict` (line 375, type: attribute)
- `HTTPException` (line 378, type: direct)
- `HTTPException` (line 388, type: direct)
- `post` (line 367, type: attribute)

### src\api\routers\ideas.py:search_ideas

Calls:
- `Query` (line 316, type: direct)
- `Query` (line 317, type: direct)
- `Query` (line 318, type: direct)
- `Query` (line 319, type: direct)
- `Depends` (line 320, type: direct)
- `search_ideas` (line 332, type: attribute)
- `HTTPException` (line 334, type: direct)
- `get` (line 314, type: attribute)

### src\api\routers\ideas.py:update_idea

Calls:
- `Depends` (line 159, type: direct)
- `get_idea` (line 164, type: attribute)
- `HTTPException` (line 166, type: direct)
- `dict` (line 172, type: attribute)
- `update_idea` (line 173, type: attribute)
- `HTTPException` (line 176, type: direct)
- `HTTPException` (line 186, type: direct)
- `put` (line 155, type: attribute)

### src\api\routers\ideas.py:update_idea_status

Calls:
- `Depends` (line 229, type: direct)
- `get_idea` (line 234, type: attribute)
- `HTTPException` (line 236, type: direct)
- `update_idea_status` (line 241, type: attribute)
- `HTTPException` (line 243, type: direct)
- `HTTPException` (line 253, type: direct)
- `patch` (line 225, type: attribute)

### src\api\routers\jobs.py:_transform_job_to_response

Calls:
- `copy` (line 56, type: attribute)
- `get` (line 63, type: attribute)
- `get` (line 64, type: attribute)
- `get` (line 68, type: attribute)
- `isinstance` (line 69, type: direct)
- `isoformat` (line 69, type: attribute)
- `str` (line 69, type: direct)
- `get` (line 71, type: attribute)
- `isinstance` (line 72, type: direct)
- `isoformat` (line 72, type: attribute)
- `str` (line 72, type: direct)

### src\api\routers\jobs.py:delete_job

Calls:
- `Depends` (line 131, type: direct)
- `delete_job` (line 135, type: attribute)
- `HTTPException` (line 137, type: direct)
- `error` (line 144, type: attribute)
- `str` (line 144, type: direct)
- `str` (line 144, type: direct)
- `HTTPException` (line 145, type: direct)
- `delete` (line 128, type: attribute)

### src\api\routers\jobs.py:get_job

Calls:
- `Depends` (line 107, type: direct)
- `get_job` (line 111, type: attribute)
- `HTTPException` (line 113, type: direct)
- `model_validate` (line 117, type: attribute)
- `_transform_job_to_response` (line 117, type: direct)
- `error` (line 121, type: attribute)
- `str` (line 121, type: direct)
- `str` (line 121, type: direct)
- `HTTPException` (line 122, type: direct)
- `get` (line 104, type: attribute)

### src\api\routers\jobs.py:list_jobs

Calls:
- `Query` (line 79, type: direct)
- `Query` (line 80, type: direct)
- `Query` (line 81, type: direct)
- `Query` (line 82, type: direct)
- `Query` (line 83, type: direct)
- `Depends` (line 84, type: direct)
- `list_jobs` (line 88, type: attribute)
- `model_validate` (line 95, type: attribute)
- `_transform_job_to_response` (line 95, type: direct)
- `error` (line 97, type: attribute)
- `str` (line 97, type: direct)
- `HTTPException` (line 98, type: direct)
- `get` (line 77, type: attribute)

### src\api\routers\library.py:delete_library_file

Calls:
- `PathParam` (line 269, type: direct)
- `Query` (line 270, type: direct)
- `Depends` (line 271, type: direct)
- `get_file_by_checksum` (line 299, type: attribute)
- `HTTPException` (line 301, type: direct)
- `delete_file` (line 307, type: attribute)
- `HTTPException` (line 310, type: direct)
- `error` (line 324, type: attribute)
- `str` (line 324, type: direct)
- `HTTPException` (line 325, type: direct)
- `str` (line 325, type: direct)
- `delete` (line 267, type: attribute)

### src\api\routers\library.py:get_library_file

Calls:
- `PathParam` (line 169, type: direct)
- `Depends` (line 170, type: direct)
- `get_file_by_checksum` (line 188, type: attribute)
- `HTTPException` (line 191, type: direct)
- `error` (line 201, type: attribute)
- `str` (line 201, type: direct)
- `HTTPException` (line 202, type: direct)
- `str` (line 202, type: direct)
- `get` (line 167, type: attribute)

### src\api\routers\library.py:get_library_service

Calls:
- `hasattr` (line 85, type: direct)
- `HTTPException` (line 86, type: direct)

### src\api\routers\library.py:get_library_statistics

Calls:
- `Depends` (line 330, type: direct)
- `get_library_statistics` (line 353, type: attribute)
- `LibraryStatsResponse` (line 356, type: direct)
- `get` (line 357, type: attribute)
- `get` (line 358, type: attribute)
- `get` (line 359, type: attribute)
- `get` (line 360, type: attribute)
- `get` (line 361, type: attribute)
- `get` (line 362, type: attribute)
- `get` (line 363, type: attribute)
- `get` (line 364, type: attribute)
- `get` (line 365, type: attribute)
- `get` (line 366, type: attribute)
- `error` (line 370, type: attribute)
- `str` (line 370, type: direct)
- `HTTPException` (line 371, type: direct)
- `str` (line 371, type: direct)
- `get` (line 328, type: attribute)

### src\api\routers\library.py:library_health_check

Calls:
- `Depends` (line 375, type: direct)
- `str` (line 396, type: direct)
- `exists` (line 401, type: attribute)
- `str` (line 405, type: direct)
- `get_library_statistics` (line 410, type: attribute)
- `str` (line 415, type: direct)
- `get` (line 416, type: attribute)
- `error` (line 421, type: attribute)
- `str` (line 421, type: direct)
- `str` (line 425, type: direct)
- `str` (line 426, type: direct)
- `get` (line 374, type: attribute)

### src\api\routers\library.py:list_library_files

Calls:
- `Query` (line 92, type: direct)
- `Query` (line 93, type: direct)
- `Query` (line 94, type: direct)
- `Query` (line 95, type: direct)
- `Query` (line 96, type: direct)
- `Query` (line 97, type: direct)
- `Query` (line 98, type: direct)
- `Query` (line 99, type: direct)
- `Query` (line 100, type: direct)
- `Query` (line 101, type: direct)
- `Query` (line 102, type: direct)
- `Query` (line 103, type: direct)
- `Depends` (line 104, type: direct)
- `list_files` (line 155, type: attribute)
- `error` (line 163, type: attribute)
- `str` (line 163, type: direct)
- `HTTPException` (line 164, type: direct)
- `str` (line 164, type: direct)
- `get` (line 90, type: attribute)

### src\api\routers\library.py:reprocess_library_file

Calls:
- `PathParam` (line 207, type: direct)
- `Depends` (line 208, type: direct)
- `get_file_by_checksum` (line 238, type: attribute)
- `HTTPException` (line 240, type: direct)
- `reprocess_file` (line 246, type: attribute)
- `HTTPException` (line 249, type: direct)
- `error` (line 263, type: attribute)
- `str` (line 263, type: direct)
- `HTTPException` (line 264, type: direct)
- `str` (line 264, type: direct)
- `post` (line 205, type: attribute)

### src\api\routers\materials.py:create_material

Calls:
- `Depends` (line 219, type: direct)
- `create_material` (line 223, type: attribute)
- `MaterialResponse` (line 225, type: direct)
- `HTTPException` (line 244, type: direct)
- `str` (line 244, type: direct)
- `HTTPException` (line 246, type: direct)
- `str` (line 246, type: direct)
- `post` (line 216, type: attribute)

### src\api\routers\materials.py:delete_material

Calls:
- `Depends` (line 321, type: direct)
- `HTTPException` (line 325, type: direct)
- `delete` (line 318, type: attribute)

### src\api\routers\materials.py:export_inventory

Calls:
- `Query` (line 154, type: direct)
- `Depends` (line 155, type: direct)
- `Path` (line 159, type: direct)
- `now` (line 159, type: attribute)
- `mkdir` (line 160, type: attribute)
- `export_inventory` (line 163, type: attribute)
- `FileResponse` (line 165, type: direct)
- `str` (line 166, type: direct)
- `HTTPException` (line 172, type: direct)
- `HTTPException` (line 174, type: direct)
- `HTTPException` (line 178, type: direct)
- `str` (line 178, type: direct)
- `get` (line 152, type: attribute)

### src\api\routers\materials.py:get_consumption_history

Calls:
- `Query` (line 333, type: direct)
- `Depends` (line 334, type: direct)
- `HTTPException` (line 338, type: direct)
- `get` (line 328, type: attribute)

### src\api\routers\materials.py:get_consumption_report

Calls:
- `Query` (line 136, type: direct)
- `Query` (line 137, type: direct)
- `Depends` (line 138, type: direct)
- `HTTPException` (line 143, type: direct)
- `generate_report` (line 145, type: attribute)
- `HTTPException` (line 149, type: direct)
- `str` (line 149, type: direct)
- `get` (line 134, type: attribute)

### src\api\routers\materials.py:get_material

Calls:
- `Depends` (line 184, type: direct)
- `get_material` (line 188, type: attribute)
- `HTTPException` (line 190, type: direct)
- `MaterialResponse` (line 192, type: direct)
- `HTTPException` (line 213, type: direct)
- `str` (line 213, type: direct)
- `get` (line 181, type: attribute)

### src\api\routers\materials.py:get_material_stats

Calls:
- `Depends` (line 115, type: direct)
- `get_statistics` (line 119, type: attribute)
- `HTTPException` (line 121, type: direct)
- `str` (line 121, type: direct)
- `get` (line 113, type: attribute)

### src\api\routers\materials.py:get_material_types

Calls:
- `get` (line 124, type: attribute)

### src\api\routers\materials.py:get_materials

Calls:
- `Depends` (line 70, type: direct)
- `get_all_materials` (line 74, type: attribute)
- `MaterialResponse` (line 89, type: direct)
- `HTTPException` (line 110, type: direct)
- `str` (line 110, type: direct)
- `get` (line 63, type: attribute)

### src\api\routers\materials.py:record_consumption

Calls:
- `Depends` (line 288, type: direct)
- `record_consumption` (line 292, type: attribute)
- `float` (line 308, type: direct)
- `HTTPException` (line 313, type: direct)
- `str` (line 313, type: direct)
- `HTTPException` (line 315, type: direct)
- `str` (line 315, type: direct)
- `post` (line 285, type: attribute)

### src\api\routers\materials.py:update_material

Calls:
- `Depends` (line 253, type: direct)
- `update_material` (line 257, type: attribute)
- `HTTPException` (line 259, type: direct)
- `MaterialResponse` (line 261, type: direct)
- `HTTPException` (line 282, type: direct)
- `str` (line 282, type: direct)
- `patch` (line 249, type: attribute)

### src\api\routers\printers.py:_printer_to_response

Calls:
- `get` (line 80, type: attribute)
- `isinstance` (line 86, type: direct)
- `strip` (line 86, type: attribute)
- `CurrentJobInfo` (line 87, type: direct)
- `strip` (line 88, type: attribute)
- `warning` (line 103, type: attribute)
- `str` (line 104, type: direct)
- `PrinterResponse` (line 106, type: direct)
- `getattr` (line 114, type: direct)
- `getattr` (line 115, type: direct)
- `getattr` (line 116, type: direct)
- `getattr` (line 118, type: direct)
- `getattr` (line 119, type: direct)
- `isoformat` (line 121, type: attribute)
- `isoformat` (line 124, type: attribute)
- `isoformat` (line 125, type: attribute)

### src\api\routers\printers.py:connect_printer

Calls:
- `Depends` (line 256, type: direct)
- `connect_printer` (line 260, type: attribute)
- `HTTPException` (line 262, type: direct)
- `error` (line 270, type: attribute)
- `str` (line 270, type: direct)
- `str` (line 270, type: direct)
- `HTTPException` (line 271, type: direct)
- `post` (line 253, type: attribute)

### src\api\routers\printers.py:create_printer

Calls:
- `Depends` (line 148, type: direct)
- `create_printer` (line 152, type: attribute)
- `info` (line 159, type: attribute)
- `type` (line 159, type: direct)
- `_printer_to_response` (line 160, type: direct)
- `info` (line 161, type: attribute)
- `model_dump` (line 161, type: attribute)
- `HTTPException` (line 164, type: direct)
- `str` (line 166, type: direct)
- `error` (line 169, type: attribute)
- `str` (line 169, type: direct)
- `HTTPException` (line 170, type: direct)
- `post` (line 145, type: attribute)

### src\api\routers\printers.py:delete_printer

Calls:
- `Depends` (line 233, type: direct)
- `delete_printer` (line 237, type: attribute)
- `HTTPException` (line 239, type: direct)
- `error` (line 246, type: attribute)
- `str` (line 246, type: direct)
- `str` (line 246, type: direct)
- `HTTPException` (line 247, type: direct)
- `delete` (line 230, type: attribute)

### src\api\routers\printers.py:disconnect_printer

Calls:
- `Depends` (line 280, type: direct)
- `disconnect_printer` (line 284, type: attribute)
- `error` (line 287, type: attribute)
- `str` (line 287, type: direct)
- `str` (line 287, type: direct)
- `HTTPException` (line 288, type: direct)
- `post` (line 277, type: attribute)

### src\api\routers\printers.py:download_current_job_file

Calls:
- `Depends` (line 372, type: direct)
- `download_current_job_file` (line 385, type: attribute)
- `str` (line 385, type: direct)
- `isinstance` (line 387, type: direct)
- `error` (line 393, type: attribute)
- `str` (line 393, type: direct)
- `str` (line 393, type: direct)
- `HTTPException` (line 394, type: direct)
- `post` (line 369, type: attribute)

### src\api\routers\printers.py:download_printer_file

Calls:
- `Depends` (line 471, type: direct)
- `str` (line 475, type: direct)
- `download_printer_file` (line 476, type: attribute)
- `HTTPException` (line 478, type: direct)
- `error` (line 486, type: attribute)
- `str` (line 486, type: direct)
- `str` (line 486, type: direct)
- `HTTPException` (line 487, type: direct)
- `post` (line 467, type: attribute)

### src\api\routers\printers.py:get_printer

Calls:
- `Depends` (line 179, type: direct)
- `get_printer` (line 183, type: attribute)
- `str` (line 183, type: direct)
- `HTTPException` (line 185, type: direct)
- `_printer_to_response` (line 189, type: direct)
- `error` (line 193, type: attribute)
- `str` (line 193, type: direct)
- `str` (line 193, type: direct)
- `HTTPException` (line 194, type: direct)
- `get` (line 176, type: attribute)

### src\api\routers\printers.py:get_printer_current_thumbnail

Calls:
- `Depends` (line 496, type: direct)
- `get_printer` (line 505, type: attribute)
- `str` (line 505, type: direct)
- `HTTPException` (line 507, type: direct)
- `get` (line 509, type: attribute)
- `getattr` (line 510, type: direct)
- `HTTPException` (line 511, type: direct)
- `getattr` (line 514, type: direct)
- `getattr` (line 515, type: direct)
- `HTTPException` (line 517, type: direct)
- `getattr` (line 520, type: direct)
- `HTTPException` (line 522, type: direct)
- `get_file_by_id` (line 524, type: attribute)
- `HTTPException` (line 526, type: direct)
- `get` (line 528, type: attribute)
- `get` (line 528, type: attribute)
- `HTTPException` (line 529, type: direct)
- `b64decode` (line 533, type: attribute)
- `HTTPException` (line 535, type: direct)
- `get` (line 537, type: attribute)
- `Response` (line 538, type: direct)
- `error` (line 549, type: attribute)
- `str` (line 549, type: direct)
- `str` (line 549, type: direct)
- `HTTPException` (line 550, type: direct)
- `get` (line 493, type: attribute)

### src\api\routers\printers.py:get_printer_files

Calls:
- `Depends` (line 400, type: direct)
- `str` (line 404, type: direct)
- `get_printer_files` (line 405, type: attribute)
- `error` (line 410, type: attribute)
- `str` (line 410, type: direct)
- `str` (line 410, type: direct)
- `HTTPException` (line 411, type: direct)
- `get` (line 397, type: attribute)

### src\api\routers\printers.py:list_printers

Calls:
- `Depends` (line 131, type: direct)
- `list_printers` (line 135, type: attribute)
- `_printer_to_response` (line 136, type: direct)
- `error` (line 138, type: attribute)
- `str` (line 138, type: direct)
- `HTTPException` (line 139, type: direct)
- `get` (line 129, type: attribute)

### src\api\routers\printers.py:pause_printer

Calls:
- `Depends` (line 297, type: direct)
- `str` (line 301, type: direct)
- `pause_printer` (line 302, type: attribute)
- `HTTPException` (line 304, type: direct)
- `error` (line 312, type: attribute)
- `str` (line 312, type: direct)
- `str` (line 312, type: direct)
- `HTTPException` (line 313, type: direct)
- `post` (line 294, type: attribute)

### src\api\routers\printers.py:resume_printer

Calls:
- `Depends` (line 322, type: direct)
- `str` (line 326, type: direct)
- `resume_printer` (line 327, type: attribute)
- `HTTPException` (line 329, type: direct)
- `error` (line 337, type: attribute)
- `str` (line 337, type: direct)
- `str` (line 337, type: direct)
- `HTTPException` (line 338, type: direct)
- `post` (line 319, type: attribute)

### src\api\routers\printers.py:start_printer_monitoring

Calls:
- `Depends` (line 420, type: direct)
- `str` (line 424, type: direct)
- `start_printer_monitoring` (line 425, type: attribute)
- `HTTPException` (line 427, type: direct)
- `error` (line 435, type: attribute)
- `str` (line 435, type: direct)
- `str` (line 435, type: direct)
- `HTTPException` (line 436, type: direct)
- `post` (line 417, type: attribute)

### src\api\routers\printers.py:stop_printer

Calls:
- `Depends` (line 347, type: direct)
- `str` (line 351, type: direct)
- `stop_printer` (line 352, type: attribute)
- `HTTPException` (line 354, type: direct)
- `error` (line 362, type: attribute)
- `str` (line 362, type: direct)
- `str` (line 362, type: direct)
- `HTTPException` (line 363, type: direct)
- `post` (line 344, type: attribute)

### src\api\routers\printers.py:stop_printer_monitoring

Calls:
- `Depends` (line 445, type: direct)
- `str` (line 449, type: direct)
- `stop_printer_monitoring` (line 450, type: attribute)
- `HTTPException` (line 452, type: direct)
- `error` (line 460, type: attribute)
- `str` (line 460, type: direct)
- `str` (line 460, type: direct)
- `HTTPException` (line 461, type: direct)
- `post` (line 442, type: attribute)

### src\api\routers\printers.py:update_printer

Calls:
- `Depends` (line 204, type: direct)
- `update_printer` (line 208, type: attribute)
- `model_dump` (line 208, type: attribute)
- `HTTPException` (line 210, type: direct)
- `_printer_to_response` (line 214, type: direct)
- `HTTPException` (line 218, type: direct)
- `str` (line 220, type: direct)
- `error` (line 223, type: attribute)
- `str` (line 223, type: direct)
- `str` (line 223, type: direct)
- `HTTPException` (line 224, type: direct)
- `put` (line 200, type: attribute)

### src\api\routers\settings.py:add_or_update_printer

Calls:
- `Depends` (line 169, type: direct)
- `add_printer` (line 173, type: attribute)
- `dict` (line 173, type: attribute)
- `HTTPException` (line 178, type: direct)
- `error` (line 184, type: attribute)
- `str` (line 184, type: direct)
- `HTTPException` (line 185, type: direct)
- `post` (line 165, type: attribute)

### src\api\routers\settings.py:get_application_settings

Calls:
- `Depends` (line 98, type: direct)
- `get_application_settings` (line 102, type: attribute)
- `ApplicationSettingsResponse` (line 103, type: direct)
- `error` (line 105, type: attribute)
- `str` (line 105, type: direct)
- `HTTPException` (line 106, type: direct)
- `get` (line 96, type: attribute)

### src\api\routers\settings.py:get_gcode_optimization_settings

Calls:
- `Depends` (line 275, type: direct)
- `get_settings` (line 280, type: direct)
- `GcodeOptimizationSettings` (line 282, type: direct)
- `error` (line 288, type: attribute)
- `str` (line 288, type: direct)
- `HTTPException` (line 289, type: direct)
- `str` (line 291, type: direct)
- `get` (line 273, type: attribute)

### src\api\routers\settings.py:get_printer_configurations

Calls:
- `Depends` (line 142, type: direct)
- `get_printers` (line 146, type: attribute)
- `dict` (line 148, type: attribute)
- `PrinterConfigResponse` (line 148, type: direct)
- `items` (line 155, type: attribute)
- `error` (line 158, type: attribute)
- `str` (line 158, type: direct)
- `HTTPException` (line 159, type: direct)
- `get` (line 140, type: attribute)

### src\api\routers\settings.py:get_watch_folder_settings

Calls:
- `Depends` (line 235, type: direct)
- `get_watch_folder_settings` (line 239, type: attribute)
- `WatchFolderSettings` (line 240, type: direct)
- `error` (line 242, type: attribute)
- `str` (line 242, type: direct)
- `HTTPException` (line 243, type: direct)
- `get` (line 233, type: attribute)

### src\api\routers\settings.py:reload_configuration

Calls:
- `Depends` (line 323, type: direct)
- `reload_config` (line 327, type: attribute)
- `HTTPException` (line 332, type: direct)
- `error` (line 338, type: attribute)
- `str` (line 338, type: direct)
- `HTTPException` (line 339, type: direct)
- `post` (line 321, type: attribute)

### src\api\routers\settings.py:remove_printer

Calls:
- `Depends` (line 194, type: direct)
- `remove_printer` (line 198, type: attribute)
- `HTTPException` (line 203, type: direct)
- `error` (line 209, type: attribute)
- `str` (line 209, type: direct)
- `HTTPException` (line 210, type: direct)
- `delete` (line 191, type: attribute)

### src\api\routers\settings.py:update_application_settings

Calls:
- `Depends` (line 115, type: direct)
- `dict` (line 120, type: attribute)
- `info` (line 121, type: attribute)
- `items` (line 122, type: attribute)
- `info` (line 123, type: attribute)
- `update_application_settings` (line 125, type: attribute)
- `list` (line 128, type: direct)
- `keys` (line 128, type: attribute)
- `error` (line 133, type: attribute)
- `str` (line 133, type: direct)
- `HTTPException` (line 134, type: direct)
- `put` (line 112, type: attribute)

### src\api\routers\settings.py:update_gcode_optimization_settings

Calls:
- `Depends` (line 298, type: direct)
- `info` (line 304, type: attribute)
- `error` (line 314, type: attribute)
- `str` (line 314, type: direct)
- `HTTPException` (line 315, type: direct)
- `str` (line 317, type: direct)
- `put` (line 295, type: attribute)

### src\api\routers\settings.py:validate_printer_connection

Calls:
- `Depends` (line 219, type: direct)
- `validate_printer_connection` (line 223, type: attribute)
- `error` (line 226, type: attribute)
- `str` (line 226, type: direct)
- `HTTPException` (line 227, type: direct)
- `post` (line 216, type: attribute)

### src\api\routers\settings.py:validate_watch_folder

Calls:
- `Depends` (line 252, type: direct)
- `validate_watch_folder` (line 256, type: attribute)
- `error` (line 259, type: attribute)
- `str` (line 259, type: direct)
- `HTTPException` (line 260, type: direct)
- `post` (line 249, type: attribute)

### src\api\routers\system.py:create_backup

Calls:
- `Depends` (line 42, type: direct)
- `create_backup` (line 46, type: attribute)
- `error` (line 49, type: attribute)
- `str` (line 49, type: direct)
- `HTTPException` (line 50, type: direct)
- `post` (line 40, type: attribute)

### src\api\routers\system.py:get_system_info

Calls:
- `Depends` (line 26, type: direct)
- `get_system_info` (line 30, type: attribute)
- `error` (line 33, type: attribute)
- `str` (line 33, type: direct)
- `HTTPException` (line 34, type: direct)
- `get` (line 24, type: attribute)

### src\api\routers\trending.py:cleanup_expired

Calls:
- `Depends` (line 226, type: direct)
- `cleanup_expired` (line 230, type: attribute)
- `HTTPException` (line 232, type: direct)
- `str` (line 232, type: direct)
- `delete` (line 224, type: attribute)

### src\api\routers\trending.py:get_platform_trending

Calls:
- `Query` (line 184, type: direct)
- `Query` (line 185, type: direct)
- `Depends` (line 186, type: direct)
- `HTTPException` (line 192, type: direct)
- `get_trending` (line 195, type: attribute)
- `len` (line 203, type: direct)
- `get` (line 210, type: attribute)
- `get` (line 211, type: attribute)
- `get` (line 212, type: attribute)
- `get` (line 213, type: attribute)
- `HTTPException` (line 221, type: direct)
- `str` (line 221, type: direct)
- `get` (line 181, type: attribute)

### src\api\routers\trending.py:get_supported_platforms

Calls:
- `get` (line 90, type: attribute)

### src\api\routers\trending.py:get_trending

Calls:
- `Query` (line 53, type: direct)
- `Query` (line 54, type: direct)
- `Query` (line 55, type: direct)
- `Depends` (line 56, type: direct)
- `get_trending` (line 60, type: attribute)
- `TrendingModel` (line 67, type: direct)
- `get` (line 73, type: attribute)
- `get` (line 74, type: attribute)
- `get` (line 75, type: attribute)
- `get` (line 76, type: attribute)
- `get` (line 77, type: attribute)
- `get` (line 78, type: attribute)
- `fromisoformat` (line 79, type: attribute)
- `fromisoformat` (line 80, type: attribute)
- `isinstance` (line 81, type: direct)
- `get` (line 81, type: attribute)
- `get` (line 81, type: attribute)
- `HTTPException` (line 87, type: direct)
- `str` (line 87, type: direct)
- `get` (line 51, type: attribute)

### src\api\routers\trending.py:get_trending_categories

Calls:
- `Query` (line 237, type: direct)
- `Depends` (line 238, type: direct)
- `get` (line 235, type: attribute)

### src\api\routers\trending.py:get_trending_stats

Calls:
- `Depends` (line 113, type: direct)
- `get_statistics` (line 117, type: attribute)
- `TrendingStats` (line 118, type: direct)
- `HTTPException` (line 120, type: direct)
- `str` (line 120, type: direct)
- `get` (line 111, type: attribute)

### src\api\routers\trending.py:refresh_trending

Calls:
- `Query` (line 125, type: direct)
- `Depends` (line 126, type: direct)
- `fetch_makerworld_trending` (line 133, type: attribute)
- `save_trending_items` (line 134, type: attribute)
- `fetch_printables_trending` (line 136, type: attribute)
- `save_trending_items` (line 137, type: attribute)
- `HTTPException` (line 139, type: direct)
- `locals` (line 143, type: direct)
- `len` (line 143, type: direct)
- `refresh_all_platforms` (line 147, type: attribute)
- `HTTPException` (line 153, type: direct)
- `str` (line 153, type: direct)
- `post` (line 123, type: attribute)

### src\api\routers\trending.py:save_trending_as_idea

Calls:
- `Depends` (line 160, type: direct)
- `save_as_idea` (line 164, type: attribute)
- `HTTPException` (line 176, type: direct)
- `str` (line 176, type: direct)
- `HTTPException` (line 178, type: direct)
- `str` (line 178, type: direct)
- `post` (line 156, type: attribute)

### src\api\routers\websocket.py:ConnectionManager.__init__

Calls:
- `set` (line 22, type: direct)

### src\api\routers\websocket.py:ConnectionManager.broadcast

Calls:
- `dumps` (line 42, type: attribute)
- `set` (line 43, type: direct)
- `send_text` (line 47, type: attribute)
- `add` (line 49, type: attribute)
- `disconnect` (line 53, type: attribute)

### src\api\routers\websocket.py:ConnectionManager.connect

Calls:
- `accept` (line 26, type: attribute)
- `add` (line 27, type: attribute)
- `info` (line 28, type: attribute)
- `len` (line 28, type: direct)

### src\api\routers\websocket.py:ConnectionManager.disconnect

Calls:
- `discard` (line 31, type: attribute)
- `items` (line 33, type: attribute)
- `discard` (line 34, type: attribute)
- `info` (line 35, type: attribute)
- `len` (line 35, type: direct)

### src\api\routers\websocket.py:ConnectionManager.send_to_printer_subscribers

Calls:
- `get` (line 57, type: attribute)
- `set` (line 57, type: direct)
- `dumps` (line 61, type: attribute)
- `set` (line 62, type: direct)
- `send_text` (line 66, type: attribute)
- `add` (line 68, type: attribute)
- `discard` (line 72, type: attribute)

### src\api\routers\websocket.py:ConnectionManager.subscribe_to_printer

Calls:
- `set` (line 77, type: direct)
- `add` (line 78, type: attribute)

### src\api\routers\websocket.py:ConnectionManager.unsubscribe_from_printer

Calls:
- `discard` (line 83, type: attribute)

### src\api\routers\websocket.py:_handle_websocket_connection

Calls:
- `connect` (line 103, type: attribute)
- `receive_text` (line 108, type: attribute)
- `loads` (line 110, type: attribute)
- `handle_client_message` (line 111, type: direct)
- `send_text` (line 113, type: attribute)
- `dumps` (line 113, type: attribute)
- `error` (line 118, type: attribute)
- `str` (line 118, type: direct)
- `send_text` (line 119, type: attribute)
- `dumps` (line 119, type: attribute)
- `disconnect` (line 125, type: attribute)

### src\api\routers\websocket.py:broadcast_job_update

Calls:
- `broadcast` (line 172, type: attribute)
- `str` (line 174, type: direct)

### src\api\routers\websocket.py:broadcast_printer_status

Calls:
- `send_to_printer_subscribers` (line 163, type: attribute)
- `str` (line 163, type: direct)
- `str` (line 165, type: direct)

### src\api\routers\websocket.py:broadcast_system_event

Calls:
- `broadcast` (line 181, type: attribute)

### src\api\routers\websocket.py:handle_client_message

Calls:
- `get` (line 130, type: attribute)
- `get` (line 133, type: attribute)
- `subscribe_to_printer` (line 135, type: attribute)
- `send_text` (line 136, type: attribute)
- `dumps` (line 136, type: attribute)
- `get` (line 142, type: attribute)
- `unsubscribe_from_printer` (line 144, type: attribute)
- `send_text` (line 145, type: attribute)
- `dumps` (line 145, type: attribute)
- `send_text` (line 151, type: attribute)
- `dumps` (line 151, type: attribute)
- `send_text` (line 154, type: attribute)
- `dumps` (line 154, type: attribute)

### src\api\routers\websocket.py:websocket_endpoint

Calls:
- `_handle_websocket_connection` (line 93, type: direct)
- `websocket` (line 89, type: attribute)

### src\api\routers\websocket.py:websocket_endpoint_no_slash

Calls:
- `_handle_websocket_connection` (line 99, type: direct)
- `websocket` (line 95, type: attribute)

### src\database\database.py:Database.__init__

Calls:
- `Path` (line 25, type: direct)
- `Path` (line 27, type: direct)
- `mkdir` (line 28, type: attribute)

### src\database\database.py:Database._create_tables

Calls:
- `cursor` (line 48, type: attribute)
- `execute` (line 50, type: attribute)
- `execute` (line 74, type: attribute)
- `execute` (line 97, type: attribute)
- `execute` (line 100, type: attribute)
- `execute` (line 103, type: attribute)
- `execute` (line 108, type: attribute)
- `execute` (line 132, type: attribute)
- `execute` (line 152, type: attribute)
- `execute` (line 162, type: attribute)
- `execute` (line 163, type: attribute)
- `execute` (line 164, type: attribute)
- `execute` (line 165, type: attribute)
- `execute` (line 166, type: attribute)
- `execute` (line 169, type: attribute)
- `execute` (line 186, type: attribute)
- `execute` (line 187, type: attribute)
- `execute` (line 188, type: attribute)
- `execute` (line 189, type: attribute)
- `commit` (line 191, type: attribute)
- `info` (line 192, type: attribute)

### src\database\database.py:Database._execute_write

Calls:
- `RuntimeError` (line 210, type: direct)
- `perf_counter` (line 214, type: attribute)
- `execute` (line 216, type: attribute)
- `commit` (line 218, type: attribute)
- `perf_counter` (line 219, type: attribute)
- `debug` (line 220, type: attribute)
- `split` (line 220, type: attribute)
- `round` (line 220, type: direct)
- `warning` (line 224, type: attribute)
- `str` (line 224, type: direct)
- `sleep` (line 225, type: attribute)
- `error` (line 229, type: attribute)
- `str` (line 229, type: direct)
- `split` (line 229, type: attribute)
- `error` (line 232, type: attribute)
- `str` (line 232, type: direct)

### src\database\database.py:Database._fetch_all

Calls:
- `RuntimeError` (line 251, type: direct)
- `perf_counter` (line 252, type: attribute)
- `execute` (line 254, type: attribute)
- `fetchall` (line 255, type: attribute)
- `perf_counter` (line 256, type: attribute)
- `debug` (line 257, type: attribute)
- `split` (line 257, type: attribute)
- `len` (line 257, type: direct)
- `round` (line 257, type: direct)
- `error` (line 260, type: attribute)
- `str` (line 260, type: direct)
- `split` (line 260, type: attribute)

### src\database\database.py:Database._fetch_one

Calls:
- `RuntimeError` (line 237, type: direct)
- `perf_counter` (line 238, type: attribute)
- `execute` (line 240, type: attribute)
- `fetchone` (line 241, type: attribute)
- `perf_counter` (line 242, type: attribute)
- `debug` (line 243, type: attribute)
- `split` (line 243, type: attribute)
- `bool` (line 243, type: direct)
- `round` (line 243, type: direct)
- `error` (line 246, type: attribute)
- `str` (line 246, type: direct)
- `split` (line 246, type: attribute)

### src\database\database.py:Database._run_migrations

Calls:
- `cursor` (line 1404, type: attribute)
- `execute` (line 1406, type: attribute)
- `execute` (line 1416, type: attribute)
- `fetchall` (line 1417, type: attribute)
- `execute` (line 1421, type: attribute)
- `fetchall` (line 1422, type: attribute)
- `info` (line 1427, type: attribute)
- `execute` (line 1428, type: attribute)
- `info` (line 1432, type: attribute)
- `execute` (line 1433, type: attribute)
- `info` (line 1437, type: attribute)
- `execute` (line 1438, type: attribute)
- `execute` (line 1440, type: attribute)
- `info` (line 1444, type: attribute)
- `info` (line 1448, type: attribute)
- `execute` (line 1451, type: attribute)
- `fetchone` (line 1452, type: attribute)
- `info` (line 1456, type: attribute)
- `Path` (line 1460, type: direct)
- `exists` (line 1462, type: attribute)
- `open` (line 1463, type: direct)
- `read` (line 1464, type: attribute)
- `strip` (line 1468, type: attribute)
- `split` (line 1468, type: attribute)
- `strip` (line 1468, type: attribute)
- `startswith` (line 1471, type: attribute)
- `execute` (line 1472, type: attribute)
- `info` (line 1474, type: attribute)
- `warning` (line 1477, type: attribute)
- `execute` (line 1478, type: attribute)
- `info` (line 1484, type: attribute)
- `execute` (line 1486, type: attribute)
- `info` (line 1490, type: attribute)
- `commit` (line 1492, type: attribute)
- `info` (line 1493, type: attribute)
- `error` (line 1496, type: attribute)
- `str` (line 1496, type: direct)

### src\database\database.py:Database.add_idea_tags

Calls:
- `_execute_write` (line 949, type: attribute)
- `error` (line 955, type: attribute)
- `str` (line 955, type: direct)

### src\database\database.py:Database.clean_expired_trending

Calls:
- `_execute_write` (line 1047, type: attribute)
- `error` (line 1052, type: attribute)
- `str` (line 1052, type: direct)

### src\database\database.py:Database.close

Calls:
- `close` (line 266, type: attribute)
- `info` (line 267, type: attribute)

### src\database\database.py:Database.connection

Calls:
- `RuntimeError` (line 279, type: direct)

### src\database\database.py:Database.create_file

Calls:
- `execute` (line 563, type: attribute)
- `fetchone` (line 564, type: attribute)
- `get` (line 569, type: attribute)
- `get` (line 570, type: attribute)
- `get` (line 571, type: attribute)
- `get` (line 572, type: attribute)
- `get` (line 576, type: attribute)
- `get` (line 578, type: attribute)
- `get` (line 582, type: attribute)
- `update_file` (line 585, type: attribute)
- `_execute_write` (line 588, type: attribute)
- `get` (line 595, type: attribute)
- `get` (line 597, type: attribute)
- `get` (line 598, type: attribute)
- `get` (line 599, type: attribute)
- `get` (line 600, type: attribute)
- `get` (line 601, type: attribute)
- `get` (line 602, type: attribute)
- `get` (line 603, type: attribute)
- `get` (line 604, type: attribute)
- `get` (line 605, type: attribute)
- `get` (line 606, type: attribute)
- `error` (line 610, type: attribute)
- `str` (line 610, type: direct)

### src\database\database.py:Database.create_idea

Calls:
- `_execute_write` (line 826, type: attribute)
- `get` (line 834, type: attribute)
- `get` (line 835, type: attribute)
- `get` (line 836, type: attribute)
- `get` (line 837, type: attribute)
- `get` (line 838, type: attribute)
- `get` (line 839, type: attribute)
- `get` (line 840, type: attribute)
- `get` (line 841, type: attribute)
- `get` (line 842, type: attribute)
- `get` (line 843, type: attribute)
- `get` (line 844, type: attribute)
- `get` (line 845, type: attribute)
- `get` (line 846, type: attribute)
- `error` (line 850, type: attribute)
- `str` (line 850, type: direct)

### src\database\database.py:Database.create_job

Calls:
- `_execute_write` (line 364, type: attribute)
- `get` (line 373, type: attribute)
- `get` (line 374, type: attribute)
- `get` (line 375, type: attribute)
- `get` (line 376, type: attribute)
- `get` (line 377, type: attribute)
- `error` (line 381, type: attribute)
- `str` (line 381, type: direct)

### src\database\database.py:Database.create_library_file

Calls:
- `_execute_write` (line 1105, type: attribute)
- `get` (line 1115, type: attribute)
- `get` (line 1120, type: attribute)
- `get` (line 1122, type: attribute)
- `get` (line 1123, type: attribute)
- `get` (line 1124, type: attribute)
- `get` (line 1125, type: attribute)
- `get` (line 1126, type: attribute)
- `error` (line 1130, type: attribute)
- `str` (line 1130, type: direct)

### src\database\database.py:Database.create_library_file_source

Calls:
- `_execute_write` (line 1293, type: attribute)
- `get` (line 1301, type: attribute)
- `get` (line 1302, type: attribute)
- `get` (line 1303, type: attribute)
- `get` (line 1304, type: attribute)
- `get` (line 1306, type: attribute)
- `get` (line 1307, type: attribute)
- `get` (line 1308, type: attribute)
- `error` (line 1312, type: attribute)
- `str` (line 1312, type: direct)

### src\database\database.py:Database.create_local_file

Calls:
- `create_file` (line 761, type: attribute)

### src\database\database.py:Database.create_printer

Calls:
- `_execute_write` (line 307, type: attribute)
- `get` (line 314, type: attribute)
- `get` (line 315, type: attribute)
- `get` (line 316, type: attribute)
- `get` (line 317, type: attribute)
- `get` (line 318, type: attribute)
- `error` (line 322, type: attribute)
- `str` (line 322, type: direct)

### src\database\database.py:Database.delete_idea

Calls:
- `_execute_write` (line 930, type: attribute)
- `_execute_write` (line 932, type: attribute)
- `error` (line 934, type: attribute)
- `str` (line 934, type: direct)

### src\database\database.py:Database.delete_job

Calls:
- `_execute_write` (line 548, type: attribute)
- `info` (line 550, type: attribute)
- `error` (line 553, type: attribute)
- `str` (line 553, type: direct)

### src\database\database.py:Database.delete_library_file

Calls:
- `_execute_write` (line 1165, type: attribute)

### src\database\database.py:Database.delete_library_file_sources

Calls:
- `_execute_write` (line 1325, type: attribute)

### src\database\database.py:Database.delete_local_file

Calls:
- `_execute_write` (line 785, type: attribute)
- `error` (line 787, type: attribute)
- `str` (line 787, type: direct)

### src\database\database.py:Database.get_all_tags

Calls:
- `_fetch_all` (line 986, type: attribute)
- `dict` (line 990, type: direct)
- `error` (line 992, type: attribute)
- `str` (line 992, type: direct)

### src\database\database.py:Database.get_connection

Calls:
- `RuntimeError` (line 272, type: direct)

### src\database\database.py:Database.get_file_statistics

Calls:
- `execute` (line 796, type: attribute)
- `fetchall` (line 797, type: attribute)
- `execute` (line 803, type: attribute)
- `fetchall` (line 804, type: attribute)
- `execute` (line 810, type: attribute)
- `fetchall` (line 811, type: attribute)
- `error` (line 819, type: attribute)
- `str` (line 819, type: direct)

### src\database\database.py:Database.get_idea

Calls:
- `_fetch_one` (line 856, type: attribute)
- `dict` (line 857, type: direct)
- `error` (line 859, type: attribute)
- `str` (line 859, type: direct)

### src\database\database.py:Database.get_idea_statistics

Calls:
- `_fetch_all` (line 1061, type: attribute)
- `_fetch_all` (line 1069, type: attribute)
- `_fetch_all` (line 1078, type: attribute)
- `_fetch_one` (line 1086, type: attribute)
- `_fetch_one` (line 1090, type: attribute)
- `round` (line 1091, type: direct)
- `error` (line 1095, type: attribute)
- `str` (line 1095, type: direct)

### src\database\database.py:Database.get_idea_tags

Calls:
- `_fetch_all` (line 974, type: attribute)
- `error` (line 980, type: attribute)
- `str` (line 980, type: direct)

### src\database\database.py:Database.get_job

Calls:
- `execute` (line 387, type: attribute)
- `fetchone` (line 390, type: attribute)
- `dict` (line 391, type: direct)
- `error` (line 393, type: attribute)
- `str` (line 393, type: direct)

### src\database\database.py:Database.get_job_statistics

Calls:
- `execute` (line 461, type: attribute)
- `fetchall` (line 466, type: attribute)
- `execute` (line 471, type: attribute)
- `fetchall` (line 476, type: attribute)
- `execute` (line 482, type: attribute)
- `fetchone` (line 495, type: attribute)
- `update` (line 497, type: attribute)
- `execute` (line 509, type: attribute)
- `fetchone` (line 510, type: attribute)
- `error` (line 516, type: attribute)
- `str` (line 516, type: direct)

### src\database\database.py:Database.get_jobs_by_date_range

Calls:
- `append` (line 444, type: attribute)
- `int` (line 444, type: direct)
- `execute` (line 448, type: attribute)
- `fetchall` (line 449, type: attribute)
- `dict` (line 450, type: direct)
- `error` (line 452, type: attribute)
- `str` (line 452, type: direct)

### src\database\database.py:Database.get_library_file

Calls:
- `_fetch_one` (line 1135, type: attribute)
- `dict` (line 1139, type: direct)

### src\database\database.py:Database.get_library_file_by_checksum

Calls:
- `_fetch_one` (line 1143, type: attribute)
- `dict` (line 1147, type: direct)

### src\database\database.py:Database.get_library_file_sources

Calls:
- `_fetch_all` (line 1317, type: attribute)
- `dict` (line 1321, type: direct)

### src\database\database.py:Database.get_library_stats

Calls:
- `_fetch_one` (line 1333, type: attribute)
- `dict` (line 1334, type: direct)
- `error` (line 1336, type: attribute)
- `str` (line 1336, type: direct)

### src\database\database.py:Database.get_printer

Calls:
- `_fetch_one` (line 328, type: attribute)
- `dict` (line 329, type: direct)
- `error` (line 331, type: attribute)
- `str` (line 331, type: direct)

### src\database\database.py:Database.get_trending

Calls:
- `append` (line 1031, type: attribute)
- `append` (line 1034, type: attribute)
- `_fetch_all` (line 1038, type: attribute)
- `dict` (line 1039, type: direct)
- `error` (line 1041, type: attribute)
- `str` (line 1041, type: direct)

### src\database\database.py:Database.health_check

Calls:
- `execute` (line 288, type: attribute)
- `fetchone` (line 289, type: attribute)
- `error` (line 292, type: attribute)
- `str` (line 292, type: direct)

### src\database\database.py:Database.initialize

Calls:
- `info` (line 33, type: attribute)
- `str` (line 33, type: direct)
- `connect` (line 35, type: attribute)
- `str` (line 35, type: direct)
- `_create_tables` (line 39, type: attribute)
- `_run_migrations` (line 42, type: attribute)
- `info` (line 44, type: attribute)

### src\database\database.py:Database.list_files

Calls:
- `append` (line 622, type: attribute)
- `append` (line 623, type: attribute)
- `append` (line 625, type: attribute)
- `append` (line 626, type: attribute)
- `append` (line 628, type: attribute)
- `append` (line 629, type: attribute)
- `join` (line 632, type: attribute)
- `execute` (line 636, type: attribute)
- `fetchall` (line 637, type: attribute)
- `dict` (line 640, type: direct)
- `get` (line 642, type: attribute)
- `isinstance` (line 642, type: direct)
- `loads` (line 644, type: attribute)
- `append` (line 648, type: attribute)
- `error` (line 651, type: attribute)
- `str` (line 651, type: direct)

### src\database\database.py:Database.list_ideas

Calls:
- `append` (line 872, type: attribute)
- `append` (line 873, type: attribute)
- `append` (line 875, type: attribute)
- `append` (line 876, type: attribute)
- `int` (line 876, type: direct)
- `append` (line 878, type: attribute)
- `append` (line 879, type: attribute)
- `append` (line 881, type: attribute)
- `append` (line 882, type: attribute)
- `join` (line 885, type: attribute)
- `append` (line 891, type: attribute)
- `append` (line 894, type: attribute)
- `_fetch_all` (line 896, type: attribute)
- `dict` (line 897, type: direct)
- `error` (line 899, type: attribute)
- `str` (line 899, type: direct)

### src\database\database.py:Database.list_jobs

Calls:
- `append` (line 406, type: attribute)
- `append` (line 407, type: attribute)
- `append` (line 409, type: attribute)
- `append` (line 410, type: attribute)
- `append` (line 412, type: attribute)
- `append` (line 413, type: attribute)
- `int` (line 413, type: direct)
- `join` (line 416, type: attribute)
- `append` (line 423, type: attribute)
- `append` (line 426, type: attribute)
- `execute` (line 428, type: attribute)
- `fetchall` (line 429, type: attribute)
- `dict` (line 430, type: direct)
- `error` (line 432, type: attribute)
- `str` (line 432, type: direct)

### src\database\database.py:Database.list_library_files

Calls:
- `get` (line 1182, type: attribute)
- `get` (line 1182, type: attribute)
- `get` (line 1188, type: attribute)
- `append` (line 1189, type: attribute)
- `append` (line 1190, type: attribute)
- `get` (line 1192, type: attribute)
- `append` (line 1193, type: attribute)
- `append` (line 1194, type: attribute)
- `get` (line 1196, type: attribute)
- `append` (line 1197, type: attribute)
- `append` (line 1198, type: attribute)
- `get` (line 1200, type: attribute)
- `append` (line 1201, type: attribute)
- `append` (line 1202, type: attribute)
- `lower` (line 1202, type: attribute)
- `get` (line 1204, type: attribute)
- `append` (line 1205, type: attribute)
- `append` (line 1206, type: attribute)
- `get` (line 1208, type: attribute)
- `append` (line 1209, type: attribute)
- `get` (line 1212, type: attribute)
- `append` (line 1213, type: attribute)
- `append` (line 1214, type: attribute)
- `get` (line 1216, type: attribute)
- `append` (line 1217, type: attribute)
- `append` (line 1218, type: attribute)
- `get` (line 1221, type: attribute)
- `append` (line 1222, type: attribute)
- `get` (line 1224, type: attribute)
- `append` (line 1225, type: attribute)
- `join` (line 1228, type: attribute)
- `copy` (line 1238, type: attribute)
- `copy` (line 1242, type: attribute)
- `_fetch_one` (line 1244, type: attribute)
- `extend` (line 1272, type: attribute)
- `_fetch_all` (line 1274, type: attribute)
- `dict` (line 1275, type: direct)
- `error` (line 1287, type: attribute)
- `str` (line 1287, type: direct)

### src\database\database.py:Database.list_local_files

Calls:
- `append` (line 771, type: attribute)
- `execute` (line 775, type: attribute)
- `fetchall` (line 776, type: attribute)
- `dict` (line 777, type: direct)
- `error` (line 779, type: attribute)
- `str` (line 779, type: direct)

### src\database\database.py:Database.list_printers

Calls:
- `_fetch_all` (line 341, type: attribute)
- `dict` (line 342, type: direct)
- `error` (line 344, type: attribute)
- `str` (line 344, type: direct)

### src\database\database.py:Database.remove_idea_tags

Calls:
- `_execute_write` (line 962, type: attribute)
- `error` (line 968, type: attribute)
- `str` (line 968, type: direct)

### src\database\database.py:Database.transaction

Calls:
- `RuntimeError` (line 299, type: direct)

### src\database\database.py:Database.update_file

Calls:
- `items` (line 661, type: attribute)
- `isinstance` (line 664, type: direct)
- `dumps` (line 665, type: attribute)
- `append` (line 667, type: attribute)
- `append` (line 668, type: attribute)
- `append` (line 673, type: attribute)
- `join` (line 674, type: attribute)
- `_execute_write` (line 676, type: attribute)
- `tuple` (line 676, type: direct)
- `error` (line 678, type: attribute)
- `str` (line 678, type: direct)

### src\database\database.py:Database.update_file_enhanced_metadata

Calls:
- `get` (line 694, type: attribute)
- `get` (line 695, type: attribute)
- `get` (line 696, type: attribute)
- `get` (line 697, type: attribute)
- `get` (line 698, type: attribute)
- `get` (line 699, type: attribute)
- `get` (line 704, type: attribute)
- `get` (line 705, type: attribute)
- `get` (line 706, type: attribute)
- `get` (line 707, type: attribute)
- `get` (line 708, type: attribute)
- `get` (line 709, type: attribute)
- `get` (line 712, type: attribute)
- `get` (line 713, type: attribute)
- `get` (line 714, type: attribute)
- `get` (line 715, type: attribute)
- `get` (line 716, type: attribute)
- `get` (line 719, type: attribute)
- `get` (line 720, type: attribute)
- `get` (line 721, type: attribute)
- `dumps` (line 721, type: attribute)
- `get` (line 721, type: attribute)
- `get` (line 724, type: attribute)
- `get` (line 725, type: attribute)
- `get` (line 726, type: attribute)
- `get` (line 729, type: attribute)
- `get` (line 730, type: attribute)
- `get` (line 731, type: attribute)
- `get` (line 734, type: attribute)
- `dumps` (line 734, type: attribute)
- `get` (line 734, type: attribute)
- `get` (line 735, type: attribute)
- `get` (line 736, type: attribute)
- `get` (line 737, type: attribute)
- `isinstance` (line 740, type: direct)
- `isoformat` (line 740, type: attribute)
- `items` (line 744, type: attribute)
- `update_file` (line 747, type: attribute)
- `error` (line 750, type: attribute)
- `str` (line 750, type: direct)
- `isinstance` (line 1347, type: direct)
- `isoformat` (line 1347, type: attribute)
- `keys` (line 1380, type: attribute)
- `join` (line 1381, type: attribute)
- `list` (line 1383, type: direct)
- `values` (line 1383, type: attribute)
- `_execute_write` (line 1384, type: attribute)
- `tuple` (line 1384, type: direct)
- `debug` (line 1387, type: attribute)
- `str` (line 1387, type: direct)
- `get_library_file` (line 1392, type: attribute)
- `update_library_file` (line 1394, type: attribute)
- `debug` (line 1397, type: attribute)
- `str` (line 1397, type: direct)

### src\database\database.py:Database.update_idea

Calls:
- `items` (line 908, type: attribute)
- `append` (line 910, type: attribute)
- `append` (line 911, type: attribute)
- `append` (line 916, type: attribute)
- `append` (line 917, type: attribute)
- `isoformat` (line 917, type: attribute)
- `now` (line 917, type: attribute)
- `append` (line 918, type: attribute)
- `join` (line 920, type: attribute)
- `_execute_write` (line 921, type: attribute)
- `tuple` (line 921, type: direct)
- `error` (line 923, type: attribute)
- `str` (line 923, type: direct)

### src\database\database.py:Database.update_idea_status

Calls:
- `isoformat` (line 941, type: attribute)
- `now` (line 941, type: attribute)
- `update_idea` (line 942, type: attribute)

### src\database\database.py:Database.update_job

Calls:
- `items` (line 526, type: attribute)
- `append` (line 528, type: attribute)
- `append` (line 529, type: attribute)
- `append` (line 534, type: attribute)
- `append` (line 535, type: attribute)
- `isoformat` (line 535, type: attribute)
- `now` (line 535, type: attribute)
- `append` (line 536, type: attribute)
- `join` (line 538, type: attribute)
- `_execute_write` (line 540, type: attribute)
- `tuple` (line 540, type: direct)
- `error` (line 542, type: attribute)
- `str` (line 542, type: direct)

### src\database\database.py:Database.update_library_file

Calls:
- `keys` (line 1155, type: attribute)
- `join` (line 1156, type: attribute)
- `list` (line 1159, type: direct)
- `values` (line 1159, type: attribute)
- `_execute_write` (line 1161, type: attribute)
- `tuple` (line 1161, type: direct)

### src\database\database.py:Database.update_printer_status

Calls:
- `now` (line 351, type: attribute)
- `_execute_write` (line 352, type: attribute)
- `isoformat` (line 354, type: attribute)
- `error` (line 357, type: attribute)
- `str` (line 357, type: direct)

### src\database\database.py:Database.upsert_trending

Calls:
- `_execute_write` (line 999, type: attribute)
- `get` (line 1010, type: attribute)
- `get` (line 1011, type: attribute)
- `get` (line 1012, type: attribute)
- `get` (line 1013, type: attribute)
- `get` (line 1014, type: attribute)
- `get` (line 1015, type: attribute)
- `error` (line 1020, type: attribute)
- `str` (line 1020, type: direct)

### src\main.py:_on_printer_status_update

Calls:
- `broadcast_printer_status` (line 147, type: direct)
- `get` (line 148, type: attribute)
- `warning` (line 152, type: attribute)
- `str` (line 152, type: direct)

### src\main.py:create_application

Calls:
- `Settings` (line 272, type: direct)
- `FastAPI` (line 274, type: direct)
- `getenv` (line 278, type: attribute)
- `getenv` (line 279, type: attribute)
- `get_cors_origins` (line 284, type: attribute)
- `extend` (line 287, type: attribute)
- `add_middleware` (line 296, type: attribute)
- `add_middleware` (line 305, type: attribute)
- `add_middleware` (line 306, type: attribute)
- `add_middleware` (line 307, type: attribute)
- `include_router` (line 310, type: attribute)
- `include_router` (line 311, type: attribute)
- `include_router` (line 312, type: attribute)
- `include_router` (line 313, type: attribute)
- `include_router` (line 314, type: attribute)
- `include_router` (line 315, type: attribute)
- `include_router` (line 316, type: attribute)
- `include_router` (line 317, type: attribute)
- `include_router` (line 318, type: attribute)
- `include_router` (line 319, type: attribute)
- `include_router` (line 320, type: attribute)
- `include_router` (line 321, type: attribute)
- `include_router` (line 322, type: attribute)
- `include_router` (line 323, type: attribute)
- `include_router` (line 325, type: attribute)
- `Path` (line 328, type: direct)
- `exists` (line 329, type: attribute)
- `mount` (line 330, type: attribute)
- `StaticFiles` (line 330, type: direct)
- `str` (line 330, type: direct)

### src\main.py:general_exception_handler

Calls:
- `get_logger` (line 380, type: attribute)
- `error` (line 381, type: attribute)
- `str` (line 381, type: direct)
- `JSONResponse` (line 383, type: direct)
- `exception_handler` (line 378, type: attribute)

### src\main.py:lifespan

Calls:
- `setup_logging` (line 91, type: direct)
- `get_logger` (line 92, type: attribute)
- `info` (line 93, type: attribute)
- `Database` (line 96, type: direct)
- `initialize` (line 97, type: attribute)
- `MigrationService` (line 101, type: direct)
- `run_migrations` (line 102, type: attribute)
- `ConfigService` (line 106, type: direct)
- `EventService` (line 107, type: direct)
- `PrinterService` (line 108, type: direct)
- `LibraryService` (line 112, type: direct)
- `initialize` (line 113, type: attribute)
- `FileWatcherService` (line 116, type: direct)
- `FileService` (line 119, type: direct)
- `ThumbnailService` (line 125, type: direct)
- `UrlParserService` (line 126, type: direct)
- `TrendingService` (line 127, type: direct)
- `start` (line 140, type: attribute)
- `initialize` (line 141, type: attribute)
- `subscribe` (line 154, type: attribute)
- `initialize` (line 157, type: attribute)
- `start_monitoring` (line 161, type: attribute)
- `info` (line 162, type: attribute)
- `warning` (line 164, type: attribute)
- `str` (line 164, type: direct)
- `start` (line 168, type: attribute)
- `info` (line 169, type: attribute)
- `warning` (line 171, type: attribute)
- `str` (line 171, type: direct)
- `info` (line 173, type: attribute)
- `info` (line 178, type: attribute)
- `hasattr` (line 195, type: direct)
- `append` (line 196, type: attribute)
- `shutdown_with_timeout` (line 197, type: direct)
- `shutdown` (line 198, type: attribute)
- `hasattr` (line 205, type: direct)
- `append` (line 206, type: attribute)
- `shutdown_with_timeout` (line 207, type: direct)
- `stop` (line 208, type: attribute)
- `hasattr` (line 215, type: direct)
- `append` (line 216, type: attribute)
- `shutdown_with_timeout` (line 217, type: direct)
- `cleanup` (line 218, type: attribute)
- `hasattr` (line 225, type: direct)
- `append` (line 226, type: attribute)
- `shutdown_with_timeout` (line 227, type: direct)
- `cleanup` (line 228, type: attribute)
- `hasattr` (line 235, type: direct)
- `append` (line 236, type: attribute)
- `shutdown_with_timeout` (line 237, type: direct)
- `close` (line 238, type: attribute)
- `gather` (line 246, type: attribute)
- `hasattr` (line 249, type: direct)
- `shutdown_with_timeout` (line 250, type: direct)
- `stop` (line 251, type: attribute)
- `hasattr` (line 257, type: direct)
- `shutdown_with_timeout` (line 258, type: direct)
- `close` (line 259, type: attribute)
- `info` (line 264, type: attribute)

### src\main.py:metrics

Calls:
- `Response` (line 346, type: direct)
- `generate_latest` (line 346, type: direct)
- `get` (line 343, type: attribute)

### src\main.py:printernizer_exception_handler

Calls:
- `get_logger` (line 351, type: attribute)
- `error` (line 352, type: attribute)
- `str` (line 352, type: direct)
- `JSONResponse` (line 354, type: direct)
- `isoformat` (line 360, type: attribute)
- `exception_handler` (line 349, type: attribute)

### src\main.py:read_debug

Calls:
- `FileResponse` (line 340, type: direct)
- `str` (line 340, type: direct)
- `get` (line 337, type: attribute)

### src\main.py:read_index

Calls:
- `FileResponse` (line 335, type: direct)
- `str` (line 335, type: direct)
- `get` (line 332, type: attribute)

### src\main.py:setup_signal_handlers

Calls:
- `signal` (line 402, type: attribute)
- `signal` (line 403, type: attribute)

### src\main.py:shutdown_with_timeout

Calls:
- `wait_for` (line 184, type: attribute)
- `info` (line 185, type: attribute)
- `warning` (line 187, type: attribute)
- `warning` (line 189, type: attribute)
- `str` (line 189, type: direct)

### src\main.py:signal_handler

Calls:
- `get_logger` (line 398, type: attribute)
- `info` (line 399, type: attribute)
- `exit` (line 400, type: attribute)

### src\main.py:validation_exception_handler

Calls:
- `get_logger` (line 366, type: attribute)
- `warning` (line 367, type: attribute)
- `errors` (line 367, type: attribute)
- `JSONResponse` (line 369, type: direct)
- `errors` (line 374, type: attribute)
- `exception_handler` (line 364, type: attribute)

### src\models\idea.py:Idea.from_dict

Calls:
- `cls` (line 76, type: direct)
- `get` (line 79, type: attribute)
- `get` (line 80, type: attribute)
- `get` (line 81, type: attribute)
- `get` (line 82, type: attribute)
- `get` (line 83, type: attribute)
- `get` (line 84, type: attribute)
- `get` (line 85, type: attribute)
- `get` (line 86, type: attribute)
- `get` (line 87, type: attribute)
- `get` (line 88, type: attribute)
- `get` (line 89, type: attribute)
- `get` (line 90, type: attribute)
- `get` (line 91, type: attribute)
- `get` (line 92, type: attribute)
- `get` (line 93, type: attribute)
- `get` (line 94, type: attribute)
- `get` (line 95, type: attribute)

### src\models\idea.py:TrendingItem.from_dict

Calls:
- `cls` (line 159, type: direct)
- `get` (line 165, type: attribute)
- `get` (line 166, type: attribute)
- `get` (line 167, type: attribute)
- `get` (line 168, type: attribute)
- `get` (line 169, type: attribute)
- `get` (line 170, type: attribute)
- `get` (line 171, type: attribute)

### src\models\idea.py:TrendingItem.is_expired

Calls:
- `fromisoformat` (line 179, type: attribute)
- `now` (line 180, type: attribute)

### src\models\job.py:Job.convert_progress_to_int

Calls:
- `isinstance` (line 47, type: direct)
- `int` (line 48, type: direct)
- `field_validator` (line 44, type: direct)

### src\models\material.py:MaterialCreate.validate_remaining

Calls:
- `ValueError` (line 119, type: direct)
- `field_validator` (line 115, type: direct)

### src\models\material.py:MaterialSpool.remaining_value

Calls:
- `Decimal` (line 96, type: direct)
- `str` (line 96, type: direct)

### src\models\material.py:MaterialSpool.total_cost

Calls:
- `Decimal` (line 91, type: direct)
- `str` (line 91, type: direct)

### src\models\watch_folder.py:WatchFolder.from_db_row

Calls:
- `cls` (line 89, type: direct)
- `bool` (line 92, type: direct)
- `bool` (line 93, type: direct)
- `int` (line 96, type: direct)
- `fromisoformat` (line 97, type: attribute)
- `bool` (line 98, type: direct)
- `fromisoformat` (line 100, type: attribute)
- `WatchFolderSource` (line 101, type: direct)
- `fromisoformat` (line 102, type: attribute)
- `fromisoformat` (line 103, type: attribute)

### src\models\watch_folder.py:WatchFolder.from_dict

Calls:
- `cls` (line 69, type: direct)
- `get` (line 70, type: attribute)
- `get` (line 71, type: attribute)
- `bool` (line 72, type: direct)
- `get` (line 72, type: attribute)
- `bool` (line 73, type: direct)
- `get` (line 73, type: attribute)
- `get` (line 74, type: attribute)
- `get` (line 75, type: attribute)
- `int` (line 76, type: direct)
- `get` (line 76, type: attribute)
- `get` (line 77, type: attribute)
- `fromisoformat` (line 77, type: attribute)
- `bool` (line 78, type: direct)
- `get` (line 78, type: attribute)
- `get` (line 79, type: attribute)
- `get` (line 80, type: attribute)
- `fromisoformat` (line 80, type: attribute)
- `WatchFolderSource` (line 81, type: direct)
- `get` (line 81, type: attribute)
- `get` (line 82, type: attribute)
- `fromisoformat` (line 82, type: attribute)
- `get` (line 83, type: attribute)
- `fromisoformat` (line 83, type: attribute)

### src\models\watch_folder.py:WatchFolder.get_display_name

Calls:
- `basename` (line 113, type: attribute)

### src\models\watch_folder.py:WatchFolder.is_accessible

Calls:
- `exists` (line 118, type: attribute)
- `isdir` (line 118, type: attribute)

### src\models\watch_folder.py:WatchFolder.to_dict

Calls:
- `isoformat` (line 57, type: attribute)
- `isoformat` (line 60, type: attribute)
- `isoformat` (line 62, type: attribute)
- `isoformat` (line 63, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter.__init__

Calls:
- `__init__` (line 42, type: attribute)
- `super` (line 42, type: direct)
- `info` (line 47, type: attribute)
- `warning` (line 50, type: attribute)
- `ImportError` (line 52, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._connect_bambu_api

Calls:
- `info` (line 135, type: attribute)
- `BambuClient` (line 139, type: direct)
- `connect` (line 150, type: attribute)
- `hasattr` (line 153, type: direct)
- `request_status` (line 154, type: attribute)
- `hasattr` (line 157, type: direct)
- `request_file_list` (line 158, type: attribute)
- `info` (line 161, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._connect_mqtt

Calls:
- `info` (line 167, type: attribute)
- `Client` (line 171, type: attribute)
- `username_pw_set` (line 172, type: attribute)
- `create_default_context` (line 175, type: attribute)
- `tls_set_context` (line 178, type: attribute)
- `connect` (line 186, type: attribute)
- `ConnectionError` (line 188, type: direct)
- `loop_start` (line 191, type: attribute)
- `sleep` (line 194, type: attribute)
- `info` (line 197, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._discover_files_via_ftp

Calls:
- `hasattr` (line 950, type: direct)
- `hasattr` (line 961, type: direct)
- `list_images_dir` (line 963, type: attribute)
- `endswith` (line 965, type: attribute)
- `lower` (line 965, type: attribute)
- `replace` (line 967, type: attribute)
- `replace` (line 967, type: attribute)
- `append` (line 971, type: attribute)
- `PrinterFile` (line 971, type: direct)
- `debug` (line 979, type: attribute)
- `str` (line 979, type: direct)
- `hasattr` (line 982, type: direct)
- `list_cache_dir` (line 984, type: attribute)
- `isinstance` (line 989, type: direct)
- `split` (line 991, type: attribute)
- `strip` (line 991, type: attribute)
- `len` (line 992, type: direct)
- `join` (line 993, type: attribute)
- `int` (line 996, type: direct)
- `str` (line 1002, type: direct)
- `any` (line 1004, type: direct)
- `endswith` (line 1004, type: attribute)
- `lower` (line 1004, type: attribute)
- `append` (line 1005, type: attribute)
- `PrinterFile` (line 1005, type: direct)
- `_get_file_type_from_name` (line 1010, type: attribute)
- `debug` (line 1013, type: attribute)
- `str` (line 1013, type: direct)
- `debug` (line 1016, type: attribute)
- `str` (line 1016, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._discover_files_via_mqtt_dump

Calls:
- `hasattr` (line 1025, type: direct)
- `mqtt_dump` (line 1026, type: attribute)
- `isinstance` (line 1029, type: direct)
- `isinstance` (line 1033, type: direct)
- `isinstance` (line 1037, type: direct)
- `append` (line 1038, type: attribute)
- `PrinterFile` (line 1038, type: direct)
- `_get_file_type_from_name` (line 1043, type: attribute)
- `isinstance` (line 1049, type: direct)
- `any` (line 1051, type: direct)
- `endswith` (line 1051, type: attribute)
- `lower` (line 1051, type: attribute)
- `append` (line 1053, type: attribute)
- `PrinterFile` (line 1053, type: direct)
- `_get_file_type_from_name` (line 1058, type: attribute)
- `isinstance` (line 1064, type: direct)
- `isinstance` (line 1069, type: direct)
- `isinstance` (line 1071, type: direct)
- `isinstance` (line 1073, type: direct)
- `append` (line 1075, type: attribute)
- `PrinterFile` (line 1075, type: direct)
- `get` (line 1077, type: attribute)
- `_get_file_type_from_name` (line 1080, type: attribute)
- `debug` (line 1084, type: attribute)
- `str` (line 1084, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._download_file_bambu_api

Calls:
- `PrinterConnectionError` (line 1321, type: direct)
- `info` (line 1323, type: attribute)
- `hasattr` (line 1327, type: direct)
- `mkdir` (line 1333, type: attribute)
- `Path` (line 1333, type: direct)
- `debug` (line 1335, type: attribute)
- `download_file` (line 1339, type: attribute)
- `getvalue` (line 1342, type: attribute)
- `len` (line 1343, type: direct)
- `open` (line 1345, type: direct)
- `write` (line 1346, type: attribute)
- `info` (line 1348, type: attribute)
- `len` (line 1351, type: direct)
- `debug` (line 1354, type: attribute)
- `debug` (line 1357, type: attribute)
- `debug` (line 1361, type: attribute)
- `str` (line 1362, type: direct)
- `_download_via_http` (line 1366, type: attribute)
- `info` (line 1368, type: attribute)
- `warning` (line 1372, type: attribute)
- `str` (line 1373, type: direct)
- `warning` (line 1375, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._download_file_direct_ftp

Calls:
- `warning` (line 1258, type: attribute)
- `_download_file_bambu_api` (line 1260, type: attribute)
- `info` (line 1262, type: attribute)
- `download_file` (line 1267, type: attribute)
- `info` (line 1270, type: attribute)
- `warning` (line 1274, type: attribute)
- `_download_file_bambu_api` (line 1277, type: attribute)
- `error` (line 1280, type: attribute)
- `str` (line 1281, type: direct)
- `_download_file_bambu_api` (line 1283, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._download_file_mqtt

Calls:
- `warning` (line 1382, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._download_via_ftp

Calls:
- `mkdir` (line 1393, type: attribute)
- `Path` (line 1393, type: direct)
- `debug` (line 1405, type: attribute)
- `download_file` (line 1411, type: attribute)
- `getvalue` (line 1415, type: attribute)
- `len` (line 1417, type: direct)
- `open` (line 1419, type: direct)
- `write` (line 1420, type: attribute)
- `info` (line 1422, type: attribute)
- `len` (line 1426, type: direct)
- `debug` (line 1429, type: attribute)
- `debug` (line 1434, type: attribute)
- `str` (line 1437, type: direct)
- `debug` (line 1442, type: attribute)
- `lower` (line 1459, type: attribute)
- `_safe_list` (line 1464, type: direct)
- `_safe_list` (line 1464, type: direct)
- `isinstance` (line 1469, type: direct)
- `get` (line 1470, type: attribute)
- `get` (line 1470, type: attribute)
- `get` (line 1471, type: attribute)
- `str` (line 1473, type: direct)
- `append` (line 1477, type: attribute)
- `debug` (line 1479, type: attribute)
- `str` (line 1479, type: direct)
- `next` (line 1483, type: direct)
- `lower` (line 1483, type: attribute)
- `startswith` (line 1486, type: attribute)
- `debug` (line 1488, type: attribute)
- `download_file` (line 1489, type: attribute)
- `getvalue` (line 1491, type: attribute)
- `open` (line 1493, type: direct)
- `write` (line 1494, type: attribute)
- `info` (line 1495, type: attribute)
- `len` (line 1495, type: direct)
- `debug` (line 1498, type: attribute)
- `str` (line 1498, type: direct)
- `rsplit` (line 1501, type: attribute)
- `lower` (line 1504, type: attribute)
- `append` (line 1506, type: attribute)
- `sort` (line 1519, type: attribute)
- `startswith` (line 1522, type: attribute)
- `debug` (line 1524, type: attribute)
- `download_file` (line 1525, type: attribute)
- `getvalue` (line 1527, type: attribute)
- `open` (line 1529, type: direct)
- `write` (line 1530, type: attribute)
- `info` (line 1531, type: attribute)
- `len` (line 1531, type: direct)
- `debug` (line 1534, type: attribute)
- `str` (line 1534, type: direct)
- `split` (line 1538, type: attribute)
- `lower` (line 1538, type: attribute)
- `warning` (line 1539, type: attribute)
- `warning` (line 1541, type: attribute)
- `debug` (line 1543, type: attribute)
- `str` (line 1543, type: direct)
- `warning` (line 1545, type: attribute)
- `error` (line 1550, type: attribute)
- `str` (line 1551, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._download_via_http

Calls:
- `mkdir` (line 1561, type: attribute)
- `Path` (line 1561, type: direct)
- `ClientTimeout` (line 1573, type: attribute)
- `ClientSession` (line 1575, type: attribute)
- `debug` (line 1578, type: attribute)
- `hasattr` (line 1583, type: direct)
- `BasicAuth` (line 1584, type: attribute)
- `get` (line 1586, type: attribute)
- `get` (line 1589, type: attribute)
- `int` (line 1590, type: direct)
- `open` (line 1593, type: direct)
- `iter_chunked` (line 1594, type: attribute)
- `write` (line 1595, type: attribute)
- `len` (line 1596, type: direct)
- `debug` (line 1601, type: attribute)
- `info` (line 1606, type: attribute)
- `debug` (line 1614, type: attribute)
- `debug` (line 1617, type: attribute)
- `debug` (line 1620, type: attribute)
- `debug` (line 1625, type: attribute)
- `str` (line 1626, type: direct)
- `debug` (line 1629, type: attribute)
- `str` (line 1630, type: direct)
- `warning` (line 1633, type: attribute)
- `error` (line 1638, type: attribute)
- `str` (line 1639, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._get_file_type_from_name

Calls:
- `lower` (line 1288, type: attribute)
- `Path` (line 1288, type: direct)
- `get` (line 1297, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._get_status_bambu_api

Calls:
- `PrinterConnectionError` (line 286, type: direct)
- `get_current_state` (line 290, type: attribute)
- `debug` (line 294, type: attribute)
- `str` (line 295, type: direct)
- `type` (line 300, type: direct)
- `hasattr` (line 303, type: direct)
- `get_state` (line 305, type: attribute)
- `get_bed_temperature` (line 312, type: attribute)
- `get_nozzle_temperature` (line 313, type: attribute)
- `get_percentage` (line 320, type: attribute)
- `hasattr` (line 328, type: direct)
- `getattr` (line 329, type: direct)
- `method` (line 330, type: direct)
- `isinstance` (line 331, type: direct)
- `strip` (line 331, type: attribute)
- `strip` (line 332, type: attribute)
- `hasattr` (line 334, type: direct)
- `hasattr` (line 340, type: direct)
- `hasattr` (line 342, type: direct)
- `info` (line 345, type: attribute)
- `debug` (line 353, type: attribute)
- `str` (line 354, type: direct)
- `PrinterStatusUpdate` (line 358, type: direct)
- `now` (line 363, type: attribute)
- `getattr` (line 368, type: direct)
- `getattr` (line 369, type: direct)
- `_map_bambu_status` (line 372, type: attribute)
- `hasattr` (line 385, type: direct)
- `mqtt_dump` (line 386, type: attribute)
- `isinstance` (line 387, type: direct)
- `isinstance` (line 389, type: direct)
- `float` (line 391, type: direct)
- `get` (line 391, type: attribute)
- `float` (line 392, type: direct)
- `get` (line 392, type: attribute)
- `int` (line 395, type: direct)
- `get` (line 395, type: attribute)
- `int` (line 401, type: direct)
- `int` (line 409, type: direct)
- `now` (line 414, type: attribute)
- `timedelta` (line 414, type: direct)
- `debug` (line 417, type: attribute)
- `list` (line 422, type: direct)
- `keys` (line 422, type: attribute)
- `hasattr` (line 425, type: direct)
- `float` (line 426, type: direct)
- `get_bed_temperature` (line 426, type: attribute)
- `hasattr` (line 428, type: direct)
- `float` (line 429, type: direct)
- `get_nozzle_temperature` (line 429, type: attribute)
- `hasattr` (line 431, type: direct)
- `int` (line 432, type: direct)
- `get_percentage` (line 432, type: attribute)
- `hasattr` (line 435, type: direct)
- `int` (line 436, type: direct)
- `current_layer_num` (line 436, type: attribute)
- `hasattr` (line 439, type: direct)
- `subtask_name` (line 440, type: attribute)
- `isinstance` (line 441, type: direct)
- `strip` (line 441, type: attribute)
- `strip` (line 442, type: attribute)
- `hasattr` (line 444, type: direct)
- `gcode_file` (line 445, type: attribute)
- `isinstance` (line 446, type: direct)
- `strip` (line 446, type: attribute)
- `strip` (line 447, type: attribute)
- `startswith` (line 449, type: attribute)
- `debug` (line 453, type: attribute)
- `str` (line 454, type: direct)
- `getattr` (line 457, type: direct)
- `getattr` (line 458, type: direct)
- `getattr` (line 459, type: direct)
- `getattr` (line 460, type: direct)
- `_map_bambu_status` (line 503, type: attribute)
- `startswith` (line 521, type: attribute)
- `find_file_by_name` (line 524, type: attribute)
- `get` (line 526, type: attribute)
- `get` (line 527, type: attribute)
- `debug` (line 528, type: attribute)
- `debug` (line 534, type: attribute)
- `str` (line 537, type: direct)
- `debug` (line 546, type: attribute)
- `PrinterStatusUpdate` (line 554, type: direct)
- `float` (line 558, type: direct)
- `float` (line 559, type: direct)
- `int` (line 560, type: direct)
- `now` (line 567, type: attribute)
- `hasattr` (line 568, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._get_status_mqtt

Calls:
- `PrinterConnectionError` (line 574, type: direct)
- `get` (line 577, type: attribute)
- `get` (line 580, type: attribute)
- `get` (line 581, type: attribute)
- `get` (line 582, type: attribute)
- `get` (line 583, type: attribute)
- `int` (line 592, type: direct)
- `now` (line 597, type: attribute)
- `timedelta` (line 597, type: direct)
- `get` (line 622, type: attribute)
- `hasattr` (line 625, type: direct)
- `hasattr` (line 630, type: direct)
- `getattr` (line 631, type: direct)
- `method` (line 632, type: direct)
- `isinstance` (line 633, type: direct)
- `strip` (line 633, type: attribute)
- `strip` (line 634, type: attribute)
- `startswith` (line 636, type: attribute)
- `debug` (line 638, type: attribute)
- `debug` (line 641, type: attribute)
- `startswith` (line 654, type: attribute)
- `find_file_by_name` (line 657, type: attribute)
- `get` (line 659, type: attribute)
- `get` (line 660, type: attribute)
- `debug` (line 661, type: attribute)
- `debug` (line 667, type: attribute)
- `str` (line 670, type: direct)
- `debug` (line 676, type: attribute)
- `PrinterStatusUpdate` (line 683, type: direct)
- `float` (line 687, type: direct)
- `float` (line 688, type: direct)
- `int` (line 689, type: direct)
- `now` (line 696, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._list_files_bambu_api

Calls:
- `PrinterConnectionError` (line 862, type: direct)
- `info` (line 864, type: attribute)
- `hasattr` (line 871, type: direct)
- `hasattr` (line 872, type: direct)
- `now` (line 873, type: attribute)
- `info` (line 874, type: attribute)
- `len` (line 875, type: direct)
- `hasattr` (line 879, type: direct)
- `get_files` (line 881, type: attribute)
- `append` (line 884, type: attribute)
- `PrinterFile` (line 884, type: direct)
- `get` (line 885, type: attribute)
- `get` (line 886, type: attribute)
- `get` (line 887, type: attribute)
- `_get_file_type_from_name` (line 889, type: attribute)
- `get` (line 889, type: attribute)
- `info` (line 891, type: attribute)
- `len` (line 892, type: direct)
- `debug` (line 895, type: attribute)
- `str` (line 896, type: direct)
- `hasattr` (line 899, type: direct)
- `_discover_files_via_ftp` (line 901, type: attribute)
- `extend` (line 902, type: attribute)
- `debug` (line 904, type: attribute)
- `str` (line 905, type: direct)
- `len` (line 908, type: direct)
- `_discover_files_via_mqtt_dump` (line 910, type: attribute)
- `extend` (line 911, type: attribute)
- `debug` (line 913, type: attribute)
- `str` (line 914, type: direct)
- `hasattr` (line 917, type: direct)
- `append` (line 921, type: attribute)
- `PrinterFile` (line 921, type: direct)
- `_get_file_type_from_name` (line 926, type: attribute)
- `debug` (line 929, type: attribute)
- `str` (line 930, type: direct)
- `warning` (line 933, type: attribute)
- `str` (line 934, type: direct)
- `len` (line 937, type: direct)
- `info` (line 938, type: attribute)
- `info` (line 941, type: attribute)
- `len` (line 942, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._list_files_direct_ftp

Calls:
- `PrinterConnectionError` (line 1223, type: direct)
- `info` (line 1225, type: attribute)
- `list_files` (line 1230, type: attribute)
- `PrinterFile` (line 1235, type: direct)
- `append` (line 1242, type: attribute)
- `info` (line 1244, type: attribute)
- `len` (line 1246, type: direct)
- `error` (line 1251, type: attribute)
- `str` (line 1252, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._list_files_mqtt

Calls:
- `_list_files_mqtt_from_bambu_api` (line 1092, type: attribute)
- `PrinterConnectionError` (line 1096, type: direct)
- `info` (line 1098, type: attribute)
- `isinstance` (line 1105, type: direct)
- `get` (line 1107, type: attribute)
- `isinstance` (line 1108, type: direct)
- `get` (line 1110, type: attribute)
- `isinstance` (line 1111, type: direct)
- `append` (line 1112, type: attribute)
- `PrinterFile` (line 1112, type: direct)
- `_get_file_type_from_name` (line 1117, type: attribute)
- `get` (line 1121, type: attribute)
- `isinstance` (line 1122, type: direct)
- `any` (line 1125, type: direct)
- `endswith` (line 1125, type: attribute)
- `lower` (line 1125, type: attribute)
- `append` (line 1127, type: attribute)
- `PrinterFile` (line 1127, type: direct)
- `_get_file_type_from_name` (line 1132, type: attribute)
- `isinstance` (line 1141, type: direct)
- `items` (line 1143, type: attribute)
- `isinstance` (line 1144, type: direct)
- `any` (line 1145, type: direct)
- `endswith` (line 1145, type: attribute)
- `lower` (line 1145, type: attribute)
- `append` (line 1147, type: attribute)
- `PrinterFile` (line 1147, type: direct)
- `_get_file_type_from_name` (line 1152, type: attribute)
- `len` (line 1156, type: direct)
- `info` (line 1157, type: attribute)
- `debug` (line 1159, type: attribute)
- `list` (line 1159, type: direct)
- `keys` (line 1159, type: attribute)
- `info` (line 1161, type: attribute)
- `len` (line 1162, type: direct)
- `warning` (line 1165, type: attribute)
- `str` (line 1166, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._list_files_mqtt_from_bambu_api

Calls:
- `hasattr` (line 1176, type: direct)
- `mqtt_dump` (line 1177, type: attribute)
- `isinstance` (line 1179, type: direct)
- `isinstance` (line 1183, type: direct)
- `isinstance` (line 1187, type: direct)
- `append` (line 1188, type: attribute)
- `PrinterFile` (line 1188, type: direct)
- `_get_file_type_from_name` (line 1193, type: attribute)
- `isinstance` (line 1199, type: direct)
- `any` (line 1201, type: direct)
- `endswith` (line 1201, type: attribute)
- `lower` (line 1201, type: attribute)
- `append` (line 1203, type: attribute)
- `PrinterFile` (line 1203, type: direct)
- `_get_file_type_from_name` (line 1208, type: attribute)
- `info` (line 1211, type: attribute)
- `len` (line 1212, type: direct)
- `debug` (line 1215, type: attribute)
- `str` (line 1216, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._map_bambu_status

Calls:
- `hasattr` (line 703, type: direct)
- `str` (line 706, type: direct)
- `get` (line 748, type: attribute)
- `upper` (line 748, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._map_job_status

Calls:
- `hasattr` (line 794, type: direct)
- `str` (line 797, type: direct)
- `get` (line 838, type: attribute)
- `upper` (line 838, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._on_bambu_file_list_update

Calls:
- `isinstance` (line 211, type: direct)
- `isinstance` (line 213, type: direct)
- `isinstance` (line 215, type: direct)
- `get` (line 216, type: attribute)
- `append` (line 218, type: attribute)
- `PrinterFile` (line 218, type: direct)
- `get` (line 220, type: attribute)
- `get` (line 221, type: attribute)
- `_get_file_type_from_name` (line 223, type: attribute)
- `now` (line 227, type: attribute)
- `info` (line 229, type: attribute)
- `len` (line 230, type: direct)
- `warning` (line 233, type: attribute)
- `str` (line 234, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._on_bambu_status_update

Calls:
- `debug` (line 205, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._on_connect

Calls:
- `info` (line 77, type: attribute)
- `subscribe` (line 80, type: attribute)
- `debug` (line 81, type: attribute)
- `error` (line 83, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._on_disconnect

Calls:
- `info` (line 96, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter._on_message

Calls:
- `loads` (line 88, type: attribute)
- `decode` (line 88, type: attribute)
- `debug` (line 90, type: attribute)
- `warning` (line 92, type: attribute)
- `str` (line 92, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter._safe_list

Calls:
- `hasattr` (line 1450, type: direct)
- `getattr` (line 1452, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.connect

Calls:
- `info` (line 101, type: attribute)
- `BambuFTPService` (line 108, type: direct)
- `test_connection` (line 110, type: attribute)
- `info` (line 112, type: attribute)
- `warning` (line 115, type: attribute)
- `warning` (line 119, type: attribute)
- `str` (line 120, type: direct)
- `_connect_bambu_api` (line 124, type: attribute)
- `_connect_mqtt` (line 126, type: attribute)
- `error` (line 129, type: attribute)
- `str` (line 130, type: direct)
- `PrinterConnectionError` (line 131, type: direct)
- `str` (line 131, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.disconnect

Calls:
- `disconnect` (line 243, type: attribute)
- `loop_stop` (line 247, type: attribute)
- `disconnect` (line 248, type: attribute)
- `info` (line 253, type: attribute)
- `error` (line 256, type: attribute)
- `str` (line 257, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.download_file

Calls:
- `PrinterConnectionError` (line 1302, type: direct)
- `_download_file_direct_ftp` (line 1307, type: attribute)
- `_download_file_bambu_api` (line 1309, type: attribute)
- `_download_file_mqtt` (line 1311, type: attribute)
- `error` (line 1314, type: attribute)
- `str` (line 1315, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.get_camera_stream_url

Calls:
- `warning` (line 1728, type: attribute)
- `debug` (line 1737, type: attribute)
- `error` (line 1742, type: attribute)
- `str` (line 1743, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.get_job_info

Calls:
- `get` (line 756, type: attribute)
- `get` (line 757, type: attribute)
- `get` (line 764, type: attribute)
- `strftime` (line 764, type: attribute)
- `now` (line 764, type: attribute)
- `get` (line 765, type: attribute)
- `get` (line 768, type: attribute)
- `JobInfo` (line 776, type: direct)
- `strftime` (line 777, type: attribute)
- `now` (line 777, type: attribute)
- `error` (line 787, type: attribute)
- `str` (line 788, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.get_status

Calls:
- `PrinterConnectionError` (line 265, type: direct)
- `_get_status_bambu_api` (line 269, type: attribute)
- `_get_status_mqtt` (line 271, type: attribute)
- `error` (line 274, type: attribute)
- `str` (line 275, type: direct)
- `PrinterStatusUpdate` (line 276, type: direct)
- `str` (line 279, type: direct)
- `now` (line 280, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter.has_camera

Calls:
- `get_camera_stream_url` (line 1719, type: attribute)
- `debug` (line 1722, type: attribute)
- `str` (line 1722, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.list_files

Calls:
- `PrinterConnectionError` (line 843, type: direct)
- `_list_files_direct_ftp` (line 848, type: attribute)
- `_list_files_bambu_api` (line 850, type: attribute)
- `_list_files_mqtt` (line 852, type: attribute)
- `error` (line 855, type: attribute)
- `str` (line 856, type: direct)
- `PrinterConnectionError` (line 857, type: direct)
- `str` (line 857, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.pause_print

Calls:
- `PrinterConnectionError` (line 1645, type: direct)
- `info` (line 1648, type: attribute)
- `pause` (line 1651, type: attribute)
- `info` (line 1654, type: attribute)
- `warning` (line 1657, type: attribute)
- `error` (line 1661, type: attribute)
- `str` (line 1662, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.rank

Calls:
- `lower` (line 1512, type: attribute)
- `endswith` (line 1514, type: attribute)
- `endswith` (line 1515, type: attribute)
- `startswith` (line 1516, type: attribute)

### src\printers\bambu_lab.py:BambuLabPrinter.resume_print

Calls:
- `PrinterConnectionError` (line 1668, type: direct)
- `info` (line 1671, type: attribute)
- `resume` (line 1674, type: attribute)
- `info` (line 1677, type: attribute)
- `warning` (line 1680, type: attribute)
- `error` (line 1684, type: attribute)
- `str` (line 1685, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.stop_print

Calls:
- `PrinterConnectionError` (line 1691, type: direct)
- `info` (line 1694, type: attribute)
- `stop` (line 1697, type: attribute)
- `info` (line 1700, type: attribute)
- `warning` (line 1703, type: attribute)
- `error` (line 1707, type: attribute)
- `str` (line 1708, type: direct)

### src\printers\bambu_lab.py:BambuLabPrinter.take_snapshot

Calls:
- `warning` (line 1749, type: attribute)
- `info` (line 1759, type: attribute)
- `ClientSession` (line 1762, type: attribute)
- `ClientTimeout` (line 1762, type: attribute)
- `get` (line 1763, type: attribute)
- `read` (line 1765, type: attribute)
- `info` (line 1766, type: attribute)
- `len` (line 1768, type: direct)
- `warning` (line 1771, type: attribute)
- `error` (line 1777, type: attribute)
- `str` (line 1778, type: direct)

### src\printers\base.py:BasePrinter.__aenter__

Calls:
- `connect` (line 287, type: attribute)

### src\printers\base.py:BasePrinter.__aexit__

Calls:
- `disconnect` (line 292, type: attribute)

### src\printers\base.py:BasePrinter.__init__

Calls:
- `Event` (line 156, type: attribute)

### src\printers\base.py:BasePrinter._monitor_loop

Calls:
- `is_set` (line 205, type: attribute)
- `perf_counter` (line 206, type: attribute)
- `get_status` (line 208, type: attribute)
- `perf_counter` (line 209, type: attribute)
- `now` (line 213, type: attribute)
- `info` (line 215, type: attribute)
- `iscoroutinefunction` (line 220, type: attribute)
- `callback` (line 221, type: direct)
- `callback` (line 223, type: direct)
- `error` (line 225, type: attribute)
- `str` (line 225, type: direct)
- `str` (line 229, type: direct)
- `now` (line 230, type: attribute)
- `error` (line 231, type: attribute)
- `str` (line 231, type: direct)
- `min` (line 232, type: direct)
- `uniform` (line 234, type: attribute)
- `max` (line 235, type: direct)
- `int` (line 235, type: direct)
- `warning` (line 236, type: attribute)
- `wait_for` (line 239, type: attribute)
- `wait` (line 239, type: attribute)

### src\printers\base.py:BasePrinter.add_status_callback

Calls:
- `append` (line 246, type: attribute)

### src\printers\base.py:BasePrinter.get_connection_info

Calls:
- `dict` (line 268, type: attribute)

### src\printers\base.py:BasePrinter.get_monitoring_metrics

Calls:
- `isoformat` (line 281, type: attribute)
- `isoformat` (line 282, type: attribute)

### src\printers\base.py:BasePrinter.health_check

Calls:
- `get_status` (line 256, type: attribute)

### src\printers\base.py:BasePrinter.remove_status_callback

Calls:
- `remove` (line 251, type: attribute)

### src\printers\base.py:BasePrinter.start_monitoring

Calls:
- `warning` (line 171, type: attribute)
- `info` (line 174, type: attribute)
- `clear` (line 175, type: attribute)
- `max` (line 176, type: direct)
- `int` (line 176, type: direct)
- `create_task` (line 183, type: attribute)
- `_monitor_loop` (line 183, type: attribute)

### src\printers\base.py:BasePrinter.stop_monitoring

Calls:
- `info` (line 190, type: attribute)
- `set` (line 191, type: attribute)
- `done` (line 193, type: attribute)
- `cancel` (line 194, type: attribute)

### src\printers\base.py:PrinterFile.__init__

Calls:
- `now` (line 38, type: attribute)
- `_guess_file_type` (line 40, type: attribute)

### src\printers\base.py:PrinterFile._guess_file_type

Calls:
- `split` (line 46, type: attribute)
- `lower` (line 46, type: attribute)
- `get` (line 55, type: attribute)

### src\printers\prusa.py:PrusaPrinter.__init__

Calls:
- `__init__` (line 26, type: attribute)
- `super` (line 26, type: direct)

### src\printers\prusa.py:PrusaPrinter._find_file_by_display_name

Calls:
- `get_files` (line 580, type: attribute)
- `debug` (line 582, type: attribute)
- `len` (line 582, type: direct)
- `get` (line 587, type: attribute)
- `get` (line 588, type: attribute)
- `debug` (line 591, type: attribute)
- `lower` (line 596, type: attribute)
- `get` (line 598, type: attribute)
- `get` (line 599, type: attribute)
- `lower` (line 601, type: attribute)
- `lower` (line 602, type: attribute)
- `lower` (line 603, type: attribute)
- `lower` (line 604, type: attribute)
- `info` (line 606, type: attribute)
- `warning` (line 611, type: attribute)
- `enumerate` (line 613, type: direct)
- `warning` (line 614, type: attribute)
- `get` (line 614, type: attribute)
- `get` (line 614, type: attribute)
- `len` (line 616, type: direct)
- `warning` (line 617, type: attribute)
- `len` (line 617, type: direct)
- `error` (line 622, type: attribute)
- `str` (line 625, type: direct)

### src\printers\prusa.py:PrusaPrinter._map_job_status

Calls:
- `lower` (line 301, type: attribute)

### src\printers\prusa.py:PrusaPrinter._map_prusa_status

Calls:
- `lower` (line 240, type: attribute)

### src\printers\prusa.py:PrusaPrinter.connect

Calls:
- `info` (line 35, type: attribute)
- `info` (line 39, type: attribute)
- `ClientTimeout` (line 49, type: attribute)
- `TCPConnector` (line 50, type: attribute)
- `ClientSession` (line 58, type: attribute)
- `range` (line 66, type: direct)
- `get` (line 68, type: attribute)
- `json` (line 70, type: attribute)
- `info` (line 71, type: attribute)
- `get` (line 73, type: attribute)
- `ClientError` (line 78, type: attribute)
- `ClientError` (line 80, type: attribute)
- `ClientError` (line 82, type: attribute)
- `warning` (line 87, type: attribute)
- `str` (line 91, type: direct)
- `sleep` (line 92, type: attribute)
- `str` (line 98, type: direct)
- `type` (line 98, type: direct)
- `error` (line 100, type: attribute)
- `lower` (line 102, type: attribute)
- `isinstance` (line 102, type: direct)
- `error` (line 103, type: attribute)
- `error` (line 106, type: attribute)
- `type` (line 108, type: direct)
- `close` (line 111, type: attribute)
- `PrinterConnectionError` (line 113, type: direct)

### src\printers\prusa.py:PrusaPrinter.disconnect

Calls:
- `close` (line 122, type: attribute)
- `info` (line 127, type: attribute)
- `error` (line 130, type: attribute)
- `str` (line 131, type: direct)

### src\printers\prusa.py:PrusaPrinter.download_file

Calls:
- `PrinterConnectionError` (line 480, type: direct)
- `info` (line 483, type: attribute)
- `_find_file_by_display_name` (line 487, type: attribute)
- `error` (line 489, type: attribute)
- `get` (line 494, type: attribute)
- `get` (line 494, type: attribute)
- `error` (line 496, type: attribute)
- `info` (line 500, type: attribute)
- `info` (line 502, type: attribute)
- `startswith` (line 512, type: attribute)
- `info` (line 517, type: attribute)
- `info` (line 520, type: attribute)
- `get` (line 526, type: attribute)
- `mkdir` (line 529, type: attribute)
- `Path` (line 529, type: direct)
- `iter_chunked` (line 535, type: attribute)
- `startswith` (line 539, type: attribute)
- `startswith` (line 539, type: attribute)
- `decode` (line 542, type: attribute)
- `error` (line 543, type: attribute)
- `append` (line 551, type: attribute)
- `open` (line 554, type: direct)
- `write` (line 556, type: attribute)
- `stat` (line 558, type: attribute)
- `Path` (line 558, type: direct)
- `info` (line 559, type: attribute)
- `error` (line 564, type: attribute)
- `error` (line 573, type: attribute)
- `str` (line 574, type: direct)

### src\printers\prusa.py:PrusaPrinter.download_thumbnail

Calls:
- `warning` (line 640, type: attribute)
- `_find_file_by_display_name` (line 646, type: attribute)
- `warning` (line 648, type: attribute)
- `get` (line 653, type: attribute)
- `get` (line 654, type: attribute)
- `get` (line 654, type: attribute)
- `debug` (line 657, type: attribute)
- `startswith` (line 663, type: attribute)
- `startswith` (line 665, type: attribute)
- `warning` (line 669, type: attribute)
- `info` (line 673, type: attribute)
- `get` (line 678, type: attribute)
- `read` (line 680, type: attribute)
- `info` (line 681, type: attribute)
- `len` (line 683, type: direct)
- `warning` (line 686, type: attribute)
- `error` (line 692, type: attribute)
- `str` (line 693, type: direct)

### src\printers\prusa.py:PrusaPrinter.extract_files_from_structure

Calls:
- `get` (line 344, type: attribute)
- `get` (line 348, type: attribute)
- `get` (line 348, type: attribute)
- `extract_files_from_structure` (line 352, type: direct)
- `extend` (line 356, type: attribute)
- `get` (line 361, type: attribute)
- `get` (line 362, type: attribute)
- `endswith` (line 365, type: attribute)
- `lower` (line 365, type: attribute)
- `endswith` (line 366, type: attribute)
- `lower` (line 366, type: attribute)
- `PrinterFile` (line 369, type: direct)
- `get` (line 371, type: attribute)
- `get` (line 373, type: attribute)
- `fromtimestamp` (line 372, type: attribute)
- `get` (line 372, type: attribute)
- `get` (line 374, type: attribute)
- `append` (line 376, type: attribute)

### src\printers\prusa.py:PrusaPrinter.extract_raw_files_from_structure

Calls:
- `get` (line 426, type: attribute)
- `get` (line 430, type: attribute)
- `get` (line 430, type: attribute)
- `extract_raw_files_from_structure` (line 434, type: direct)
- `extend` (line 438, type: attribute)
- `get` (line 443, type: attribute)
- `get` (line 444, type: attribute)
- `endswith` (line 447, type: attribute)
- `lower` (line 447, type: attribute)
- `endswith` (line 448, type: attribute)
- `lower` (line 448, type: attribute)
- `dict` (line 452, type: direct)
- `append` (line 454, type: attribute)

### src\printers\prusa.py:PrusaPrinter.get_camera_stream_url

Calls:
- `debug` (line 777, type: attribute)

### src\printers\prusa.py:PrusaPrinter.get_files

Calls:
- `PrinterConnectionError` (line 402, type: direct)
- `get` (line 406, type: attribute)
- `warning` (line 408, type: attribute)
- `warning` (line 412, type: attribute)
- `json` (line 416, type: attribute)
- `get` (line 459, type: attribute)
- `extend` (line 460, type: attribute)
- `extract_raw_files_from_structure` (line 460, type: direct)
- `get` (line 463, type: attribute)
- `get` (line 464, type: attribute)
- `get` (line 464, type: attribute)
- `extract_raw_files_from_structure` (line 465, type: direct)
- `extend` (line 466, type: attribute)
- `info` (line 468, type: attribute)
- `len` (line 469, type: direct)
- `warning` (line 473, type: attribute)
- `str` (line 474, type: direct)

### src\printers\prusa.py:PrusaPrinter.get_job_info

Calls:
- `get` (line 259, type: attribute)
- `json` (line 263, type: attribute)
- `get` (line 265, type: attribute)
- `get` (line 266, type: attribute)
- `get` (line 266, type: attribute)
- `get` (line 269, type: attribute)
- `get` (line 270, type: attribute)
- `get` (line 272, type: attribute)
- `get` (line 272, type: attribute)
- `int` (line 273, type: direct)
- `get` (line 273, type: attribute)
- `get` (line 276, type: attribute)
- `_map_job_status` (line 277, type: attribute)
- `get` (line 280, type: attribute)
- `get` (line 281, type: attribute)
- `JobInfo` (line 283, type: direct)
- `strftime` (line 284, type: attribute)
- `now` (line 284, type: attribute)
- `error` (line 295, type: attribute)
- `str` (line 296, type: direct)

### src\printers\prusa.py:PrusaPrinter.get_status

Calls:
- `PrinterConnectionError` (line 136, type: direct)
- `get` (line 140, type: attribute)
- `ClientError` (line 142, type: attribute)
- `json` (line 144, type: attribute)
- `get` (line 149, type: attribute)
- `json` (line 151, type: attribute)
- `warning` (line 153, type: attribute)
- `str` (line 154, type: direct)
- `get` (line 157, type: attribute)
- `get` (line 157, type: attribute)
- `_map_prusa_status` (line 158, type: attribute)
- `get` (line 161, type: attribute)
- `get` (line 162, type: attribute)
- `get` (line 162, type: attribute)
- `get` (line 163, type: attribute)
- `get` (line 163, type: attribute)
- `get` (line 172, type: attribute)
- `get` (line 173, type: attribute)
- `get` (line 174, type: attribute)
- `get` (line 176, type: attribute)
- `get` (line 176, type: attribute)
- `get` (line 178, type: attribute)
- `int` (line 180, type: direct)
- `get` (line 180, type: attribute)
- `get` (line 183, type: attribute)
- `int` (line 186, type: direct)
- `now` (line 189, type: attribute)
- `timedelta` (line 189, type: direct)
- `find_file_by_name` (line 196, type: attribute)
- `get` (line 198, type: attribute)
- `get` (line 199, type: attribute)
- `debug` (line 200, type: attribute)
- `debug` (line 206, type: attribute)
- `str` (line 209, type: direct)
- `PrinterStatusUpdate` (line 211, type: direct)
- `float` (line 215, type: direct)
- `float` (line 216, type: direct)
- `now` (line 224, type: attribute)
- `error` (line 229, type: attribute)
- `str` (line 230, type: direct)
- `PrinterStatusUpdate` (line 231, type: direct)
- `str` (line 234, type: direct)
- `now` (line 235, type: attribute)

### src\printers\prusa.py:PrusaPrinter.list_files

Calls:
- `PrinterConnectionError` (line 319, type: direct)
- `get` (line 323, type: attribute)
- `warning` (line 325, type: attribute)
- `warning` (line 329, type: attribute)
- `json` (line 333, type: attribute)
- `get` (line 381, type: attribute)
- `extend` (line 382, type: attribute)
- `extract_files_from_structure` (line 382, type: direct)
- `get` (line 385, type: attribute)
- `get` (line 386, type: attribute)
- `get` (line 386, type: attribute)
- `extract_files_from_structure` (line 387, type: direct)
- `extend` (line 388, type: attribute)
- `info` (line 390, type: attribute)
- `len` (line 391, type: direct)
- `warning` (line 395, type: attribute)
- `str` (line 396, type: direct)

### src\printers\prusa.py:PrusaPrinter.pause_print

Calls:
- `PrinterConnectionError` (line 699, type: direct)
- `info` (line 702, type: attribute)
- `post` (line 705, type: attribute)
- `info` (line 708, type: attribute)
- `warning` (line 711, type: attribute)
- `error` (line 716, type: attribute)
- `str` (line 717, type: direct)

### src\printers\prusa.py:PrusaPrinter.resume_print

Calls:
- `PrinterConnectionError` (line 723, type: direct)
- `info` (line 726, type: attribute)
- `post` (line 729, type: attribute)
- `info` (line 732, type: attribute)
- `warning` (line 735, type: attribute)
- `error` (line 740, type: attribute)
- `str` (line 741, type: direct)

### src\printers\prusa.py:PrusaPrinter.stop_print

Calls:
- `PrinterConnectionError` (line 747, type: direct)
- `info` (line 750, type: attribute)
- `post` (line 753, type: attribute)
- `info` (line 756, type: attribute)
- `warning` (line 759, type: attribute)
- `error` (line 764, type: attribute)
- `str` (line 765, type: direct)

### src\printers\prusa.py:PrusaPrinter.take_snapshot

Calls:
- `debug` (line 783, type: attribute)

### src\services\analytics_service.py:AnalyticsService._get_file_statistics

Calls:
- `get_file_statistics` (line 286, type: attribute)
- `get` (line 290, type: attribute)
- `get` (line 291, type: attribute)
- `get` (line 292, type: attribute)
- `error` (line 303, type: attribute)
- `str` (line 303, type: direct)

### src\services\analytics_service.py:AnalyticsService._get_job_statistics

Calls:
- `error` (line 275, type: attribute)
- `str` (line 275, type: direct)

### src\services\analytics_service.py:AnalyticsService._get_printer_statistics

Calls:
- `list_printers` (line 314, type: attribute)
- `len` (line 316, type: direct)
- `len` (line 317, type: direct)
- `get` (line 317, type: attribute)
- `error` (line 324, type: attribute)
- `str` (line 324, type: direct)

### src\services\analytics_service.py:AnalyticsService.export_data

Calls:
- `info` (line 119, type: attribute)

### src\services\analytics_service.py:AnalyticsService.get_business_analytics

Calls:
- `now` (line 173, type: attribute)
- `timedelta` (line 175, type: direct)
- `get_jobs_by_date_range` (line 178, type: attribute)
- `isoformat` (line 179, type: attribute)
- `isoformat` (line 179, type: attribute)
- `get` (line 183, type: attribute)
- `get` (line 184, type: attribute)
- `sum` (line 187, type: direct)
- `get` (line 187, type: attribute)
- `sum` (line 188, type: direct)
- `get` (line 188, type: attribute)
- `get` (line 194, type: attribute)
- `get` (line 202, type: attribute)
- `sorted` (line 205, type: direct)
- `values` (line 206, type: attribute)
- `len` (line 212, type: direct)
- `len` (line 213, type: direct)
- `round` (line 214, type: direct)
- `round` (line 215, type: direct)
- `round` (line 216, type: direct)
- `error` (line 220, type: attribute)
- `str` (line 220, type: direct)

### src\services\analytics_service.py:AnalyticsService.get_business_report

Calls:
- `info` (line 50, type: attribute)
- `isoformat` (line 51, type: attribute)
- `isoformat` (line 51, type: attribute)
- `get_jobs_by_date_range` (line 54, type: attribute)
- `isoformat` (line 55, type: attribute)
- `isoformat` (line 55, type: attribute)
- `get` (line 59, type: attribute)
- `get` (line 60, type: attribute)
- `sum` (line 63, type: direct)
- `get` (line 63, type: attribute)
- `sum` (line 64, type: direct)
- `get` (line 64, type: attribute)
- `sum` (line 65, type: direct)
- `get` (line 65, type: attribute)
- `sum` (line 69, type: direct)
- `get` (line 69, type: attribute)
- `isoformat` (line 73, type: attribute)
- `isoformat` (line 74, type: attribute)
- `len` (line 77, type: direct)
- `len` (line 78, type: direct)
- `len` (line 79, type: direct)
- `error` (line 93, type: attribute)
- `str` (line 93, type: direct)
- `isoformat` (line 96, type: attribute)
- `isoformat` (line 97, type: attribute)

### src\services\analytics_service.py:AnalyticsService.get_dashboard_overview

Calls:
- `_get_job_statistics` (line 227, type: attribute)
- `_get_file_statistics` (line 230, type: attribute)
- `_get_printer_statistics` (line 233, type: attribute)
- `error` (line 242, type: attribute)
- `str` (line 242, type: direct)

### src\services\analytics_service.py:AnalyticsService.get_summary

Calls:
- `now` (line 133, type: attribute)
- `timedelta` (line 135, type: direct)
- `get_jobs_by_date_range` (line 138, type: attribute)
- `isoformat` (line 139, type: attribute)
- `isoformat` (line 139, type: attribute)
- `len` (line 143, type: direct)
- `len` (line 144, type: direct)
- `get` (line 144, type: attribute)
- `len` (line 145, type: direct)
- `get` (line 145, type: attribute)
- `sum` (line 147, type: direct)
- `get` (line 147, type: attribute)
- `sum` (line 148, type: direct)
- `get` (line 148, type: attribute)
- `sum` (line 149, type: direct)
- `get` (line 149, type: attribute)
- `round` (line 158, type: direct)
- `round` (line 159, type: direct)
- `round` (line 160, type: direct)
- `round` (line 161, type: direct)
- `round` (line 162, type: direct)
- `error` (line 165, type: attribute)
- `str` (line 165, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPFile.__init__

Calls:
- `_determine_file_type` (line 39, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPFile._determine_file_type

Calls:
- `lower` (line 43, type: attribute)
- `Path` (line 43, type: direct)
- `get` (line 57, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPFile.to_dict

Calls:
- `isoformat` (line 70, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPService.__init__

Calls:
- `info` (line 99, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPService._connect_ftp

Calls:
- `_create_ssl_context` (line 121, type: attribute)
- `get_event_loop` (line 150, type: attribute)
- `run_in_executor` (line 151, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPService._create_ssl_context

Calls:
- `create_default_context` (line 104, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPService._parse_ftp_line

Calls:
- `split` (line 258, type: attribute)
- `strip` (line 258, type: attribute)
- `len` (line 259, type: direct)
- `startswith` (line 265, type: attribute)
- `isdigit` (line 269, type: attribute)
- `int` (line 269, type: direct)
- `join` (line 270, type: attribute)
- `len` (line 278, type: direct)
- `BambuFTPFile` (line 284, type: direct)
- `debug` (line 293, type: attribute)
- `str` (line 293, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService._sync_connect

Calls:
- `FTP_TLS` (line 125, type: attribute)
- `set_pasv` (line 126, type: attribute)
- `connect` (line 130, type: attribute)
- `login` (line 133, type: attribute)
- `prot_p` (line 136, type: attribute)
- `close` (line 141, type: attribute)
- `PermissionError` (line 142, type: direct)
- `close` (line 144, type: attribute)
- `ConnectionError` (line 145, type: direct)
- `close` (line 147, type: attribute)
- `ConnectionError` (line 148, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService._sync_download

Calls:
- `cwd` (line 323, type: attribute)
- `open` (line 326, type: direct)
- `retrbinary` (line 327, type: attribute)
- `error` (line 332, type: attribute)
- `str` (line 335, type: direct)
- `error` (line 338, type: attribute)
- `str` (line 341, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService._sync_list

Calls:
- `cwd` (line 215, type: attribute)
- `retrlines` (line 219, type: attribute)
- `_parse_ftp_line` (line 223, type: attribute)
- `append` (line 225, type: attribute)
- `str` (line 230, type: direct)
- `warning` (line 231, type: attribute)
- `str` (line 232, type: direct)
- `PermissionError` (line 235, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService.download_file

Calls:
- `info` (line 309, type: attribute)
- `mkdir` (line 317, type: attribute)
- `Path` (line 317, type: direct)
- `ftp_connection` (line 319, type: attribute)
- `get_event_loop` (line 344, type: attribute)
- `run_in_executor` (line 345, type: attribute)
- `exists` (line 347, type: attribute)
- `Path` (line 347, type: direct)
- `stat` (line 348, type: attribute)
- `Path` (line 348, type: direct)
- `info` (line 349, type: attribute)
- `error` (line 356, type: attribute)
- `error` (line 362, type: attribute)
- `str` (line 365, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService.file_exists

Calls:
- `list_files` (line 380, type: attribute)
- `any` (line 381, type: direct)
- `debug` (line 383, type: attribute)
- `str` (line 386, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService.ftp_connection

Calls:
- `range` (line 163, type: direct)
- `_connect_ftp` (line 165, type: attribute)
- `debug` (line 166, type: attribute)
- `warning` (line 172, type: attribute)
- `str` (line 176, type: direct)
- `sleep` (line 182, type: attribute)
- `run_in_executor` (line 187, type: attribute)
- `get_event_loop` (line 187, type: attribute)
- `close` (line 190, type: attribute)

### src\services\bambu_ftp_service.py:BambuFTPService.get_file_info

Calls:
- `list_files` (line 401, type: attribute)
- `next` (line 402, type: direct)
- `debug` (line 404, type: attribute)
- `str` (line 407, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService.list_files

Calls:
- `info` (line 208, type: attribute)
- `ftp_connection` (line 211, type: attribute)
- `get_event_loop` (line 237, type: attribute)
- `run_in_executor` (line 238, type: attribute)
- `info` (line 240, type: attribute)
- `len` (line 243, type: direct)

### src\services\bambu_ftp_service.py:BambuFTPService.test_connection

Calls:
- `ftp_connection` (line 418, type: attribute)
- `get_event_loop` (line 420, type: attribute)
- `run_in_executor` (line 421, type: attribute)

### src\services\bambu_ftp_service.py:create_bambu_ftp_service

Calls:
- `BambuFTPService` (line 447, type: direct)
- `test_connection` (line 450, type: attribute)
- `ConnectionError` (line 452, type: direct)
- `info` (line 454, type: attribute)

### src\services\bambu_parser.py:BambuParser._calculate_complexity_score

Calls:
- `get` (line 516, type: attribute)
- `get` (line 526, type: attribute)
- `get` (line 526, type: attribute)
- `get` (line 530, type: attribute)
- `get` (line 530, type: attribute)
- `get` (line 536, type: attribute)
- `get` (line 536, type: attribute)
- `any` (line 539, type: direct)
- `lower` (line 539, type: attribute)
- `str` (line 539, type: direct)
- `get` (line 543, type: attribute)
- `isinstance` (line 544, type: direct)
- `len` (line 544, type: direct)
- `sum` (line 546, type: direct)
- `get` (line 551, type: attribute)
- `max` (line 559, type: direct)
- `min` (line 559, type: direct)

### src\services\bambu_parser.py:BambuParser._calculate_derived_metrics

Calls:
- `round` (line 447, type: direct)
- `isinstance` (line 454, type: direct)
- `round` (line 455, type: direct)
- `sum` (line 455, type: direct)
- `isinstance` (line 456, type: direct)
- `round` (line 457, type: direct)
- `float` (line 457, type: direct)
- `isinstance` (line 462, type: direct)
- `round` (line 464, type: direct)
- `sum` (line 464, type: direct)
- `isinstance` (line 465, type: direct)
- `round` (line 466, type: direct)
- `float` (line 466, type: direct)
- `_calculate_complexity_score` (line 473, type: attribute)
- `_calculate_difficulty_level` (line 476, type: attribute)
- `get` (line 480, type: attribute)
- `get` (line 480, type: attribute)
- `round` (line 483, type: direct)
- `get` (line 488, type: attribute)
- `round` (line 501, type: direct)
- `round` (line 505, type: direct)

### src\services\bambu_parser.py:BambuParser._calculate_difficulty_level

Calls:
- `_calculate_complexity_score` (line 563, type: attribute)

### src\services\bambu_parser.py:BambuParser._convert_metadata_value

Calls:
- `float` (line 394, type: direct)
- `int` (line 402, type: direct)
- `float` (line 412, type: direct)
- `strip` (line 412, type: attribute)
- `split` (line 412, type: attribute)
- `float` (line 414, type: direct)
- `lower` (line 420, type: attribute)
- `strip` (line 428, type: attribute)
- `strip` (line 428, type: attribute)
- `split` (line 428, type: attribute)
- `strip` (line 431, type: attribute)
- `strip` (line 431, type: attribute)

### src\services\bambu_parser.py:BambuParser._extract_3mf_metadata

Calls:
- `fromstring` (line 579, type: attribute)
- `iter` (line 582, type: attribute)
- `lower` (line 583, type: attribute)
- `get` (line 584, type: attribute)
- `get` (line 585, type: attribute)
- `lower` (line 589, type: attribute)
- `lower` (line 593, type: attribute)
- `float` (line 593, type: direct)
- `lower` (line 595, type: attribute)
- `int` (line 595, type: direct)
- `lower` (line 597, type: attribute)
- `lower` (line 599, type: attribute)
- `warning` (line 602, type: attribute)
- `str` (line 602, type: direct)

### src\services\bambu_parser.py:BambuParser._extract_advanced_metadata

Calls:
- `items` (line 379, type: attribute)
- `search` (line 380, type: attribute)
- `strip` (line 382, type: attribute)
- `group` (line 382, type: attribute)
- `_convert_metadata_value` (line 383, type: attribute)

### src\services\bambu_parser.py:BambuParser._extract_gcode_metadata

Calls:
- `items` (line 319, type: attribute)
- `search` (line 320, type: attribute)
- `strip` (line 322, type: attribute)
- `group` (line 322, type: attribute)
- `float` (line 327, type: direct)
- `int` (line 332, type: direct)
- `_parse_time_duration` (line 336, type: attribute)
- `lower` (line 338, type: attribute)
- `items` (line 343, type: attribute)
- `search` (line 344, type: attribute)
- `strip` (line 346, type: attribute)
- `group` (line 346, type: attribute)
- `float` (line 351, type: direct)
- `strip` (line 351, type: attribute)
- `split` (line 351, type: attribute)
- `sum` (line 353, type: direct)
- `float` (line 358, type: direct)
- `strip` (line 363, type: attribute)
- `split` (line 363, type: attribute)
- `update` (line 368, type: attribute)
- `_extract_advanced_metadata` (line 368, type: attribute)
- `update` (line 371, type: attribute)
- `_calculate_derived_metrics` (line 371, type: attribute)

### src\services\bambu_parser.py:BambuParser._extract_gcode_thumbnails

Calls:
- `list` (line 260, type: direct)
- `finditer` (line 260, type: attribute)
- `list` (line 261, type: direct)
- `finditer` (line 261, type: attribute)
- `len` (line 263, type: direct)
- `len` (line 263, type: direct)
- `warning` (line 264, type: attribute)
- `len` (line 265, type: direct)
- `len` (line 266, type: direct)
- `enumerate` (line 269, type: direct)
- `int` (line 271, type: direct)
- `group` (line 271, type: attribute)
- `int` (line 272, type: direct)
- `group` (line 272, type: attribute)
- `int` (line 273, type: direct)
- `group` (line 273, type: attribute)
- `len` (line 275, type: direct)
- `end` (line 279, type: attribute)
- `start` (line 280, type: attribute)
- `split` (line 285, type: attribute)
- `strip` (line 286, type: attribute)
- `startswith` (line 287, type: attribute)
- `len` (line 287, type: direct)
- `strip` (line 289, type: attribute)
- `_is_valid_base64` (line 293, type: attribute)
- `append` (line 294, type: attribute)
- `debug` (line 303, type: attribute)
- `warning` (line 306, type: attribute)
- `warning` (line 309, type: attribute)
- `str` (line 309, type: direct)

### src\services\bambu_parser.py:BambuParser._extract_png_dimensions

Calls:
- `len` (line 767, type: direct)
- `from_bytes` (line 768, type: attribute)
- `from_bytes` (line 769, type: attribute)

### src\services\bambu_parser.py:BambuParser._is_valid_base64

Calls:
- `len` (line 824, type: direct)
- `len` (line 825, type: direct)
- `b64decode` (line 827, type: attribute)

### src\services\bambu_parser.py:BambuParser._parse_3mf_file

Calls:
- `ZipFile` (line 182, type: attribute)
- `namelist` (line 184, type: attribute)
- `startswith` (line 185, type: attribute)
- `endswith` (line 185, type: attribute)
- `open` (line 190, type: attribute)
- `read` (line 191, type: attribute)
- `decode` (line 192, type: attribute)
- `b64encode` (line 192, type: attribute)
- `_parse_thumbnail_dimensions` (line 195, type: attribute)
- `append` (line 197, type: attribute)
- `warning` (line 206, type: attribute)
- `str` (line 207, type: direct)
- `open` (line 212, type: attribute)
- `decode` (line 213, type: attribute)
- `read` (line 213, type: attribute)
- `update` (line 214, type: attribute)
- `_extract_3mf_metadata` (line 214, type: attribute)
- `warning` (line 216, type: attribute)
- `str` (line 216, type: direct)
- `namelist` (line 219, type: attribute)
- `startswith` (line 220, type: attribute)
- `endswith` (line 220, type: attribute)
- `open` (line 224, type: attribute)
- `decode` (line 225, type: attribute)
- `read` (line 225, type: attribute)
- `update` (line 226, type: attribute)
- `_extract_3mf_metadata` (line 226, type: attribute)
- `warning` (line 228, type: attribute)
- `str` (line 229, type: direct)
- `info` (line 232, type: attribute)
- `str` (line 233, type: direct)
- `len` (line 234, type: direct)
- `list` (line 235, type: direct)
- `keys` (line 235, type: attribute)
- `len` (line 242, type: direct)
- `error` (line 246, type: attribute)
- `str` (line 246, type: direct)
- `str` (line 246, type: direct)
- `str` (line 249, type: direct)

### src\services\bambu_parser.py:BambuParser._parse_bgcode_file

Calls:
- `open` (line 616, type: direct)
- `read` (line 619, type: attribute)
- `warning` (line 621, type: attribute)
- `hex` (line 622, type: attribute)
- `hex` (line 625, type: attribute)
- `seek` (line 632, type: attribute)
- `read` (line 633, type: attribute)
- `find` (line 640, type: attribute)
- `append` (line 643, type: attribute)
- `enumerate` (line 647, type: direct)
- `len` (line 650, type: direct)
- `find` (line 655, type: attribute)
- `len` (line 657, type: direct)
- `min` (line 660, type: direct)
- `len` (line 660, type: direct)
- `len` (line 665, type: direct)
- `decode` (line 669, type: attribute)
- `b64encode` (line 669, type: attribute)
- `_extract_png_dimensions` (line 672, type: attribute)
- `append` (line 674, type: attribute)
- `debug` (line 681, type: attribute)
- `len` (line 682, type: direct)
- `warning` (line 685, type: attribute)
- `str` (line 686, type: direct)
- `len` (line 692, type: direct)
- `len` (line 694, type: direct)
- `info` (line 697, type: attribute)
- `str` (line 698, type: direct)
- `len` (line 699, type: direct)
- `list` (line 700, type: direct)
- `keys` (line 700, type: attribute)
- `len` (line 707, type: direct)
- `error` (line 711, type: attribute)
- `str` (line 711, type: direct)
- `str` (line 711, type: direct)
- `str` (line 714, type: direct)

### src\services\bambu_parser.py:BambuParser._parse_gcode_file

Calls:
- `open` (line 144, type: direct)
- `read` (line 145, type: attribute)
- `_extract_gcode_thumbnails` (line 148, type: attribute)
- `_extract_gcode_metadata` (line 151, type: attribute)
- `info` (line 153, type: attribute)
- `str` (line 154, type: direct)
- `len` (line 155, type: direct)
- `list` (line 156, type: direct)
- `keys` (line 156, type: attribute)
- `len` (line 163, type: direct)
- `error` (line 167, type: attribute)
- `str` (line 167, type: direct)
- `str` (line 167, type: direct)
- `str` (line 170, type: direct)

### src\services\bambu_parser.py:BambuParser._parse_stl_file

Calls:
- `stat` (line 734, type: attribute)
- `info` (line 741, type: attribute)
- `str` (line 742, type: direct)
- `error` (line 754, type: attribute)
- `str` (line 754, type: direct)
- `str` (line 754, type: direct)
- `str` (line 757, type: direct)

### src\services\bambu_parser.py:BambuParser._parse_thumbnail_dimensions

Calls:
- `search` (line 778, type: attribute)
- `int` (line 780, type: direct)
- `group` (line 780, type: attribute)
- `int` (line 780, type: direct)
- `group` (line 780, type: attribute)

### src\services\bambu_parser.py:BambuParser._parse_time_duration

Calls:
- `strip` (line 789, type: attribute)
- `lower` (line 789, type: attribute)
- `search` (line 793, type: attribute)
- `int` (line 795, type: direct)
- `group` (line 795, type: attribute)
- `search` (line 798, type: attribute)
- `int` (line 800, type: direct)
- `group` (line 800, type: attribute)
- `search` (line 803, type: attribute)
- `int` (line 805, type: direct)
- `group` (line 805, type: attribute)
- `int` (line 810, type: direct)
- `float` (line 810, type: direct)
- `warning` (line 817, type: attribute)
- `str` (line 817, type: direct)

### src\services\bambu_parser.py:BambuParser.get_largest_thumbnail

Calls:
- `max` (line 838, type: direct)
- `get` (line 838, type: attribute)
- `get` (line 838, type: attribute)

### src\services\bambu_parser.py:BambuParser.get_thumbnail_by_size

Calls:
- `min` (line 851, type: direct)
- `abs` (line 852, type: direct)
- `get` (line 852, type: attribute)
- `get` (line 852, type: attribute)

### src\services\bambu_parser.py:BambuParser.parse_file

Calls:
- `Path` (line 102, type: direct)
- `exists` (line 104, type: attribute)
- `lower` (line 114, type: attribute)
- `_parse_3mf_file` (line 115, type: attribute)
- `lower` (line 116, type: attribute)
- `_parse_gcode_file` (line 117, type: attribute)
- `lower` (line 118, type: attribute)
- `_parse_bgcode_file` (line 119, type: attribute)
- `lower` (line 120, type: attribute)
- `_parse_stl_file` (line 121, type: attribute)
- `error` (line 132, type: attribute)
- `str` (line 132, type: direct)
- `str` (line 132, type: direct)
- `str` (line 135, type: direct)

### src\services\config_service.py:ConfigService.__init__

Calls:
- `Settings` (line 194, type: direct)
- `WatchFolderDbService` (line 195, type: direct)
- `Path` (line 199, type: direct)
- `Path` (line 201, type: direct)
- `_load_printer_configs` (line 203, type: attribute)

### src\services\config_service.py:ConfigService._create_default_config

Calls:
- `mkdir` (line 278, type: attribute)
- `open` (line 301, type: direct)
- `dump` (line 302, type: attribute)
- `info` (line 303, type: attribute)
- `str` (line 303, type: direct)
- `error` (line 305, type: attribute)
- `str` (line 305, type: direct)

### src\services\config_service.py:ConfigService._ensure_env_migration

Calls:
- `get_settings` (line 641, type: direct)
- `migrate_env_folders` (line 645, type: attribute)
- `info` (line 646, type: attribute)
- `len` (line 647, type: direct)
- `error` (line 652, type: attribute)
- `str` (line 652, type: direct)

### src\services\config_service.py:ConfigService._get_cors_origins_list

Calls:
- `strip` (line 488, type: attribute)
- `split` (line 488, type: attribute)
- `strip` (line 488, type: attribute)

### src\services\config_service.py:ConfigService._load_from_environment

Calls:
- `items` (line 241, type: attribute)
- `startswith` (line 242, type: attribute)
- `split` (line 243, type: attribute)
- `len` (line 244, type: direct)
- `join` (line 246, type: attribute)
- `lower` (line 247, type: attribute)
- `len` (line 253, type: direct)
- `len` (line 255, type: direct)
- `len` (line 257, type: direct)
- `len` (line 259, type: direct)
- `lower` (line 263, type: attribute)
- `items` (line 268, type: attribute)
- `from_dict` (line 270, type: attribute)
- `info` (line 271, type: attribute)
- `error` (line 273, type: attribute)
- `str` (line 274, type: direct)

### src\services\config_service.py:ConfigService._load_printer_configs

Calls:
- `_load_from_environment` (line 208, type: attribute)
- `exists` (line 211, type: attribute)
- `warning` (line 212, type: attribute)
- `str` (line 212, type: direct)
- `_create_default_config` (line 213, type: attribute)
- `open` (line 217, type: direct)
- `load` (line 218, type: attribute)
- `items` (line 221, type: attribute)
- `get` (line 221, type: attribute)
- `from_dict` (line 223, type: attribute)
- `error` (line 225, type: attribute)
- `str` (line 225, type: direct)
- `info` (line 228, type: attribute)
- `len` (line 228, type: direct)
- `error` (line 231, type: attribute)
- `str` (line 231, type: direct)
- `str` (line 231, type: direct)
- `_create_default_config` (line 232, type: attribute)

### src\services\config_service.py:ConfigService._persist_settings_to_env

Calls:
- `Path` (line 539, type: direct)
- `exists` (line 543, type: attribute)
- `open` (line 544, type: direct)
- `strip` (line 546, type: attribute)
- `startswith` (line 547, type: attribute)
- `split` (line 548, type: attribute)
- `strip` (line 549, type: attribute)
- `strip` (line 549, type: attribute)
- `items` (line 562, type: attribute)
- `isinstance` (line 566, type: direct)
- `str` (line 569, type: direct)
- `info` (line 570, type: attribute)
- `open` (line 573, type: direct)
- `items` (line 574, type: attribute)
- `write` (line 575, type: attribute)
- `info` (line 577, type: attribute)
- `str` (line 577, type: direct)

### src\services\config_service.py:ConfigService._save_config

Calls:
- `isoformat` (line 351, type: attribute)
- `now` (line 351, type: attribute)
- `to_dict` (line 353, type: attribute)
- `items` (line 354, type: attribute)
- `exists` (line 360, type: attribute)
- `with_suffix` (line 361, type: attribute)
- `copy2` (line 363, type: attribute)
- `open` (line 365, type: direct)
- `dump` (line 366, type: attribute)
- `info` (line 368, type: attribute)
- `str` (line 368, type: direct)
- `error` (line 370, type: attribute)
- `str` (line 370, type: direct)

### src\services\config_service.py:ConfigService.add_printer

Calls:
- `from_dict` (line 326, type: attribute)
- `_save_config` (line 328, type: attribute)
- `info` (line 329, type: attribute)
- `error` (line 332, type: attribute)
- `str` (line 332, type: direct)
- `error` (line 335, type: attribute)
- `str` (line 335, type: direct)

### src\services\config_service.py:ConfigService.add_watch_folder

Calls:
- `_ensure_env_migration` (line 582, type: attribute)
- `get_watch_folder_by_path` (line 585, type: attribute)
- `warning` (line 587, type: attribute)
- `validate_watch_folder` (line 591, type: attribute)
- `error` (line 593, type: attribute)
- `WatchFolder` (line 598, type: direct)
- `Path` (line 600, type: direct)
- `create_watch_folder` (line 605, type: attribute)
- `info` (line 606, type: attribute)
- `error` (line 610, type: attribute)
- `str` (line 610, type: direct)

### src\services\config_service.py:ConfigService.get_active_printers

Calls:
- `items` (line 318, type: attribute)

### src\services\config_service.py:ConfigService.get_application_settings

Calls:
- `get_settings` (line 456, type: direct)
- `str` (line 458, type: direct)
- `getattr` (line 461, type: direct)
- `str` (line 467, type: direct)
- `_get_cors_origins_list` (line 471, type: attribute)
- `str` (line 478, type: direct)
- `getattr` (line 481, type: direct)

### src\services\config_service.py:ConfigService.get_printer

Calls:
- `get` (line 313, type: attribute)

### src\services\config_service.py:ConfigService.get_printers

Calls:
- `copy` (line 309, type: attribute)

### src\services\config_service.py:ConfigService.get_watch_folder_settings

Calls:
- `_ensure_env_migration` (line 443, type: attribute)
- `get_settings` (line 444, type: direct)
- `get_all_watch_folders` (line 445, type: attribute)

### src\services\config_service.py:ConfigService.get_watch_folders

Calls:
- `_ensure_env_migration` (line 409, type: attribute)
- `get_active_folder_paths` (line 410, type: attribute)

### src\services\config_service.py:ConfigService.is_recursive_watching_enabled

Calls:
- `get_settings` (line 419, type: direct)

### src\services\config_service.py:ConfigService.is_watch_folders_enabled

Calls:
- `get_settings` (line 414, type: direct)

### src\services\config_service.py:ConfigService.reload_config

Calls:
- `len` (line 396, type: direct)
- `clear` (line 397, type: attribute)
- `_load_printer_configs` (line 398, type: attribute)
- `info` (line 400, type: attribute)
- `len` (line 401, type: direct)
- `error` (line 404, type: attribute)
- `str` (line 404, type: direct)

### src\services\config_service.py:ConfigService.remove_printer

Calls:
- `_save_config` (line 342, type: attribute)
- `info` (line 343, type: attribute)

### src\services\config_service.py:ConfigService.remove_watch_folder

Calls:
- `_ensure_env_migration` (line 616, type: attribute)
- `get_watch_folder_by_path` (line 619, type: attribute)
- `warning` (line 621, type: attribute)
- `delete_watch_folder_by_path` (line 625, type: attribute)
- `info` (line 627, type: attribute)
- `error` (line 632, type: attribute)
- `str` (line 632, type: direct)

### src\services\config_service.py:ConfigService.update_application_settings

Calls:
- `info` (line 492, type: attribute)
- `get_settings` (line 494, type: direct)
- `info` (line 495, type: attribute)
- `type` (line 495, type: direct)
- `info` (line 503, type: attribute)
- `items` (line 505, type: attribute)
- `info` (line 506, type: attribute)
- `info` (line 508, type: attribute)
- `hasattr` (line 509, type: direct)
- `getattr` (line 510, type: direct)
- `info` (line 511, type: attribute)
- `setattr` (line 513, type: direct)
- `append` (line 514, type: attribute)
- `info` (line 515, type: attribute)
- `warning` (line 517, type: attribute)
- `warning` (line 519, type: attribute)
- `info` (line 523, type: attribute)
- `_persist_settings_to_env` (line 525, type: attribute)
- `info` (line 526, type: attribute)
- `error` (line 528, type: attribute)
- `str` (line 528, type: direct)
- `len` (line 531, type: direct)

### src\services\config_service.py:ConfigService.validate_printer_connection

Calls:
- `get_printer` (line 374, type: attribute)
- `_validate_config` (line 379, type: attribute)
- `str` (line 382, type: direct)

### src\services\config_service.py:ConfigService.validate_watch_folder

Calls:
- `Path` (line 425, type: direct)
- `exists` (line 427, type: attribute)
- `is_dir` (line 430, type: attribute)
- `access` (line 433, type: attribute)
- `str` (line 439, type: direct)

### src\services\config_service.py:PrinterConfig.__post_init__

Calls:
- `_validate_config` (line 35, type: attribute)

### src\services\config_service.py:PrinterConfig._validate_config

Calls:
- `ValueError` (line 41, type: direct)
- `ValueError` (line 44, type: direct)
- `warning` (line 46, type: attribute)

### src\services\config_service.py:PrinterConfig.from_dict

Calls:
- `cls` (line 51, type: direct)
- `get` (line 53, type: attribute)
- `get` (line 54, type: attribute)
- `get` (line 55, type: attribute)
- `get` (line 56, type: attribute)
- `get` (line 57, type: attribute)
- `get` (line 58, type: attribute)
- `get` (line 59, type: attribute)

### src\services\config_service.py:Settings.get_cors_origins

Calls:
- `strip` (line 117, type: attribute)
- `split` (line 117, type: attribute)
- `strip` (line 117, type: attribute)

### src\services\config_service.py:Settings.normalize_downloads_path

Calls:
- `any` (line 137, type: direct)
- `replace` (line 138, type: attribute)
- `replace` (line 138, type: attribute)
- `replace` (line 138, type: attribute)
- `replace` (line 140, type: attribute)
- `replace` (line 142, type: attribute)
- `replace` (line 143, type: attribute)
- `replace` (line 143, type: attribute)
- `replace` (line 143, type: attribute)
- `startswith` (line 147, type: attribute)
- `startswith` (line 147, type: attribute)
- `str` (line 148, type: direct)
- `resolve` (line 148, type: attribute)
- `expanduser` (line 148, type: attribute)
- `Path` (line 148, type: direct)
- `info` (line 154, type: attribute)
- `field_validator` (line 122, type: direct)

### src\services\config_service.py:Settings.normalize_library_path

Calls:
- `any` (line 165, type: direct)
- `replace` (line 166, type: attribute)
- `replace` (line 166, type: attribute)
- `replace` (line 166, type: attribute)
- `replace` (line 168, type: attribute)
- `replace` (line 170, type: attribute)
- `replace` (line 171, type: attribute)
- `replace` (line 171, type: attribute)
- `replace` (line 171, type: attribute)
- `startswith` (line 174, type: attribute)
- `startswith` (line 174, type: attribute)
- `str` (line 175, type: direct)
- `resolve` (line 175, type: attribute)
- `expanduser` (line 175, type: attribute)
- `Path` (line 175, type: direct)
- `info` (line 179, type: attribute)
- `field_validator` (line 157, type: direct)

### src\services\event_service.py:EventService.__init__

Calls:
- `now` (line 31, type: attribute)

### src\services\event_service.py:EventService._file_discovery_task

Calls:
- `info` (line 335, type: attribute)
- `sleep` (line 340, type: attribute)
- `list_printers` (line 349, type: attribute)
- `discover_printer_files` (line 356, type: attribute)
- `extend` (line 359, type: attribute)
- `get` (line 364, type: attribute)
- `get` (line 365, type: attribute)
- `isoformat` (line 366, type: attribute)
- `now` (line 366, type: attribute)
- `len` (line 373, type: direct)
- `debug` (line 377, type: attribute)
- `len` (line 379, type: direct)
- `warning` (line 382, type: attribute)
- `str` (line 383, type: direct)
- `str` (line 388, type: direct)
- `hasattr` (line 392, type: direct)
- `scan_local_files` (line 395, type: attribute)
- `extend` (line 397, type: attribute)
- `get` (line 402, type: attribute)
- `get` (line 403, type: attribute)
- `get` (line 404, type: attribute)
- `isoformat` (line 405, type: attribute)
- `now` (line 405, type: attribute)
- `len` (line 412, type: direct)
- `warning` (line 416, type: attribute)
- `str` (line 416, type: direct)
- `emit_event` (line 419, type: attribute)
- `isoformat` (line 420, type: attribute)
- `now` (line 420, type: attribute)
- `len` (line 423, type: direct)
- `emit_event` (line 429, type: attribute)
- `isoformat` (line 430, type: attribute)
- `now` (line 430, type: attribute)
- `len` (line 432, type: direct)
- `info` (line 435, type: attribute)
- `len` (line 435, type: direct)
- `now` (line 437, type: attribute)
- `error` (line 440, type: attribute)
- `str` (line 440, type: direct)
- `sleep` (line 442, type: attribute)
- `error` (line 447, type: attribute)
- `str` (line 447, type: direct)
- `sleep` (line 448, type: attribute)
- `info` (line 450, type: attribute)

### src\services\event_service.py:EventService._job_status_task

Calls:
- `info` (line 224, type: attribute)
- `sleep` (line 229, type: attribute)
- `get_active_jobs` (line 234, type: attribute)
- `get` (line 240, type: attribute)
- `get` (line 243, type: attribute)
- `get` (line 244, type: attribute)
- `get` (line 245, type: attribute)
- `append` (line 251, type: attribute)
- `isoformat` (line 258, type: attribute)
- `now` (line 258, type: attribute)
- `emit_event` (line 264, type: attribute)
- `isoformat` (line 268, type: attribute)
- `now` (line 268, type: attribute)
- `emit_event` (line 272, type: attribute)
- `isoformat` (line 277, type: attribute)
- `now` (line 277, type: attribute)
- `abs` (line 282, type: direct)
- `append` (line 283, type: attribute)
- `isoformat` (line 290, type: attribute)
- `now` (line 290, type: attribute)
- `isoformat` (line 299, type: attribute)
- `now` (line 299, type: attribute)
- `items` (line 303, type: attribute)
- `emit_event` (line 310, type: attribute)
- `isoformat` (line 311, type: attribute)
- `now` (line 311, type: attribute)
- `len` (line 312, type: direct)
- `debug` (line 318, type: attribute)
- `len` (line 318, type: direct)
- `error` (line 321, type: attribute)
- `str` (line 321, type: direct)
- `sleep` (line 323, type: attribute)
- `error` (line 328, type: attribute)
- `str` (line 328, type: direct)
- `sleep` (line 329, type: attribute)
- `info` (line 331, type: attribute)

### src\services\event_service.py:EventService._printer_monitoring_task

Calls:
- `info` (line 113, type: attribute)
- `sleep` (line 118, type: attribute)
- `list_printers` (line 127, type: attribute)
- `get_printer_status` (line 134, type: attribute)
- `append` (line 137, type: attribute)
- `get` (line 141, type: attribute)
- `get` (line 142, type: attribute)
- `get` (line 143, type: attribute)
- `get` (line 144, type: attribute)
- `isoformat` (line 145, type: attribute)
- `now` (line 145, type: attribute)
- `get` (line 149, type: attribute)
- `get` (line 150, type: attribute)
- `get` (line 150, type: attribute)
- `append` (line 151, type: attribute)
- `get` (line 153, type: attribute)
- `get` (line 154, type: attribute)
- `isoformat` (line 155, type: attribute)
- `now` (line 155, type: attribute)
- `get` (line 159, type: attribute)
- `get` (line 159, type: attribute)
- `emit_event` (line 160, type: attribute)
- `isoformat` (line 163, type: attribute)
- `now` (line 163, type: attribute)
- `get` (line 166, type: attribute)
- `get` (line 166, type: attribute)
- `emit_event` (line 167, type: attribute)
- `isoformat` (line 170, type: attribute)
- `now` (line 170, type: attribute)
- `update_printer_status` (line 179, type: attribute)
- `get` (line 181, type: attribute)
- `now` (line 182, type: attribute)
- `warning` (line 186, type: attribute)
- `str` (line 186, type: direct)
- `append` (line 188, type: attribute)
- `str` (line 193, type: direct)
- `isoformat` (line 194, type: attribute)
- `now` (line 194, type: attribute)
- `emit_event` (line 198, type: attribute)
- `isoformat` (line 199, type: attribute)
- `now` (line 199, type: attribute)
- `debug` (line 205, type: attribute)
- `len` (line 206, type: direct)
- `len` (line 207, type: direct)
- `error` (line 210, type: attribute)
- `str` (line 210, type: direct)
- `sleep` (line 212, type: attribute)
- `error` (line 217, type: attribute)
- `str` (line 217, type: direct)
- `sleep` (line 218, type: attribute)
- `info` (line 220, type: attribute)

### src\services\event_service.py:EventService.emit_event

Calls:
- `copy` (line 100, type: attribute)
- `iscoroutinefunction` (line 103, type: attribute)
- `handler` (line 104, type: direct)
- `handler` (line 106, type: direct)
- `error` (line 108, type: attribute)
- `str` (line 109, type: direct)

### src\services\event_service.py:EventService.force_discovery

Calls:
- `info` (line 495, type: attribute)
- `list_printers` (line 506, type: attribute)
- `discover_printer_files` (line 511, type: attribute)
- `extend` (line 513, type: attribute)
- `len` (line 515, type: direct)
- `str` (line 522, type: direct)
- `emit_event` (line 526, type: attribute)
- `isoformat` (line 527, type: attribute)
- `now` (line 527, type: attribute)
- `len` (line 535, type: direct)
- `len` (line 536, type: direct)
- `error` (line 540, type: attribute)
- `str` (line 540, type: direct)
- `str` (line 541, type: direct)

### src\services\event_service.py:EventService.get_status

Calls:
- `len` (line 456, type: direct)
- `done` (line 456, type: attribute)
- `len` (line 457, type: direct)
- `len` (line 459, type: direct)
- `items` (line 460, type: attribute)
- `len` (line 463, type: direct)
- `len` (line 464, type: direct)
- `isoformat` (line 465, type: attribute)
- `copy` (line 467, type: attribute)

### src\services\event_service.py:EventService.reset_monitoring_state

Calls:
- `info` (line 545, type: attribute)
- `clear` (line 546, type: attribute)
- `clear` (line 547, type: attribute)
- `now` (line 548, type: attribute)

### src\services\event_service.py:EventService.set_services

Calls:
- `info` (line 487, type: attribute)

### src\services\event_service.py:EventService.start

Calls:
- `warning` (line 48, type: attribute)
- `info` (line 52, type: attribute)
- `extend` (line 55, type: attribute)
- `create_task` (line 56, type: attribute)
- `_printer_monitoring_task` (line 56, type: attribute)
- `create_task` (line 57, type: attribute)
- `_job_status_task` (line 57, type: attribute)
- `create_task` (line 58, type: attribute)
- `_file_discovery_task` (line 58, type: attribute)
- `info` (line 61, type: attribute)
- `len` (line 61, type: direct)

### src\services\event_service.py:EventService.stop

Calls:
- `info` (line 68, type: attribute)
- `done` (line 73, type: attribute)
- `cancel` (line 74, type: attribute)
- `gather` (line 78, type: attribute)
- `clear` (line 80, type: attribute)
- `info` (line 81, type: attribute)

### src\services\event_service.py:EventService.subscribe

Calls:
- `append` (line 87, type: attribute)

### src\services\event_service.py:EventService.unsubscribe

Calls:
- `remove` (line 93, type: attribute)

### src\services\file_service.py:FileService.__init__

Calls:
- `BambuParser` (line 34, type: direct)
- `PreviewRenderService` (line 35, type: direct)

### src\services\file_service.py:FileService._extract_printer_info

Calls:
- `get` (line 567, type: attribute)
- `get` (line 574, type: attribute)
- `lower` (line 579, type: attribute)
- `lower` (line 579, type: attribute)
- `lower` (line 586, type: attribute)
- `lower` (line 586, type: attribute)

### src\services\file_service.py:FileService._get_file_type

Calls:
- `lower` (line 540, type: attribute)
- `Path` (line 540, type: direct)
- `get` (line 549, type: attribute)

### src\services\file_service.py:FileService._log_thumbnail_processing

Calls:
- `isoformat` (line 986, type: attribute)
- `utcnow` (line 986, type: attribute)
- `lower` (line 991, type: attribute)
- `Path` (line 991, type: direct)
- `insert` (line 995, type: attribute)
- `len` (line 998, type: direct)

### src\services\file_service.py:FileService.cleanup_download_status

Calls:
- `timestamp` (line 785, type: attribute)
- `now` (line 785, type: attribute)
- `items` (line 789, type: attribute)
- `append` (line 791, type: attribute)
- `info` (line 799, type: attribute)
- `len` (line 799, type: direct)
- `error` (line 801, type: attribute)
- `str` (line 801, type: direct)

### src\services\file_service.py:FileService.delete_file

Calls:
- `get_file_by_id` (line 735, type: attribute)
- `NotFoundError` (line 737, type: direct)
- `get` (line 741, type: attribute)
- `get` (line 742, type: attribute)
- `get` (line 742, type: attribute)
- `get` (line 745, type: attribute)
- `Path` (line 747, type: direct)
- `exists` (line 748, type: attribute)
- `unlink` (line 749, type: attribute)
- `info` (line 750, type: attribute)
- `str` (line 750, type: direct)
- `warning` (line 752, type: attribute)
- `str` (line 752, type: direct)
- `get` (line 755, type: attribute)
- `delete_local_file` (line 756, type: attribute)
- `update_file` (line 759, type: attribute)
- `info` (line 767, type: attribute)
- `emit_event` (line 770, type: attribute)
- `get` (line 772, type: attribute)
- `get` (line 773, type: attribute)
- `error` (line 779, type: attribute)
- `str` (line 779, type: direct)

### src\services\file_service.py:FileService.discover_printer_files

Calls:
- `info` (line 662, type: attribute)
- `get_printer_files` (line 665, type: attribute)
- `append` (line 670, type: attribute)
- `get` (line 672, type: attribute)
- `get` (line 673, type: attribute)
- `get` (line 675, type: attribute)
- `info` (line 678, type: attribute)
- `len` (line 680, type: direct)
- `error` (line 685, type: attribute)
- `str` (line 685, type: direct)

### src\services\file_service.py:FileService.download_file

Calls:
- `ValueError` (line 197, type: direct)
- `warning` (line 213, type: attribute)
- `str` (line 214, type: direct)
- `Path` (line 216, type: direct)
- `mkdir` (line 218, type: attribute)
- `debug` (line 219, type: attribute)
- `str` (line 219, type: direct)
- `error` (line 222, type: attribute)
- `str` (line 223, type: direct)
- `str` (line 223, type: direct)
- `ValueError` (line 224, type: direct)
- `str` (line 225, type: direct)
- `info` (line 227, type: attribute)
- `download_printer_file` (line 234, type: attribute)
- `update_file` (line 241, type: attribute)
- `isoformat` (line 244, type: attribute)
- `now` (line 244, type: attribute)
- `exists` (line 252, type: attribute)
- `Path` (line 252, type: direct)
- `error` (line 253, type: attribute)
- `stat` (line 262, type: attribute)
- `Path` (line 262, type: direct)
- `info` (line 263, type: attribute)
- `info` (line 268, type: attribute)
- `create_task` (line 272, type: attribute)
- `process_file_thumbnails` (line 272, type: attribute)
- `get_printer` (line 278, type: attribute)
- `get` (line 279, type: attribute)
- `_extract_printer_info` (line 282, type: attribute)
- `isoformat` (line 295, type: attribute)
- `now` (line 295, type: attribute)
- `add_file_to_library` (line 299, type: attribute)
- `Path` (line 300, type: direct)
- `info` (line 305, type: attribute)
- `error` (line 313, type: attribute)
- `str` (line 316, type: direct)
- `emit_event` (line 321, type: attribute)
- `warning` (line 328, type: attribute)
- `str` (line 328, type: direct)
- `info` (line 330, type: attribute)
- `error` (line 341, type: attribute)
- `str` (line 342, type: direct)
- `str` (line 346, type: direct)
- `error` (line 358, type: attribute)
- `str` (line 358, type: direct)
- `str` (line 363, type: direct)

### src\services\file_service.py:FileService.extract_enhanced_metadata

Calls:
- `info` (line 1028, type: attribute)
- `get_file` (line 1031, type: attribute)
- `error` (line 1033, type: attribute)
- `get` (line 1036, type: attribute)
- `exists` (line 1037, type: attribute)
- `Path` (line 1037, type: direct)
- `warning` (line 1038, type: attribute)
- `Path` (line 1042, type: direct)
- `lower` (line 1043, type: attribute)
- `ThreeMFAnalyzer` (line 1050, type: direct)
- `analyze_file` (line 1051, type: attribute)
- `get` (line 1053, type: attribute)
- `warning` (line 1056, type: attribute)
- `get` (line 1057, type: attribute)
- `parse_file` (line 1062, type: attribute)
- `str` (line 1062, type: direct)
- `get` (line 1064, type: attribute)
- `get` (line 1065, type: attribute)
- `get` (line 1070, type: attribute)
- `get` (line 1071, type: attribute)
- `get` (line 1072, type: attribute)
- `get` (line 1076, type: attribute)
- `get` (line 1077, type: attribute)
- `get` (line 1078, type: attribute)
- `get` (line 1079, type: attribute)
- `get` (line 1080, type: attribute)
- `get` (line 1081, type: attribute)
- `get` (line 1081, type: attribute)
- `get` (line 1082, type: attribute)
- `get` (line 1082, type: attribute)
- `get` (line 1083, type: attribute)
- `get` (line 1083, type: attribute)
- `get` (line 1084, type: attribute)
- `get` (line 1085, type: attribute)
- `get` (line 1086, type: attribute)
- `get` (line 1087, type: attribute)
- `get` (line 1090, type: attribute)
- `get` (line 1090, type: attribute)
- `get` (line 1091, type: attribute)
- `isinstance` (line 1092, type: direct)
- `get` (line 1092, type: attribute)
- `len` (line 1093, type: direct)
- `get` (line 1093, type: attribute)
- `get` (line 1096, type: attribute)
- `get` (line 1097, type: attribute)
- `get` (line 1098, type: attribute)
- `get` (line 1101, type: attribute)
- `get` (line 1102, type: attribute)
- `get` (line 1103, type: attribute)
- `get` (line 1103, type: attribute)
- `get` (line 1106, type: attribute)
- `get` (line 1107, type: attribute)
- `get` (line 1108, type: attribute)
- `warning` (line 1113, type: attribute)
- `warning` (line 1117, type: attribute)
- `EnhancedFileMetadata` (line 1123, type: direct)
- `get` (line 1125, type: attribute)
- `PhysicalProperties` (line 1124, type: direct)
- `get` (line 1124, type: attribute)
- `get` (line 1127, type: attribute)
- `PrintSettings` (line 1126, type: direct)
- `get` (line 1126, type: attribute)
- `get` (line 1129, type: attribute)
- `MaterialRequirements` (line 1128, type: direct)
- `get` (line 1128, type: attribute)
- `get` (line 1131, type: attribute)
- `CostBreakdown` (line 1130, type: direct)
- `get` (line 1130, type: attribute)
- `get` (line 1133, type: attribute)
- `QualityMetrics` (line 1132, type: direct)
- `get` (line 1132, type: attribute)
- `get` (line 1135, type: attribute)
- `CompatibilityInfo` (line 1134, type: direct)
- `get` (line 1134, type: attribute)
- `update_file_enhanced_metadata` (line 1139, type: attribute)
- `model_dump` (line 1141, type: attribute)
- `now` (line 1142, type: attribute)
- `info` (line 1145, type: attribute)
- `emit_event` (line 1148, type: attribute)
- `str` (line 1150, type: direct)
- `model_dump` (line 1156, type: attribute)
- `error` (line 1159, type: attribute)
- `str` (line 1159, type: direct)
- `error` (line 1163, type: attribute)
- `str` (line 1163, type: direct)
- `copy` (line 1164, type: attribute)

### src\services\file_service.py:FileService.find_file_by_name

Calls:
- `list_files` (line 713, type: attribute)
- `get` (line 715, type: attribute)
- `dict` (line 716, type: direct)
- `get_local_files` (line 720, type: attribute)
- `get` (line 722, type: attribute)
- `get` (line 724, type: attribute)
- `dict` (line 725, type: direct)
- `error` (line 729, type: attribute)
- `str` (line 729, type: direct)

### src\services\file_service.py:FileService.get_download_status

Calls:
- `get` (line 375, type: attribute)
- `list_files` (line 379, type: attribute)
- `get` (line 384, type: attribute)
- `get` (line 385, type: attribute)
- `get` (line 386, type: attribute)
- `get` (line 387, type: attribute)
- `error` (line 398, type: attribute)
- `str` (line 398, type: direct)
- `str` (line 403, type: direct)

### src\services\file_service.py:FileService.get_file_by_id

Calls:
- `list_files` (line 692, type: attribute)
- `dict` (line 695, type: direct)
- `get_local_files` (line 699, type: attribute)
- `get` (line 701, type: attribute)
- `dict` (line 702, type: direct)
- `error` (line 706, type: attribute)
- `str` (line 706, type: direct)

### src\services\file_service.py:FileService.get_file_statistics

Calls:
- `get_files` (line 462, type: attribute)
- `len` (line 465, type: direct)
- `get` (line 468, type: attribute)
- `get` (line 469, type: attribute)
- `sum` (line 472, type: direct)
- `get` (line 472, type: attribute)
- `len` (line 476, type: direct)
- `get` (line 476, type: attribute)
- `len` (line 479, type: direct)
- `get` (line 479, type: attribute)
- `len` (line 482, type: direct)
- `get` (line 482, type: attribute)
- `len` (line 485, type: direct)
- `info` (line 491, type: attribute)
- `len` (line 495, type: direct)
- `len` (line 497, type: direct)
- `debug` (line 503, type: attribute)
- `min` (line 504, type: direct)
- `len` (line 504, type: direct)
- `get` (line 506, type: attribute)
- `get` (line 507, type: attribute)
- `get` (line 508, type: attribute)
- `get` (line 509, type: attribute)
- `len` (line 514, type: direct)
- `len` (line 515, type: direct)
- `error` (line 525, type: attribute)
- `str` (line 525, type: direct)

### src\services\file_service.py:FileService.get_files

Calls:
- `list_files` (line 58, type: attribute)
- `list_printers` (line 67, type: attribute)
- `warning` (line 71, type: attribute)
- `str` (line 71, type: direct)
- `dict` (line 75, type: direct)
- `get` (line 79, type: attribute)
- `hasattr` (line 84, type: direct)
- `str` (line 84, type: direct)
- `append` (line 94, type: attribute)
- `debug` (line 96, type: attribute)
- `len` (line 96, type: direct)
- `error` (line 99, type: attribute)
- `str` (line 99, type: direct)
- `get_local_files` (line 104, type: attribute)
- `get` (line 108, type: attribute)
- `extend` (line 113, type: attribute)
- `debug` (line 114, type: attribute)
- `len` (line 114, type: direct)
- `error` (line 116, type: attribute)
- `str` (line 116, type: direct)
- `get` (line 120, type: attribute)
- `get` (line 120, type: attribute)
- `get` (line 123, type: attribute)
- `get` (line 126, type: attribute)
- `bool` (line 129, type: direct)
- `get` (line 129, type: attribute)
- `lower` (line 133, type: attribute)
- `lower` (line 134, type: attribute)
- `get` (line 134, type: attribute)
- `lower` (line 137, type: attribute)
- `sorted` (line 139, type: direct)
- `get` (line 139, type: attribute)
- `get` (line 139, type: attribute)
- `sorted` (line 141, type: direct)
- `get` (line 141, type: attribute)
- `sorted` (line 143, type: direct)
- `get` (line 143, type: attribute)
- `sorted` (line 145, type: direct)
- `get` (line 145, type: attribute)

### src\services\file_service.py:FileService.get_local_files

Calls:
- `get_local_files` (line 412, type: attribute)
- `error` (line 414, type: attribute)
- `str` (line 414, type: direct)

### src\services\file_service.py:FileService.get_printer_files

Calls:
- `warning` (line 158, type: attribute)
- `get_printer_files` (line 162, type: attribute)
- `get` (line 172, type: attribute)
- `_get_file_type` (line 173, type: attribute)
- `get` (line 177, type: attribute)
- `create_file` (line 181, type: attribute)
- `append` (line 182, type: attribute)
- `info` (line 184, type: attribute)
- `len` (line 184, type: direct)
- `error` (line 188, type: attribute)
- `str` (line 188, type: direct)
- `list_files` (line 190, type: attribute)

### src\services\file_service.py:FileService.get_watch_status

Calls:
- `get_watch_status` (line 441, type: attribute)
- `error` (line 443, type: attribute)
- `str` (line 443, type: direct)
- `str` (line 444, type: direct)

### src\services\file_service.py:FileService.process_file_thumbnails

Calls:
- `utcnow` (line 814, type: attribute)
- `_log_thumbnail_processing` (line 818, type: attribute)
- `exists` (line 820, type: attribute)
- `warning` (line 822, type: attribute)
- `_log_thumbnail_processing` (line 823, type: attribute)
- `parse_file` (line 827, type: attribute)
- `get` (line 830, type: attribute)
- `info` (line 831, type: attribute)
- `_log_thumbnail_processing` (line 833, type: attribute)
- `get_thumbnail_by_size` (line 848, type: attribute)
- `get` (line 856, type: attribute)
- `get` (line 858, type: attribute)
- `startswith` (line 862, type: attribute)
- `split` (line 866, type: attribute)
- `basename` (line 866, type: attribute)
- `info` (line 868, type: attribute)
- `get` (line 872, type: attribute)
- `hasattr` (line 873, type: direct)
- `download_thumbnail` (line 874, type: attribute)
- `decode` (line 877, type: attribute)
- `b64encode` (line 877, type: attribute)
- `len` (line 879, type: direct)
- `unpack` (line 882, type: attribute)
- `info` (line 893, type: attribute)
- `len` (line 894, type: direct)
- `warning` (line 896, type: attribute)
- `str` (line 897, type: direct)
- `_get_file_type` (line 903, type: attribute)
- `basename` (line 903, type: attribute)
- `info` (line 904, type: attribute)
- `get_or_generate_preview` (line 907, type: attribute)
- `decode` (line 912, type: attribute)
- `b64encode` (line 912, type: attribute)
- `info` (line 917, type: attribute)
- `warning` (line 920, type: attribute)
- `error` (line 923, type: attribute)
- `str` (line 924, type: direct)
- `get_file_by_id` (line 937, type: attribute)
- `get` (line 939, type: attribute)
- `update_file` (line 945, type: attribute)
- `len` (line 948, type: direct)
- `info` (line 949, type: attribute)
- `len` (line 952, type: direct)
- `len` (line 953, type: direct)
- `list` (line 954, type: direct)
- `keys` (line 954, type: attribute)
- `_log_thumbnail_processing` (line 956, type: attribute)
- `len` (line 957, type: direct)
- `emit_event` (line 960, type: attribute)
- `len` (line 963, type: direct)
- `len` (line 964, type: direct)
- `error` (line 971, type: attribute)
- `_log_thumbnail_processing` (line 972, type: attribute)
- `str` (line 976, type: direct)
- `error` (line 977, type: attribute)
- `str` (line 978, type: direct)
- `_log_thumbnail_processing` (line 979, type: attribute)

### src\services\file_service.py:FileService.reload_watch_folders

Calls:
- `reload_watch_folders` (line 452, type: attribute)
- `error` (line 455, type: attribute)
- `str` (line 455, type: direct)
- `str` (line 456, type: direct)

### src\services\file_service.py:FileService.scan_local_files

Calls:
- `get_local_files` (line 424, type: attribute)
- `debug` (line 429, type: attribute)
- `len` (line 429, type: direct)
- `error` (line 432, type: attribute)
- `str` (line 432, type: direct)

### src\services\file_service.py:FileService.sync_printer_files

Calls:
- `info` (line 602, type: attribute)
- `get_printer_files` (line 605, type: attribute)
- `list_files` (line 608, type: attribute)
- `update_file` (line 621, type: attribute)
- `info` (line 626, type: attribute)
- `len` (line 628, type: direct)
- `len` (line 629, type: direct)
- `len` (line 634, type: direct)
- `len` (line 635, type: direct)
- `isoformat` (line 637, type: attribute)
- `now` (line 637, type: attribute)
- `error` (line 641, type: attribute)
- `str` (line 641, type: direct)
- `str` (line 644, type: direct)
- `isoformat` (line 645, type: attribute)
- `now` (line 645, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService.__init__

Calls:
- `Lock` (line 136, type: attribute)
- `PrintFileHandler` (line 139, type: direct)

### src\services\file_watcher_service.py:FileWatcherService._add_watch_folder

Calls:
- `Path` (line 244, type: direct)
- `validate_watch_folder` (line 247, type: attribute)
- `str` (line 247, type: direct)
- `error` (line 249, type: attribute)
- `schedule` (line 258, type: attribute)
- `str` (line 260, type: direct)
- `info` (line 263, type: attribute)
- `info` (line 266, type: attribute)
- `error` (line 277, type: attribute)
- `str` (line 278, type: direct)

### src\services\file_watcher_service.py:FileWatcherService._emit_file_event

Calls:
- `isoformat` (line 479, type: attribute)
- `emit_event` (line 485, type: attribute)
- `error` (line 488, type: attribute)
- `str` (line 489, type: direct)

### src\services\file_watcher_service.py:FileWatcherService._find_watch_folder_for_file

Calls:
- `Path` (line 390, type: direct)
- `keys` (line 392, type: attribute)
- `Path` (line 393, type: direct)
- `relative_to` (line 396, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService._handle_file_created

Calls:
- `_process_discovered_file` (line 405, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService._handle_file_deleted

Calls:
- `list` (line 432, type: direct)
- `items` (line 432, type: attribute)
- `_emit_file_event` (line 436, type: attribute)
- `debug` (line 438, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService._handle_file_modified

Calls:
- `values` (line 410, type: attribute)
- `Path` (line 414, type: direct)
- `exists` (line 415, type: attribute)
- `stat` (line 416, type: attribute)
- `fromtimestamp` (line 418, type: attribute)
- `_emit_file_event` (line 420, type: attribute)
- `debug` (line 422, type: attribute)
- `error` (line 425, type: attribute)
- `str` (line 426, type: direct)

### src\services\file_watcher_service.py:FileWatcherService._handle_file_moved

Calls:
- `values` (line 445, type: attribute)
- `Path` (line 448, type: direct)
- `str` (line 449, type: direct)
- `_find_watch_folder_for_file` (line 453, type: attribute)
- `Path` (line 455, type: direct)
- `relative_to` (line 457, type: attribute)
- `str` (line 458, type: direct)
- `_emit_file_event` (line 462, type: attribute)
- `debug` (line 464, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService._initial_scan

Calls:
- `info` (line 282, type: attribute)
- `items` (line 284, type: attribute)
- `_scan_folder` (line 286, type: attribute)
- `error` (line 289, type: attribute)
- `str` (line 290, type: direct)
- `info` (line 292, type: attribute)
- `len` (line 292, type: direct)

### src\services\file_watcher_service.py:FileWatcherService._process_discovered_file

Calls:
- `Path` (line 313, type: direct)
- `exists` (line 315, type: attribute)
- `stat` (line 318, type: attribute)
- `_find_watch_folder_for_file` (line 321, type: attribute)
- `warning` (line 323, type: attribute)
- `Path` (line 327, type: direct)
- `relative_to` (line 329, type: attribute)
- `Path` (line 331, type: direct)
- `abs` (line 334, type: direct)
- `hash` (line 334, type: direct)
- `LocalFile` (line 337, type: direct)
- `str` (line 340, type: direct)
- `lower` (line 342, type: attribute)
- `fromtimestamp` (line 343, type: attribute)
- `str` (line 345, type: direct)
- `str` (line 357, type: direct)
- `isoformat` (line 358, type: attribute)
- `now` (line 358, type: attribute)
- `add_file_to_library` (line 362, type: attribute)
- `info` (line 368, type: attribute)
- `error` (line 373, type: attribute)
- `str` (line 375, type: direct)
- `_emit_file_event` (line 379, type: attribute)
- `debug` (line 381, type: attribute)
- `error` (line 385, type: attribute)
- `str` (line 386, type: direct)

### src\services\file_watcher_service.py:FileWatcherService._scan_folder

Calls:
- `glob` (line 302, type: attribute)
- `is_file` (line 303, type: attribute)
- `should_process_file` (line 303, type: attribute)
- `str` (line 303, type: direct)
- `_process_discovered_file` (line 304, type: attribute)
- `str` (line 304, type: direct)
- `error` (line 307, type: attribute)
- `str` (line 308, type: direct)
- `str` (line 308, type: direct)

### src\services\file_watcher_service.py:FileWatcherService.get_local_files

Calls:
- `values` (line 495, type: attribute)
- `append` (line 496, type: attribute)
- `isoformat` (line 502, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService.get_watch_status

Calls:
- `list` (line 515, type: direct)
- `keys` (line 515, type: attribute)
- `len` (line 516, type: direct)
- `list` (line 517, type: direct)

### src\services\file_watcher_service.py:FileWatcherService.reload_watch_folders

Calls:
- `warning` (line 523, type: attribute)
- `stop` (line 528, type: attribute)
- `start` (line 531, type: attribute)
- `info` (line 533, type: attribute)
- `error` (line 536, type: attribute)
- `str` (line 536, type: direct)

### src\services\file_watcher_service.py:FileWatcherService.start

Calls:
- `warning` (line 144, type: attribute)
- `debug` (line 147, type: attribute)
- `type` (line 147, type: direct)
- `type` (line 147, type: direct)
- `is_watch_folders_enabled` (line 149, type: attribute)
- `info` (line 150, type: attribute)
- `Observer` (line 156, type: direct)
- `warning` (line 158, type: attribute)
- `str` (line 158, type: direct)
- `WindowsObserver` (line 160, type: direct)
- `get_watch_folders` (line 163, type: attribute)
- `is_recursive_watching_enabled` (line 164, type: attribute)
- `_add_watch_folder` (line 167, type: attribute)
- `start` (line 173, type: attribute)
- `info` (line 176, type: attribute)
- `len` (line 177, type: direct)
- `type` (line 179, type: direct)
- `warning` (line 181, type: attribute)
- `str` (line 182, type: direct)
- `type` (line 183, type: direct)
- `stop` (line 188, type: attribute)
- `_initial_scan` (line 195, type: attribute)
- `error` (line 198, type: attribute)
- `str` (line 198, type: direct)
- `info` (line 201, type: attribute)

### src\services\file_watcher_service.py:FileWatcherService.stop

Calls:
- `stop` (line 213, type: attribute)
- `hasattr` (line 216, type: direct)
- `is_alive` (line 216, type: attribute)
- `get_running_loop` (line 218, type: attribute)
- `run_in_executor` (line 219, type: attribute)
- `join` (line 221, type: attribute)
- `hasattr` (line 225, type: direct)
- `is_alive` (line 225, type: attribute)
- `warning` (line 226, type: attribute)
- `warning` (line 229, type: attribute)
- `str` (line 229, type: direct)
- `clear` (line 233, type: attribute)
- `info` (line 236, type: attribute)
- `error` (line 239, type: attribute)
- `str` (line 239, type: direct)

### src\services\file_watcher_service.py:PrintFileHandler.__init__

Calls:
- `__init__` (line 56, type: attribute)
- `super` (line 56, type: direct)

### src\services\file_watcher_service.py:PrintFileHandler._debounce_event

Calls:
- `now` (line 82, type: attribute)
- `total_seconds` (line 86, type: attribute)

### src\services\file_watcher_service.py:PrintFileHandler.on_created

Calls:
- `should_process_file` (line 94, type: attribute)
- `_debounce_event` (line 95, type: attribute)
- `info` (line 96, type: attribute)
- `create_task` (line 97, type: attribute)
- `_handle_file_created` (line 97, type: attribute)

### src\services\file_watcher_service.py:PrintFileHandler.on_deleted

Calls:
- `should_process_file` (line 108, type: attribute)
- `info` (line 109, type: attribute)
- `create_task` (line 110, type: attribute)
- `_handle_file_deleted` (line 110, type: attribute)

### src\services\file_watcher_service.py:PrintFileHandler.on_modified

Calls:
- `should_process_file` (line 101, type: attribute)
- `_debounce_event` (line 102, type: attribute)
- `debug` (line 103, type: attribute)
- `create_task` (line 104, type: attribute)
- `_handle_file_modified` (line 104, type: attribute)

### src\services\file_watcher_service.py:PrintFileHandler.on_moved

Calls:
- `hasattr` (line 114, type: direct)
- `should_process_file` (line 115, type: attribute)
- `info` (line 116, type: attribute)
- `create_task` (line 118, type: attribute)
- `_handle_file_moved` (line 119, type: attribute)

### src\services\file_watcher_service.py:PrintFileHandler.should_process_file

Calls:
- `Path` (line 63, type: direct)
- `lower` (line 66, type: attribute)
- `startswith` (line 71, type: attribute)
- `endswith` (line 72, type: attribute)
- `startswith` (line 74, type: attribute)
- `startswith` (line 75, type: attribute)

### src\services\idea_service.py:IdeaService.__init__

Calls:
- `UrlParserService` (line 22, type: direct)

### src\services\idea_service.py:IdeaService._extract_url_metadata

Calls:
- `parse_url` (line 236, type: attribute)
- `error` (line 238, type: attribute)
- `str` (line 238, type: direct)

### src\services\idea_service.py:IdeaService.cache_trending

Calls:
- `now` (line 246, type: attribute)
- `timedelta` (line 246, type: direct)
- `get` (line 250, type: attribute)
- `uuid4` (line 250, type: attribute)
- `str` (line 252, type: direct)
- `get` (line 252, type: attribute)
- `uuid4` (line 252, type: attribute)
- `get` (line 255, type: attribute)
- `get` (line 256, type: attribute)
- `get` (line 257, type: attribute)
- `get` (line 258, type: attribute)
- `get` (line 259, type: attribute)
- `isoformat` (line 260, type: attribute)
- `upsert_trending` (line 263, type: attribute)
- `info` (line 265, type: attribute)
- `len` (line 265, type: direct)
- `error` (line 269, type: attribute)
- `str` (line 269, type: direct)

### src\services\idea_service.py:IdeaService.cleanup_expired_trending

Calls:
- `clean_expired_trending` (line 323, type: attribute)
- `info` (line 325, type: attribute)
- `error` (line 329, type: attribute)
- `str` (line 329, type: direct)

### src\services\idea_service.py:IdeaService.create_idea

Calls:
- `str` (line 29, type: direct)
- `uuid4` (line 29, type: attribute)
- `get` (line 32, type: attribute)
- `ValueError` (line 33, type: direct)
- `from_dict` (line 36, type: attribute)
- `validate` (line 37, type: attribute)
- `ValueError` (line 38, type: direct)
- `to_dict` (line 41, type: attribute)
- `get` (line 44, type: attribute)
- `dumps` (line 45, type: attribute)
- `create_idea` (line 48, type: attribute)
- `RuntimeError` (line 50, type: direct)
- `get` (line 53, type: attribute)
- `add_idea_tags` (line 54, type: attribute)
- `info` (line 56, type: attribute)
- `error` (line 60, type: attribute)
- `str` (line 60, type: direct)

### src\services\idea_service.py:IdeaService.delete_idea

Calls:
- `delete_idea` (line 168, type: attribute)
- `info` (line 170, type: attribute)
- `error` (line 174, type: attribute)
- `str` (line 174, type: direct)

### src\services\idea_service.py:IdeaService.get_all_tags

Calls:
- `get_all_tags` (line 192, type: attribute)
- `error` (line 194, type: attribute)
- `str` (line 194, type: direct)

### src\services\idea_service.py:IdeaService.get_idea

Calls:
- `get_idea` (line 67, type: attribute)
- `get` (line 72, type: attribute)
- `loads` (line 74, type: attribute)
- `get_idea_tags` (line 79, type: attribute)
- `from_dict` (line 82, type: attribute)
- `error` (line 85, type: attribute)
- `str` (line 85, type: direct)

### src\services\idea_service.py:IdeaService.get_statistics

Calls:
- `get_idea_statistics` (line 200, type: attribute)
- `error` (line 202, type: attribute)
- `str` (line 202, type: direct)

### src\services\idea_service.py:IdeaService.get_trending

Calls:
- `get_trending` (line 276, type: attribute)
- `to_dict` (line 277, type: attribute)
- `from_dict` (line 277, type: attribute)
- `error` (line 280, type: attribute)
- `str` (line 280, type: direct)

### src\services\idea_service.py:IdeaService.import_from_url

Calls:
- `_extract_url_metadata` (line 209, type: attribute)
- `ValueError` (line 211, type: direct)
- `get` (line 215, type: attribute)
- `get` (line 216, type: attribute)
- `get` (line 217, type: attribute)
- `get` (line 219, type: attribute)
- `update` (line 225, type: attribute)
- `create_idea` (line 227, type: attribute)
- `error` (line 230, type: attribute)
- `str` (line 230, type: direct)

### src\services\idea_service.py:IdeaService.list_ideas

Calls:
- `list_ideas` (line 96, type: attribute)
- `get` (line 97, type: attribute)
- `get` (line 98, type: attribute)
- `get` (line 99, type: attribute)
- `get` (line 100, type: attribute)
- `get` (line 108, type: attribute)
- `loads` (line 110, type: attribute)
- `get_idea_tags` (line 115, type: attribute)
- `append` (line 118, type: attribute)
- `from_dict` (line 118, type: attribute)
- `to_dict` (line 121, type: attribute)
- `len` (line 127, type: direct)
- `error` (line 131, type: attribute)
- `str` (line 131, type: direct)

### src\services\idea_service.py:IdeaService.save_trending_as_idea

Calls:
- `get_trending` (line 288, type: attribute)
- `next` (line 289, type: direct)
- `ValueError` (line 292, type: direct)
- `get` (line 300, type: attribute)
- `get` (line 304, type: attribute)
- `get` (line 305, type: attribute)
- `get` (line 306, type: attribute)
- `update` (line 312, type: attribute)
- `create_idea` (line 314, type: attribute)
- `error` (line 317, type: attribute)
- `str` (line 317, type: direct)

### src\services\idea_service.py:IdeaService.search_ideas

Calls:
- `list_ideas` (line 336, type: attribute)
- `lower` (line 340, type: attribute)
- `lower` (line 344, type: attribute)
- `get` (line 345, type: attribute)
- `lower` (line 345, type: attribute)
- `any` (line 346, type: direct)
- `lower` (line 346, type: attribute)
- `get` (line 346, type: attribute)
- `append` (line 347, type: attribute)
- `error` (line 352, type: attribute)
- `str` (line 352, type: direct)

### src\services\idea_service.py:IdeaService.update_idea

Calls:
- `dumps` (line 139, type: attribute)
- `pop` (line 142, type: attribute)
- `update_idea` (line 145, type: attribute)
- `get_idea_tags` (line 152, type: attribute)
- `remove_idea_tags` (line 154, type: attribute)
- `add_idea_tags` (line 156, type: attribute)
- `info` (line 158, type: attribute)
- `error` (line 162, type: attribute)
- `str` (line 162, type: direct)

### src\services\idea_service.py:IdeaService.update_idea_status

Calls:
- `update_idea_status` (line 180, type: attribute)
- `info` (line 182, type: attribute)
- `error` (line 186, type: attribute)
- `str` (line 186, type: direct)

### src\services\job_service.py:JobService.calculate_material_costs

Calls:
- `get_job` (line 437, type: attribute)
- `get` (line 444, type: attribute)
- `get` (line 448, type: attribute)
- `update_job` (line 455, type: attribute)
- `info` (line 460, type: attribute)
- `error` (line 464, type: attribute)
- `str` (line 464, type: direct)
- `str` (line 465, type: direct)

### src\services\job_service.py:JobService.create_job

Calls:
- `isinstance` (line 234, type: direct)
- `JobCreate` (line 235, type: direct)
- `str` (line 240, type: direct)
- `uuid4` (line 240, type: attribute)
- `ValueError` (line 242, type: direct)
- `dumps` (line 254, type: attribute)
- `get` (line 260, type: attribute)
- `ValueError` (line 261, type: direct)
- `create_job` (line 264, type: attribute)
- `info` (line 267, type: attribute)
- `emit_event` (line 270, type: attribute)
- `isoformat` (line 275, type: attribute)
- `now` (line 275, type: attribute)
- `error` (line 280, type: attribute)
- `Exception` (line 281, type: direct)
- `error` (line 284, type: attribute)
- `str` (line 284, type: direct)
- `type` (line 284, type: direct)

### src\services\job_service.py:JobService.delete_job

Calls:
- `get_job` (line 171, type: attribute)
- `str` (line 171, type: direct)
- `warning` (line 173, type: attribute)
- `delete_job` (line 177, type: attribute)
- `str` (line 177, type: direct)
- `info` (line 180, type: attribute)
- `emit_event` (line 182, type: attribute)
- `str` (line 183, type: direct)
- `isoformat` (line 184, type: attribute)
- `now` (line 184, type: attribute)
- `error` (line 190, type: attribute)
- `str` (line 190, type: direct)

### src\services\job_service.py:JobService.get_active_jobs

Calls:
- `list_jobs` (line 201, type: attribute)
- `extend` (line 202, type: attribute)
- `get` (line 209, type: attribute)
- `loads` (line 210, type: attribute)
- `get` (line 214, type: attribute)
- `fromisoformat` (line 215, type: attribute)
- `Job` (line 217, type: direct)
- `append` (line 218, type: attribute)
- `dict` (line 218, type: attribute)
- `warning` (line 220, type: attribute)
- `get` (line 220, type: attribute)
- `str` (line 220, type: direct)
- `info` (line 223, type: attribute)
- `len` (line 223, type: direct)
- `error` (line 227, type: attribute)
- `str` (line 227, type: direct)

### src\services\job_service.py:JobService.get_business_jobs

Calls:
- `list_jobs` (line 428, type: attribute)

### src\services\job_service.py:JobService.get_job

Calls:
- `get_job` (line 145, type: attribute)
- `str` (line 145, type: direct)
- `get` (line 150, type: attribute)
- `loads` (line 151, type: attribute)
- `get` (line 155, type: attribute)
- `fromisoformat` (line 156, type: attribute)
- `Job` (line 159, type: direct)
- `info` (line 160, type: attribute)
- `dict` (line 161, type: attribute)
- `error` (line 164, type: attribute)
- `str` (line 164, type: direct)

### src\services\job_service.py:JobService.get_job_statistics

Calls:
- `get_job_statistics` (line 343, type: attribute)
- `get` (line 347, type: attribute)
- `get` (line 348, type: attribute)
- `get` (line 349, type: attribute)
- `items` (line 375, type: attribute)
- `info` (line 379, type: attribute)
- `error` (line 383, type: attribute)
- `str` (line 383, type: direct)

### src\services\job_service.py:JobService.get_jobs

Calls:
- `list_jobs` (line 28, type: attribute)
- `get` (line 41, type: attribute)
- `error` (line 42, type: attribute)
- `get` (line 43, type: attribute)
- `get` (line 44, type: attribute)
- `get` (line 50, type: attribute)
- `loads` (line 51, type: attribute)
- `get` (line 55, type: attribute)
- `fromisoformat` (line 56, type: attribute)
- `Job` (line 58, type: direct)
- `append` (line 59, type: attribute)
- `dict` (line 59, type: attribute)
- `error` (line 61, type: attribute)
- `get` (line 62, type: attribute)
- `str` (line 63, type: direct)
- `type` (line 64, type: direct)
- `warning` (line 69, type: attribute)
- `len` (line 71, type: direct)
- `info` (line 73, type: attribute)
- `len` (line 73, type: direct)
- `len` (line 73, type: direct)
- `error` (line 77, type: attribute)
- `str` (line 77, type: direct)

### src\services\job_service.py:JobService.get_jobs_by_date_range

Calls:
- `get_jobs_by_date_range` (line 394, type: attribute)
- `get` (line 401, type: attribute)
- `loads` (line 402, type: attribute)
- `get` (line 406, type: attribute)
- `fromisoformat` (line 407, type: attribute)
- `Job` (line 409, type: direct)
- `append` (line 410, type: attribute)
- `dict` (line 410, type: attribute)
- `warning` (line 412, type: attribute)
- `get` (line 412, type: attribute)
- `str` (line 412, type: direct)
- `info` (line 415, type: attribute)
- `len` (line 419, type: direct)
- `error` (line 423, type: attribute)
- `str` (line 423, type: direct)

### src\services\job_service.py:JobService.get_printer_jobs

Calls:
- `list_jobs` (line 469, type: attribute)

### src\services\job_service.py:JobService.get_private_jobs

Calls:
- `list_jobs` (line 432, type: attribute)

### src\services\job_service.py:JobService.list_jobs

Calls:
- `list_jobs` (line 84, type: attribute)
- `get` (line 98, type: attribute)
- `error` (line 99, type: attribute)
- `get` (line 100, type: attribute)
- `get` (line 101, type: attribute)
- `get` (line 106, type: attribute)
- `loads` (line 107, type: attribute)
- `get` (line 111, type: attribute)
- `fromisoformat` (line 112, type: attribute)
- `Job` (line 114, type: direct)
- `append` (line 115, type: attribute)
- `dict` (line 115, type: attribute)
- `error` (line 117, type: attribute)
- `get` (line 118, type: attribute)
- `str` (line 119, type: direct)
- `type` (line 120, type: direct)
- `warning` (line 125, type: attribute)
- `len` (line 127, type: direct)
- `info` (line 129, type: attribute)
- `len` (line 133, type: direct)
- `error` (line 139, type: attribute)
- `str` (line 139, type: direct)

### src\services\job_service.py:JobService.update_job_progress

Calls:
- `max` (line 475, type: direct)
- `min` (line 475, type: direct)
- `isoformat` (line 476, type: attribute)
- `now` (line 476, type: attribute)
- `update_job` (line 482, type: attribute)
- `str` (line 482, type: direct)
- `info` (line 485, type: attribute)
- `emit_event` (line 488, type: attribute)
- `str` (line 489, type: direct)
- `isoformat` (line 492, type: attribute)
- `now` (line 492, type: attribute)
- `error` (line 498, type: attribute)
- `str` (line 498, type: direct)

### src\services\job_service.py:JobService.update_job_status

Calls:
- `ValueError` (line 292, type: direct)
- `isoformat` (line 297, type: attribute)
- `now` (line 297, type: attribute)
- `isoformat` (line 316, type: attribute)
- `now` (line 316, type: attribute)
- `isoformat` (line 318, type: attribute)
- `now` (line 318, type: attribute)
- `update_job` (line 321, type: attribute)
- `str` (line 321, type: direct)
- `info` (line 324, type: attribute)
- `emit_event` (line 327, type: attribute)
- `str` (line 328, type: direct)
- `isoformat` (line 331, type: attribute)
- `now` (line 331, type: attribute)
- `error` (line 334, type: attribute)
- `error` (line 337, type: attribute)
- `str` (line 337, type: direct)

### src\services\library_service.py:LibraryService.__init__

Calls:
- `Path` (line 38, type: direct)
- `getattr` (line 38, type: direct)
- `getattr` (line 39, type: direct)
- `getattr` (line 40, type: direct)
- `getattr` (line 41, type: direct)
- `getattr` (line 42, type: direct)
- `getattr` (line 43, type: direct)
- `set` (line 46, type: direct)
- `info` (line 48, type: attribute)
- `str` (line 49, type: direct)

### src\services\library_service.py:LibraryService._calculate_checksum_sync

Calls:
- `sha256` (line 109, type: attribute)
- `md5` (line 111, type: attribute)
- `ValueError` (line 113, type: direct)
- `stat` (line 115, type: attribute)
- `open` (line 118, type: direct)
- `read` (line 120, type: attribute)
- `update` (line 121, type: attribute)
- `len` (line 122, type: direct)
- `debug` (line 128, type: attribute)
- `str` (line 129, type: direct)
- `hexdigest` (line 132, type: attribute)

### src\services\library_service.py:LibraryService._check_duplicate

Calls:
- `get_file_by_checksum` (line 212, type: attribute)

### src\services\library_service.py:LibraryService._extract_metadata_async

Calls:
- `debug` (line 581, type: attribute)
- `add` (line 584, type: attribute)
- `update_library_file` (line 587, type: attribute)
- `get_file_by_checksum` (line 592, type: attribute)
- `info` (line 602, type: attribute)
- `update_library_file` (line 608, type: attribute)
- `isoformat` (line 610, type: attribute)
- `now` (line 610, type: attribute)
- `info` (line 613, type: attribute)
- `error` (line 616, type: attribute)
- `str` (line 616, type: direct)
- `update_library_file` (line 617, type: attribute)
- `str` (line 619, type: direct)
- `discard` (line 623, type: attribute)

### src\services\library_service.py:LibraryService._resolve_filename_conflict

Calls:
- `exists` (line 179, type: attribute)
- `exists` (line 191, type: attribute)
- `info` (line 192, type: attribute)
- `RuntimeError` (line 200, type: direct)

### src\services\library_service.py:LibraryService.add_file_source

Calls:
- `get_file_by_checksum` (line 479, type: attribute)
- `ValueError` (line 481, type: direct)
- `loads` (line 484, type: attribute)
- `get` (line 484, type: attribute)
- `get` (line 487, type: attribute)
- `get` (line 487, type: attribute)
- `get` (line 487, type: attribute)
- `get` (line 488, type: attribute)
- `get` (line 488, type: attribute)
- `get` (line 488, type: attribute)
- `isoformat` (line 493, type: attribute)
- `now` (line 493, type: attribute)
- `append` (line 495, type: attribute)
- `update_library_file` (line 498, type: attribute)
- `dumps` (line 499, type: attribute)
- `info` (line 502, type: attribute)
- `get` (line 502, type: attribute)
- `create_library_file_source` (line 505, type: attribute)
- `get` (line 507, type: attribute)
- `get` (line 508, type: attribute)
- `get` (line 508, type: attribute)
- `get` (line 509, type: attribute)
- `get` (line 509, type: attribute)
- `get` (line 510, type: attribute)
- `get` (line 511, type: attribute)
- `get` (line 512, type: attribute)
- `get` (line 513, type: attribute)
- `get` (line 514, type: attribute)
- `isoformat` (line 514, type: attribute)
- `now` (line 514, type: attribute)
- `dumps` (line 515, type: attribute)

### src\services\library_service.py:LibraryService.add_file_to_library

Calls:
- `exists` (line 235, type: attribute)
- `FileNotFoundError` (line 236, type: direct)
- `get` (line 239, type: attribute)
- `ValueError` (line 241, type: direct)
- `info` (line 245, type: attribute)
- `str` (line 245, type: direct)
- `calculate_checksum` (line 246, type: attribute)
- `info` (line 247, type: attribute)
- `str` (line 247, type: direct)
- `get` (line 249, type: attribute)
- `ValueError` (line 251, type: direct)
- `_check_duplicate` (line 254, type: attribute)
- `info` (line 259, type: attribute)
- `info` (line 267, type: attribute)
- `info` (line 269, type: attribute)
- `stat` (line 274, type: attribute)
- `disk_usage` (line 276, type: attribute)
- `IOError` (line 280, type: direct)
- `get` (line 286, type: attribute)
- `get_library_path_for_file` (line 287, type: attribute)
- `_resolve_filename_conflict` (line 295, type: attribute)
- `mkdir` (line 298, type: attribute)
- `debug` (line 302, type: attribute)
- `str` (line 303, type: direct)
- `str` (line 304, type: direct)
- `to_thread` (line 305, type: attribute)
- `debug` (line 307, type: attribute)
- `str` (line 308, type: direct)
- `str` (line 309, type: direct)
- `to_thread` (line 310, type: attribute)
- `calculate_checksum` (line 313, type: attribute)
- `unlink` (line 316, type: attribute)
- `ValueError` (line 317, type: direct)
- `stat` (line 320, type: attribute)
- `lower` (line 322, type: attribute)
- `str` (line 330, type: direct)
- `uuid4` (line 330, type: direct)
- `str` (line 334, type: direct)
- `uuid4` (line 334, type: direct)
- `lower` (line 340, type: attribute)
- `str` (line 347, type: direct)
- `relative_to` (line 347, type: attribute)
- `dumps` (line 350, type: attribute)
- `isoformat` (line 352, type: attribute)
- `now` (line 352, type: attribute)
- `isoformat` (line 353, type: attribute)
- `fromtimestamp` (line 353, type: attribute)
- `create_library_file` (line 362, type: attribute)
- `get_file_by_checksum` (line 367, type: attribute)
- `info` (line 369, type: attribute)
- `unlink` (line 372, type: attribute)
- `add_file_source` (line 373, type: attribute)
- `unlink` (line 377, type: attribute)
- `RuntimeError` (line 378, type: direct)
- `exists` (line 382, type: attribute)
- `unlink` (line 383, type: attribute)
- `error` (line 384, type: attribute)
- `str` (line 384, type: direct)
- `add_file_source` (line 388, type: attribute)
- `get` (line 392, type: attribute)
- `update_library_file` (line 393, type: attribute)
- `info` (line 396, type: attribute)
- `info` (line 400, type: attribute)
- `str` (line 402, type: direct)
- `emit_event` (line 406, type: attribute)
- `create_task` (line 415, type: attribute)
- `_extract_metadata_async` (line 415, type: attribute)
- `error` (line 420, type: attribute)
- `str` (line 421, type: direct)
- `str` (line 422, type: direct)

### src\services\library_service.py:LibraryService.calculate_checksum

Calls:
- `to_thread` (line 104, type: attribute)

### src\services\library_service.py:LibraryService.delete_file

Calls:
- `get_file_by_checksum` (line 530, type: attribute)
- `warning` (line 532, type: attribute)
- `exists` (line 538, type: attribute)
- `unlink` (line 539, type: attribute)
- `info` (line 540, type: attribute)
- `str` (line 540, type: direct)
- `delete_library_file` (line 543, type: attribute)
- `delete_library_file_sources` (line 544, type: attribute)
- `info` (line 546, type: attribute)
- `emit_event` (line 549, type: attribute)
- `get` (line 551, type: attribute)
- `error` (line 557, type: attribute)
- `str` (line 557, type: direct)

### src\services\library_service.py:LibraryService.get_file_by_checksum

Calls:
- `get_library_file_by_checksum` (line 435, type: attribute)

### src\services\library_service.py:LibraryService.get_file_by_id

Calls:
- `get_library_file` (line 447, type: attribute)

### src\services\library_service.py:LibraryService.get_library_path_for_file

Calls:
- `ValueError` (line 150, type: direct)
- `ValueError` (line 167, type: direct)

### src\services\library_service.py:LibraryService.get_library_statistics

Calls:
- `get_library_stats` (line 567, type: attribute)

### src\services\library_service.py:LibraryService.initialize

Calls:
- `info` (line 55, type: attribute)
- `mkdir` (line 70, type: attribute)
- `debug` (line 71, type: attribute)
- `str` (line 71, type: direct)
- `write_text` (line 76, type: attribute)
- `unlink` (line 77, type: attribute)
- `info` (line 78, type: attribute)
- `error` (line 80, type: attribute)
- `str` (line 80, type: direct)
- `info` (line 83, type: attribute)
- `error` (line 86, type: attribute)
- `str` (line 86, type: direct)

### src\services\library_service.py:LibraryService.list_files

Calls:
- `list_library_files` (line 468, type: attribute)

### src\services\library_service.py:LibraryService.reprocess_file

Calls:
- `get_file_by_checksum` (line 636, type: attribute)
- `warning` (line 638, type: attribute)
- `create_task` (line 642, type: attribute)
- `_extract_metadata_async` (line 642, type: attribute)
- `info` (line 644, type: attribute)
- `error` (line 648, type: attribute)
- `str` (line 648, type: direct)

### src\services\material_service.py:MaterialService._calculate_consumption_period

Calls:
- `now` (line 388, type: attribute)
- `timedelta` (line 388, type: direct)
- `get_connection` (line 390, type: attribute)
- `execute` (line 391, type: attribute)
- `isoformat` (line 395, type: attribute)
- `fetchone` (line 397, type: attribute)

### src\services\material_service.py:MaterialService._create_tables

Calls:
- `connection` (line 58, type: attribute)
- `execute` (line 60, type: attribute)
- `execute` (line 82, type: attribute)
- `execute` (line 100, type: attribute)
- `execute` (line 101, type: attribute)
- `execute` (line 102, type: attribute)
- `execute` (line 103, type: attribute)
- `execute` (line 104, type: attribute)
- `commit` (line 106, type: attribute)

### src\services\material_service.py:MaterialService._load_materials

Calls:
- `get_connection` (line 110, type: attribute)
- `execute` (line 111, type: attribute)
- `fetchall` (line 112, type: attribute)
- `clear` (line 114, type: attribute)
- `_row_to_material` (line 116, type: attribute)

### src\services\material_service.py:MaterialService._row_to_material

Calls:
- `MaterialSpool` (line 121, type: direct)
- `MaterialType` (line 123, type: direct)
- `MaterialBrand` (line 124, type: direct)
- `MaterialColor` (line 125, type: direct)
- `Decimal` (line 129, type: direct)
- `str` (line 129, type: direct)
- `fromisoformat` (line 130, type: attribute)
- `fromisoformat` (line 135, type: attribute)
- `fromisoformat` (line 136, type: attribute)

### src\services\material_service.py:MaterialService.cleanup

Calls:
- `clear` (line 541, type: attribute)
- `info` (line 542, type: attribute)

### src\services\material_service.py:MaterialService.create_material

Calls:
- `str` (line 141, type: direct)
- `uuid4` (line 141, type: direct)
- `now` (line 142, type: attribute)
- `MaterialSpool` (line 144, type: direct)
- `get_connection` (line 162, type: attribute)
- `execute` (line 163, type: attribute)
- `str` (line 172, type: direct)
- `isoformat` (line 173, type: attribute)
- `isoformat` (line 175, type: attribute)
- `isoformat` (line 175, type: attribute)
- `commit` (line 177, type: attribute)
- `emit_event` (line 180, type: attribute)

### src\services\material_service.py:MaterialService.export_inventory

Calls:
- `list` (line 516, type: direct)
- `values` (line 516, type: attribute)
- `append` (line 523, type: attribute)
- `open` (line 529, type: attribute)
- `write` (line 530, type: attribute)
- `join` (line 530, type: attribute)
- `info` (line 532, type: attribute)
- `len` (line 532, type: direct)
- `error` (line 536, type: attribute)

### src\services\material_service.py:MaterialService.generate_report

Calls:
- `get_connection` (line 404, type: attribute)
- `execute` (line 406, type: attribute)
- `isoformat` (line 413, type: attribute)
- `isoformat` (line 413, type: attribute)
- `fetchall` (line 415, type: attribute)
- `MaterialReport` (line 418, type: direct)
- `Decimal` (line 422, type: direct)
- `sum` (line 431, type: direct)
- `sum` (line 432, type: direct)
- `Decimal` (line 432, type: direct)
- `str` (line 432, type: direct)
- `Decimal` (line 441, type: direct)
- `Decimal` (line 445, type: direct)
- `str` (line 445, type: direct)
- `Decimal` (line 455, type: direct)
- `Decimal` (line 459, type: direct)
- `str` (line 459, type: direct)
- `Decimal` (line 463, type: direct)
- `Decimal` (line 464, type: direct)
- `get` (line 467, type: attribute)
- `Decimal` (line 469, type: direct)
- `str` (line 469, type: direct)
- `get` (line 479, type: attribute)
- `Decimal` (line 481, type: direct)
- `Decimal` (line 484, type: direct)
- `str` (line 484, type: direct)
- `sorted` (line 486, type: direct)
- `values` (line 486, type: attribute)
- `sum` (line 491, type: direct)
- `float` (line 497, type: direct)
- `len` (line 497, type: direct)
- `set` (line 497, type: direct)
- `MaterialReport` (line 501, type: direct)

### src\services\material_service.py:MaterialService.get_all_materials

Calls:
- `list` (line 290, type: direct)
- `values` (line 290, type: attribute)

### src\services\material_service.py:MaterialService.get_low_stock_materials

Calls:
- `values` (line 302, type: attribute)

### src\services\material_service.py:MaterialService.get_material

Calls:
- `get` (line 286, type: attribute)

### src\services\material_service.py:MaterialService.get_materials_by_printer

Calls:
- `values` (line 298, type: attribute)

### src\services\material_service.py:MaterialService.get_materials_by_type

Calls:
- `values` (line 294, type: attribute)

### src\services\material_service.py:MaterialService.get_statistics

Calls:
- `list` (line 306, type: direct)
- `values` (line 306, type: attribute)
- `MaterialStats` (line 309, type: direct)
- `Decimal` (line 313, type: direct)
- `Decimal` (line 314, type: direct)
- `sum` (line 324, type: direct)
- `sum` (line 325, type: direct)
- `sum` (line 326, type: direct)
- `sum` (line 327, type: direct)
- `Decimal` (line 338, type: direct)
- `get` (line 363, type: attribute)
- `_calculate_consumption_period` (line 369, type: attribute)
- `MaterialStats` (line 372, type: direct)
- `len` (line 373, type: direct)

### src\services\material_service.py:MaterialService.initialize

Calls:
- `_create_tables` (line 49, type: attribute)
- `_load_materials` (line 50, type: attribute)
- `info` (line 51, type: attribute)
- `error` (line 53, type: attribute)

### src\services\material_service.py:MaterialService.record_consumption

Calls:
- `ValueError` (line 230, type: direct)
- `Decimal` (line 234, type: direct)
- `str` (line 234, type: direct)
- `MaterialConsumption` (line 236, type: direct)
- `max` (line 247, type: direct)
- `now` (line 248, type: attribute)
- `get_connection` (line 250, type: attribute)
- `str` (line 252, type: direct)
- `uuid4` (line 252, type: direct)
- `execute` (line 253, type: attribute)
- `str` (line 260, type: direct)
- `isoformat` (line 261, type: attribute)
- `execute` (line 266, type: attribute)
- `isoformat` (line 270, type: attribute)
- `commit` (line 272, type: attribute)
- `emit_event` (line 276, type: attribute)

### src\services\material_service.py:MaterialService.update_material

Calls:
- `model_dump` (line 190, type: attribute)
- `items` (line 196, type: attribute)
- `hasattr` (line 197, type: direct)
- `setattr` (line 198, type: direct)
- `now` (line 200, type: attribute)
- `get_connection` (line 203, type: attribute)
- `items` (line 206, type: attribute)
- `append` (line 207, type: attribute)
- `isinstance` (line 208, type: direct)
- `append` (line 209, type: attribute)
- `str` (line 209, type: direct)
- `append` (line 211, type: attribute)
- `append` (line 213, type: attribute)
- `append` (line 214, type: attribute)
- `isoformat` (line 214, type: attribute)
- `append` (line 215, type: attribute)
- `join` (line 217, type: attribute)
- `execute` (line 218, type: attribute)
- `commit` (line 219, type: attribute)
- `emit_event` (line 221, type: attribute)

### src\services\migration_service.py:MigrationService.__init__

Calls:
- `Path` (line 22, type: direct)
- `mkdir` (line 23, type: attribute)

### src\services\migration_service.py:MigrationService._ensure_migrations_table

Calls:
- `RuntimeError` (line 64, type: direct)
- `get_connection` (line 66, type: attribute)
- `execute` (line 67, type: attribute)
- `commit` (line 75, type: attribute)
- `error` (line 78, type: attribute)
- `str` (line 78, type: direct)

### src\services\migration_service.py:MigrationService._get_completed_migrations

Calls:
- `RuntimeError` (line 85, type: direct)
- `get_connection` (line 87, type: attribute)
- `execute` (line 91, type: attribute)
- `fetchall` (line 92, type: attribute)
- `set` (line 96, type: direct)
- `error` (line 99, type: attribute)
- `str` (line 99, type: direct)

### src\services\migration_service.py:MigrationService._get_migration_files

Calls:
- `list` (line 105, type: direct)
- `glob` (line 105, type: attribute)
- `sort` (line 106, type: attribute)
- `debug` (line 108, type: attribute)
- `len` (line 109, type: direct)
- `error` (line 115, type: attribute)
- `str` (line 115, type: direct)

### src\services\migration_service.py:MigrationService._run_migration_file

Calls:
- `RuntimeError` (line 122, type: direct)
- `info` (line 124, type: attribute)
- `read_text` (line 127, type: attribute)
- `get_connection` (line 130, type: attribute)
- `executescript` (line 133, type: attribute)
- `execute` (line 136, type: attribute)
- `commit` (line 142, type: attribute)
- `info` (line 144, type: attribute)
- `error` (line 147, type: attribute)
- `str` (line 149, type: direct)

### src\services\migration_service.py:MigrationService.force_run_migration

Calls:
- `RuntimeError` (line 181, type: direct)
- `exists` (line 185, type: attribute)
- `ValueError` (line 186, type: direct)
- `_run_migration_file` (line 188, type: attribute)
- `info` (line 189, type: attribute)
- `error` (line 192, type: attribute)
- `str` (line 193, type: direct)

### src\services\migration_service.py:MigrationService.get_migration_status

Calls:
- `_get_completed_migrations` (line 158, type: attribute)
- `_get_migration_files` (line 159, type: attribute)
- `len` (line 165, type: direct)
- `len` (line 166, type: direct)
- `len` (line 167, type: direct)
- `sorted` (line 168, type: direct)
- `sorted` (line 169, type: direct)
- `error` (line 174, type: attribute)
- `str` (line 174, type: direct)

### src\services\migration_service.py:MigrationService.run_migrations

Calls:
- `warning` (line 29, type: attribute)
- `info` (line 32, type: attribute)
- `_ensure_migrations_table` (line 35, type: attribute)
- `_get_completed_migrations` (line 38, type: attribute)
- `_get_migration_files` (line 41, type: attribute)
- `_run_migration_file` (line 49, type: attribute)
- `info` (line 52, type: attribute)
- `len` (line 53, type: direct)
- `error` (line 57, type: attribute)
- `str` (line 57, type: direct)

### src\services\monitoring_service.py:MonitoringService.__init__

Calls:
- `get_settings` (line 22, type: direct)

### src\services\monitoring_service.py:MonitoringService._check_database_health

Calls:
- `Database` (line 179, type: direct)
- `execute_query` (line 182, type: attribute)
- `Path` (line 185, type: direct)
- `exists` (line 186, type: attribute)
- `stat` (line 187, type: attribute)
- `isoformat` (line 191, type: attribute)
- `now` (line 191, type: attribute)
- `isoformat` (line 197, type: attribute)
- `now` (line 197, type: attribute)
- `str` (line 203, type: direct)
- `isoformat` (line 204, type: attribute)
- `now` (line 204, type: attribute)

### src\services\monitoring_service.py:MonitoringService._check_error_patterns

Calls:
- `items` (line 126, type: attribute)
- `_trigger_alert` (line 128, type: attribute)
- `items` (line 135, type: attribute)
- `_trigger_alert` (line 137, type: attribute)
- `error` (line 144, type: attribute)
- `str` (line 144, type: direct)

### src\services\monitoring_service.py:MonitoringService._check_error_rates

Calls:
- `get_error_statistics` (line 85, type: attribute)
- `get` (line 89, type: attribute)
- `_trigger_alert` (line 91, type: attribute)
- `get` (line 98, type: attribute)
- `_trigger_alert` (line 100, type: attribute)
- `_trigger_alert` (line 108, type: attribute)
- `_check_error_patterns` (line 115, type: attribute)
- `error` (line 118, type: attribute)
- `str` (line 118, type: direct)

### src\services\monitoring_service.py:MonitoringService._check_file_system_health

Calls:
- `Path` (line 211, type: direct)
- `mkdir` (line 212, type: attribute)
- `write_text` (line 215, type: attribute)
- `unlink` (line 216, type: attribute)
- `disk_usage` (line 220, type: attribute)
- `isoformat` (line 228, type: attribute)
- `now` (line 228, type: attribute)
- `str` (line 234, type: direct)
- `isoformat` (line 235, type: attribute)
- `now` (line 235, type: attribute)

### src\services\monitoring_service.py:MonitoringService._cleanup_old_logs

Calls:
- `Path` (line 294, type: direct)
- `exists` (line 295, type: attribute)
- `now` (line 299, type: attribute)
- `timedelta` (line 299, type: direct)
- `timestamp` (line 300, type: attribute)
- `glob` (line 303, type: attribute)
- `stat` (line 305, type: attribute)
- `unlink` (line 306, type: attribute)
- `warning` (line 309, type: attribute)
- `str` (line 309, type: direct)
- `info` (line 312, type: attribute)
- `error` (line 315, type: attribute)
- `str` (line 315, type: direct)

### src\services\monitoring_service.py:MonitoringService._cleanup_old_logs_loop

Calls:
- `_cleanup_old_logs` (line 75, type: attribute)
- `sleep` (line 76, type: attribute)
- `error` (line 78, type: attribute)
- `str` (line 78, type: direct)
- `sleep` (line 79, type: attribute)

### src\services\monitoring_service.py:MonitoringService._error_monitoring_loop

Calls:
- `_check_error_rates` (line 55, type: attribute)
- `sleep` (line 56, type: attribute)
- `error` (line 58, type: attribute)
- `str` (line 58, type: direct)
- `sleep` (line 59, type: attribute)

### src\services\monitoring_service.py:MonitoringService._health_check_loop

Calls:
- `_perform_health_checks` (line 65, type: attribute)
- `sleep` (line 66, type: attribute)
- `error` (line 68, type: attribute)
- `str` (line 68, type: direct)
- `sleep` (line 69, type: attribute)

### src\services\monitoring_service.py:MonitoringService._perform_health_checks

Calls:
- `_check_database_health` (line 153, type: attribute)
- `_check_file_system_health` (line 157, type: attribute)
- `items` (line 160, type: attribute)
- `_trigger_alert` (line 162, type: attribute)
- `join` (line 164, type: attribute)
- `debug` (line 168, type: attribute)
- `error` (line 171, type: attribute)
- `str` (line 171, type: direct)

### src\services\monitoring_service.py:MonitoringService._store_alert

Calls:
- `Path` (line 275, type: direct)
- `mkdir` (line 276, type: attribute)
- `isoformat` (line 279, type: attribute)
- `now` (line 279, type: attribute)
- `open` (line 285, type: direct)
- `write` (line 286, type: attribute)
- `dumps` (line 286, type: attribute)
- `error` (line 289, type: attribute)
- `str` (line 289, type: direct)

### src\services\monitoring_service.py:MonitoringService._trigger_alert

Calls:
- `timestamp` (line 241, type: attribute)
- `now` (line 241, type: attribute)
- `get` (line 242, type: attribute)
- `warning` (line 252, type: attribute)
- `isoformat` (line 257, type: attribute)
- `now` (line 257, type: attribute)
- `_store_alert` (line 261, type: attribute)
- `error` (line 270, type: attribute)
- `str` (line 270, type: direct)

### src\services\monitoring_service.py:MonitoringService.get_monitoring_status

Calls:
- `get_error_statistics` (line 321, type: attribute)
- `Path` (line 324, type: direct)
- `exists` (line 326, type: attribute)
- `open` (line 328, type: direct)
- `readlines` (line 329, type: attribute)
- `loads` (line 334, type: attribute)
- `strip` (line 334, type: attribute)
- `append` (line 335, type: attribute)
- `_check_database_health` (line 343, type: attribute)
- `_check_file_system_health` (line 344, type: attribute)
- `isoformat` (line 349, type: attribute)
- `now` (line 349, type: attribute)
- `list` (line 351, type: direct)
- `reversed` (line 351, type: direct)
- `error` (line 357, type: attribute)
- `str` (line 357, type: direct)
- `str` (line 360, type: direct)
- `isoformat` (line 361, type: attribute)
- `now` (line 361, type: attribute)

### src\services\monitoring_service.py:MonitoringService.start_monitoring

Calls:
- `info` (line 42, type: attribute)
- `create_task` (line 45, type: attribute)
- `_error_monitoring_loop` (line 45, type: attribute)
- `create_task` (line 46, type: attribute)
- `_health_check_loop` (line 46, type: attribute)
- `create_task` (line 47, type: attribute)
- `_cleanup_old_logs_loop` (line 47, type: attribute)
- `info` (line 49, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService.__init__

Calls:
- `Path` (line 39, type: direct)
- `mkdir` (line 40, type: attribute)
- `get_settings` (line 60, type: direct)
- `GcodeAnalyzer` (line 73, type: direct)
- `timedelta` (line 76, type: direct)

### src\services\preview_render_service.py:PreviewRenderService._get_cache_key

Calls:
- `getmtime` (line 492, type: attribute)
- `hexdigest` (line 497, type: attribute)
- `md5` (line 497, type: attribute)
- `encode` (line 497, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService._render_3mf

Calls:
- `load` (line 277, type: attribute)
- `isinstance` (line 280, type: direct)
- `concatenate` (line 282, type: attribute)
- `values` (line 283, type: attribute)
- `isinstance` (line 283, type: direct)
- `_render_mesh_common` (line 289, type: attribute)
- `warning` (line 291, type: attribute)
- `error` (line 295, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService._render_file

Calls:
- `lower` (line 169, type: attribute)
- `_render_stl` (line 172, type: attribute)
- `_render_3mf` (line 174, type: attribute)
- `_render_gcode_toolpath` (line 176, type: attribute)
- `warning` (line 178, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService._render_gcode_toolpath

Calls:
- `info` (line 384, type: attribute)
- `open` (line 388, type: direct)
- `enumerate` (line 390, type: direct)
- `append` (line 397, type: attribute)
- `rstrip` (line 397, type: attribute)
- `len` (line 401, type: direct)
- `get_optimized_gcode_lines` (line 402, type: attribute)
- `len` (line 405, type: direct)
- `open` (line 406, type: direct)
- `readlines` (line 407, type: attribute)
- `len` (line 408, type: direct)
- `min` (line 409, type: direct)
- `len` (line 409, type: direct)
- `rstrip` (line 410, type: attribute)
- `info` (line 412, type: attribute)
- `len` (line 412, type: direct)
- `startswith` (line 420, type: attribute)
- `startswith` (line 420, type: attribute)
- `split` (line 421, type: attribute)
- `strip` (line 421, type: attribute)
- `startswith` (line 424, type: attribute)
- `float` (line 425, type: direct)
- `startswith` (line 426, type: attribute)
- `float` (line 427, type: direct)
- `startswith` (line 428, type: attribute)
- `float` (line 429, type: direct)
- `append` (line 433, type: attribute)
- `copy` (line 433, type: attribute)
- `warning` (line 436, type: attribute)
- `array` (line 440, type: attribute)
- `debug` (line 441, type: attribute)
- `len` (line 441, type: direct)
- `figure` (line 448, type: attribute)
- `add_subplot` (line 449, type: attribute)
- `plot` (line 452, type: attribute)
- `set_facecolor` (line 456, type: attribute)
- `set_facecolor` (line 457, type: attribute)
- `set_axis_off` (line 458, type: attribute)
- `len` (line 461, type: direct)
- `set_xlim` (line 462, type: attribute)
- `min` (line 462, type: attribute)
- `max` (line 462, type: attribute)
- `set_ylim` (line 463, type: attribute)
- `min` (line 463, type: attribute)
- `max` (line 463, type: attribute)
- `set_zlim` (line 464, type: attribute)
- `min` (line 464, type: attribute)
- `max` (line 464, type: attribute)
- `BytesIO` (line 467, type: direct)
- `savefig` (line 468, type: attribute)
- `close` (line 470, type: attribute)
- `seek` (line 472, type: attribute)
- `read` (line 473, type: attribute)
- `error` (line 476, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService._render_mesh_common

Calls:
- `max` (line 314, type: direct)
- `figure` (line 322, type: attribute)
- `add_subplot` (line 323, type: attribute)
- `set_facecolor` (line 326, type: attribute)
- `set_facecolor` (line 327, type: attribute)
- `plot_trisurf` (line 330, type: attribute)
- `view_init` (line 344, type: attribute)
- `set_axis_off` (line 345, type: attribute)
- `set_xlim` (line 349, type: attribute)
- `set_ylim` (line 350, type: attribute)
- `set_zlim` (line 351, type: attribute)
- `BytesIO` (line 354, type: direct)
- `savefig` (line 355, type: attribute)
- `close` (line 363, type: attribute)
- `seek` (line 365, type: attribute)
- `read` (line 366, type: attribute)
- `error` (line 369, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService._render_stl

Calls:
- `load_mesh` (line 194, type: attribute)
- `max` (line 201, type: direct)
- `figure` (line 209, type: attribute)
- `add_subplot` (line 210, type: attribute)
- `set_facecolor` (line 213, type: attribute)
- `set_facecolor` (line 214, type: attribute)
- `plot_trisurf` (line 217, type: attribute)
- `view_init` (line 231, type: attribute)
- `set_axis_off` (line 234, type: attribute)
- `set_xlim` (line 238, type: attribute)
- `set_ylim` (line 239, type: attribute)
- `set_zlim` (line 240, type: attribute)
- `BytesIO` (line 243, type: direct)
- `savefig` (line 244, type: attribute)
- `close` (line 252, type: attribute)
- `seek` (line 254, type: attribute)
- `read` (line 255, type: attribute)
- `warning` (line 257, type: attribute)
- `error` (line 261, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService.clear_cache

Calls:
- `now` (line 515, type: attribute)
- `timedelta` (line 515, type: direct)
- `glob` (line 517, type: attribute)
- `is_file` (line 518, type: attribute)
- `unlink` (line 521, type: attribute)
- `fromtimestamp` (line 525, type: attribute)
- `stat` (line 525, type: attribute)
- `unlink` (line 527, type: attribute)
- `info` (line 530, type: attribute)
- `error` (line 533, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService.get_or_generate_preview

Calls:
- `warning` (line 104, type: attribute)
- `_get_cache_key` (line 109, type: attribute)
- `exists` (line 112, type: attribute)
- `now` (line 114, type: attribute)
- `fromtimestamp` (line 114, type: attribute)
- `stat` (line 114, type: attribute)
- `debug` (line 116, type: attribute)
- `open` (line 117, type: direct)
- `read` (line 119, type: attribute)
- `info` (line 122, type: attribute)
- `get_event_loop` (line 125, type: attribute)
- `wait_for` (line 126, type: attribute)
- `run_in_executor` (line 127, type: attribute)
- `open` (line 133, type: direct)
- `write` (line 134, type: attribute)
- `info` (line 137, type: attribute)
- `error` (line 144, type: attribute)
- `error` (line 148, type: attribute)

### src\services\preview_render_service.py:PreviewRenderService.get_statistics

Calls:
- `sum` (line 539, type: direct)
- `stat` (line 540, type: attribute)
- `glob` (line 540, type: attribute)
- `is_file` (line 540, type: attribute)
- `len` (line 542, type: direct)
- `list` (line 542, type: direct)
- `glob` (line 542, type: attribute)
- `round` (line 546, type: direct)

### src\services\preview_render_service.py:PreviewRenderService.update_config

Calls:
- `update` (line 559, type: attribute)
- `update` (line 562, type: attribute)
- `timedelta` (line 568, type: direct)
- `info` (line 573, type: attribute)

### src\services\printer_service.py:PrinterService._attempt

Calls:
- `download_file` (line 180, type: attribute)
- `debug` (line 182, type: attribute)
- `str` (line 182, type: direct)
- `str` (line 183, type: direct)

### src\services\printer_service.py:PrinterService._attempt_download_current_job

Calls:
- `info` (line 175, type: attribute)
- `_attempt` (line 187, type: direct)
- `append` (line 188, type: attribute)
- `get` (line 190, type: attribute)
- `info` (line 191, type: attribute)
- `get_printer_files` (line 196, type: attribute)
- `debug` (line 199, type: attribute)
- `str` (line 199, type: direct)
- `strip` (line 201, type: attribute)
- `lower` (line 201, type: attribute)
- `set` (line 203, type: direct)
- `get` (line 206, type: attribute)
- `lower` (line 207, type: attribute)
- `add` (line 208, type: attribute)
- `strip` (line 210, type: attribute)
- `replace` (line 210, type: attribute)
- `replace` (line 210, type: attribute)
- `replace` (line 210, type: attribute)
- `replace` (line 210, type: attribute)
- `add` (line 212, type: attribute)
- `replace` (line 213, type: attribute)
- `add` (line 215, type: attribute)
- `strip` (line 218, type: attribute)
- `sub` (line 218, type: attribute)
- `add` (line 220, type: attribute)
- `get` (line 223, type: attribute)
- `startswith` (line 224, type: attribute)
- `lower` (line 224, type: attribute)
- `abs` (line 224, type: direct)
- `len` (line 224, type: direct)
- `len` (line 224, type: direct)
- `add` (line 225, type: attribute)
- `get` (line 229, type: attribute)
- `set` (line 229, type: direct)
- `add` (line 231, type: attribute)
- `_attempt` (line 232, type: direct)
- `append` (line 233, type: attribute)
- `get` (line 234, type: attribute)
- `info` (line 235, type: attribute)
- `get` (line 239, type: attribute)
- `warning` (line 240, type: attribute)
- `get` (line 240, type: attribute)
- `get` (line 240, type: attribute)
- `warning` (line 242, type: attribute)
- `str` (line 242, type: direct)

### src\services\printer_service.py:PrinterService._connect_and_monitor_printer

Calls:
- `info` (line 408, type: attribute)
- `connect` (line 409, type: attribute)
- `update_printer_status` (line 413, type: attribute)
- `now` (line 416, type: attribute)
- `info` (line 418, type: attribute)
- `warning` (line 420, type: attribute)
- `start_monitoring` (line 423, type: attribute)
- `info` (line 424, type: attribute)
- `error` (line 427, type: attribute)
- `str` (line 428, type: direct)

### src\services\printer_service.py:PrinterService._create_printer_instance

Calls:
- `BambuLabPrinter` (line 73, type: direct)
- `PrusaPrinter` (line 82, type: direct)
- `warning` (line 90, type: attribute)

### src\services\printer_service.py:PrinterService._handle_status_update

Calls:
- `_store_status_update` (line 119, type: attribute)
- `emit_event` (line 122, type: attribute)
- `isoformat` (line 133, type: attribute)
- `set` (line 149, type: direct)
- `startswith` (line 152, type: attribute)
- `split` (line 153, type: attribute)
- `_is_print_file` (line 158, type: attribute)
- `add` (line 160, type: attribute)
- `create_task` (line 161, type: attribute)
- `_attempt_download_current_job` (line 161, type: attribute)
- `debug` (line 163, type: attribute)
- `str` (line 163, type: direct)

### src\services\printer_service.py:PrinterService._is_print_file

Calls:
- `lower` (line 168, type: attribute)
- `splitext` (line 170, type: attribute)

### src\services\printer_service.py:PrinterService._load_printers

Calls:
- `get_active_printers` (line 44, type: attribute)
- `items` (line 46, type: attribute)
- `_create_printer_instance` (line 49, type: attribute)
- `add_status_callback` (line 55, type: attribute)
- `create_task` (line 56, type: attribute)
- `_handle_status_update` (line 57, type: attribute)
- `info` (line 61, type: attribute)
- `error` (line 65, type: attribute)
- `str` (line 66, type: direct)
- `info` (line 68, type: attribute)
- `len` (line 68, type: direct)

### src\services\printer_service.py:PrinterService._store_status_update

Calls:
- `info` (line 249, type: attribute)

### src\services\printer_service.py:PrinterService._sync_database_printers

Calls:
- `cursor` (line 95, type: attribute)
- `items` (line 96, type: attribute)
- `execute` (line 98, type: attribute)
- `replace` (line 105, type: attribute)
- `lower` (line 105, type: attribute)
- `getattr` (line 105, type: direct)
- `getattr` (line 107, type: direct)
- `getattr` (line 108, type: direct)
- `getattr` (line 109, type: direct)
- `commit` (line 113, type: attribute)
- `info` (line 114, type: attribute)

### src\services\printer_service.py:PrinterService.connect_printer

Calls:
- `get` (line 372, type: attribute)
- `NotFoundError` (line 374, type: direct)
- `connect` (line 377, type: attribute)
- `update_printer_status` (line 381, type: attribute)
- `now` (line 384, type: attribute)
- `error` (line 388, type: attribute)
- `str` (line 388, type: direct)
- `PrinterConnectionError` (line 389, type: direct)
- `str` (line 389, type: direct)

### src\services\printer_service.py:PrinterService.create_printer

Calls:
- `str` (line 676, type: direct)
- `uuid4` (line 676, type: direct)
- `add_printer` (line 689, type: attribute)
- `ValueError` (line 690, type: direct)
- `get_printer` (line 693, type: attribute)
- `_create_printer_instance` (line 695, type: attribute)
- `create_printer` (line 700, type: attribute)
- `get` (line 704, type: attribute)
- `get` (line 705, type: attribute)
- `get` (line 706, type: attribute)
- `get` (line 707, type: attribute)
- `Printer` (line 711, type: direct)
- `get` (line 715, type: attribute)
- `get` (line 716, type: attribute)
- `get` (line 717, type: attribute)
- `get` (line 718, type: attribute)

### src\services\printer_service.py:PrinterService.delete_printer

Calls:
- `str` (line 777, type: direct)
- `disconnect` (line 783, type: attribute)
- `remove_printer` (line 787, type: attribute)

### src\services\printer_service.py:PrinterService.disconnect_printer

Calls:
- `get` (line 393, type: attribute)
- `NotFoundError` (line 395, type: direct)
- `disconnect` (line 398, type: attribute)
- `error` (line 401, type: attribute)
- `str` (line 401, type: direct)

### src\services\printer_service.py:PrinterService.download_current_job_file

Calls:
- `get` (line 565, type: attribute)
- `NotFoundError` (line 567, type: direct)
- `connect` (line 572, type: attribute)
- `get_status` (line 577, type: attribute)
- `startswith` (line 585, type: attribute)
- `split` (line 586, type: attribute)
- `find_file_by_name` (line 591, type: attribute)
- `get` (line 595, type: attribute)
- `get` (line 598, type: attribute)
- `get` (line 603, type: attribute)
- `get` (line 603, type: attribute)
- `process_file_thumbnails` (line 604, type: attribute)
- `get` (line 604, type: attribute)
- `get` (line 604, type: attribute)
- `get` (line 607, type: attribute)
- `download_file` (line 613, type: attribute)
- `get` (line 615, type: attribute)
- `get` (line 616, type: attribute)
- `get` (line 617, type: attribute)

### src\services\printer_service.py:PrinterService.download_printer_file

Calls:
- `get` (line 528, type: attribute)
- `NotFoundError` (line 530, type: direct)
- `connect` (line 533, type: attribute)
- `download_file` (line 538, type: attribute)
- `get` (line 539, type: attribute)
- `error` (line 541, type: attribute)
- `str` (line 542, type: direct)
- `download_file` (line 546, type: attribute)
- `error` (line 548, type: attribute)
- `str` (line 549, type: direct)

### src\services\printer_service.py:PrinterService.get_printer

Calls:
- `get` (line 307, type: attribute)
- `Printer` (line 320, type: direct)
- `lower` (line 323, type: attribute)
- `type` (line 323, type: direct)
- `getattr` (line 325, type: direct)
- `getattr` (line 326, type: direct)
- `getattr` (line 327, type: direct)

### src\services\printer_service.py:PrinterService.get_printer_driver

Calls:
- `get` (line 335, type: attribute)

### src\services\printer_service.py:PrinterService.get_printer_files

Calls:
- `get` (line 504, type: attribute)
- `NotFoundError` (line 506, type: direct)
- `connect` (line 509, type: attribute)
- `list_files` (line 512, type: attribute)
- `isoformat` (line 517, type: attribute)
- `error` (line 523, type: attribute)
- `str` (line 523, type: direct)
- `PrinterConnectionError` (line 524, type: direct)
- `str` (line 524, type: direct)

### src\services\printer_service.py:PrinterService.get_printer_status

Calls:
- `get` (line 339, type: attribute)
- `NotFoundError` (line 341, type: direct)
- `get_status` (line 344, type: attribute)
- `update_printer_status` (line 347, type: attribute)
- `lower` (line 349, type: attribute)
- `now` (line 350, type: attribute)
- `isoformat` (line 360, type: attribute)
- `error` (line 363, type: attribute)
- `str` (line 363, type: direct)
- `str` (line 367, type: direct)

### src\services\printer_service.py:PrinterService.get_printers

Calls:
- `items` (line 292, type: attribute)
- `replace` (line 296, type: attribute)
- `lower` (line 296, type: attribute)
- `type` (line 296, type: direct)
- `dict` (line 299, type: attribute)
- `append` (line 301, type: attribute)

### src\services\printer_service.py:PrinterService.health_check

Calls:
- `len` (line 628, type: direct)
- `items` (line 634, type: attribute)
- `health_check` (line 636, type: attribute)
- `isoformat` (line 646, type: attribute)
- `getattr` (line 648, type: direct)

### src\services\printer_service.py:PrinterService.initialize

Calls:
- `info` (line 37, type: attribute)
- `_load_printers` (line 38, type: attribute)
- `_sync_database_printers` (line 39, type: attribute)

### src\services\printer_service.py:PrinterService.list_printers

Calls:
- `items` (line 258, type: attribute)
- `now` (line 270, type: attribute)
- `Printer` (line 272, type: direct)
- `lower` (line 275, type: attribute)
- `type` (line 275, type: direct)
- `getattr` (line 277, type: direct)
- `getattr` (line 278, type: direct)
- `getattr` (line 279, type: direct)
- `append` (line 284, type: attribute)

### src\services\printer_service.py:PrinterService.pause_printer

Calls:
- `get` (line 791, type: attribute)
- `NotFoundError` (line 793, type: direct)
- `connect` (line 797, type: attribute)
- `pause_print` (line 798, type: attribute)
- `error` (line 800, type: attribute)
- `str` (line 800, type: direct)
- `PrinterConnectionError` (line 801, type: direct)
- `str` (line 801, type: direct)

### src\services\printer_service.py:PrinterService.resume_printer

Calls:
- `get` (line 805, type: attribute)
- `NotFoundError` (line 807, type: direct)
- `connect` (line 811, type: attribute)
- `resume_print` (line 812, type: attribute)
- `error` (line 814, type: attribute)
- `str` (line 814, type: direct)
- `PrinterConnectionError` (line 815, type: direct)
- `str` (line 815, type: direct)

### src\services\printer_service.py:PrinterService.shutdown

Calls:
- `info` (line 655, type: attribute)
- `stop_monitoring` (line 658, type: attribute)
- `items` (line 661, type: attribute)
- `disconnect` (line 663, type: attribute)
- `error` (line 665, type: attribute)
- `str` (line 665, type: direct)
- `clear` (line 667, type: attribute)
- `info` (line 668, type: attribute)

### src\services\printer_service.py:PrinterService.start_monitoring

Calls:
- `get` (line 434, type: attribute)
- `NotFoundError` (line 436, type: direct)
- `connect` (line 440, type: attribute)
- `update_printer_status` (line 444, type: attribute)
- `now` (line 447, type: attribute)
- `start_monitoring` (line 449, type: attribute)
- `info` (line 450, type: attribute)
- `error` (line 453, type: attribute)
- `str` (line 453, type: direct)
- `items` (line 459, type: attribute)
- `create_task` (line 461, type: attribute)
- `_connect_and_monitor_printer` (line 462, type: attribute)
- `append` (line 464, type: attribute)
- `info` (line 468, type: attribute)
- `len` (line 469, type: direct)
- `len` (line 472, type: direct)

### src\services\printer_service.py:PrinterService.start_printer_monitoring

Calls:
- `get` (line 833, type: attribute)
- `NotFoundError` (line 835, type: direct)
- `connect` (line 839, type: attribute)
- `info` (line 843, type: attribute)
- `error` (line 846, type: attribute)
- `str` (line 846, type: direct)

### src\services\printer_service.py:PrinterService.stop_monitoring

Calls:
- `get` (line 479, type: attribute)
- `NotFoundError` (line 481, type: direct)
- `stop_monitoring` (line 484, type: attribute)
- `info` (line 485, type: attribute)
- `error` (line 488, type: attribute)
- `str` (line 488, type: direct)
- `items` (line 492, type: attribute)
- `stop_monitoring` (line 494, type: attribute)
- `error` (line 496, type: attribute)
- `str` (line 496, type: direct)
- `info` (line 499, type: attribute)

### src\services\printer_service.py:PrinterService.stop_printer

Calls:
- `get` (line 819, type: attribute)
- `NotFoundError` (line 821, type: direct)
- `connect` (line 825, type: attribute)
- `stop_print` (line 826, type: attribute)
- `error` (line 828, type: attribute)
- `str` (line 828, type: direct)
- `PrinterConnectionError` (line 829, type: direct)
- `str` (line 829, type: direct)

### src\services\printer_service.py:PrinterService.stop_printer_monitoring

Calls:
- `get` (line 851, type: attribute)
- `NotFoundError` (line 853, type: direct)
- `info` (line 858, type: attribute)
- `error` (line 861, type: attribute)
- `str` (line 861, type: direct)

### src\services\printer_service.py:PrinterService.update_printer

Calls:
- `str` (line 725, type: direct)
- `get_printer` (line 728, type: attribute)
- `to_dict` (line 733, type: attribute)
- `update` (line 739, type: attribute)
- `add_printer` (line 744, type: attribute)
- `disconnect` (line 751, type: attribute)
- `get_printer` (line 753, type: attribute)
- `_create_printer_instance` (line 755, type: attribute)
- `get_printer` (line 760, type: attribute)
- `Printer` (line 762, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._analyze_compatibility

Calls:
- `namelist` (line 236, type: attribute)
- `open` (line 237, type: attribute)
- `loads` (line 238, type: attribute)
- `decode` (line 238, type: attribute)
- `read` (line 238, type: attribute)
- `get` (line 241, type: attribute)
- `isinstance` (line 242, type: direct)
- `isinstance` (line 244, type: direct)
- `strip` (line 246, type: attribute)
- `split` (line 246, type: attribute)
- `get` (line 250, type: attribute)
- `debug` (line 256, type: attribute)
- `len` (line 257, type: direct)
- `get` (line 257, type: attribute)
- `warning` (line 260, type: attribute)
- `str` (line 260, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._analyze_material_usage

Calls:
- `namelist` (line 183, type: attribute)
- `open` (line 184, type: attribute)
- `decode` (line 185, type: attribute)
- `read` (line 185, type: attribute)
- `fromstring` (line 188, type: attribute)
- `find` (line 189, type: attribute)
- `find` (line 193, type: attribute)
- `float` (line 195, type: direct)
- `get` (line 195, type: attribute)
- `find` (line 197, type: attribute)
- `int` (line 199, type: direct)
- `get` (line 199, type: attribute)
- `find` (line 201, type: attribute)
- `get` (line 203, type: attribute)
- `find` (line 206, type: attribute)
- `split` (line 208, type: attribute)
- `get` (line 208, type: attribute)
- `int` (line 210, type: direct)
- `isdigit` (line 210, type: attribute)
- `namelist` (line 214, type: attribute)
- `open` (line 215, type: attribute)
- `loads` (line 216, type: attribute)
- `decode` (line 216, type: attribute)
- `read` (line 216, type: attribute)
- `get` (line 218, type: attribute)
- `get` (line 219, type: attribute)
- `debug` (line 221, type: attribute)
- `get` (line 222, type: attribute)
- `len` (line 223, type: direct)
- `get` (line 223, type: attribute)
- `warning` (line 226, type: attribute)
- `str` (line 226, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._analyze_model_geometry

Calls:
- `namelist` (line 79, type: attribute)
- `open` (line 80, type: attribute)
- `loads` (line 81, type: attribute)
- `decode` (line 81, type: attribute)
- `read` (line 81, type: attribute)
- `round` (line 86, type: direct)
- `round` (line 87, type: direct)
- `len` (line 99, type: direct)
- `get` (line 101, type: attribute)
- `get` (line 106, type: attribute)
- `get` (line 107, type: attribute)
- `round` (line 109, type: direct)
- `debug` (line 111, type: attribute)
- `get` (line 112, type: attribute)
- `get` (line 113, type: attribute)
- `debug` (line 116, type: attribute)
- `warning` (line 118, type: attribute)
- `str` (line 118, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._analyze_print_settings

Calls:
- `namelist` (line 128, type: attribute)
- `open` (line 129, type: attribute)
- `loads` (line 130, type: attribute)
- `decode` (line 130, type: attribute)
- `read` (line 130, type: attribute)
- `_safe_extract` (line 133, type: attribute)
- `_safe_extract` (line 134, type: attribute)
- `_safe_extract` (line 135, type: attribute)
- `_safe_extract` (line 136, type: attribute)
- `_safe_extract` (line 137, type: attribute)
- `_safe_extract` (line 138, type: attribute)
- `_safe_extract` (line 141, type: attribute)
- `isinstance` (line 142, type: direct)
- `float` (line 143, type: direct)
- `rstrip` (line 143, type: attribute)
- `float` (line 145, type: direct)
- `_safe_extract` (line 147, type: attribute)
- `get` (line 148, type: attribute)
- `_safe_extract` (line 151, type: attribute)
- `_safe_extract` (line 152, type: attribute)
- `_safe_extract` (line 153, type: attribute)
- `_safe_extract` (line 156, type: attribute)
- `_safe_extract` (line 157, type: attribute)
- `_safe_extract` (line 158, type: attribute)
- `round` (line 162, type: direct)
- `debug` (line 166, type: attribute)
- `get` (line 167, type: attribute)
- `get` (line 168, type: attribute)
- `debug` (line 171, type: attribute)
- `warning` (line 173, type: attribute)
- `str` (line 173, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._assess_quality

Calls:
- `get` (line 330, type: attribute)
- `get` (line 331, type: attribute)
- `get` (line 337, type: attribute)
- `get` (line 346, type: attribute)
- `get` (line 346, type: attribute)
- `lower` (line 350, type: attribute)
- `get` (line 350, type: attribute)
- `any` (line 351, type: direct)
- `get` (line 355, type: attribute)
- `get` (line 359, type: attribute)
- `len` (line 360, type: direct)
- `len` (line 361, type: direct)
- `max` (line 364, type: direct)
- `min` (line 364, type: direct)
- `round` (line 378, type: direct)
- `max` (line 379, type: direct)
- `debug` (line 382, type: attribute)
- `warning` (line 388, type: attribute)
- `str` (line 388, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._calculate_costs

Calls:
- `get` (line 276, type: attribute)
- `get` (line 276, type: attribute)
- `round` (line 280, type: direct)
- `round` (line 281, type: direct)
- `get` (line 284, type: attribute)
- `get` (line 284, type: attribute)
- `get` (line 285, type: attribute)
- `get` (line 285, type: attribute)
- `round` (line 298, type: direct)
- `round` (line 301, type: direct)
- `round` (line 307, type: direct)
- `debug` (line 311, type: attribute)
- `warning` (line 317, type: attribute)
- `str` (line 317, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer._safe_extract

Calls:
- `get` (line 394, type: attribute)
- `isinstance` (line 397, type: direct)
- `len` (line 397, type: direct)
- `isinstance` (line 403, type: direct)
- `int` (line 403, type: direct)
- `float` (line 403, type: direct)
- `int` (line 403, type: direct)
- `isinstance` (line 408, type: direct)
- `float` (line 410, type: direct)

### src\services\threemf_analyzer.py:ThreeMFAnalyzer.analyze_file

Calls:
- `ZipFile` (line 43, type: attribute)
- `_analyze_model_geometry` (line 45, type: attribute)
- `_analyze_print_settings` (line 46, type: attribute)
- `_analyze_material_usage` (line 47, type: attribute)
- `_analyze_compatibility` (line 48, type: attribute)
- `_calculate_costs` (line 51, type: attribute)
- `_assess_quality` (line 52, type: attribute)
- `info` (line 55, type: attribute)
- `str` (line 56, type: direct)
- `get` (line 57, type: attribute)
- `error` (line 60, type: attribute)
- `str` (line 60, type: direct)
- `error` (line 63, type: attribute)
- `str` (line 63, type: direct)
- `error` (line 66, type: attribute)
- `str` (line 67, type: direct)
- `str` (line 68, type: direct)
- `str` (line 69, type: direct)

### src\services\thumbnail_service.py:ThumbnailService.__init__

Calls:
- `Path` (line 31, type: direct)
- `mkdir` (line 32, type: attribute)
- `timedelta` (line 35, type: direct)

### src\services\thumbnail_service.py:ThumbnailService._get_cache_path

Calls:
- `hexdigest` (line 50, type: attribute)
- `md5` (line 50, type: attribute)
- `encode` (line 50, type: attribute)
- `urlparse` (line 53, type: direct)
- `split` (line 54, type: attribute)
- `len` (line 55, type: direct)
- `lower` (line 55, type: attribute)
- `lower` (line 56, type: attribute)
- `mkdir` (line 62, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService._get_session

Calls:
- `ClientTimeout` (line 43, type: attribute)
- `ClientSession` (line 44, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService._process_and_save_image

Calls:
- `with_suffix` (line 115, type: attribute)
- `open` (line 118, type: attribute)
- `write` (line 119, type: attribute)
- `open` (line 122, type: attribute)
- `new` (line 126, type: attribute)
- `paste` (line 128, type: attribute)
- `split` (line 128, type: attribute)
- `paste` (line 130, type: attribute)
- `thumbnail` (line 135, type: attribute)
- `with_suffix` (line 138, type: attribute)
- `save` (line 139, type: attribute)
- `unlink` (line 142, type: attribute)
- `emit_event` (line 145, type: attribute)
- `str` (line 147, type: direct)
- `stat` (line 149, type: attribute)
- `error` (line 155, type: attribute)
- `locals` (line 157, type: direct)
- `unlink` (line 158, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.cache_multiple_thumbnails

Calls:
- `Semaphore` (line 184, type: attribute)
- `download_single` (line 195, type: direct)
- `gather` (line 198, type: attribute)
- `isinstance` (line 202, type: direct)
- `warning` (line 203, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.cleanup

Calls:
- `close` (line 318, type: attribute)
- `info` (line 321, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.cleanup_expired

Calls:
- `now` (line 213, type: attribute)
- `rglob` (line 216, type: attribute)
- `is_file` (line 217, type: attribute)
- `fromtimestamp` (line 218, type: attribute)
- `stat` (line 218, type: attribute)
- `unlink` (line 221, type: attribute)
- `warning` (line 224, type: attribute)
- `info` (line 226, type: attribute)
- `error` (line 229, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.clear_cache

Calls:
- `exists` (line 295, type: attribute)
- `iterdir` (line 296, type: attribute)
- `is_file` (line 297, type: attribute)
- `unlink` (line 298, type: attribute)
- `rglob` (line 302, type: attribute)
- `is_file` (line 303, type: attribute)
- `unlink` (line 304, type: attribute)
- `info` (line 307, type: attribute)
- `error` (line 311, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.download_single

Calls:
- `get` (line 190, type: attribute)
- `download_thumbnail` (line 191, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.download_thumbnail

Calls:
- `_get_cache_path` (line 70, type: attribute)
- `exists` (line 73, type: attribute)
- `now` (line 75, type: attribute)
- `fromtimestamp` (line 75, type: attribute)
- `stat` (line 75, type: attribute)
- `debug` (line 77, type: attribute)
- `str` (line 78, type: direct)
- `_get_session` (line 81, type: attribute)
- `get` (line 82, type: attribute)
- `get` (line 84, type: attribute)
- `startswith` (line 86, type: attribute)
- `warning` (line 87, type: attribute)
- `read` (line 91, type: attribute)
- `_process_and_save_image` (line 94, type: attribute)
- `info` (line 99, type: attribute)
- `str` (line 100, type: direct)
- `warning` (line 103, type: attribute)
- `error` (line 106, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.get_cache_statistics

Calls:
- `rglob` (line 248, type: attribute)
- `is_file` (line 249, type: attribute)
- `stat` (line 253, type: attribute)
- `fromtimestamp` (line 267, type: attribute)
- `stat` (line 267, type: attribute)
- `str` (line 270, type: direct)
- `str` (line 273, type: direct)
- `round` (line 278, type: direct)
- `values` (line 279, type: attribute)
- `round` (line 280, type: direct)
- `error` (line 283, type: attribute)

### src\services\thumbnail_service.py:ThumbnailService.get_thumbnail

Calls:
- `_get_cache_path` (line 164, type: attribute)
- `exists` (line 167, type: attribute)
- `str` (line 168, type: direct)
- `with_suffix` (line 171, type: attribute)
- `exists` (line 172, type: attribute)
- `str` (line 173, type: direct)
- `download_thumbnail` (line 177, type: attribute)

### src\services\trending_service.py:TrendingService.__init__

Calls:
- `Path` (line 39, type: direct)
- `mkdir` (line 40, type: attribute)

### src\services\trending_service.py:TrendingService._close_session

Calls:
- `close` (line 191, type: attribute)
- `debug` (line 192, type: attribute)
- `warning` (line 194, type: attribute)

### src\services\trending_service.py:TrendingService._create_tables

Calls:
- `connection` (line 67, type: attribute)
- `execute` (line 68, type: attribute)
- `execute` (line 89, type: attribute)
- `execute` (line 90, type: attribute)
- `execute` (line 91, type: attribute)
- `commit` (line 93, type: attribute)

### src\services\trending_service.py:TrendingService._extract_id_from_url

Calls:
- `search` (line 381, type: attribute)
- `group` (line 382, type: attribute)
- `search` (line 384, type: attribute)
- `group` (line 385, type: attribute)

### src\services\trending_service.py:TrendingService._fetch

Calls:
- `_get_session` (line 244, type: attribute)
- `get` (line 247, type: attribute)
- `raise_for_status` (line 248, type: attribute)
- `get` (line 251, type: attribute)
- `int` (line 252, type: direct)
- `warning` (line 253, type: attribute)
- `iter_chunked` (line 260, type: attribute)
- `len` (line 261, type: direct)
- `ClientPayloadError` (line 263, type: attribute)
- `append` (line 264, type: attribute)
- `join` (line 267, type: attribute)
- `get_encoding` (line 268, type: attribute)
- `decode` (line 270, type: attribute)
- `decode` (line 273, type: attribute)

### src\services\trending_service.py:TrendingService._fetch_url

Calls:
- `_retry_with_backoff` (line 276, type: attribute)
- `isoformat` (line 278, type: attribute)
- `now` (line 278, type: attribute)
- `str` (line 282, type: direct)

### src\services\trending_service.py:TrendingService._get_session

Calls:
- `ClientTimeout` (line 163, type: attribute)
- `TCPConnector` (line 166, type: attribute)
- `ClientSession` (line 174, type: attribute)
- `debug` (line 181, type: attribute)
- `error` (line 183, type: attribute)

### src\services\trending_service.py:TrendingService._needs_refresh

Calls:
- `connection` (line 221, type: attribute)
- `execute` (line 222, type: attribute)
- `fetchone` (line 227, type: attribute)
- `fromisoformat` (line 233, type: attribute)
- `now` (line 234, type: attribute)

### src\services\trending_service.py:TrendingService._parse_count

Calls:
- `upper` (line 394, type: attribute)
- `strip` (line 394, type: attribute)
- `int` (line 398, type: direct)
- `float` (line 398, type: direct)
- `replace` (line 398, type: attribute)
- `int` (line 400, type: direct)
- `float` (line 400, type: direct)
- `replace` (line 400, type: attribute)
- `findall` (line 404, type: attribute)
- `int` (line 405, type: direct)

### src\services\trending_service.py:TrendingService._refresh_loop

Calls:
- `_needs_refresh` (line 207, type: attribute)
- `refresh_all_platforms` (line 208, type: attribute)
- `sleep` (line 211, type: attribute)
- `error` (line 216, type: attribute)
- `sleep` (line 217, type: attribute)

### src\services\trending_service.py:TrendingService._retry_with_backoff

Calls:
- `range` (line 99, type: direct)
- `func` (line 101, type: direct)
- `lower` (line 105, type: attribute)
- `str` (line 105, type: direct)
- `warning` (line 106, type: attribute)
- `_close_session` (line 109, type: attribute)
- `min` (line 111, type: direct)
- `warning` (line 112, type: attribute)
- `str` (line 117, type: direct)
- `sleep` (line 119, type: attribute)
- `error` (line 121, type: attribute)
- `str` (line 122, type: direct)
- `lower` (line 125, type: attribute)
- `str` (line 125, type: direct)
- `any` (line 127, type: direct)
- `error` (line 128, type: attribute)
- `_close_session` (line 130, type: attribute)
- `min` (line 133, type: direct)
- `warning` (line 134, type: attribute)
- `str` (line 138, type: direct)
- `sleep` (line 140, type: attribute)
- `error` (line 142, type: attribute)
- `str` (line 142, type: direct)
- `error` (line 145, type: attribute)

### src\services\trending_service.py:TrendingService._start_refresh_task

Calls:
- `create_task` (line 200, type: attribute)
- `_refresh_loop` (line 200, type: attribute)

### src\services\trending_service.py:TrendingService.cleanup

Calls:
- `cancel` (line 655, type: attribute)
- `close` (line 658, type: attribute)
- `info` (line 660, type: attribute)

### src\services\trending_service.py:TrendingService.cleanup_expired

Calls:
- `connection` (line 526, type: attribute)
- `execute` (line 528, type: attribute)
- `execute` (line 534, type: attribute)
- `fetchall` (line 535, type: attribute)
- `glob` (line 539, type: attribute)
- `str` (line 540, type: direct)
- `unlink` (line 542, type: attribute)
- `commit` (line 546, type: attribute)

### src\services\trending_service.py:TrendingService.fetch_makerworld_trending

Calls:
- `_fetch_url` (line 293, type: attribute)
- `BeautifulSoup` (line 294, type: direct)
- `find_all` (line 297, type: attribute)
- `find` (line 302, type: attribute)
- `find` (line 303, type: attribute)
- `find` (line 304, type: attribute)
- `find` (line 305, type: attribute)
- `_extract_id_from_url` (line 309, type: attribute)
- `append` (line 311, type: attribute)
- `str` (line 313, type: direct)
- `uuid4` (line 313, type: direct)
- `strip` (line 314, type: attribute)
- `strip` (line 316, type: attribute)
- `_parse_count` (line 317, type: attribute)
- `warning` (line 321, type: attribute)
- `info` (line 323, type: attribute)
- `len` (line 323, type: direct)
- `error` (line 326, type: attribute)

### src\services\trending_service.py:TrendingService.fetch_printables_trending

Calls:
- `_fetch_url` (line 338, type: attribute)
- `BeautifulSoup` (line 339, type: direct)
- `find_all` (line 342, type: attribute)
- `find` (line 346, type: attribute)
- `find` (line 347, type: attribute)
- `find` (line 348, type: attribute)
- `find` (line 349, type: attribute)
- `find` (line 350, type: attribute)
- `_extract_id_from_url` (line 354, type: attribute)
- `append` (line 356, type: attribute)
- `str` (line 358, type: direct)
- `uuid4` (line 358, type: direct)
- `strip` (line 359, type: attribute)
- `strip` (line 361, type: attribute)
- `_parse_count` (line 362, type: attribute)
- `_parse_count` (line 363, type: attribute)
- `warning` (line 367, type: attribute)
- `info` (line 369, type: attribute)
- `len` (line 369, type: direct)
- `error` (line 372, type: attribute)

### src\services\trending_service.py:TrendingService.get_statistics

Calls:
- `connection` (line 597, type: attribute)
- `execute` (line 599, type: attribute)
- `fetchone` (line 600, type: attribute)
- `execute` (line 603, type: attribute)
- `fetchone` (line 607, type: attribute)
- `execute` (line 610, type: attribute)
- `fetchall` (line 616, type: attribute)
- `execute` (line 619, type: attribute)
- `fetchall` (line 625, type: attribute)

### src\services\trending_service.py:TrendingService.get_trending

Calls:
- `append` (line 479, type: attribute)
- `append` (line 483, type: attribute)
- `append` (line 486, type: attribute)
- `connection` (line 488, type: attribute)
- `execute` (line 489, type: attribute)
- `fetchall` (line 490, type: attribute)
- `dict` (line 492, type: direct)

### src\services\trending_service.py:TrendingService.initialize

Calls:
- `_create_tables` (line 58, type: attribute)
- `_start_refresh_task` (line 59, type: attribute)
- `info` (line 60, type: attribute)
- `error` (line 62, type: attribute)

### src\services\trending_service.py:TrendingService.refresh_all_platforms

Calls:
- `info` (line 496, type: attribute)
- `fetch_makerworld_trending` (line 500, type: attribute)
- `fetch_printables_trending` (line 501, type: attribute)
- `save_trending_items` (line 505, type: attribute)
- `info` (line 506, type: attribute)
- `len` (line 506, type: direct)
- `save_trending_items` (line 509, type: attribute)
- `info` (line 510, type: attribute)
- `len` (line 510, type: direct)
- `cleanup_expired` (line 513, type: attribute)
- `emit_event` (line 516, type: attribute)
- `isoformat` (line 518, type: attribute)
- `now` (line 518, type: attribute)
- `error` (line 522, type: attribute)

### src\services\trending_service.py:TrendingService.save_as_idea

Calls:
- `connection` (line 550, type: attribute)
- `execute` (line 552, type: attribute)
- `fetchone` (line 556, type: attribute)
- `ValueError` (line 558, type: direct)
- `str` (line 561, type: direct)
- `uuid4` (line 561, type: direct)
- `execute` (line 563, type: attribute)
- `isoformat` (line 574, type: attribute)
- `now` (line 574, type: attribute)
- `dumps` (line 575, type: attribute)
- `commit` (line 584, type: attribute)
- `emit_event` (line 587, type: attribute)

### src\services\trending_service.py:TrendingService.save_trending_items

Calls:
- `now` (line 411, type: attribute)
- `timedelta` (line 411, type: direct)
- `connection` (line 413, type: attribute)
- `str` (line 416, type: direct)
- `uuid4` (line 416, type: direct)
- `execute` (line 419, type: attribute)
- `fetchone` (line 424, type: attribute)
- `execute` (line 428, type: attribute)
- `get` (line 436, type: attribute)
- `get` (line 436, type: attribute)
- `get` (line 437, type: attribute)
- `get` (line 437, type: attribute)
- `isoformat` (line 438, type: attribute)
- `now` (line 438, type: attribute)
- `isoformat` (line 438, type: attribute)
- `dumps` (line 439, type: attribute)
- `get` (line 439, type: attribute)
- `execute` (line 444, type: attribute)
- `get` (line 453, type: attribute)
- `get` (line 454, type: attribute)
- `get` (line 455, type: attribute)
- `get` (line 455, type: attribute)
- `get` (line 456, type: attribute)
- `get` (line 456, type: attribute)
- `isoformat` (line 457, type: attribute)
- `now` (line 457, type: attribute)
- `isoformat` (line 457, type: attribute)
- `dumps` (line 458, type: attribute)
- `get` (line 458, type: attribute)
- `warning` (line 462, type: attribute)
- `commit` (line 464, type: attribute)

### src\services\url_parser_service.py:UrlParserService._clean_title

Calls:
- `sub` (line 125, type: attribute)
- `strip` (line 127, type: attribute)

### src\services\url_parser_service.py:UrlParserService._get_session

Calls:
- `ClientTimeout` (line 28, type: attribute)
- `ClientSession` (line 29, type: attribute)

### src\services\url_parser_service.py:UrlParserService.close

Calls:
- `close` (line 35, type: attribute)

### src\services\url_parser_service.py:UrlParserService.detect_platform

Calls:
- `lower` (line 40, type: attribute)

### src\services\url_parser_service.py:UrlParserService.extract_creator_from_title

Calls:
- `search` (line 134, type: attribute)
- `strip` (line 135, type: attribute)
- `group` (line 135, type: attribute)
- `warning` (line 140, type: attribute)
- `str` (line 140, type: direct)

### src\services\url_parser_service.py:UrlParserService.extract_model_id

Calls:
- `search` (line 60, type: attribute)
- `group` (line 61, type: attribute)
- `search` (line 65, type: attribute)
- `group` (line 66, type: attribute)
- `search` (line 70, type: attribute)
- `group` (line 71, type: attribute)
- `search` (line 75, type: attribute)
- `group` (line 76, type: attribute)
- `urlparse` (line 81, type: attribute)
- `split` (line 82, type: attribute)
- `warning` (line 85, type: attribute)
- `str` (line 85, type: direct)

### src\services\url_parser_service.py:UrlParserService.fetch_page_title

Calls:
- `_get_session` (line 92, type: attribute)
- `get` (line 93, type: attribute)
- `text` (line 95, type: attribute)
- `BeautifulSoup` (line 96, type: direct)
- `find` (line 98, type: attribute)
- `strip` (line 100, type: attribute)
- `get_text` (line 100, type: attribute)
- `_clean_title` (line 102, type: attribute)
- `warning` (line 106, type: attribute)
- `str` (line 106, type: direct)

### src\services\url_parser_service.py:UrlParserService.get_platform_info

Calls:
- `get` (line 238, type: attribute)
- `title` (line 239, type: attribute)

### src\services\url_parser_service.py:UrlParserService.parse_url

Calls:
- `urlparse` (line 148, type: attribute)
- `ValueError` (line 150, type: direct)
- `detect_platform` (line 153, type: attribute)
- `extract_model_id` (line 159, type: attribute)
- `fetch_page_title` (line 162, type: attribute)
- `_clean_title` (line 168, type: attribute)
- `extract_creator_from_title` (line 169, type: attribute)
- `title` (line 176, type: attribute)
- `isoformat` (line 179, type: attribute)
- `now` (line 179, type: attribute)
- `info` (line 183, type: attribute)
- `error` (line 187, type: attribute)
- `str` (line 187, type: direct)
- `str` (line 194, type: direct)
- `isoformat` (line 195, type: attribute)
- `now` (line 195, type: attribute)

### src\services\url_parser_service.py:UrlParserService.validate_url

Calls:
- `urlparse` (line 246, type: attribute)
- `detect_platform` (line 250, type: attribute)

### src\services\watch_folder_db_service.py:WatchFolderDbService.create_watch_folder

Calls:
- `RuntimeError` (line 29, type: direct)
- `get_connection` (line 31, type: attribute)
- `execute` (line 32, type: attribute)
- `isoformat` (line 45, type: attribute)
- `isoformat` (line 48, type: attribute)
- `commit` (line 53, type: attribute)
- `info` (line 55, type: attribute)
- `error` (line 60, type: attribute)
- `str` (line 61, type: direct)
- `ValueError` (line 62, type: direct)
- `error` (line 64, type: attribute)
- `str` (line 65, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.delete_watch_folder

Calls:
- `RuntimeError` (line 177, type: direct)
- `get_connection` (line 179, type: attribute)
- `execute` (line 180, type: attribute)
- `commit` (line 183, type: attribute)
- `info` (line 186, type: attribute)
- `error` (line 191, type: attribute)
- `str` (line 191, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.delete_watch_folder_by_path

Calls:
- `RuntimeError` (line 198, type: direct)
- `get_connection` (line 200, type: attribute)
- `execute` (line 201, type: attribute)
- `commit` (line 204, type: attribute)
- `info` (line 207, type: attribute)
- `error` (line 212, type: attribute)
- `str` (line 212, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.get_active_folder_paths

Calls:
- `RuntimeError` (line 219, type: direct)
- `get_connection` (line 221, type: attribute)
- `execute` (line 222, type: attribute)
- `fetchall` (line 223, type: attribute)
- `error` (line 227, type: attribute)
- `str` (line 227, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.get_all_watch_folders

Calls:
- `RuntimeError` (line 108, type: direct)
- `get_connection` (line 110, type: attribute)
- `execute` (line 117, type: attribute)
- `fetchall` (line 118, type: attribute)
- `from_db_row` (line 119, type: attribute)
- `error` (line 122, type: attribute)
- `str` (line 122, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.get_watch_folder_by_id

Calls:
- `RuntimeError` (line 72, type: direct)
- `get_connection` (line 74, type: attribute)
- `execute` (line 75, type: attribute)
- `fetchone` (line 76, type: attribute)
- `from_db_row` (line 79, type: attribute)
- `error` (line 83, type: attribute)
- `str` (line 83, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.get_watch_folder_by_path

Calls:
- `RuntimeError` (line 90, type: direct)
- `get_connection` (line 92, type: attribute)
- `execute` (line 93, type: attribute)
- `fetchone` (line 94, type: attribute)
- `from_db_row` (line 97, type: attribute)
- `error` (line 101, type: attribute)
- `str` (line 101, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.migrate_env_folders

Calls:
- `get_watch_folder_by_path` (line 284, type: attribute)
- `debug` (line 286, type: attribute)
- `WatchFolder` (line 290, type: direct)
- `Path` (line 293, type: direct)
- `create_watch_folder` (line 297, type: attribute)
- `info` (line 299, type: attribute)
- `info` (line 304, type: attribute)
- `error` (line 308, type: attribute)
- `str` (line 308, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.update_folder_statistics

Calls:
- `RuntimeError` (line 234, type: direct)
- `now` (line 236, type: attribute)
- `get_connection` (line 237, type: attribute)
- `execute` (line 238, type: attribute)
- `isoformat` (line 242, type: attribute)
- `commit` (line 245, type: attribute)
- `error` (line 249, type: attribute)
- `str` (line 250, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.update_watch_folder

Calls:
- `RuntimeError` (line 129, type: direct)
- `items` (line 138, type: attribute)
- `append` (line 140, type: attribute)
- `append` (line 141, type: attribute)
- `append` (line 143, type: attribute)
- `append` (line 144, type: attribute)
- `bool` (line 144, type: direct)
- `append` (line 146, type: attribute)
- `append` (line 147, type: attribute)
- `int` (line 147, type: direct)
- `append` (line 149, type: attribute)
- `append` (line 150, type: attribute)
- `isinstance` (line 150, type: direct)
- `isoformat` (line 150, type: attribute)
- `append` (line 155, type: attribute)
- `get_connection` (line 157, type: attribute)
- `join` (line 158, type: attribute)
- `execute` (line 159, type: attribute)
- `commit` (line 162, type: attribute)
- `info` (line 165, type: attribute)
- `list` (line 165, type: direct)
- `keys` (line 165, type: attribute)
- `error` (line 170, type: attribute)
- `str` (line 170, type: direct)

### src\services\watch_folder_db_service.py:WatchFolderDbService.validate_and_update_folder

Calls:
- `RuntimeError` (line 258, type: direct)
- `now` (line 260, type: attribute)
- `get_connection` (line 261, type: attribute)
- `execute` (line 262, type: attribute)
- `isoformat` (line 266, type: attribute)
- `commit` (line 269, type: attribute)
- `error` (line 273, type: attribute)
- `str` (line 274, type: direct)

### src\utils\config.py:PrinternizerSettings.cors_origins_list

Calls:
- `strip` (line 128, type: attribute)
- `split` (line 128, type: attribute)
- `strip` (line 128, type: attribute)

### src\utils\config.py:PrinternizerSettings.is_homeassistant_addon

Calls:
- `exists` (line 140, type: attribute)

### src\utils\config.py:PrinternizerSettings.validate_library_path

Calls:
- `Path` (line 111, type: direct)
- `is_absolute` (line 114, type: attribute)
- `warning` (line 115, type: attribute)
- `absolute` (line 117, type: attribute)
- `str` (line 119, type: direct)
- `absolute` (line 119, type: attribute)
- `validator` (line 104, type: direct)

### src\utils\config.py:PrinternizerSettings.validate_secret_key

Calls:
- `token_urlsafe` (line 94, type: attribute)
- `warning` (line 95, type: attribute)
- `info` (line 96, type: attribute)
- `len` (line 100, type: direct)
- `ValueError` (line 101, type: direct)
- `validator` (line 89, type: direct)

### src\utils\config.py:PrinternizerSettings.watch_folders_list

Calls:
- `strip` (line 135, type: attribute)
- `split` (line 135, type: attribute)
- `strip` (line 135, type: attribute)

### src\utils\config.py:get_settings

Calls:
- `PrinternizerSettings` (line 161, type: direct)

### src\utils\config.py:reload_settings

Calls:
- `PrinternizerSettings` (line 168, type: direct)

### src\utils\dependencies.py:get_analytics_service

Calls:
- `Depends` (line 53, type: direct)
- `AnalyticsService` (line 56, type: direct)

### src\utils\dependencies.py:get_idea_service

Calls:
- `Depends` (line 60, type: direct)
- `IdeaService` (line 63, type: direct)

### src\utils\dependencies.py:get_job_service

Calls:
- `Depends` (line 40, type: direct)
- `Depends` (line 41, type: direct)
- `JobService` (line 44, type: direct)

### src\utils\error_handling.py:ErrorHandler.__init__

Calls:
- `Path` (line 46, type: direct)
- `ensure_log_directory` (line 47, type: attribute)

### src\utils\error_handling.py:ErrorHandler._calculate_statistics

Calls:
- `get` (line 208, type: attribute)
- `get` (line 209, type: attribute)
- `get` (line 212, type: attribute)
- `get` (line 213, type: attribute)
- `get` (line 216, type: attribute)
- `get` (line 217, type: attribute)
- `len` (line 221, type: direct)

### src\utils\error_handling.py:ErrorHandler._generate_error_id

Calls:
- `int` (line 111, type: direct)
- `timestamp` (line 111, type: attribute)
- `now` (line 111, type: attribute)
- `id` (line 111, type: direct)
- `object` (line 111, type: direct)

### src\utils\error_handling.py:ErrorHandler._generate_user_message

Calls:
- `get` (line 138, type: attribute)

### src\utils\error_handling.py:ErrorHandler._get_log_level

Calls:
- `get` (line 121, type: attribute)

### src\utils\error_handling.py:ErrorHandler._handle_critical_error

Calls:
- `critical` (line 150, type: attribute)

### src\utils\error_handling.py:ErrorHandler._log_to_file

Calls:
- `open` (line 143, type: direct)
- `write` (line 144, type: attribute)
- `dumps` (line 144, type: attribute)
- `error` (line 146, type: attribute)
- `str` (line 146, type: direct)

### src\utils\error_handling.py:ErrorHandler.ensure_log_directory

Calls:
- `mkdir` (line 51, type: attribute)

### src\utils\error_handling.py:ErrorHandler.get_error_statistics

Calls:
- `exists` (line 167, type: attribute)
- `_empty_stats` (line 168, type: attribute)
- `timestamp` (line 170, type: attribute)
- `now` (line 170, type: attribute)
- `open` (line 173, type: direct)
- `loads` (line 176, type: attribute)
- `strip` (line 176, type: attribute)
- `timestamp` (line 177, type: attribute)
- `fromisoformat` (line 177, type: attribute)
- `append` (line 179, type: attribute)
- `_calculate_statistics` (line 183, type: attribute)
- `error` (line 186, type: attribute)
- `str` (line 186, type: direct)
- `_empty_stats` (line 187, type: attribute)

### src\utils\error_handling.py:ErrorHandler.handle_error

Calls:
- `_generate_error_id` (line 77, type: attribute)
- `isoformat` (line 78, type: attribute)
- `now` (line 78, type: attribute)
- `type` (line 81, type: direct)
- `str` (line 82, type: direct)
- `format_exc` (line 83, type: attribute)
- `_generate_user_message` (line 85, type: attribute)
- `_get_log_level` (line 89, type: attribute)
- `getattr` (line 90, type: direct)
- `title` (line 91, type: attribute)
- `_log_to_file` (line 101, type: attribute)
- `_handle_critical_error` (line 105, type: attribute)

### src\utils\error_handling.py:ErrorReportingMixin.report_error

Calls:
- `handle_error` (line 306, type: attribute)

### src\utils\error_handling.py:async_wrapper

Calls:
- `func` (line 272, type: direct)
- `handle_error` (line 274, type: attribute)
- `str` (line 280, type: direct)
- `str` (line 281, type: direct)
- `wraps` (line 269, type: attribute)

### src\utils\error_handling.py:decorator

Calls:
- `iscoroutinefunction` (line 289, type: attribute)

### src\utils\error_handling.py:handle_api_error

Calls:
- `handle_error` (line 328, type: attribute)

### src\utils\error_handling.py:handle_database_error

Calls:
- `handle_error` (line 318, type: attribute)

### src\utils\error_handling.py:handle_file_error

Calls:
- `handle_error` (line 348, type: attribute)

### src\utils\error_handling.py:handle_printer_error

Calls:
- `handle_error` (line 338, type: attribute)

### src\utils\error_handling.py:handle_validation_error

Calls:
- `handle_error` (line 358, type: attribute)

### src\utils\error_handling.py:sync_wrapper

Calls:
- `func` (line 252, type: direct)
- `handle_error` (line 254, type: attribute)
- `str` (line 260, type: direct)
- `str` (line 261, type: direct)
- `wraps` (line 249, type: attribute)

### src\utils\exceptions.py:AuthenticationError.__init__

Calls:
- `__init__` (line 92, type: attribute)
- `super` (line 92, type: direct)

### src\utils\exceptions.py:AuthorizationError.__init__

Calls:
- `__init__` (line 104, type: attribute)
- `super` (line 104, type: direct)

### src\utils\exceptions.py:ConfigurationError.__init__

Calls:
- `__init__` (line 32, type: attribute)
- `super` (line 32, type: direct)

### src\utils\exceptions.py:DatabaseError.__init__

Calls:
- `__init__` (line 44, type: attribute)
- `super` (line 44, type: direct)

### src\utils\exceptions.py:FileOperationError.__init__

Calls:
- `__init__` (line 68, type: attribute)
- `super` (line 68, type: direct)

### src\utils\exceptions.py:NotFoundError.__init__

Calls:
- `__init__` (line 116, type: attribute)
- `super` (line 116, type: direct)

### src\utils\exceptions.py:PrinterConnectionError.__init__

Calls:
- `__init__` (line 56, type: attribute)
- `super` (line 56, type: direct)

### src\utils\exceptions.py:PrinternizerException.__init__

Calls:
- `__init__` (line 20, type: attribute)
- `super` (line 20, type: direct)
- `now` (line 25, type: attribute)

### src\utils\exceptions.py:ValidationError.__init__

Calls:
- `__init__` (line 80, type: attribute)
- `super` (line 80, type: direct)

### src\utils\gcode_analyzer.py:GcodeAnalyzer._is_likely_print_move

Calls:
- `search` (line 120, type: attribute)
- `float` (line 123, type: direct)
- `group` (line 123, type: attribute)
- `abs` (line 125, type: direct)
- `search` (line 131, type: attribute)
- `search` (line 132, type: attribute)
- `float` (line 136, type: direct)
- `group` (line 136, type: attribute)
- `float` (line 137, type: direct)
- `group` (line 137, type: attribute)

### src\utils\gcode_analyzer.py:GcodeAnalyzer.analyze_gcode_file

Calls:
- `open` (line 190, type: direct)
- `enumerate` (line 192, type: direct)
- `append` (line 195, type: attribute)
- `rstrip` (line 195, type: attribute)
- `find_print_start_line` (line 197, type: attribute)
- `len` (line 200, type: direct)
- `error` (line 208, type: attribute)
- `str` (line 215, type: direct)

### src\utils\gcode_analyzer.py:GcodeAnalyzer.find_print_start_line

Calls:
- `enumerate` (line 63, type: direct)
- `upper` (line 64, type: attribute)
- `strip` (line 64, type: attribute)
- `strip` (line 65, type: attribute)
- `upper` (line 69, type: attribute)
- `debug` (line 70, type: attribute)
- `startswith` (line 74, type: attribute)
- `startswith` (line 74, type: attribute)
- `startswith` (line 76, type: attribute)
- `startswith` (line 76, type: attribute)
- `match` (line 81, type: attribute)
- `startswith` (line 85, type: attribute)
- `_is_likely_print_move` (line 92, type: attribute)
- `debug` (line 93, type: attribute)
- `debug` (line 106, type: attribute)

### src\utils\gcode_analyzer.py:GcodeAnalyzer.get_optimized_gcode_lines

Calls:
- `find_print_start_line` (line 166, type: attribute)
- `debug` (line 169, type: attribute)
- `info` (line 173, type: attribute)
- `len` (line 174, type: direct)

### src\utils\logging_config.py:get_logger

Calls:
- `get_logger` (line 68, type: attribute)

### src\utils\logging_config.py:setup_logging

Calls:
- `basicConfig` (line 16, type: attribute)
- `getattr` (line 19, type: direct)
- `upper` (line 19, type: attribute)
- `PositionalArgumentsFormatter` (line 27, type: attribute)
- `TimeStamper` (line 28, type: attribute)
- `StackInfoRenderer` (line 29, type: attribute)
- `UnicodeDecoder` (line 31, type: attribute)
- `Path` (line 36, type: direct)
- `mkdir` (line 37, type: attribute)
- `FileHandler` (line 39, type: attribute)
- `setLevel` (line 40, type: attribute)
- `getattr` (line 40, type: direct)
- `upper` (line 40, type: attribute)
- `Formatter` (line 42, type: attribute)
- `setFormatter` (line 45, type: attribute)
- `getLogger` (line 48, type: attribute)
- `addHandler` (line 49, type: attribute)
- `upper` (line 52, type: attribute)
- `append` (line 53, type: attribute)
- `ConsoleRenderer` (line 53, type: attribute)
- `append` (line 55, type: attribute)
- `JSONRenderer` (line 55, type: attribute)
- `configure` (line 57, type: attribute)
- `LoggerFactory` (line 60, type: attribute)

### src\utils\middleware.py:GermanComplianceMiddleware.dispatch

Calls:
- `info` (line 83, type: attribute)
- `hash` (line 87, type: direct)
- `time` (line 88, type: attribute)
- `call_next` (line 92, type: direct)

### src\utils\middleware.py:RequestTimingMiddleware.dispatch

Calls:
- `time` (line 19, type: attribute)
- `call_next` (line 22, type: direct)
- `time` (line 25, type: attribute)
- `str` (line 28, type: direct)
- `info` (line 31, type: attribute)
- `str` (line 34, type: direct)
- `get` (line 37, type: attribute)

### src\utils\middleware.py:SecurityHeadersMiddleware.dispatch

Calls:
- `call_next` (line 48, type: direct)

### tests\backend\test_api_files.py:TestFileAPI.test_delete_file_available_only

Calls:
- `patch` (line 261, type: direct)
- `delete` (line 264, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_delete_file_local

Calls:
- `join` (line 240, type: attribute)
- `open` (line 241, type: direct)
- `write` (line 242, type: attribute)
- `patch` (line 244, type: direct)
- `patch` (line 247, type: direct)
- `delete` (line 250, type: attribute)
- `exists` (line 255, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_get_file_download_history

Calls:
- `patch` (line 296, type: direct)
- `get` (line 299, type: attribute)
- `json` (line 302, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_get_file_download_progress

Calls:
- `patch` (line 273, type: direct)
- `get` (line 284, type: attribute)
- `json` (line 289, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_get_files_filter_by_printer

Calls:
- `patch` (line 65, type: direct)
- `get` (line 68, type: attribute)
- `json` (line 71, type: attribute)
- `len` (line 72, type: direct)

### tests\backend\test_api_files.py:TestFileAPI.test_get_files_filter_by_status

Calls:
- `patch` (line 77, type: direct)
- `get` (line 80, type: attribute)
- `json` (line 83, type: attribute)
- `len` (line 84, type: direct)

### tests\backend\test_api_files.py:TestFileAPI.test_get_files_filter_by_type

Calls:
- `patch` (line 89, type: direct)
- `get` (line 92, type: attribute)
- `json` (line 95, type: attribute)
- `len` (line 96, type: direct)

### tests\backend\test_api_files.py:TestFileAPI.test_get_files_unified_empty

Calls:
- `patch` (line 19, type: direct)
- `get` (line 22, type: attribute)
- `json` (line 25, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_get_files_unified_with_data

Calls:
- `patch` (line 34, type: direct)
- `get` (line 37, type: attribute)
- `json` (line 40, type: attribute)
- `len` (line 41, type: direct)
- `next` (line 45, type: direct)
- `next` (line 52, type: direct)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_cleanup

Calls:
- `patch` (line 316, type: direct)
- `patch` (line 319, type: direct)
- `post` (line 326, type: attribute)
- `json` (line 332, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_download_already_downloaded

Calls:
- `patch` (line 156, type: direct)
- `post` (line 159, type: attribute)
- `json` (line 164, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_download_bambu_lab

Calls:
- `patch` (line 103, type: direct)
- `patch` (line 109, type: direct)
- `patch` (line 112, type: direct)
- `post` (line 115, type: attribute)
- `json` (line 120, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_download_disk_space_error

Calls:
- `patch` (line 190, type: direct)
- `patch` (line 193, type: direct)
- `patch` (line 197, type: direct)
- `post` (line 200, type: attribute)
- `json` (line 205, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_download_printer_offline

Calls:
- `patch` (line 171, type: direct)
- `patch` (line 175, type: direct)
- `ConnectionError` (line 176, type: direct)
- `post` (line 178, type: attribute)
- `json` (line 183, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_download_prusa

Calls:
- `patch` (line 132, type: direct)
- `patch` (line 138, type: direct)
- `patch` (line 141, type: direct)
- `post` (line 144, type: attribute)
- `json` (line 149, type: attribute)

### tests\backend\test_api_files.py:TestFileAPI.test_post_file_download_with_progress_tracking

Calls:
- `patch` (line 213, type: direct)
- `Mock` (line 217, type: direct)
- `patch` (line 220, type: direct)
- `patch` (line 223, type: direct)
- `post` (line 226, type: attribute)
- `json` (line 231, type: attribute)

### tests\backend\test_api_files.py:TestFileAPIPerformance.download_file

Calls:
- `post` (line 498, type: attribute)
- `append` (line 501, type: attribute)
- `append` (line 503, type: attribute)

### tests\backend\test_api_files.py:TestFileAPIPerformance.test_concurrent_file_downloads

Calls:
- `range` (line 507, type: direct)
- `Thread` (line 508, type: attribute)
- `append` (line 509, type: attribute)
- `start` (line 512, type: attribute)
- `join` (line 515, type: attribute)
- `len` (line 518, type: direct)
- `len` (line 519, type: direct)

### tests\backend\test_api_files.py:TestFileAPIPerformance.test_large_file_list_performance

Calls:
- `cursor` (line 454, type: attribute)
- `range` (line 457, type: direct)
- `execute` (line 458, type: attribute)
- `commit` (line 470, type: attribute)
- `time` (line 474, type: attribute)
- `patch` (line 476, type: direct)
- `get` (line 478, type: attribute)
- `time` (line 480, type: attribute)
- `json` (line 487, type: attribute)
- `len` (line 488, type: direct)

### tests\backend\test_api_files.py:TestFileBusinessLogic.test_disk_space_monitoring

Calls:
- `patch` (line 436, type: direct)
- `check_disk_space` (line 441, type: direct)
- `check_disk_space` (line 445, type: direct)

### tests\backend\test_api_files.py:TestFileBusinessLogic.test_file_checksum_verification

Calls:
- `hexdigest` (line 397, type: attribute)
- `md5` (line 397, type: attribute)
- `hexdigest` (line 398, type: attribute)
- `sha256` (line 398, type: attribute)
- `calculate_file_checksum` (line 401, type: direct)
- `calculate_file_checksum` (line 402, type: direct)

### tests\backend\test_api_files.py:TestFileBusinessLogic.test_file_download_path_organization

Calls:
- `berlin_timestamp` (line 373, type: attribute)
- `patch` (line 375, type: direct)
- `generate_download_path` (line 378, type: direct)
- `join` (line 384, type: attribute)
- `normpath` (line 392, type: attribute)
- `normpath` (line 392, type: attribute)

### tests\backend\test_api_files.py:TestFileBusinessLogic.test_file_metadata_extraction_3mf

Calls:
- `extract_3mf_metadata` (line 425, type: direct)

### tests\backend\test_api_files.py:TestFileBusinessLogic.test_file_size_validation_german_limits

Calls:
- `validate_file_size` (line 420, type: direct)

### tests\backend\test_api_files.py:TestFileBusinessLogic.test_german_file_naming_sanitization

Calls:
- `sanitize_german_filename` (line 361, type: direct)

### tests\backend\test_api_files.py:calculate_file_checksum

Calls:
- `hexdigest` (line 565, type: attribute)
- `md5` (line 565, type: attribute)
- `hexdigest` (line 567, type: attribute)
- `sha256` (line 567, type: attribute)
- `ValueError` (line 569, type: direct)

### tests\backend\test_api_files.py:check_disk_space

Calls:
- `disk_usage` (line 603, type: attribute)

### tests\backend\test_api_files.py:extract_3mf_metadata

Calls:
- `fromstring` (line 583, type: attribute)
- `decode` (line 583, type: attribute)
- `findall` (line 587, type: attribute)
- `get` (line 588, type: attribute)
- `lower` (line 591, type: attribute)

### tests\backend\test_api_files.py:generate_download_path

Calls:
- `strftime` (line 557, type: attribute)
- `now` (line 557, type: attribute)
- `join` (line 559, type: attribute)

### tests\backend\test_api_files.py:sanitize_german_filename

Calls:
- `items` (line 536, type: attribute)
- `replace` (line 537, type: attribute)
- `sub` (line 540, type: attribute)
- `sub` (line 541, type: attribute)
- `lower` (line 542, type: attribute)
- `replace` (line 545, type: attribute)
- `replace` (line 546, type: attribute)
- `replace` (line 547, type: attribute)

### tests\backend\test_api_health.py:TestHealthEndpoint.test_health_check_german_timezone

Calls:
- `get` (line 58, type: attribute)
- `json` (line 61, type: attribute)
- `get` (line 63, type: attribute)

### tests\backend\test_api_health.py:TestHealthEndpoint.test_health_check_includes_system_info

Calls:
- `get` (line 33, type: attribute)
- `json` (line 36, type: attribute)

### tests\backend\test_api_health.py:TestHealthEndpoint.test_health_check_performance

Calls:
- `time` (line 72, type: attribute)
- `get` (line 73, type: attribute)
- `time` (line 74, type: attribute)

### tests\backend\test_api_health.py:TestHealthEndpoint.test_health_check_response_format

Calls:
- `get` (line 45, type: attribute)
- `json` (line 51, type: attribute)

### tests\backend\test_api_health.py:TestHealthEndpoint.test_health_check_success

Calls:
- `get` (line 22, type: attribute)
- `json` (line 25, type: attribute)

### tests\backend\test_api_health.py:client

Calls:
- `TestClient` (line 14, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_delete_active_job_forbidden

Calls:
- `patch` (line 374, type: direct)
- `delete` (line 377, type: attribute)
- `json` (line 380, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_delete_job

Calls:
- `patch` (line 363, type: direct)
- `delete` (line 366, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_job_details

Calls:
- `patch` (line 211, type: direct)
- `get` (line 214, type: attribute)
- `json` (line 217, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_job_details_not_found

Calls:
- `get` (line 241, type: attribute)
- `json` (line 244, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_date_range_filter

Calls:
- `strftime` (line 93, type: attribute)
- `now` (line 93, type: attribute)
- `strftime` (line 94, type: attribute)
- `now` (line 94, type: attribute)
- `timedelta` (line 94, type: direct)
- `patch` (line 96, type: direct)
- `get` (line 99, type: attribute)
- `json` (line 104, type: attribute)
- `isinstance` (line 106, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_empty_database

Calls:
- `patch` (line 18, type: direct)
- `get` (line 21, type: attribute)
- `json` (line 24, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_filter_by_business_type

Calls:
- `patch` (line 80, type: direct)
- `get` (line 83, type: attribute)
- `json` (line 86, type: attribute)
- `len` (line 87, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_filter_by_printer

Calls:
- `patch` (line 68, type: direct)
- `get` (line 71, type: attribute)
- `json` (line 74, type: attribute)
- `len` (line 75, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_filter_by_status

Calls:
- `patch` (line 56, type: direct)
- `get` (line 59, type: attribute)
- `json` (line 62, type: attribute)
- `len` (line 63, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_pagination

Calls:
- `patch` (line 110, type: direct)
- `get` (line 113, type: attribute)
- `json` (line 116, type: attribute)
- `len` (line 117, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_get_jobs_with_data

Calls:
- `patch` (line 32, type: direct)
- `get` (line 35, type: attribute)
- `json` (line 38, type: attribute)
- `len` (line 39, type: direct)
- `next` (line 44, type: direct)
- `next` (line 50, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_post_jobs_create_new_job

Calls:
- `patch` (line 143, type: direct)
- `post` (line 146, type: attribute)
- `json` (line 152, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_post_jobs_validation_errors

Calls:
- `post` (line 198, type: attribute)
- `json` (line 205, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_put_job_completion_with_quality_assessment

Calls:
- `isoformat` (line 277, type: attribute)
- `now` (line 277, type: attribute)
- `patch` (line 286, type: direct)
- `put` (line 289, type: attribute)
- `json` (line 295, type: attribute)
- `abs` (line 303, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPI.test_put_job_failure_handling

Calls:
- `isoformat` (line 311, type: attribute)
- `now` (line 311, type: attribute)
- `patch` (line 318, type: direct)
- `put` (line 321, type: attribute)
- `json` (line 327, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_put_job_status_invalid_transitions

Calls:
- `put` (line 351, type: attribute)
- `json` (line 357, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPI.test_put_job_status_update

Calls:
- `patch` (line 256, type: direct)
- `put` (line 259, type: attribute)
- `json` (line 265, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIErrorHandling.test_job_api_database_connection_error

Calls:
- `patch` (line 587, type: direct)
- `OperationalError` (line 588, type: attribute)
- `get` (line 590, type: attribute)
- `json` (line 593, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIErrorHandling.test_job_creation_with_invalid_printer

Calls:
- `post` (line 603, type: attribute)
- `json` (line 609, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIErrorHandling.test_job_deletion_safety_checks

Calls:
- `delete` (line 638, type: attribute)
- `delete` (line 643, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIErrorHandling.test_job_update_race_condition_handling

Calls:
- `patch` (line 616, type: direct)
- `put` (line 620, type: attribute)
- `put` (line 626, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIPerformance.test_concurrent_job_updates

Calls:
- `range` (line 565, type: direct)
- `Thread` (line 566, type: attribute)
- `append` (line 567, type: attribute)
- `start` (line 571, type: attribute)
- `join` (line 575, type: attribute)
- `len` (line 578, type: direct)

### tests\backend\test_api_jobs.py:TestJobAPIPerformance.test_job_filtering_performance

Calls:
- `time` (line 536, type: attribute)
- `get` (line 538, type: attribute)
- `time` (line 540, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIPerformance.test_large_job_list_performance

Calls:
- `cursor` (line 489, type: attribute)
- `range` (line 492, type: direct)
- `execute` (line 493, type: attribute)
- `commit` (line 504, type: attribute)
- `time` (line 508, type: attribute)
- `patch` (line 510, type: direct)
- `get` (line 512, type: attribute)
- `time` (line 514, type: attribute)
- `json` (line 521, type: attribute)

### tests\backend\test_api_jobs.py:TestJobAPIPerformance.update_job_status

Calls:
- `put` (line 555, type: attribute)
- `append` (line 559, type: attribute)
- `append` (line 561, type: attribute)

### tests\backend\test_api_jobs.py:TestJobBusinessLogic.test_business_vs_private_job_classification

Calls:
- `cursor` (line 421, type: attribute)
- `execute` (line 424, type: attribute)
- `fetchone` (line 425, type: attribute)
- `len` (line 428, type: direct)
- `execute` (line 431, type: attribute)
- `fetchone` (line 432, type: attribute)

### tests\backend\test_api_jobs.py:TestJobBusinessLogic.test_german_cost_calculations

Calls:
- `float` (line 405, type: direct)
- `round` (line 406, type: direct)
- `round` (line 409, type: direct)

### tests\backend\test_api_jobs.py:TestJobBusinessLogic.test_job_timezone_handling

Calls:
- `cursor` (line 438, type: attribute)
- `execute` (line 439, type: attribute)
- `fetchone` (line 440, type: attribute)
- `berlin_timestamp` (line 443, type: attribute)

### tests\backend\test_api_jobs.py:TestJobBusinessLogic.test_material_usage_tracking

Calls:
- `abs` (line 462, type: direct)

### tests\backend\test_api_jobs.py:TestJobBusinessLogic.test_print_quality_assessment_german_standards

Calls:
- `get` (line 469, type: attribute)
- `get` (line 474, type: attribute)
- `get` (line 479, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_delete_printer_with_active_jobs

Calls:
- `patch` (line 329, type: direct)
- `delete` (line 332, type: attribute)
- `json` (line 337, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_delete_printers

Calls:
- `patch` (line 309, type: direct)
- `delete` (line 312, type: attribute)
- `cursor` (line 319, type: attribute)
- `execute` (line 320, type: attribute)
- `fetchone` (line 321, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printer_status_bambu_lab

Calls:
- `patch` (line 181, type: direct)
- `get` (line 184, type: attribute)
- `json` (line 189, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printer_status_not_found

Calls:
- `get` (line 251, type: attribute)
- `json` (line 256, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printer_status_offline

Calls:
- `patch` (line 237, type: direct)
- `ConnectionError` (line 238, type: direct)
- `get` (line 240, type: attribute)
- `json` (line 245, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printer_status_prusa

Calls:
- `patch` (line 213, type: direct)
- `get` (line 216, type: attribute)
- `json` (line 221, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printers_empty_database

Calls:
- `patch` (line 19, type: direct)
- `get` (line 22, type: attribute)
- `json` (line 25, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printers_filter_by_active_status

Calls:
- `patch` (line 67, type: direct)
- `get` (line 70, type: attribute)
- `json` (line 73, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printers_filter_by_type

Calls:
- `patch` (line 55, type: direct)
- `get` (line 58, type: attribute)
- `json` (line 61, type: attribute)
- `len` (line 62, type: direct)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_get_printers_with_data

Calls:
- `patch` (line 32, type: direct)
- `get` (line 35, type: attribute)
- `json` (line 38, type: attribute)
- `len` (line 39, type: direct)
- `next` (line 43, type: direct)
- `next` (line 49, type: direct)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_post_printers_bambu_lab

Calls:
- `patch` (line 91, type: direct)
- `post` (line 94, type: attribute)
- `json` (line 100, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_post_printers_prusa

Calls:
- `patch` (line 116, type: direct)
- `post` (line 119, type: attribute)
- `json` (line 125, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_post_printers_validation_errors

Calls:
- `post` (line 168, type: attribute)
- `json` (line 175, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_printer_connection_test

Calls:
- `patch` (line 344, type: direct)
- `post` (line 348, type: attribute)
- `json` (line 353, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_printer_connection_test_failed

Calls:
- `patch` (line 361, type: direct)
- `ConnectionError` (line 362, type: direct)
- `post` (line 364, type: attribute)
- `json` (line 369, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_put_printers_invalid_update

Calls:
- `put` (line 297, type: attribute)
- `json` (line 303, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPI.test_put_printers_update_config

Calls:
- `patch` (line 267, type: direct)
- `put` (line 270, type: attribute)
- `json` (line 276, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPIEdgeCases.make_request

Calls:
- `get` (line 473, type: attribute)
- `append` (line 474, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPIEdgeCases.test_concurrent_printer_requests

Calls:
- `range` (line 478, type: direct)
- `Thread` (line 479, type: attribute)
- `append` (line 480, type: attribute)
- `start` (line 484, type: attribute)
- `join` (line 488, type: attribute)
- `all` (line 491, type: direct)
- `len` (line 492, type: direct)

### tests\backend\test_api_printers.py:TestPrinterAPIEdgeCases.test_invalid_json_handling

Calls:
- `post` (line 550, type: attribute)
- `json` (line 557, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPIEdgeCases.test_large_printer_list_performance

Calls:
- `cursor` (line 497, type: attribute)
- `range` (line 499, type: direct)
- `execute` (line 500, type: attribute)
- `commit` (line 512, type: attribute)
- `time` (line 516, type: attribute)
- `patch` (line 518, type: direct)
- `get` (line 520, type: attribute)
- `time` (line 522, type: attribute)
- `json` (line 529, type: attribute)
- `len` (line 530, type: direct)

### tests\backend\test_api_printers.py:TestPrinterAPIEdgeCases.test_oversized_request_handling

Calls:
- `post` (line 570, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterAPIEdgeCases.test_printer_api_rate_limiting

Calls:
- `range` (line 538, type: direct)
- `get` (line 539, type: attribute)
- `append` (line 540, type: attribute)
- `len` (line 544, type: direct)

### tests\backend\test_api_printers.py:TestPrinterBusinessLogic.test_printer_business_hours_validation

Calls:
- `fromisoformat` (line 419, type: attribute)
- `fromisoformat` (line 420, type: attribute)
- `time` (line 424, type: direct)
- `time` (line 425, type: direct)
- `time` (line 426, type: direct)
- `time` (line 427, type: direct)
- `time` (line 428, type: direct)

### tests\backend\test_api_printers.py:TestPrinterBusinessLogic.test_printer_cost_calculations_euro

Calls:
- `calculate_vat` (line 405, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterBusinessLogic.test_printer_id_generation_german_locale

Calls:
- `generate_printer_id` (line 445, type: direct)
- `startswith` (line 446, type: attribute)
- `split` (line 446, type: attribute)

### tests\backend\test_api_printers.py:TestPrinterBusinessLogic.test_printer_timezone_handling

Calls:
- `cursor` (line 379, type: attribute)
- `execute` (line 380, type: attribute)
- `fetchone` (line 384, type: attribute)
- `berlin_timestamp` (line 388, type: attribute)

### tests\backend\test_api_printers.py:generate_printer_id

Calls:
- `sub` (line 454, type: attribute)
- `lower` (line 454, type: attribute)
- `sub` (line 455, type: attribute)
- `strip` (line 455, type: attribute)

### tests\backend\test_database.py:TestDatabasePerformance.test_database_size_estimates

Calls:
- `cursor` (line 520, type: attribute)
- `execute` (line 523, type: attribute)
- `fetchone` (line 524, type: attribute)
- `range` (line 528, type: direct)
- `execute` (line 529, type: attribute)
- `round` (line 535, type: direct)
- `round` (line 536, type: direct)
- `round` (line 537, type: direct)
- `range` (line 540, type: direct)
- `execute` (line 541, type: attribute)
- `commit` (line 550, type: attribute)
- `execute` (line 553, type: attribute)
- `fetchone` (line 554, type: attribute)

### tests\backend\test_database.py:TestDatabasePerformance.test_job_query_performance_with_indexes

Calls:
- `cursor` (line 480, type: attribute)
- `range` (line 483, type: direct)
- `execute` (line 484, type: attribute)
- `isoformat` (line 492, type: attribute)
- `now` (line 492, type: attribute)
- `commit` (line 495, type: attribute)
- `time` (line 501, type: attribute)
- `execute` (line 502, type: attribute)
- `fetchone` (line 503, type: attribute)
- `time` (line 504, type: attribute)
- `time` (line 510, type: attribute)
- `execute` (line 511, type: attribute)
- `fetchone` (line 512, type: attribute)
- `time` (line 513, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_database_creation

Calls:
- `connect` (line 16, type: attribute)
- `cursor` (line 17, type: attribute)
- `execute` (line 20, type: attribute)
- `fetchall` (line 25, type: attribute)
- `close` (line 35, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_database_indexes

Calls:
- `connect` (line 137, type: attribute)
- `cursor` (line 138, type: attribute)
- `execute` (line 141, type: attribute)
- `fetchall` (line 145, type: attribute)
- `close` (line 161, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_database_triggers

Calls:
- `cursor` (line 165, type: attribute)
- `now` (line 168, type: attribute)
- `execute` (line 170, type: attribute)
- `commit` (line 174, type: attribute)
- `execute` (line 176, type: attribute)
- `fetchone` (line 179, type: attribute)
- `fromisoformat` (line 180, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_database_views

Calls:
- `cursor` (line 239, type: attribute)
- `execute` (line 242, type: attribute)
- `fetchall` (line 243, type: attribute)
- `len` (line 245, type: direct)
- `execute` (line 253, type: attribute)
- `fetchall` (line 254, type: attribute)
- `len` (line 256, type: direct)
- `execute` (line 259, type: attribute)
- `fetchall` (line 260, type: attribute)
- `len` (line 263, type: direct)

### tests\backend\test_database.py:TestDatabaseSchema.test_file_table_generated_columns

Calls:
- `cursor` (line 108, type: attribute)
- `enumerate` (line 119, type: direct)
- `execute` (line 120, type: attribute)
- `execute` (line 126, type: attribute)
- `fetchone` (line 130, type: attribute)
- `commit` (line 133, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_foreign_key_constraints

Calls:
- `cursor` (line 219, type: attribute)
- `execute` (line 222, type: attribute)
- `raises` (line 225, type: attribute)
- `execute` (line 226, type: attribute)
- `commit` (line 227, type: attribute)
- `raises` (line 230, type: attribute)
- `execute` (line 231, type: attribute)
- `commit` (line 235, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_job_status_change_trigger

Calls:
- `cursor` (line 187, type: attribute)
- `execute` (line 190, type: attribute)
- `fetchone` (line 191, type: attribute)
- `execute` (line 194, type: attribute)
- `commit` (line 198, type: attribute)
- `execute` (line 201, type: attribute)
- `fetchone` (line 202, type: attribute)
- `execute` (line 207, type: attribute)
- `fetchone` (line 212, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_job_table_constraints

Calls:
- `cursor` (line 66, type: attribute)
- `execute` (line 69, type: attribute)
- `commit` (line 73, type: attribute)
- `execute` (line 76, type: attribute)
- `fetchone` (line 79, type: attribute)
- `raises` (line 83, type: attribute)
- `execute` (line 84, type: attribute)
- `commit` (line 88, type: attribute)
- `raises` (line 91, type: attribute)
- `execute` (line 92, type: attribute)
- `commit` (line 96, type: attribute)
- `raises` (line 99, type: attribute)
- `execute` (line 100, type: attribute)
- `commit` (line 104, type: attribute)

### tests\backend\test_database.py:TestDatabaseSchema.test_printer_table_constraints

Calls:
- `cursor` (line 39, type: attribute)
- `execute` (line 42, type: attribute)
- `commit` (line 46, type: attribute)
- `raises` (line 49, type: attribute)
- `execute` (line 50, type: attribute)
- `commit` (line 54, type: attribute)
- `raises` (line 57, type: attribute)
- `execute` (line 58, type: attribute)
- `commit` (line 62, type: attribute)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_business_vs_private_job_tracking

Calls:
- `cursor` (line 397, type: attribute)
- `execute` (line 400, type: attribute)
- `execute` (line 408, type: attribute)
- `commit` (line 415, type: attribute)
- `execute` (line 418, type: attribute)
- `fetchone` (line 422, type: attribute)
- `execute` (line 424, type: attribute)
- `fetchone` (line 428, type: attribute)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_euro_currency_calculations

Calls:
- `cursor` (line 298, type: attribute)
- `execute` (line 301, type: attribute)
- `float` (line 302, type: direct)
- `fetchone` (line 302, type: attribute)
- `execute` (line 310, type: attribute)
- `commit` (line 314, type: attribute)
- `execute` (line 317, type: attribute)
- `fetchone` (line 320, type: attribute)
- `abs` (line 323, type: direct)
- `round` (line 326, type: direct)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_european_timezone_handling

Calls:
- `cursor` (line 271, type: attribute)
- `execute` (line 274, type: attribute)
- `fetchone` (line 275, type: attribute)
- `berlin_timestamp` (line 279, type: attribute)
- `execute` (line 281, type: attribute)
- `isoformat` (line 284, type: attribute)
- `commit` (line 285, type: attribute)
- `execute` (line 288, type: attribute)
- `fetchone` (line 291, type: attribute)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_german_business_hours_config

Calls:
- `cursor` (line 335, type: attribute)
- `execute` (line 345, type: attribute)
- `fetchone` (line 346, type: attribute)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_german_file_retention_policies

Calls:
- `cursor` (line 437, type: attribute)
- `execute` (line 440, type: attribute)
- `int` (line 443, type: direct)
- `fetchone` (line 443, type: attribute)
- `now` (line 447, type: attribute)
- `timedelta` (line 447, type: direct)
- `now` (line 448, type: attribute)
- `timedelta` (line 448, type: direct)
- `execute` (line 451, type: attribute)
- `isoformat` (line 454, type: attribute)
- `execute` (line 457, type: attribute)
- `isoformat` (line 460, type: attribute)
- `commit` (line 462, type: attribute)
- `execute` (line 465, type: attribute)
- `fetchone` (line 470, type: attribute)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_material_cost_per_gram_tracking

Calls:
- `cursor` (line 352, type: attribute)
- `execute` (line 355, type: attribute)
- `float` (line 359, type: direct)
- `fetchone` (line 359, type: attribute)
- `round` (line 370, type: direct)
- `abs` (line 371, type: direct)

### tests\backend\test_database.py:TestGermanBusinessLogic.test_power_cost_calculation_german_rates

Calls:
- `cursor` (line 375, type: attribute)
- `execute` (line 378, type: attribute)
- `float` (line 381, type: direct)
- `fetchone` (line 381, type: attribute)
- `round` (line 392, type: direct)
- `abs` (line 393, type: direct)

### tests\backend\test_end_to_end.py:TestE2EDashboardWorkflow.mock_websocket_handler

Calls:
- `send` (line 630, type: attribute)
- `dumps` (line 630, type: attribute)
- `append` (line 664, type: attribute)
- `sleep` (line 665, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EDashboardWorkflow.test_complete_dashboard_monitoring

Calls:
- `patch` (line 520, type: direct)
- `get` (line 526, type: attribute)
- `json` (line 529, type: attribute)
- `patch` (line 550, type: direct)
- `post` (line 576, type: attribute)
- `json` (line 579, type: attribute)
- `round` (line 584, type: direct)
- `abs` (line 585, type: direct)
- `post` (line 596, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EDashboardWorkflow.test_real_time_dashboard_updates

Calls:
- `patch` (line 609, type: direct)
- `mock_websocket_handler` (line 668, type: direct)
- `len` (line 671, type: direct)

### tests\backend\test_end_to_end.py:TestE2EFileManagementWorkflow.test_complete_file_download_workflow

Calls:
- `patch` (line 357, type: direct)
- `patch` (line 363, type: direct)
- `post` (line 384, type: attribute)
- `json` (line 387, type: attribute)
- `get` (line 391, type: attribute)
- `json` (line 394, type: attribute)
- `len` (line 395, type: direct)
- `len` (line 400, type: direct)
- `patch` (line 405, type: direct)
- `post` (line 414, type: attribute)
- `json` (line 417, type: attribute)
- `get` (line 422, type: attribute)
- `json` (line 423, type: attribute)
- `next` (line 425, type: direct)
- `patch` (line 437, type: direct)
- `len` (line 440, type: direct)
- `post` (line 446, type: attribute)
- `json` (line 449, type: attribute)
- `len` (line 451, type: direct)
- `get` (line 454, type: attribute)
- `json` (line 455, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EFileManagementWorkflow.test_file_cleanup_workflow

Calls:
- `patch` (line 467, type: direct)
- `get` (line 480, type: attribute)
- `json` (line 483, type: attribute)
- `patch` (line 494, type: direct)
- `post` (line 505, type: attribute)
- `json` (line 508, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EGermanBusinessCompliance.test_complete_vat_compliance_workflow

Calls:
- `patch` (line 689, type: direct)
- `connect` (line 690, type: attribute)
- `cursor` (line 695, type: attribute)
- `execute` (line 696, type: attribute)
- `commit` (line 703, type: attribute)
- `post` (line 731, type: attribute)
- `append` (line 733, type: attribute)
- `json` (line 733, type: attribute)
- `enumerate` (line 736, type: direct)
- `patch` (line 744, type: direct)
- `round` (line 746, type: direct)
- `put` (line 756, type: attribute)
- `patch` (line 767, type: direct)
- `post` (line 790, type: attribute)
- `json` (line 793, type: attribute)
- `len` (line 796, type: direct)
- `sum` (line 799, type: direct)
- `abs` (line 800, type: direct)
- `post` (line 813, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EJobManagementWorkflow.test_complete_print_job_lifecycle

Calls:
- `patch` (line 175, type: direct)
- `post` (line 197, type: attribute)
- `json` (line 200, type: attribute)
- `isoformat` (line 212, type: attribute)
- `now` (line 212, type: attribute)
- `put` (line 215, type: attribute)
- `put` (line 226, type: attribute)
- `cursor` (line 230, type: attribute)
- `execute` (line 231, type: attribute)
- `fetchone` (line 232, type: attribute)
- `abs` (line 233, type: direct)
- `isoformat` (line 244, type: attribute)
- `now` (line 244, type: attribute)
- `patch` (line 247, type: direct)
- `put` (line 259, type: attribute)
- `get` (line 263, type: attribute)
- `json` (line 266, type: attribute)
- `abs` (line 279, type: direct)
- `get` (line 282, type: attribute)
- `json` (line 285, type: attribute)
- `next` (line 286, type: direct)

### tests\backend\test_end_to_end.py:TestE2EJobManagementWorkflow.test_job_failure_and_recovery

Calls:
- `patch` (line 292, type: direct)
- `post` (line 306, type: attribute)
- `json` (line 307, type: attribute)
- `put` (line 310, type: attribute)
- `isoformat` (line 320, type: attribute)
- `now` (line 320, type: attribute)
- `put` (line 323, type: attribute)
- `get` (line 327, type: attribute)
- `json` (line 328, type: attribute)
- `put` (line 340, type: attribute)
- `get` (line 344, type: attribute)
- `json` (line 345, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EPrinterSetupWorkflow.test_complete_bambu_lab_setup

Calls:
- `patch` (line 27, type: direct)
- `connect` (line 28, type: attribute)
- `patch` (line 46, type: direct)
- `patch` (line 48, type: direct)
- `post` (line 51, type: attribute)
- `json` (line 54, type: attribute)
- `cursor` (line 58, type: attribute)
- `execute` (line 59, type: attribute)
- `fetchone` (line 60, type: attribute)
- `get` (line 66, type: attribute)
- `json` (line 69, type: attribute)
- `len` (line 70, type: direct)
- `next` (line 72, type: direct)
- `patch` (line 77, type: direct)
- `get` (line 92, type: attribute)
- `json` (line 95, type: attribute)
- `put` (line 106, type: attribute)
- `execute` (line 110, type: attribute)
- `fetchone` (line 111, type: attribute)

### tests\backend\test_end_to_end.py:TestE2EPrinterSetupWorkflow.test_complete_prusa_setup

Calls:
- `patch` (line 118, type: direct)
- `connect` (line 119, type: attribute)
- `patch` (line 136, type: direct)
- `post` (line 139, type: attribute)
- `json` (line 142, type: attribute)
- `patch` (line 145, type: direct)
- `get` (line 161, type: attribute)
- `json` (line 164, type: attribute)

### tests\backend\test_error_handling.py:TestConcurrencyErrorHandling.create_job

Calls:
- `post` (line 511, type: attribute)
- `append` (line 512, type: attribute)
- `append` (line 514, type: attribute)

### tests\backend\test_error_handling.py:TestConcurrencyErrorHandling.make_update

Calls:
- `put` (line 460, type: attribute)
- `append` (line 461, type: attribute)
- `append` (line 463, type: attribute)

### tests\backend\test_error_handling.py:TestConcurrencyErrorHandling.test_concurrent_resource_access

Calls:
- `patch` (line 437, type: direct)
- `patch` (line 447, type: direct)
- `Error` (line 451, type: attribute)
- `Thread` (line 466, type: attribute)
- `Thread` (line 467, type: attribute)
- `start` (line 471, type: attribute)
- `join` (line 474, type: attribute)
- `hasattr` (line 477, type: direct)

### tests\backend\test_error_handling.py:TestConcurrencyErrorHandling.test_race_condition_in_job_creation

Calls:
- `patch` (line 483, type: direct)
- `patch` (line 495, type: direct)
- `patch` (line 499, type: direct)
- `IntegrityError` (line 503, type: attribute)
- `Thread` (line 516, type: attribute)
- `range` (line 516, type: direct)
- `start` (line 519, type: attribute)
- `join` (line 522, type: attribute)
- `sum` (line 525, type: direct)
- `hasattr` (line 525, type: direct)

### tests\backend\test_error_handling.py:TestDataValidationErrors.test_invalid_data_types

Calls:
- `patch` (line 171, type: direct)
- `next` (line 176, type: direct)
- `iter` (line 176, type: direct)
- `keys` (line 176, type: attribute)
- `type` (line 179, type: direct)
- `list` (line 179, type: direct)
- `values` (line 179, type: attribute)
- `post` (line 184, type: attribute)
- `json` (line 187, type: attribute)

### tests\backend\test_error_handling.py:TestDataValidationErrors.test_malformed_json_requests

Calls:
- `patch` (line 138, type: direct)
- `Mock` (line 139, type: direct)
- `mock_post` (line 148, type: direct)
- `json` (line 152, type: attribute)

### tests\backend\test_error_handling.py:TestDataValidationErrors.test_out_of_range_values

Calls:
- `patch` (line 205, type: direct)
- `post` (line 215, type: attribute)
- `json` (line 218, type: attribute)
- `len` (line 219, type: direct)

### tests\backend\test_error_handling.py:TestDataValidationErrors.test_string_length_validation

Calls:
- `patch` (line 241, type: direct)
- `list` (line 245, type: direct)
- `keys` (line 245, type: attribute)
- `post` (line 251, type: attribute)

### tests\backend\test_error_handling.py:TestDatabaseErrorHandling.test_constraint_violations

Calls:
- `patch` (line 291, type: direct)
- `patch` (line 303, type: direct)
- `IntegrityError` (line 304, type: attribute)
- `post` (line 306, type: attribute)
- `json` (line 309, type: attribute)

### tests\backend\test_error_handling.py:TestDatabaseErrorHandling.test_database_connection_failure

Calls:
- `patch` (line 262, type: direct)
- `OperationalError` (line 263, type: attribute)
- `get` (line 265, type: attribute)
- `json` (line 268, type: attribute)
- `lower` (line 270, type: attribute)

### tests\backend\test_error_handling.py:TestDatabaseErrorHandling.test_database_corruption

Calls:
- `open` (line 276, type: direct)
- `write` (line 277, type: attribute)
- `patch` (line 279, type: direct)
- `DatabaseError` (line 280, type: attribute)
- `get` (line 282, type: attribute)
- `json` (line 285, type: attribute)
- `lower` (line 287, type: attribute)

### tests\backend\test_error_handling.py:TestDatabaseErrorHandling.test_transaction_rollback_on_error

Calls:
- `patch` (line 315, type: direct)
- `patch` (line 327, type: direct)
- `patch` (line 328, type: direct)
- `Error` (line 331, type: attribute)
- `post` (line 333, type: attribute)
- `cursor` (line 338, type: attribute)
- `execute` (line 339, type: attribute)
- `fetchone` (line 340, type: attribute)

### tests\backend\test_error_handling.py:TestEdgeCaseScenarios.slow_download

Calls:
- `sleep` (line 768, type: attribute)

### tests\backend\test_error_handling.py:TestEdgeCaseScenarios.test_circular_references_in_data

Calls:
- `CircularReference` (line 791, type: direct)
- `patch` (line 794, type: direct)
- `ValueError` (line 795, type: direct)
- `dumps` (line 799, type: attribute)
- `lower` (line 801, type: attribute)
- `str` (line 801, type: direct)
- `lower` (line 801, type: attribute)
- `str` (line 801, type: direct)

### tests\backend\test_error_handling.py:TestEdgeCaseScenarios.test_extreme_numeric_values

Calls:
- `float` (line 736, type: direct)
- `float` (line 737, type: direct)
- `float` (line 738, type: direct)
- `Decimal` (line 741, type: direct)
- `post` (line 752, type: attribute)
- `json` (line 756, type: attribute)

### tests\backend\test_error_handling.py:TestEdgeCaseScenarios.test_unicode_and_special_characters

Calls:
- `post` (line 722, type: attribute)
- `json` (line 727, type: attribute)

### tests\backend\test_error_handling.py:TestEdgeCaseScenarios.test_very_long_operations

Calls:
- `patch` (line 763, type: direct)
- `patch` (line 774, type: direct)
- `post` (line 775, type: attribute)
- `json` (line 778, type: attribute)
- `lower` (line 780, type: attribute)

### tests\backend\test_error_handling.py:TestFileSystemErrorHandling.test_file_corruption_during_download

Calls:
- `patch` (line 387, type: direct)
- `patch` (line 388, type: direct)
- `post` (line 402, type: attribute)
- `json` (line 405, type: attribute)
- `lower` (line 407, type: attribute)

### tests\backend\test_error_handling.py:TestFileSystemErrorHandling.test_insufficient_disk_space

Calls:
- `patch` (line 352, type: direct)
- `post` (line 359, type: attribute)
- `json` (line 362, type: attribute)

### tests\backend\test_error_handling.py:TestFileSystemErrorHandling.test_missing_file_errors

Calls:
- `patch` (line 414, type: direct)
- `post` (line 417, type: attribute)
- `json` (line 420, type: attribute)
- `delete` (line 425, type: attribute)
- `json` (line 428, type: attribute)

### tests\backend\test_error_handling.py:TestFileSystemErrorHandling.test_permission_denied_errors

Calls:
- `patch` (line 372, type: direct)
- `PermissionError` (line 373, type: direct)
- `post` (line 375, type: attribute)
- `json` (line 378, type: attribute)
- `lower` (line 380, type: attribute)

### tests\backend\test_error_handling.py:TestNetworkErrorHandling.test_dns_resolution_failure

Calls:
- `patch` (line 82, type: direct)
- `ConnectionError` (line 83, type: attribute)
- `post` (line 87, type: attribute)
- `json` (line 90, type: attribute)
- `lower` (line 92, type: attribute)

### tests\backend\test_error_handling.py:TestNetworkErrorHandling.test_network_interruption_during_operation

Calls:
- `patch` (line 56, type: direct)
- `patch` (line 62, type: direct)
- `ConnectionError` (line 63, type: attribute)
- `get` (line 65, type: attribute)
- `json` (line 68, type: attribute)

### tests\backend\test_error_handling.py:TestNetworkErrorHandling.test_printer_connection_timeout

Calls:
- `patch` (line 43, type: direct)
- `ConnectTimeout` (line 44, type: attribute)
- `post` (line 46, type: attribute)
- `json` (line 49, type: attribute)
- `lower` (line 51, type: attribute)

### tests\backend\test_error_handling.py:TestNetworkErrorHandling.test_ssl_certificate_errors

Calls:
- `patch` (line 104, type: direct)
- `SSLError` (line 105, type: attribute)
- `post` (line 109, type: attribute)
- `json` (line 112, type: attribute)
- `lower` (line 114, type: attribute)

### tests\backend\test_error_handling.py:TestResourceExhaustionHandling.test_disk_space_exhaustion

Calls:
- `patch` (line 686, type: direct)
- `OSError` (line 687, type: direct)
- `post` (line 689, type: attribute)
- `json` (line 692, type: attribute)
- `lower` (line 694, type: attribute)

### tests\backend\test_error_handling.py:TestResourceExhaustionHandling.test_memory_exhaustion_handling

Calls:
- `patch` (line 648, type: direct)
- `MemoryError` (line 649, type: direct)
- `post` (line 651, type: attribute)
- `json` (line 654, type: attribute)
- `lower` (line 656, type: attribute)

### tests\backend\test_error_handling.py:TestResourceExhaustionHandling.test_too_many_concurrent_requests

Calls:
- `patch` (line 664, type: direct)
- `get` (line 673, type: attribute)
- `json` (line 678, type: attribute)

### tests\backend\test_error_handling.py:TestSecurityErrorHandling.test_path_traversal_attempts

Calls:
- `patch` (line 586, type: direct)
- `post` (line 593, type: attribute)
- `json` (line 596, type: attribute)
- `lower` (line 598, type: attribute)

### tests\backend\test_error_handling.py:TestSecurityErrorHandling.test_sql_injection_attempts

Calls:
- `patch` (line 552, type: direct)
- `post` (line 559, type: attribute)
- `json` (line 562, type: attribute)

### tests\backend\test_error_handling.py:TestSecurityErrorHandling.test_xss_prevention

Calls:
- `patch` (line 620, type: direct)
- `post` (line 627, type: attribute)
- `json` (line 631, type: attribute)
- `json` (line 635, type: attribute)

### tests\backend\test_german_business.py:TestGermanAccountingStandards.test_gob_electronic_records

Calls:
- `patch` (line 385, type: direct)
- `datetime` (line 388, type: direct)
- `timezone` (line 388, type: attribute)
- `Decimal` (line 390, type: direct)
- `datetime` (line 399, type: direct)
- `datetime` (line 402, type: direct)
- `mock_gobd` (line 408, type: direct)

### tests\backend\test_german_business.py:TestGermanAccountingStandards.test_hgb_compliance

Calls:
- `patch` (line 352, type: direct)
- `datetime` (line 355, type: direct)
- `mock_validate` (line 377, type: direct)
- `len` (line 379, type: direct)

### tests\backend\test_german_business.py:TestGermanAccountingStandards.test_invoice_numbering_sequence

Calls:
- `patch` (line 416, type: direct)
- `patch` (line 417, type: direct)
- `enumerate` (line 421, type: direct)
- `mock_generate` (line 423, type: direct)
- `mock_validate` (line 435, type: direct)
- `len` (line 437, type: direct)

### tests\backend\test_german_business.py:TestGermanBusinessWorkflows.test_b2b_invoice_workflow

Calls:
- `patch` (line 568, type: direct)
- `Decimal` (line 584, type: direct)
- `Decimal` (line 585, type: direct)
- `Decimal` (line 590, type: direct)
- `Decimal` (line 591, type: direct)
- `strftime` (line 599, type: attribute)
- `datetime` (line 599, type: direct)
- `strftime` (line 600, type: attribute)
- `datetime` (line 600, type: direct)
- `Decimal` (line 606, type: direct)
- `Decimal` (line 607, type: direct)
- `Decimal` (line 608, type: direct)
- `Decimal` (line 613, type: direct)
- `Decimal` (line 614, type: direct)
- `Decimal` (line 615, type: direct)
- `Decimal` (line 618, type: direct)
- `Decimal` (line 619, type: direct)
- `Decimal` (line 620, type: direct)
- `mock_b2b` (line 625, type: direct)
- `startswith` (line 627, type: attribute)
- `Decimal` (line 628, type: direct)
- `Decimal` (line 629, type: direct)
- `Decimal` (line 630, type: direct)

### tests\backend\test_german_business.py:TestGermanBusinessWorkflows.test_kleinunternehmer_exemption

Calls:
- `patch` (line 640, type: direct)
- `Decimal` (line 643, type: direct)
- `Decimal` (line 644, type: direct)
- `date` (line 653, type: attribute)
- `datetime` (line 653, type: direct)
- `mock_exempt` (line 656, type: direct)

### tests\backend\test_german_business.py:TestGermanCurrencyHandling.test_currency_conversion_edge_cases

Calls:
- `patch` (line 70, type: direct)
- `Decimal` (line 72, type: direct)
- `mock_handle` (line 73, type: direct)
- `Decimal` (line 73, type: direct)
- `Decimal` (line 74, type: direct)
- `Decimal` (line 77, type: direct)
- `mock_handle` (line 78, type: direct)
- `Decimal` (line 78, type: direct)
- `Decimal` (line 79, type: direct)
- `Decimal` (line 82, type: direct)
- `mock_handle` (line 83, type: direct)
- `Decimal` (line 83, type: direct)
- `Decimal` (line 84, type: direct)

### tests\backend\test_german_business.py:TestGermanCurrencyHandling.test_currency_precision

Calls:
- `patch` (line 50, type: direct)
- `Decimal` (line 53, type: direct)
- `Decimal` (line 54, type: direct)
- `Decimal` (line 55, type: direct)
- `Decimal` (line 56, type: direct)
- `Decimal` (line 57, type: direct)
- `Decimal` (line 58, type: direct)
- `mock_round` (line 63, type: direct)
- `Decimal` (line 63, type: direct)
- `str` (line 63, type: direct)

### tests\backend\test_german_business.py:TestGermanCurrencyHandling.test_eur_currency_formatting

Calls:
- `patch` (line 40, type: direct)
- `mock_format` (line 43, type: direct)

### tests\backend\test_german_business.py:TestGermanDateTimeFormatting.test_german_date_formatting

Calls:
- `patch` (line 297, type: direct)
- `datetime` (line 299, type: direct)
- `datetime` (line 300, type: direct)
- `datetime` (line 301, type: direct)
- `datetime` (line 302, type: direct)
- `mock_format` (line 307, type: direct)

### tests\backend\test_german_business.py:TestGermanDateTimeFormatting.test_german_datetime_formatting

Calls:
- `patch` (line 331, type: direct)
- `datetime` (line 332, type: direct)
- `items` (line 339, type: attribute)
- `mock_format` (line 341, type: direct)

### tests\backend\test_german_business.py:TestGermanDateTimeFormatting.test_german_time_formatting

Calls:
- `patch` (line 314, type: direct)
- `datetime` (line 316, type: direct)
- `datetime` (line 317, type: direct)
- `datetime` (line 318, type: direct)
- `datetime` (line 319, type: direct)
- `mock_format` (line 324, type: direct)

### tests\backend\test_german_business.py:TestGermanTaxReporting.test_annual_tax_declaration

Calls:
- `patch` (line 485, type: direct)
- `Decimal` (line 489, type: direct)
- `Decimal` (line 490, type: direct)
- `Decimal` (line 491, type: direct)
- `Decimal` (line 492, type: direct)
- `Decimal` (line 493, type: direct)
- `Decimal` (line 494, type: direct)
- `Decimal` (line 499, type: direct)
- `Decimal` (line 500, type: direct)
- `Decimal` (line 501, type: direct)
- `Decimal` (line 502, type: direct)
- `Decimal` (line 503, type: direct)
- `Decimal` (line 504, type: direct)
- `Decimal` (line 505, type: direct)
- `mock_annual` (line 508, type: direct)
- `Decimal` (line 510, type: direct)

### tests\backend\test_german_business.py:TestGermanTaxReporting.test_elster_xml_export

Calls:
- `patch` (line 516, type: direct)
- `mock_elster` (line 555, type: direct)

### tests\backend\test_german_business.py:TestGermanTaxReporting.test_ustva_vat_return_format

Calls:
- `patch` (line 447, type: direct)
- `Decimal` (line 462, type: direct)
- `Decimal` (line 463, type: direct)
- `Decimal` (line 464, type: direct)
- `Decimal` (line 465, type: direct)
- `Decimal` (line 466, type: direct)
- `mock_ustva` (line 476, type: direct)
- `Decimal` (line 479, type: direct)

### tests\backend\test_german_business.py:TestGermanTimezoneHandling.test_berlin_timezone_conversion

Calls:
- `patch` (line 204, type: direct)
- `patch` (line 205, type: direct)
- `datetime` (line 207, type: direct)
- `datetime` (line 208, type: direct)
- `timezone` (line 208, type: attribute)
- `mock_to_berlin` (line 211, type: direct)
- `mock_from_berlin` (line 218, type: direct)

### tests\backend\test_german_business.py:TestGermanTimezoneHandling.test_business_hours_calculation

Calls:
- `timezone` (line 260, type: attribute)
- `patch` (line 262, type: direct)
- `patch` (line 263, type: direct)
- `localize` (line 265, type: attribute)
- `datetime` (line 265, type: direct)
- `mock_hours` (line 267, type: direct)
- `localize` (line 270, type: attribute)
- `datetime` (line 270, type: direct)
- `mock_hours` (line 272, type: direct)
- `localize` (line 275, type: attribute)
- `datetime` (line 275, type: direct)
- `localize` (line 276, type: attribute)
- `datetime` (line 276, type: direct)
- `mock_duration` (line 285, type: direct)

### tests\backend\test_german_business.py:TestGermanTimezoneHandling.test_daylight_saving_time_transitions

Calls:
- `patch` (line 227, type: direct)
- `datetime` (line 229, type: direct)
- `datetime` (line 232, type: direct)
- `datetime` (line 233, type: direct)
- `mock_dst` (line 238, type: direct)
- `datetime` (line 243, type: direct)
- `datetime` (line 246, type: direct)
- `datetime` (line 247, type: direct)
- `mock_dst` (line 252, type: direct)

### tests\backend\test_german_business.py:TestGermanVATCalculations.test_complex_invoice_vat_calculation

Calls:
- `Decimal` (line 170, type: direct)
- `Decimal` (line 171, type: direct)
- `Decimal` (line 172, type: direct)
- `Decimal` (line 173, type: direct)
- `patch` (line 176, type: direct)
- `Decimal` (line 179, type: direct)
- `Decimal` (line 180, type: direct)
- `Decimal` (line 181, type: direct)
- `Decimal` (line 184, type: direct)
- `Decimal` (line 185, type: direct)
- `mock_invoice` (line 190, type: direct)
- `Decimal` (line 190, type: direct)
- `Decimal` (line 192, type: direct)
- `Decimal` (line 193, type: direct)
- `Decimal` (line 194, type: direct)

### tests\backend\test_german_business.py:TestGermanVATCalculations.test_reverse_vat_calculation

Calls:
- `patch` (line 124, type: direct)
- `Decimal` (line 127, type: direct)
- `Decimal` (line 127, type: direct)
- `Decimal` (line 127, type: direct)
- `Decimal` (line 128, type: direct)
- `Decimal` (line 128, type: direct)
- `Decimal` (line 128, type: direct)
- `Decimal` (line 129, type: direct)
- `Decimal` (line 129, type: direct)
- `Decimal` (line 129, type: direct)
- `Decimal` (line 130, type: direct)
- `Decimal` (line 130, type: direct)
- `Decimal` (line 130, type: direct)
- `Decimal` (line 138, type: direct)
- `mock_reverse` (line 141, type: direct)
- `Decimal` (line 141, type: direct)

### tests\backend\test_german_business.py:TestGermanVATCalculations.test_standard_vat_rate_19_percent

Calls:
- `patch` (line 94, type: direct)
- `Decimal` (line 97, type: direct)
- `Decimal` (line 97, type: direct)
- `Decimal` (line 97, type: direct)
- `Decimal` (line 98, type: direct)
- `Decimal` (line 98, type: direct)
- `Decimal` (line 98, type: direct)
- `Decimal` (line 99, type: direct)
- `Decimal` (line 99, type: direct)
- `Decimal` (line 99, type: direct)
- `Decimal` (line 100, type: direct)
- `Decimal` (line 100, type: direct)
- `Decimal` (line 100, type: direct)
- `Decimal` (line 101, type: direct)
- `Decimal` (line 101, type: direct)
- `Decimal` (line 101, type: direct)
- `Decimal` (line 102, type: direct)
- `Decimal` (line 102, type: direct)
- `Decimal` (line 102, type: direct)
- `Decimal` (line 108, type: direct)
- `mock_vat` (line 113, type: direct)
- `Decimal` (line 113, type: direct)
- `Decimal` (line 118, type: direct)

### tests\backend\test_german_business.py:TestGermanVATCalculations.test_vat_exemption_cases

Calls:
- `patch` (line 150, type: direct)
- `Decimal` (line 152, type: direct)
- `Decimal` (line 153, type: direct)
- `Decimal` (line 154, type: direct)
- `Decimal` (line 155, type: direct)
- `mock_exempt` (line 159, type: direct)
- `Decimal` (line 159, type: direct)
- `Decimal` (line 161, type: direct)

### tests\backend\test_integration.py:TestAPIIntegration.test_complete_job_workflow

Calls:
- `patch` (line 86, type: direct)
- `post` (line 105, type: attribute)
- `json` (line 107, type: attribute)
- `put` (line 118, type: attribute)
- `patch` (line 122, type: direct)
- `get` (line 130, type: attribute)
- `json` (line 132, type: attribute)
- `put` (line 146, type: attribute)
- `get` (line 150, type: attribute)
- `json` (line 152, type: attribute)
- `round` (line 167, type: direct)
- `float` (line 167, type: direct)
- `abs` (line 168, type: direct)
- `float` (line 168, type: direct)

### tests\backend\test_integration.py:TestAPIIntegration.test_complete_printer_lifecycle

Calls:
- `patch` (line 23, type: direct)
- `connect` (line 24, type: attribute)
- `patch` (line 42, type: direct)
- `post` (line 44, type: attribute)
- `json` (line 46, type: attribute)
- `patch` (line 49, type: direct)
- `get` (line 59, type: attribute)
- `json` (line 61, type: attribute)
- `put` (line 67, type: attribute)
- `get` (line 71, type: attribute)
- `json` (line 73, type: attribute)
- `delete` (line 77, type: attribute)
- `get` (line 81, type: attribute)

### tests\backend\test_integration.py:TestAPIIntegration.test_dashboard_real_time_updates

Calls:
- `patch` (line 233, type: direct)
- `get` (line 239, type: attribute)
- `json` (line 241, type: attribute)

### tests\backend\test_integration.py:TestAPIIntegration.test_file_management_workflow

Calls:
- `patch` (line 172, type: direct)
- `patch` (line 178, type: direct)
- `get` (line 190, type: attribute)
- `json` (line 192, type: attribute)
- `len` (line 195, type: direct)
- `next` (line 198, type: direct)
- `patch` (line 203, type: direct)
- `post` (line 210, type: attribute)
- `json` (line 212, type: attribute)
- `get` (line 219, type: attribute)
- `json` (line 221, type: attribute)
- `next` (line 223, type: direct)
- `delete` (line 228, type: attribute)

### tests\backend\test_integration.py:TestErrorHandlingIntegration.mock_connect

Calls:
- `append` (line 511, type: attribute)

### tests\backend\test_integration.py:TestErrorHandlingIntegration.mock_disconnect

Calls:
- `append` (line 515, type: attribute)

### tests\backend\test_integration.py:TestErrorHandlingIntegration.test_database_transaction_rollback

Calls:
- `patch` (line 483, type: direct)
- `connect` (line 484, type: attribute)
- `post` (line 495, type: attribute)
- `cursor` (line 499, type: attribute)
- `execute` (line 500, type: attribute)
- `fetchone` (line 501, type: attribute)

### tests\backend\test_integration.py:TestErrorHandlingIntegration.test_file_download_interruption_recovery

Calls:
- `patch` (line 532, type: direct)
- `ConnectionError` (line 534, type: direct)
- `post` (line 536, type: attribute)
- `post` (line 548, type: attribute)
- `json` (line 550, type: attribute)

### tests\backend\test_integration.py:TestErrorHandlingIntegration.test_printer_connection_failure_recovery

Calls:
- `patch` (line 473, type: direct)
- `ConnectionError` (line 474, type: direct)
- `post` (line 476, type: attribute)
- `json` (line 478, type: attribute)

### tests\backend\test_integration.py:TestErrorHandlingIntegration.test_websocket_reconnection

Calls:
- `patch` (line 517, type: direct)
- `patch` (line 518, type: direct)

### tests\backend\test_integration.py:TestGermanBusinessLogic.test_berlin_timezone_handling

Calls:
- `patch` (line 397, type: direct)
- `timezone` (line 398, type: attribute)
- `localize` (line 399, type: attribute)
- `datetime` (line 399, type: direct)
- `mock_timestamp` (line 402, type: direct)

### tests\backend\test_integration.py:TestGermanBusinessLogic.test_business_hours_validation

Calls:
- `patch` (line 419, type: direct)
- `timezone` (line 421, type: attribute)
- `localize` (line 422, type: attribute)
- `datetime` (line 422, type: direct)
- `mock_hours` (line 425, type: direct)
- `localize` (line 429, type: attribute)
- `datetime` (line 429, type: direct)
- `mock_hours` (line 432, type: direct)

### tests\backend\test_integration.py:TestGermanBusinessLogic.test_currency_formatting

Calls:
- `format_currency` (line 411, type: attribute)
- `format_currency` (line 412, type: attribute)
- `format_currency` (line 413, type: attribute)

### tests\backend\test_integration.py:TestGermanBusinessLogic.test_export_data_format

Calls:
- `patch` (line 437, type: direct)
- `get` (line 443, type: attribute)

### tests\backend\test_integration.py:TestGermanBusinessLogic.test_vat_calculations

Calls:
- `patch` (line 365, type: direct)
- `Decimal` (line 367, type: direct)
- `Decimal` (line 368, type: direct)
- `Decimal` (line 369, type: direct)
- `Decimal` (line 370, type: direct)
- `Decimal` (line 371, type: direct)
- `Decimal` (line 372, type: direct)
- `Decimal` (line 373, type: direct)
- `mock_calc` (line 382, type: direct)
- `Decimal` (line 385, type: direct)
- `abs` (line 386, type: direct)
- `Decimal` (line 386, type: direct)
- `abs` (line 390, type: direct)
- `Decimal` (line 390, type: direct)

### tests\backend\test_integration.py:TestWebSocketIntegration.mock_send

Calls:
- `append` (line 275, type: attribute)
- `loads` (line 275, type: attribute)
- `append` (line 306, type: attribute)
- `loads` (line 306, type: attribute)
- `append` (line 337, type: attribute)
- `loads` (line 337, type: attribute)

### tests\backend\test_integration.py:TestWebSocketIntegration.test_file_download_progress

Calls:
- `patch` (line 342, type: direct)
- `mock_broadcast` (line 353, type: direct)
- `assert_called_once_with` (line 354, type: attribute)

### tests\backend\test_integration.py:TestWebSocketIntegration.test_printer_status_broadcast

Calls:
- `patch` (line 311, type: direct)
- `mock_broadcast` (line 327, type: direct)
- `assert_called_once_with` (line 328, type: attribute)

### tests\backend\test_integration.py:TestWebSocketIntegration.test_real_time_job_updates

Calls:
- `patch` (line 280, type: direct)
- `mock_broadcast` (line 296, type: direct)
- `assert_called_once_with` (line 297, type: attribute)

### tests\backend\test_job_null_fix.py:TestNullJobIDFix.test_database_prevents_null_job_ids

Calls:
- `mkstemp` (line 50, type: attribute)
- `close` (line 51, type: attribute)
- `Database` (line 53, type: direct)
- `initialize` (line 54, type: attribute)
- `raises` (line 58, type: attribute)
- `connection` (line 59, type: attribute)
- `execute` (line 60, type: attribute)
- `commit` (line 64, type: attribute)
- `raises` (line 67, type: attribute)
- `connection` (line 68, type: attribute)
- `execute` (line 69, type: attribute)
- `commit` (line 73, type: attribute)
- `close` (line 76, type: attribute)
- `unlink` (line 78, type: attribute)

### tests\backend\test_job_null_fix.py:TestNullJobIDFix.test_job_model_rejects_null_id

Calls:
- `Job` (line 24, type: direct)
- `str` (line 25, type: direct)
- `uuid4` (line 25, type: attribute)
- `raises` (line 34, type: attribute)
- `Job` (line 35, type: direct)
- `errors` (line 43, type: attribute)
- `any` (line 44, type: direct)

### tests\backend\test_job_null_fix.py:TestNullJobIDFix.test_job_service_creates_valid_ids

Calls:
- `mkstemp` (line 86, type: attribute)
- `close` (line 87, type: attribute)
- `Database` (line 89, type: direct)
- `initialize` (line 90, type: attribute)
- `EventService` (line 93, type: direct)
- `JobService` (line 94, type: direct)
- `range` (line 98, type: direct)
- `create_job` (line 99, type: attribute)
- `append` (line 104, type: attribute)
- `len` (line 109, type: direct)
- `UUID` (line 110, type: attribute)
- `len` (line 113, type: direct)
- `len` (line 113, type: direct)
- `set` (line 113, type: direct)
- `get_job` (line 117, type: attribute)
- `close` (line 122, type: attribute)
- `unlink` (line 124, type: attribute)

### tests\backend\test_job_null_fix.py:TestNullJobIDFix.test_job_service_error_logging

Calls:
- `mkstemp` (line 166, type: attribute)
- `close` (line 167, type: attribute)
- `Database` (line 169, type: direct)
- `initialize` (line 170, type: attribute)
- `EventService` (line 173, type: direct)
- `JobService` (line 174, type: direct)
- `create_job` (line 177, type: attribute)
- `get_jobs` (line 184, type: attribute)
- `len` (line 185, type: direct)
- `list_jobs` (line 189, type: attribute)
- `len` (line 190, type: direct)
- `close` (line 193, type: attribute)
- `unlink` (line 195, type: attribute)

### tests\backend\test_job_null_fix.py:TestNullJobIDFix.test_migration_005_applied

Calls:
- `mkstemp` (line 132, type: attribute)
- `close` (line 133, type: attribute)
- `Database` (line 135, type: direct)
- `initialize` (line 136, type: attribute)
- `connection` (line 140, type: attribute)
- `execute` (line 141, type: attribute)
- `fetchone` (line 144, type: attribute)
- `execute` (line 148, type: attribute)
- `fetchone` (line 151, type: attribute)
- `close` (line 156, type: attribute)
- `unlink` (line 158, type: attribute)

### tests\backend\test_job_validation.py:TestJobCreationValidation.test_create_job_generates_unique_ids

Calls:
- `range` (line 227, type: direct)
- `create_job` (line 228, type: attribute)
- `append` (line 233, type: attribute)
- `len` (line 236, type: direct)
- `len` (line 236, type: direct)
- `set` (line 236, type: direct)
- `UUID` (line 240, type: attribute)

### tests\backend\test_job_validation.py:TestJobCreationValidation.test_create_job_validates_required_fields

Calls:
- `raises` (line 211, type: attribute)
- `create_job` (line 212, type: attribute)
- `raises` (line 217, type: attribute)
- `create_job` (line 218, type: attribute)

### tests\backend\test_job_validation.py:TestJobCreationValidation.test_create_job_with_business_info

Calls:
- `create_job` (line 245, type: attribute)
- `get_job` (line 257, type: attribute)

### tests\backend\test_job_validation.py:TestJobIDValidation.test_database_schema_prevents_empty_ids

Calls:
- `create_test_db` (line 52, type: direct)
- `raises` (line 55, type: attribute)
- `connection` (line 56, type: attribute)
- `execute` (line 57, type: attribute)
- `commit` (line 61, type: attribute)
- `close` (line 63, type: attribute)
- `unlink` (line 64, type: attribute)

### tests\backend\test_job_validation.py:TestJobIDValidation.test_database_schema_prevents_null_ids

Calls:
- `create_test_db` (line 35, type: direct)
- `raises` (line 38, type: attribute)
- `connection` (line 39, type: attribute)
- `execute` (line 40, type: attribute)
- `commit` (line 44, type: attribute)
- `close` (line 46, type: attribute)
- `unlink` (line 47, type: attribute)

### tests\backend\test_job_validation.py:TestJobIDValidation.test_get_jobs_skips_invalid_jobs

Calls:
- `create_job` (line 128, type: attribute)
- `get_jobs` (line 135, type: attribute)
- `len` (line 136, type: direct)

### tests\backend\test_job_validation.py:TestJobIDValidation.test_job_model_validates_id_field

Calls:
- `Job` (line 101, type: direct)
- `str` (line 102, type: direct)
- `uuid4` (line 102, type: attribute)
- `raises` (line 112, type: attribute)
- `Job` (line 113, type: direct)
- `errors` (line 121, type: attribute)
- `any` (line 122, type: direct)

### tests\backend\test_job_validation.py:TestJobIDValidation.test_job_service_creates_valid_id

Calls:
- `create_test_db` (line 69, type: direct)
- `EventService` (line 71, type: direct)
- `JobService` (line 72, type: direct)
- `create_job` (line 82, type: attribute)
- `len` (line 87, type: direct)
- `get_job` (line 90, type: attribute)
- `close` (line 94, type: attribute)
- `unlink` (line 95, type: attribute)

### tests\backend\test_job_validation.py:TestJobIDValidation.test_list_jobs_skips_invalid_jobs

Calls:
- `create_job` (line 143, type: attribute)
- `create_job` (line 149, type: attribute)
- `list_jobs` (line 156, type: attribute)
- `len` (line 157, type: direct)
- `list_jobs` (line 160, type: attribute)
- `len` (line 161, type: direct)

### tests\backend\test_job_validation.py:TestMigration005.test_jobs_table_has_not_null_constraint

Calls:
- `connection` (line 193, type: attribute)
- `execute` (line 194, type: attribute)
- `fetchall` (line 195, type: attribute)
- `next` (line 198, type: direct)

### tests\backend\test_job_validation.py:TestMigration005.test_migration_005_recorded

Calls:
- `connection` (line 181, type: attribute)
- `execute` (line 182, type: attribute)
- `fetchone` (line 185, type: attribute)
- `lower` (line 188, type: attribute)

### tests\backend\test_job_validation.py:TestMigration005.test_migration_tracking_table_created

Calls:
- `connection` (line 171, type: attribute)
- `execute` (line 172, type: attribute)
- `fetchone` (line 175, type: attribute)

### tests\backend\test_job_validation.py:create_test_db

Calls:
- `mkstemp` (line 21, type: attribute)
- `close` (line 22, type: attribute)
- `Database` (line 24, type: direct)
- `initialize` (line 25, type: attribute)

### tests\backend\test_library_service.py:TestChecksumCalculation.test_calculate_checksum_consistent

Calls:
- `calculate_checksum` (line 123, type: attribute)
- `calculate_checksum` (line 124, type: attribute)

### tests\backend\test_library_service.py:TestChecksumCalculation.test_calculate_checksum_different_files

Calls:
- `write_bytes` (line 132, type: attribute)
- `write_bytes` (line 133, type: attribute)
- `calculate_checksum` (line 135, type: attribute)
- `calculate_checksum` (line 136, type: attribute)

### tests\backend\test_library_service.py:TestChecksumCalculation.test_calculate_checksum_sha256

Calls:
- `calculate_checksum` (line 116, type: attribute)
- `len` (line 118, type: direct)

### tests\backend\test_library_service.py:TestErrorHandling.test_add_file_invalid_source_type

Calls:
- `raises` (line 487, type: attribute)
- `add_file_to_library` (line 488, type: attribute)

### tests\backend\test_library_service.py:TestErrorHandling.test_add_file_missing_source

Calls:
- `raises` (line 478, type: attribute)
- `Path` (line 479, type: direct)
- `add_file_to_library` (line 480, type: attribute)

### tests\backend\test_library_service.py:TestErrorHandling.test_database_error_cleanup

Calls:
- `Exception` (line 495, type: direct)
- `raises` (line 499, type: attribute)
- `add_file_to_library` (line 500, type: attribute)

### tests\backend\test_library_service.py:TestFileAddition.test_add_duplicate_file_adds_source

Calls:
- `add_file_to_library` (line 236, type: attribute)
- `assert_not_called` (line 241, type: attribute)
- `assert_called` (line 242, type: attribute)

### tests\backend\test_library_service.py:TestFileAddition.test_add_new_file_to_library

Calls:
- `add_file_to_library` (line 211, type: attribute)
- `assert_called_once` (line 218, type: attribute)

### tests\backend\test_library_service.py:TestFileAddition.test_checksum_verification_after_copy

Calls:
- `add_file_to_library` (line 280, type: attribute)

### tests\backend\test_library_service.py:TestFileAddition.test_disk_space_check

Calls:
- `write_bytes` (line 249, type: attribute)
- `patch` (line 251, type: direct)
- `Mock` (line 252, type: direct)
- `raises` (line 256, type: attribute)
- `add_file_to_library` (line 257, type: attribute)

### tests\backend\test_library_service.py:TestFileAddition.test_file_copy_preserves_original

Calls:
- `add_file_to_library` (line 266, type: attribute)
- `exists` (line 271, type: attribute)
- `read_bytes` (line 272, type: attribute)

### tests\backend\test_library_service.py:TestFileDeletion.test_delete_file_database_only

Calls:
- `mkdir` (line 374, type: attribute)
- `write_bytes` (line 375, type: attribute)
- `delete_file` (line 385, type: attribute)
- `exists` (line 388, type: attribute)
- `assert_called_once` (line 389, type: attribute)

### tests\backend\test_library_service.py:TestFileDeletion.test_delete_file_with_physical

Calls:
- `mkdir` (line 353, type: attribute)
- `write_bytes` (line 354, type: attribute)
- `delete_file` (line 364, type: attribute)
- `exists` (line 367, type: attribute)
- `assert_called_once` (line 368, type: attribute)

### tests\backend\test_library_service.py:TestIntegration.test_full_file_lifecycle

Calls:
- `add_file_to_library` (line 537, type: attribute)
- `get_file_by_checksum` (line 549, type: attribute)
- `reprocess_file` (line 553, type: attribute)
- `delete_file` (line 557, type: attribute)

### tests\backend\test_library_service.py:TestLibraryPathGeneration.test_path_sharding_distribution

Calls:
- `get_library_path_for_file` (line 190, type: attribute)
- `len` (line 196, type: direct)
- `set` (line 196, type: direct)
- `len` (line 196, type: direct)

### tests\backend\test_library_service.py:TestLibraryPathGeneration.test_printer_path_generation

Calls:
- `get_library_path_for_file` (line 158, type: attribute)
- `str` (line 162, type: direct)
- `str` (line 163, type: direct)
- `str` (line 164, type: direct)
- `str` (line 165, type: direct)
- `str` (line 166, type: direct)

### tests\backend\test_library_service.py:TestLibraryPathGeneration.test_upload_path_generation

Calls:
- `get_library_path_for_file` (line 171, type: attribute)
- `str` (line 175, type: direct)
- `str` (line 176, type: direct)
- `str` (line 177, type: direct)

### tests\backend\test_library_service.py:TestLibraryPathGeneration.test_watch_folder_path_generation

Calls:
- `get_library_path_for_file` (line 146, type: attribute)
- `str` (line 150, type: direct)
- `str` (line 151, type: direct)
- `str` (line 152, type: direct)

### tests\backend\test_library_service.py:TestLibraryServiceInitialization.test_disabled_library_skips_initialization

Calls:
- `LibraryService` (line 105, type: direct)
- `initialize` (line 106, type: attribute)

### tests\backend\test_library_service.py:TestLibraryServiceInitialization.test_initialize_creates_folders

Calls:
- `exists` (line 88, type: attribute)
- `exists` (line 89, type: attribute)
- `exists` (line 90, type: attribute)
- `exists` (line 91, type: attribute)
- `exists` (line 92, type: attribute)

### tests\backend\test_library_service.py:TestListFiles.test_list_files_with_filters

Calls:
- `list_files` (line 420, type: attribute)

### tests\backend\test_library_service.py:TestListFiles.test_list_files_with_pagination

Calls:
- `range` (line 400, type: direct)
- `list_files` (line 405, type: attribute)
- `len` (line 407, type: direct)
- `assert_called_once` (line 409, type: attribute)

### tests\backend\test_library_service.py:TestReprocessing.test_reprocess_file

Calls:
- `reprocess_file` (line 439, type: attribute)

### tests\backend\test_library_service.py:TestReprocessing.test_reprocess_nonexistent_file

Calls:
- `reprocess_file` (line 448, type: attribute)

### tests\backend\test_library_service.py:TestSourceTracking.test_add_multiple_sources

Calls:
- `isoformat` (line 298, type: attribute)
- `now` (line 298, type: attribute)
- `isoformat` (line 304, type: attribute)
- `now` (line 304, type: attribute)
- `dumps` (line 310, type: attribute)
- `add_file_source` (line 314, type: attribute)
- `assert_called` (line 317, type: attribute)
- `loads` (line 320, type: attribute)
- `len` (line 321, type: direct)

### tests\backend\test_library_service.py:TestSourceTracking.test_duplicate_source_not_added

Calls:
- `dumps` (line 335, type: attribute)
- `add_file_source` (line 339, type: attribute)
- `assert_not_called` (line 342, type: attribute)

### tests\backend\test_library_service.py:TestStatistics.test_get_statistics

Calls:
- `get_library_statistics` (line 466, type: attribute)
- `assert_called_once` (line 469, type: attribute)

### tests\backend\test_library_service.py:library_service

Calls:
- `LibraryService` (line 69, type: direct)
- `initialize` (line 70, type: attribute)

### tests\backend\test_library_service.py:mock_config_service

Calls:
- `Mock` (line 46, type: direct)
- `Mock` (line 47, type: direct)
- `str` (line 48, type: direct)

### tests\backend\test_library_service.py:mock_database

Calls:
- `Mock` (line 31, type: direct)
- `AsyncMock` (line 32, type: direct)
- `AsyncMock` (line 33, type: direct)
- `AsyncMock` (line 34, type: direct)
- `AsyncMock` (line 35, type: direct)
- `AsyncMock` (line 36, type: direct)
- `AsyncMock` (line 37, type: direct)
- `AsyncMock` (line 38, type: direct)
- `AsyncMock` (line 39, type: direct)

### tests\backend\test_library_service.py:mock_event_service

Calls:
- `Mock` (line 60, type: direct)
- `AsyncMock` (line 61, type: direct)

### tests\backend\test_library_service.py:sample_test_file

Calls:
- `write_bytes` (line 78, type: attribute)

### tests\backend\test_library_service.py:temp_library_path

Calls:
- `mkdtemp` (line 23, type: attribute)
- `Path` (line 24, type: direct)
- `rmtree` (line 25, type: attribute)

### tests\backend\test_performance.py:DatabaseConnectionPool.__init__

Calls:
- `range` (line 674, type: direct)
- `connect` (line 675, type: attribute)
- `append` (line 677, type: attribute)

### tests\backend\test_performance.py:DatabaseConnectionPool.close_all

Calls:
- `close` (line 694, type: attribute)

### tests\backend\test_performance.py:DatabaseConnectionPool.get_connection

Calls:
- `pop` (line 681, type: attribute)
- `append` (line 682, type: attribute)
- `Exception` (line 685, type: direct)

### tests\backend\test_performance.py:DatabaseConnectionPool.return_connection

Calls:
- `remove` (line 689, type: attribute)
- `append` (line 690, type: attribute)

### tests\backend\test_performance.py:PerformanceTestBase.bounded_request

Calls:
- `async_func` (line 87, type: direct)

### tests\backend\test_performance.py:PerformanceTestBase.load_test

Calls:
- `Semaphore` (line 83, type: attribute)
- `perf_counter` (line 89, type: attribute)
- `bounded_request` (line 91, type: direct)
- `range` (line 91, type: direct)
- `gather` (line 92, type: attribute)
- `perf_counter` (line 94, type: attribute)
- `sum` (line 98, type: direct)
- `isinstance` (line 98, type: direct)
- `len` (line 99, type: direct)
- `len` (line 100, type: direct)
- `len` (line 101, type: direct)
- `len` (line 110, type: direct)

### tests\backend\test_performance.py:PerformanceTestBase.measure_performance

Calls:
- `Process` (line 46, type: attribute)
- `perf_counter` (line 49, type: attribute)
- `memory_info` (line 50, type: attribute)
- `cpu_percent` (line 51, type: attribute)
- `func` (line 55, type: direct)
- `str` (line 61, type: direct)
- `perf_counter` (line 64, type: attribute)
- `memory_info` (line 65, type: attribute)
- `cpu_percent` (line 66, type: attribute)

### tests\backend\test_performance.py:TestAPIPerformance.api_request

Calls:
- `patch` (line 318, type: direct)
- `get` (line 322, type: attribute)
- `hasattr` (line 326, type: direct)
- `total_seconds` (line 326, type: attribute)
- `str` (line 332, type: direct)

### tests\backend\test_performance.py:TestAPIPerformance.create_large_dataset_response

Calls:
- `float` (line 374, type: direct)
- `float` (line 381, type: direct)
- `float` (line 382, type: direct)
- `range` (line 385, type: direct)

### tests\backend\test_performance.py:TestAPIPerformance.serialize_response

Calls:
- `dumps` (line 412, type: attribute)

### tests\backend\test_performance.py:TestAPIPerformance.test_concurrent_api_requests

Calls:
- `load_test` (line 343, type: attribute)

### tests\backend\test_performance.py:TestAPIPerformance.test_large_response_performance

Calls:
- `measure_performance` (line 403, type: attribute)
- `measure_performance` (line 414, type: attribute)
- `len` (line 419, type: direct)

### tests\backend\test_performance.py:TestAPIPerformance.test_websocket_performance

Calls:
- `WebSocketLoadTester` (line 477, type: direct)
- `send_high_frequency_updates` (line 479, type: attribute)
- `get_performance_metrics` (line 480, type: attribute)
- `abs` (line 487, type: direct)

### tests\backend\test_performance.py:TestDatabasePerformance.complex_query

Calls:
- `fetchall` (line 173, type: attribute)
- `execute` (line 173, type: attribute)

### tests\backend\test_performance.py:TestDatabasePerformance.database_worker

Calls:
- `connect` (line 199, type: attribute)
- `cursor` (line 200, type: attribute)
- `range` (line 203, type: direct)
- `execute` (line 207, type: attribute)
- `fetchone` (line 208, type: attribute)
- `append` (line 209, type: attribute)
- `execute` (line 212, type: attribute)
- `float` (line 214, type: direct)
- `commit` (line 215, type: attribute)
- `append` (line 216, type: attribute)
- `execute` (line 219, type: attribute)
- `isoformat` (line 228, type: attribute)
- `now` (line 228, type: attribute)
- `commit` (line 230, type: attribute)
- `append` (line 231, type: attribute)
- `append` (line 234, type: attribute)
- `str` (line 234, type: direct)
- `close` (line 236, type: attribute)

### tests\backend\test_performance.py:TestDatabasePerformance.insert_large_dataset

Calls:
- `range` (line 129, type: direct)
- `append` (line 130, type: attribute)
- `executemany` (line 139, type: attribute)
- `range` (line 146, type: direct)
- `append` (line 148, type: attribute)
- `float` (line 153, type: direct)
- `isoformat` (line 154, type: attribute)
- `now` (line 154, type: attribute)
- `executemany` (line 158, type: attribute)
- `commit` (line 163, type: attribute)

### tests\backend\test_performance.py:TestDatabasePerformance.query_without_index

Calls:
- `fetchall` (line 284, type: attribute)
- `execute` (line 284, type: attribute)

### tests\backend\test_performance.py:TestDatabasePerformance.test_concurrent_database_access

Calls:
- `perf_counter` (line 240, type: attribute)
- `ThreadPoolExecutor` (line 242, type: attribute)
- `submit` (line 244, type: attribute)
- `range` (line 245, type: direct)
- `as_completed` (line 249, type: attribute)
- `extend` (line 250, type: attribute)
- `result` (line 250, type: attribute)
- `perf_counter` (line 252, type: attribute)
- `sum` (line 256, type: direct)
- `len` (line 257, type: direct)
- `len` (line 258, type: direct)
- `len` (line 261, type: direct)

### tests\backend\test_performance.py:TestDatabasePerformance.test_database_indexing_performance

Calls:
- `connect` (line 267, type: attribute)
- `cursor` (line 268, type: attribute)
- `float` (line 273, type: direct)
- `isoformat` (line 273, type: attribute)
- `now` (line 273, type: attribute)
- `range` (line 274, type: direct)
- `executemany` (line 276, type: attribute)
- `commit` (line 280, type: attribute)
- `measure_performance` (line 292, type: attribute)
- `execute` (line 295, type: attribute)
- `execute` (line 296, type: attribute)
- `execute` (line 297, type: attribute)
- `measure_performance` (line 300, type: attribute)
- `close` (line 306, type: attribute)

### tests\backend\test_performance.py:TestDatabasePerformance.test_large_dataset_queries

Calls:
- `connect` (line 119, type: attribute)
- `cursor` (line 121, type: attribute)
- `measure_performance` (line 166, type: attribute)
- `measure_performance` (line 188, type: attribute)
- `len` (line 191, type: direct)
- `close` (line 193, type: attribute)

### tests\backend\test_performance.py:TestFileDownloadPerformance.download_worker

Calls:
- `range` (line 549, type: direct)
- `join` (line 551, type: attribute)
- `perf_counter` (line 554, type: attribute)
- `open` (line 557, type: direct)
- `write` (line 558, type: attribute)
- `perf_counter` (line 560, type: attribute)
- `append` (line 562, type: attribute)
- `sleep` (line 570, type: attribute)

### tests\backend\test_performance.py:TestFileDownloadPerformance.simulate_large_file_download

Calls:
- `join` (line 504, type: attribute)
- `perf_counter` (line 506, type: attribute)
- `open` (line 508, type: direct)
- `range` (line 509, type: direct)
- `sleep` (line 511, type: attribute)
- `write` (line 515, type: attribute)
- `perf_counter` (line 517, type: attribute)
- `getsize` (line 520, type: attribute)

### tests\backend\test_performance.py:TestFileDownloadPerformance.test_concurrent_file_downloads

Calls:
- `perf_counter` (line 575, type: attribute)
- `ThreadPoolExecutor` (line 577, type: attribute)
- `submit` (line 579, type: attribute)
- `range` (line 580, type: direct)
- `as_completed` (line 584, type: attribute)
- `extend` (line 585, type: attribute)
- `result` (line 585, type: attribute)
- `perf_counter` (line 587, type: attribute)
- `len` (line 591, type: direct)
- `sum` (line 592, type: direct)
- `sum` (line 593, type: direct)

### tests\backend\test_performance.py:TestFileDownloadPerformance.test_large_file_download_performance

Calls:
- `simulate_large_file_download` (line 534, type: direct)
- `abs` (line 537, type: direct)

### tests\backend\test_performance.py:TestMemoryAndResourceUsage.cpu_intensive_task

Calls:
- `range` (line 765, type: direct)
- `sin` (line 767, type: attribute)
- `cos` (line 767, type: attribute)
- `sqrt` (line 767, type: attribute)
- `time` (line 771, type: attribute)
- `dumps` (line 773, type: attribute)

### tests\backend\test_performance.py:TestMemoryAndResourceUsage.database_operation_with_pool

Calls:
- `get_connection` (line 701, type: attribute)
- `cursor` (line 703, type: attribute)
- `execute` (line 706, type: attribute)
- `fetchone` (line 707, type: attribute)
- `execute` (line 709, type: attribute)
- `fetchone` (line 710, type: attribute)
- `return_connection` (line 715, type: attribute)

### tests\backend\test_performance.py:TestMemoryAndResourceUsage.simulate_heavy_workload

Calls:
- `range` (line 615, type: direct)
- `range` (line 619, type: direct)
- `range` (line 620, type: direct)
- `format` (line 621, type: attribute)
- `float` (line 621, type: direct)
- `range` (line 621, type: direct)
- `range` (line 623, type: direct)
- `append` (line 625, type: attribute)
- `items` (line 631, type: attribute)
- `len` (line 633, type: direct)
- `len` (line 634, type: direct)
- `sum` (line 635, type: direct)
- `values` (line 635, type: attribute)
- `len` (line 635, type: direct)
- `append` (line 637, type: attribute)

### tests\backend\test_performance.py:TestMemoryAndResourceUsage.test_cpu_usage_optimization

Calls:
- `Process` (line 781, type: attribute)
- `cpu_percent` (line 784, type: attribute)
- `perf_counter` (line 785, type: attribute)
- `cpu_intensive_task` (line 787, type: direct)
- `perf_counter` (line 789, type: attribute)
- `cpu_percent` (line 790, type: attribute)

### tests\backend\test_performance.py:TestMemoryAndResourceUsage.test_database_connection_pooling_performance

Calls:
- `DatabaseConnectionPool` (line 697, type: direct)
- `perf_counter` (line 718, type: attribute)
- `range` (line 722, type: direct)
- `database_operation_with_pool` (line 723, type: direct)
- `append` (line 724, type: attribute)
- `perf_counter` (line 726, type: attribute)
- `perf_counter` (line 729, type: attribute)
- `range` (line 732, type: direct)
- `connect` (line 733, type: attribute)
- `cursor` (line 734, type: attribute)
- `execute` (line 736, type: attribute)
- `fetchone` (line 737, type: attribute)
- `execute` (line 739, type: attribute)
- `fetchone` (line 740, type: attribute)
- `append` (line 742, type: attribute)
- `close` (line 743, type: attribute)
- `perf_counter` (line 745, type: attribute)
- `close_all` (line 747, type: attribute)
- `len` (line 753, type: direct)
- `len` (line 753, type: direct)

### tests\backend\test_performance.py:TestMemoryAndResourceUsage.test_memory_usage_under_load

Calls:
- `Process` (line 642, type: attribute)
- `memory_info` (line 644, type: attribute)
- `simulate_heavy_workload` (line 646, type: direct)
- `memory_info` (line 648, type: attribute)
- `collect` (line 654, type: attribute)
- `memory_info` (line 656, type: attribute)

### tests\backend\test_performance.py:WebSocketLoadTester.send_high_frequency_updates

Calls:
- `perf_counter` (line 435, type: attribute)
- `range` (line 439, type: direct)
- `float` (line 444, type: direct)
- `send` (line 450, type: attribute)
- `dumps` (line 450, type: attribute)
- `sleep` (line 454, type: attribute)
- `perf_counter` (line 456, type: attribute)

### tests\backend\test_watch_folders.py:TestFileWatcherService.file_watcher

Calls:
- `Mock` (line 62, type: direct)
- `Mock` (line 68, type: direct)
- `AsyncMock` (line 69, type: direct)
- `FileWatcherService` (line 71, type: direct)

### tests\backend\test_watch_folders.py:TestFileWatcherService.test_file_watcher_status

Calls:
- `get_watch_status` (line 94, type: attribute)

### tests\backend\test_watch_folders.py:TestFileWatcherService.test_local_file_creation

Calls:
- `LocalFile` (line 76, type: direct)

### tests\backend\test_watch_folders.py:TestFileWatcherService.test_local_files_list

Calls:
- `get_local_files` (line 131, type: attribute)
- `isinstance` (line 134, type: direct)
- `len` (line 135, type: direct)

### tests\backend\test_watch_folders.py:TestFileWatcherService.test_print_file_handler_extension_filtering

Calls:
- `Mock` (line 109, type: direct)
- `PrintFileHandler` (line 110, type: direct)
- `should_process_file` (line 113, type: attribute)
- `should_process_file` (line 114, type: attribute)
- `should_process_file` (line 115, type: attribute)
- `should_process_file` (line 116, type: attribute)
- `should_process_file` (line 117, type: attribute)
- `should_process_file` (line 120, type: attribute)
- `should_process_file` (line 121, type: attribute)
- `should_process_file` (line 122, type: attribute)
- `should_process_file` (line 125, type: attribute)
- `should_process_file` (line 126, type: attribute)
- `should_process_file` (line 127, type: attribute)

### tests\backend\test_watch_folders.py:TestWatchFolderConfiguration.test_config_service_watch_folders

Calls:
- `ConfigService` (line 42, type: direct)
- `validate_watch_folder` (line 45, type: attribute)
- `TemporaryDirectory` (line 50, type: attribute)
- `validate_watch_folder` (line 51, type: attribute)

### tests\backend\test_watch_folders.py:TestWatchFolderConfiguration.test_config_settings

Calls:
- `PrinternizerSettings` (line 25, type: direct)
- `PrinternizerSettings` (line 34, type: direct)
- `len` (line 36, type: direct)

### tests\backend\test_watch_folders.py:TestWatchFolderIntegration.test_file_service_local_integration

Calls:
- `Mock` (line 169, type: direct)
- `Mock` (line 170, type: direct)
- `Mock` (line 171, type: direct)
- `FileService` (line 174, type: direct)

### tests\backend\test_websocket.py:TestWebSocketConnection.test_websocket_authentication

Calls:
- `dumps` (line 39, type: attribute)
- `send` (line 46, type: attribute)
- `dumps` (line 46, type: attribute)
- `recv` (line 49, type: attribute)
- `loads` (line 50, type: attribute)
- `assert_called_once_with` (line 55, type: attribute)
- `dumps` (line 55, type: attribute)
- `assert_called_once` (line 56, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketConnection.test_websocket_connection_error_handling

Calls:
- `patch` (line 87, type: direct)
- `ConnectionError` (line 89, type: direct)
- `raises` (line 91, type: attribute)
- `mock_connect` (line 92, type: direct)

### tests\backend\test_websocket.py:TestWebSocketConnection.test_websocket_connection_establishment

Calls:
- `patch` (line 21, type: direct)
- `mock_connect` (line 26, type: direct)
- `assert_called_once_with` (line 28, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketConnection.test_websocket_reconnection_logic

Calls:
- `patch` (line 100, type: direct)
- `ConnectionError` (line 103, type: direct)
- `range` (line 109, type: direct)
- `mock_connect` (line 111, type: direct)
- `sleep` (line 117, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketConnection.test_websocket_subscription_management

Calls:
- `dumps` (line 67, type: attribute)
- `send` (line 73, type: attribute)
- `dumps` (line 73, type: attribute)
- `recv` (line 76, type: attribute)
- `loads` (line 77, type: attribute)
- `set` (line 80, type: direct)
- `set` (line 80, type: direct)

### tests\backend\test_websocket.py:TestWebSocketErrorHandling.test_connection_recovery_after_network_error

Calls:
- `patch` (line 355, type: direct)
- `ConnectionClosedError` (line 358, type: attribute)
- `ConnectionClosedError` (line 359, type: attribute)
- `enumerate` (line 368, type: direct)
- `mock_connect` (line 370, type: direct)
- `len` (line 374, type: direct)
- `sleep` (line 376, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketErrorHandling.test_connection_timeout_handling

Calls:
- `patch` (line 313, type: direct)
- `TimeoutError` (line 315, type: attribute)
- `raises` (line 317, type: attribute)
- `wait_for` (line 318, type: attribute)
- `mock_connect` (line 318, type: direct)

### tests\backend\test_websocket.py:TestWebSocketErrorHandling.test_heartbeat_mechanism

Calls:
- `send` (line 336, type: attribute)
- `dumps` (line 336, type: attribute)
- `dumps` (line 339, type: attribute)
- `recv` (line 342, type: attribute)
- `loads` (line 343, type: attribute)
- `assert_called_once_with` (line 348, type: attribute)
- `dumps` (line 348, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketErrorHandling.test_message_parsing_errors

Calls:
- `ConnectionClosedError` (line 296, type: attribute)
- `recv` (line 301, type: attribute)
- `loads` (line 303, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketErrorHandling.test_message_queue_overflow_handling

Calls:
- `range` (line 385, type: direct)
- `isoformat` (line 390, type: attribute)
- `now` (line 390, type: attribute)
- `append` (line 392, type: attribute)
- `dumps` (line 392, type: attribute)
- `range` (line 400, type: direct)
- `len` (line 402, type: direct)
- `recv` (line 403, type: attribute)
- `append` (line 404, type: attribute)
- `loads` (line 404, type: attribute)
- `pop` (line 407, type: attribute)
- `recv` (line 408, type: attribute)
- `append` (line 409, type: attribute)
- `loads` (line 409, type: attribute)
- `len` (line 414, type: direct)

### tests\backend\test_websocket.py:TestWebSocketGermanBusinessIntegration.test_business_cost_updates_via_websocket

Calls:
- `dumps` (line 578, type: attribute)
- `recv` (line 580, type: attribute)
- `loads` (line 581, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketGermanBusinessIntegration.test_german_quality_assessment_updates

Calls:
- `dumps` (line 606, type: attribute)
- `recv` (line 608, type: attribute)
- `loads` (line 609, type: attribute)
- `range` (line 611, type: direct)

### tests\backend\test_websocket.py:TestWebSocketGermanBusinessIntegration.test_german_timezone_in_websocket_messages

Calls:
- `berlin_timestamp` (line 539, type: attribute)
- `isoformat` (line 545, type: attribute)
- `dumps` (line 549, type: attribute)
- `recv` (line 551, type: attribute)
- `loads` (line 552, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketPerformance.receive_messages

Calls:
- `recv` (line 478, type: attribute)
- `loads` (line 479, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketPerformance.test_concurrent_websocket_connections

Calls:
- `range` (line 467, type: direct)
- `AsyncMock` (line 468, type: direct)
- `dumps` (line 469, type: attribute)
- `isoformat` (line 472, type: attribute)
- `now` (line 472, type: attribute)
- `append` (line 474, type: attribute)
- `receive_messages` (line 484, type: direct)
- `enumerate` (line 485, type: direct)
- `gather` (line 488, type: attribute)
- `len` (line 491, type: direct)
- `set` (line 492, type: direct)
- `set` (line 492, type: direct)
- `range` (line 492, type: direct)

### tests\backend\test_websocket.py:TestWebSocketPerformance.test_high_frequency_updates_performance

Calls:
- `range` (line 427, type: direct)
- `isoformat` (line 432, type: attribute)
- `now` (line 432, type: attribute)
- `append` (line 434, type: attribute)
- `dumps` (line 434, type: attribute)
- `time` (line 441, type: attribute)
- `range` (line 444, type: direct)
- `recv` (line 445, type: attribute)
- `loads` (line 446, type: attribute)
- `append` (line 447, type: attribute)
- `time` (line 449, type: attribute)
- `len` (line 453, type: direct)
- `enumerate` (line 457, type: direct)

### tests\backend\test_websocket.py:TestWebSocketPerformance.test_memory_usage_with_long_running_connection

Calls:
- `collect` (line 501, type: attribute)
- `len` (line 502, type: direct)
- `get_objects` (line 502, type: attribute)
- `range` (line 506, type: direct)
- `isoformat` (line 511, type: attribute)
- `now` (line 511, type: attribute)
- `dumps` (line 514, type: attribute)
- `recv` (line 517, type: attribute)
- `loads` (line 518, type: attribute)
- `collect` (line 525, type: attribute)
- `len` (line 526, type: direct)
- `get_objects` (line 526, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketRealTimeUpdates.test_batch_update_processing

Calls:
- `dumps` (line 263, type: attribute)
- `recv` (line 266, type: attribute)
- `loads` (line 267, type: attribute)
- `len` (line 270, type: direct)

### tests\backend\test_websocket.py:TestWebSocketRealTimeUpdates.test_file_download_progress_updates

Calls:
- `dumps` (line 204, type: attribute)
- `recv` (line 207, type: attribute)
- `loads` (line 208, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketRealTimeUpdates.test_job_progress_updates

Calls:
- `dumps` (line 175, type: attribute)
- `recv` (line 178, type: attribute)
- `loads` (line 179, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketRealTimeUpdates.test_printer_status_updates

Calls:
- `dumps` (line 147, type: attribute)
- `recv` (line 150, type: attribute)
- `loads` (line 151, type: attribute)

### tests\backend\test_websocket.py:TestWebSocketRealTimeUpdates.test_system_event_notifications

Calls:
- `dumps` (line 229, type: attribute)
- `recv` (line 232, type: attribute)
- `loads` (line 233, type: attribute)

### tests\conftest.py:AsyncMock.__call__

Calls:
- `__call__` (line 286, type: attribute)
- `super` (line 286, type: direct)

### tests\conftest.py:TestUtils.berlin_timestamp

Calls:
- `fromisoformat` (line 388, type: attribute)
- `timezone` (line 389, type: attribute)
- `localize` (line 390, type: attribute)

### tests\conftest.py:TestUtils.calculate_vat

Calls:
- `round` (line 395, type: direct)

### tests\conftest.py:TestUtils.generate_test_file_id

Calls:
- `uuid4` (line 406, type: attribute)

### tests\conftest.py:api_client

Calls:
- `Session` (line 431, type: attribute)
- `update` (line 432, type: attribute)

### tests\conftest.py:db_connection

Calls:
- `connect` (line 43, type: attribute)
- `close` (line 46, type: attribute)

### tests\conftest.py:event_loop

Calls:
- `new_event_loop` (line 418, type: attribute)
- `close` (line 420, type: attribute)
- `fixture` (line 415, type: attribute)

### tests\conftest.py:mock_bambu_api

Calls:
- `Mock` (line 194, type: direct)

### tests\conftest.py:mock_prusa_api

Calls:
- `Mock` (line 236, type: direct)

### tests\conftest.py:mock_websocket

Calls:
- `MagicMock` (line 276, type: direct)
- `AsyncMock` (line 277, type: direct)
- `AsyncMock` (line 278, type: direct)
- `AsyncMock` (line 279, type: direct)

### tests\conftest.py:network_error_scenarios

Calls:
- `JSONDecodeError` (line 452, type: attribute)

### tests\conftest.py:populated_database

Calls:
- `cursor` (line 160, type: attribute)
- `join` (line 164, type: attribute)
- `keys` (line 164, type: attribute)
- `join` (line 165, type: attribute)
- `execute` (line 166, type: attribute)
- `list` (line 167, type: direct)
- `values` (line 167, type: attribute)
- `join` (line 171, type: attribute)
- `keys` (line 171, type: attribute)
- `join` (line 172, type: attribute)
- `execute` (line 173, type: attribute)
- `list` (line 174, type: direct)
- `values` (line 174, type: attribute)
- `join` (line 178, type: attribute)
- `keys` (line 178, type: attribute)
- `join` (line 179, type: attribute)
- `execute` (line 180, type: attribute)
- `list` (line 181, type: direct)
- `values` (line 181, type: attribute)
- `commit` (line 183, type: attribute)

### tests\conftest.py:temp_database

Calls:
- `NamedTemporaryFile` (line 22, type: attribute)
- `close` (line 23, type: attribute)
- `join` (line 26, type: attribute)
- `dirname` (line 26, type: attribute)
- `open` (line 27, type: direct)
- `read` (line 28, type: attribute)
- `connect` (line 30, type: attribute)
- `executescript` (line 31, type: attribute)
- `close` (line 32, type: attribute)
- `unlink` (line 37, type: attribute)

### tests\conftest.py:temp_download_directory

Calls:
- `mkdtemp` (line 332, type: attribute)
- `rmtree` (line 335, type: attribute)

### tests\conftest.py:test_utils

Calls:
- `TestUtils` (line 408, type: direct)

### tests\fixtures\ideas_fixtures.py:IdeasTestFixtures.get_sample_ideas

Calls:
- `create_sample_idea` (line 71, type: direct)
- `create_sample_idea` (line 80, type: direct)
- `isoformat` (line 86, type: attribute)
- `date` (line 86, type: attribute)
- `now` (line 86, type: attribute)
- `timedelta` (line 86, type: direct)
- `create_sample_idea` (line 88, type: direct)
- `create_sample_idea` (line 96, type: direct)
- `isoformat` (line 102, type: attribute)
- `date` (line 102, type: attribute)
- `now` (line 102, type: attribute)
- `create_sample_idea` (line 104, type: direct)

### tests\fixtures\ideas_fixtures.py:IdeasTestFixtures.get_sample_trending_items

Calls:
- `create_sample_trending_item` (line 118, type: direct)
- `create_sample_trending_item` (line 126, type: direct)
- `create_sample_trending_item` (line 134, type: direct)
- `create_sample_trending_item` (line 142, type: direct)

### tests\fixtures\ideas_fixtures.py:create_business_idea

Calls:
- `create_sample_idea` (line 188, type: direct)

### tests\fixtures\ideas_fixtures.py:create_external_idea

Calls:
- `create_sample_idea` (line 204, type: direct)
- `isoformat` (line 210, type: attribute)
- `now` (line 210, type: attribute)

### tests\fixtures\ideas_fixtures.py:create_idea_with_tags

Calls:
- `create_sample_idea` (line 177, type: direct)

### tests\fixtures\ideas_fixtures.py:create_sample_idea

Calls:
- `str` (line 18, type: direct)
- `uuid4` (line 18, type: attribute)
- `isoformat` (line 28, type: attribute)
- `now` (line 28, type: attribute)
- `isoformat` (line 29, type: attribute)
- `now` (line 29, type: attribute)
- `update` (line 33, type: attribute)

### tests\fixtures\ideas_fixtures.py:create_sample_trending_item

Calls:
- `now` (line 42, type: attribute)
- `timedelta` (line 42, type: direct)
- `uuid4` (line 45, type: attribute)
- `str` (line 47, type: direct)
- `uuid4` (line 47, type: attribute)
- `title` (line 48, type: attribute)
- `isoformat` (line 55, type: attribute)
- `now` (line 55, type: attribute)
- `isoformat` (line 56, type: attribute)
- `update` (line 60, type: attribute)

### tests\run_essential_tests.py:main

Calls:
- `ArgumentParser` (line 15, type: attribute)
- `add_argument` (line 16, type: attribute)
- `add_argument` (line 17, type: attribute)
- `add_argument` (line 18, type: attribute)
- `parse_args` (line 19, type: attribute)
- `Path` (line 22, type: direct)
- `Path` (line 23, type: direct)
- `print` (line 33, type: direct)
- `print` (line 34, type: direct)
- `print` (line 35, type: direct)
- `print` (line 36, type: direct)
- `print` (line 37, type: direct)
- `exists` (line 43, type: attribute)
- `append` (line 44, type: attribute)
- `print` (line 47, type: direct)
- `print` (line 49, type: direct)
- `print` (line 50, type: direct)
- `print` (line 51, type: direct)
- `append` (line 58, type: attribute)
- `append` (line 60, type: attribute)
- `extend` (line 63, type: attribute)
- `extend` (line 70, type: attribute)
- `append` (line 74, type: attribute)
- `str` (line 74, type: direct)
- `chdir` (line 77, type: attribute)
- `print` (line 79, type: direct)
- `print` (line 81, type: direct)
- `print` (line 82, type: direct)
- `print` (line 85, type: direct)
- `print` (line 86, type: direct)
- `join` (line 86, type: attribute)
- `print` (line 87, type: direct)
- `run` (line 90, type: attribute)
- `print` (line 93, type: direct)
- `print` (line 94, type: direct)
- `print` (line 97, type: direct)
- `print` (line 100, type: direct)
- `print` (line 101, type: direct)
- `print` (line 104, type: direct)
- `print` (line 105, type: direct)
- `print` (line 106, type: direct)
- `print` (line 107, type: direct)
- `print` (line 108, type: direct)
- `print` (line 109, type: direct)
- `print` (line 110, type: direct)
- `print` (line 111, type: direct)
- `print` (line 114, type: direct)
- `print` (line 115, type: direct)
- `print` (line 118, type: direct)
- `print` (line 119, type: direct)
- `print` (line 120, type: direct)
- `print` (line 121, type: direct)
- `print` (line 122, type: direct)
- `print` (line 123, type: direct)
- `print` (line 124, type: direct)
- `print` (line 125, type: direct)
- `print` (line 126, type: direct)

### tests\run_essential_tests.py:run_frontend_tests

Calls:
- `print` (line 133, type: direct)
- `run` (line 137, type: attribute)
- `run` (line 138, type: attribute)
- `print` (line 140, type: direct)
- `Path` (line 143, type: direct)
- `exists` (line 144, type: attribute)
- `run` (line 145, type: attribute)
- `str` (line 146, type: direct)
- `print` (line 150, type: direct)
- `print` (line 152, type: direct)
- `print` (line 156, type: direct)
- `print` (line 160, type: direct)
- `print` (line 161, type: direct)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.__init__

Calls:
- `Path` (line 29, type: direct)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.check_dependencies

Calls:
- `print` (line 63, type: direct)
- `__import__` (line 75, type: direct)
- `replace` (line 75, type: attribute)
- `append` (line 77, type: attribute)
- `print` (line 80, type: direct)
- `join` (line 80, type: attribute)
- `print` (line 81, type: direct)
- `print` (line 84, type: direct)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.print_header

Calls:
- `print` (line 49, type: direct)
- `print` (line 50, type: direct)
- `print` (line 51, type: direct)
- `print` (line 52, type: direct)
- `print` (line 53, type: direct)
- `print` (line 54, type: direct)
- `print` (line 55, type: direct)
- `print` (line 56, type: direct)
- `print` (line 57, type: direct)
- `print` (line 58, type: direct)
- `print` (line 59, type: direct)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.print_summary

Calls:
- `now` (line 173, type: attribute)
- `total_seconds` (line 174, type: attribute)
- `print` (line 176, type: direct)
- `print` (line 179, type: direct)
- `print` (line 180, type: direct)
- `print` (line 181, type: direct)
- `print` (line 182, type: direct)
- `print` (line 183, type: direct)
- `print` (line 184, type: direct)
- `print` (line 185, type: direct)
- `print` (line 186, type: direct)
- `print` (line 187, type: direct)
- `print` (line 188, type: direct)
- `print` (line 189, type: direct)
- `print` (line 191, type: direct)
- `print` (line 193, type: direct)
- `print` (line 195, type: direct)
- `print` (line 197, type: direct)
- `print` (line 198, type: direct)
- `strftime` (line 198, type: attribute)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.run_backend_tests

Calls:
- `print` (line 89, type: direct)
- `print` (line 90, type: direct)
- `extend` (line 96, type: attribute)
- `extend` (line 99, type: attribute)
- `endswith` (line 106, type: attribute)
- `exists` (line 108, type: attribute)
- `append` (line 109, type: attribute)
- `str` (line 109, type: direct)
- `exists` (line 114, type: attribute)
- `append` (line 115, type: attribute)
- `str` (line 115, type: direct)
- `print` (line 118, type: direct)
- `extend` (line 121, type: attribute)
- `print` (line 123, type: direct)
- `join` (line 123, type: attribute)
- `Path` (line 123, type: direct)
- `print` (line 124, type: direct)
- `join` (line 124, type: attribute)
- `print` (line 125, type: direct)
- `run` (line 128, type: attribute)
- `print` (line 131, type: direct)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.run_frontend_tests

Calls:
- `print` (line 136, type: direct)
- `print` (line 137, type: direct)
- `exists` (line 142, type: attribute)
- `print` (line 143, type: direct)
- `run` (line 148, type: attribute)
- `print` (line 151, type: direct)
- `print` (line 152, type: direct)
- `str` (line 156, type: direct)
- `append` (line 158, type: attribute)
- `print` (line 160, type: direct)
- `print` (line 161, type: direct)
- `join` (line 161, type: attribute)
- `print` (line 162, type: direct)
- `run` (line 165, type: attribute)
- `print` (line 168, type: direct)

### tests\run_milestone_1_2_tests.py:Milestone12TestRunner.run_tests

Calls:
- `now` (line 202, type: attribute)
- `print_header` (line 204, type: attribute)
- `check_dependencies` (line 207, type: attribute)
- `run_backend_tests` (line 211, type: attribute)
- `run_frontend_tests` (line 214, type: attribute)
- `print_summary` (line 217, type: attribute)

### tests\run_milestone_1_2_tests.py:main

Calls:
- `ArgumentParser` (line 224, type: attribute)
- `add_argument` (line 236, type: attribute)
- `add_argument` (line 242, type: attribute)
- `parse_args` (line 248, type: attribute)
- `Milestone12TestRunner` (line 251, type: direct)
- `run_tests` (line 252, type: attribute)
- `exit` (line 255, type: attribute)

### tests\test_essential_config.py:TestBusinessLogic.is_business_job

Calls:
- `any` (line 203, type: direct)

### tests\test_essential_config.py:TestBusinessLogic.test_business_hours_validation

Calls:
- `int` (line 164, type: direct)
- `split` (line 164, type: attribute)
- `int` (line 165, type: direct)
- `split` (line 165, type: attribute)

### tests\test_essential_config.py:TestBusinessLogic.test_customer_data_validation

Calls:
- `isoformat` (line 177, type: attribute)
- `now` (line 177, type: attribute)
- `endswith` (line 182, type: attribute)

### tests\test_essential_config.py:TestBusinessLogic.test_file_naming_conventions

Calls:
- `split` (line 221, type: attribute)

### tests\test_essential_config.py:TestBusinessLogic.test_job_classification

Calls:
- `is_business_job` (line 205, type: direct)
- `is_business_job` (line 206, type: direct)
- `is_business_job` (line 207, type: direct)
- `is_business_job` (line 208, type: direct)

### tests\test_essential_config.py:TestConfigService.test_config_service_german_settings

Calls:
- `ConfigService` (line 147, type: direct)
- `hasattr` (line 150, type: direct)

### tests\test_essential_config.py:TestConfigService.test_config_service_initialization

Calls:
- `ConfigService` (line 142, type: direct)

### tests\test_essential_config.py:TestGermanBusinessConfig.test_german_timezone_configuration

Calls:
- `timezone` (line 22, type: attribute)
- `now` (line 23, type: attribute)
- `str` (line 27, type: direct)

### tests\test_essential_config.py:TestGermanBusinessConfig.test_material_cost_calculation

Calls:
- `abs` (line 53, type: direct)
- `round` (line 55, type: direct)

### tests\test_essential_config.py:TestGermanBusinessConfig.test_power_cost_calculation

Calls:
- `abs` (line 67, type: direct)

### tests\test_essential_config.py:TestSystemConfiguration.test_api_base_configuration

Calls:
- `isinstance` (line 107, type: direct)

### tests\test_essential_config.py:TestSystemConfiguration.test_database_path_configuration

Calls:
- `endswith` (line 94, type: attribute)

### tests\test_essential_config.py:TestSystemConfiguration.test_environment_variables

Calls:
- `items` (line 80, type: attribute)
- `getenv` (line 82, type: attribute)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_analytics_basic_functionality

Calls:
- `get` (line 101, type: attribute)
- `json` (line 103, type: attribute)
- `isinstance` (line 106, type: direct)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_complete_printer_setup_workflow

Calls:
- `post` (line 37, type: attribute)
- `json` (line 39, type: attribute)
- `get` (line 43, type: attribute)
- `json` (line 45, type: attribute)
- `post` (line 49, type: attribute)
- `get` (line 53, type: attribute)
- `json` (line 55, type: attribute)
- `len` (line 56, type: direct)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_files_discovery_workflow

Calls:
- `get` (line 81, type: attribute)
- `json` (line 83, type: attribute)
- `isinstance` (line 86, type: direct)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_german_business_integration

Calls:
- `post` (line 148, type: attribute)
- `json` (line 151, type: attribute)
- `get` (line 155, type: attribute)
- `json` (line 157, type: attribute)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_health_check_system_integration

Calls:
- `get` (line 63, type: attribute)
- `json` (line 66, type: attribute)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_jobs_monitoring_workflow

Calls:
- `get` (line 92, type: attribute)
- `json` (line 94, type: attribute)
- `isinstance` (line 97, type: direct)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_system_configuration_workflow

Calls:
- `get` (line 110, type: attribute)
- `json` (line 112, type: attribute)
- `isinstance` (line 115, type: direct)

### tests\test_essential_integration.py:TestCoreWorkflowIntegration.test_websocket_connection_basic

Calls:
- `startswith` (line 129, type: attribute)
- `skip` (line 134, type: attribute)

### tests\test_essential_integration.py:TestErrorHandlingIntegration.test_duplicate_printer_handling

Calls:
- `post` (line 201, type: attribute)
- `post` (line 205, type: attribute)

### tests\test_essential_integration.py:TestErrorHandlingIntegration.test_invalid_printer_data_handling

Calls:
- `post` (line 173, type: attribute)
- `json` (line 176, type: attribute)

### tests\test_essential_integration.py:TestErrorHandlingIntegration.test_nonexistent_resource_handling

Calls:
- `get` (line 184, type: attribute)
- `json` (line 187, type: attribute)

### tests\test_essential_integration.py:TestGermanBusinessIntegration.calculate_job_cost

Calls:
- `round` (line 230, type: direct)

### tests\test_essential_integration.py:TestGermanBusinessIntegration.classify_customer

Calls:
- `any` (line 244, type: direct)

### tests\test_essential_integration.py:TestGermanBusinessIntegration.test_business_vs_private_classification

Calls:
- `classify_customer` (line 247, type: direct)
- `classify_customer` (line 248, type: direct)
- `classify_customer` (line 249, type: direct)
- `classify_customer` (line 250, type: direct)

### tests\test_essential_integration.py:TestGermanBusinessIntegration.test_currency_formatting_integration

Calls:
- `calculate_job_cost` (line 233, type: direct)
- `round` (line 234, type: direct)

### tests\test_essential_integration.py:TestGermanBusinessIntegration.test_file_naming_german_support

Calls:
- `any` (line 263, type: direct)
- `endswith` (line 265, type: attribute)

### tests\test_essential_integration.py:TestGermanBusinessIntegration.test_timezone_integration

Calls:
- `timezone` (line 217, type: attribute)
- `now` (line 218, type: attribute)
- `str` (line 221, type: direct)
- `str` (line 221, type: direct)
- `str` (line 221, type: direct)

### tests\test_essential_integration.py:TestHardwareIntegration.test_bambu_lab_real_connection

Calls:
- `skip` (line 277, type: attribute)

### tests\test_essential_integration.py:TestHardwareIntegration.test_prusa_real_connection

Calls:
- `skip` (line 281, type: attribute)

### tests\test_essential_integration.py:async_client

Calls:
- `TestClient` (line 18, type: direct)

### tests\test_essential_models.py:TestEnumValidation.test_job_status_enum_values

Calls:
- `hasattr` (line 193, type: direct)
- `upper` (line 193, type: attribute)

### tests\test_essential_models.py:TestEnumValidation.test_printer_status_enum_values

Calls:
- `hasattr` (line 186, type: direct)
- `upper` (line 186, type: attribute)

### tests\test_essential_models.py:TestFileModel.test_file_download_status_progression

Calls:
- `File` (line 150, type: direct)
- `File` (line 160, type: direct)

### tests\test_essential_models.py:TestFileModel.test_valid_file_creation

Calls:
- `File` (line 142, type: direct)

### tests\test_essential_models.py:TestJobModel.test_job_business_logic_fields

Calls:
- `Job` (line 92, type: direct)

### tests\test_essential_models.py:TestJobModel.test_job_create_minimal

Calls:
- `JobCreate` (line 109, type: direct)

### tests\test_essential_models.py:TestJobModel.test_job_update_fields

Calls:
- `JobUpdate` (line 119, type: direct)

### tests\test_essential_models.py:TestJobModel.test_valid_job_creation

Calls:
- `Job` (line 84, type: direct)

### tests\test_essential_models.py:TestModelSerialization.test_job_json_serialization

Calls:
- `Job` (line 223, type: direct)
- `model_dump` (line 232, type: attribute)

### tests\test_essential_models.py:TestModelSerialization.test_printer_json_serialization

Calls:
- `Printer` (line 208, type: direct)
- `now` (line 212, type: attribute)
- `model_dump` (line 215, type: attribute)

### tests\test_essential_models.py:TestPrinterModel.test_printer_config_optional_fields

Calls:
- `PrinterConfig` (line 64, type: direct)

### tests\test_essential_models.py:TestPrinterModel.test_printer_required_fields

Calls:
- `raises` (line 52, type: attribute)
- `Printer` (line 53, type: direct)
- `errors` (line 55, type: attribute)

### tests\test_essential_models.py:TestPrinterModel.test_valid_bambu_printer_creation

Calls:
- `Printer` (line 28, type: direct)

### tests\test_essential_models.py:TestPrinterModel.test_valid_prusa_printer_creation

Calls:
- `Printer` (line 45, type: direct)

### tests\test_essential_printer_api.py:TestEssentialGermanBusinessIntegration.test_german_business_customer_classification

Calls:
- `any` (line 400, type: direct)

### tests\test_essential_printer_api.py:TestEssentialGermanBusinessIntegration.test_german_material_cost_calculation

Calls:
- `approx` (line 379, type: attribute)
- `approx` (line 380, type: attribute)
- `approx` (line 381, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialGermanBusinessIntegration.test_german_timezone_handling

Calls:
- `ZoneInfo` (line 410, type: direct)
- `now` (line 411, type: attribute)
- `str` (line 414, type: direct)
- `astimezone` (line 417, type: attribute)
- `abs` (line 421, type: direct)
- `total_seconds` (line 421, type: attribute)
- `astimezone` (line 421, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.mock_bambu_printer

Calls:
- `patch` (line 32, type: direct)
- `BambuLabPrinter` (line 33, type: direct)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.mock_printer_id

Calls:
- `str` (line 27, type: direct)
- `uuid4` (line 27, type: direct)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.mock_prusa_printer

Calls:
- `PrusaPrinter` (line 45, type: direct)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.test_current_job_real_time_progress

Calls:
- `str` (line 201, type: direct)
- `uuid4` (line 201, type: direct)
- `object` (line 216, type: attribute)
- `get_job_info` (line 219, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.test_drucker_dateien_file_listing

Calls:
- `object` (line 140, type: attribute)
- `list_files` (line 143, type: attribute)
- `len` (line 146, type: direct)
- `any` (line 150, type: direct)
- `any` (line 151, type: direct)
- `any` (line 152, type: direct)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.test_job_sync_history_integration

Calls:
- `str` (line 245, type: direct)
- `uuid4` (line 245, type: direct)
- `str` (line 255, type: direct)
- `uuid4` (line 255, type: direct)
- `object` (line 266, type: attribute)
- `isoformat` (line 271, type: attribute)
- `now` (line 271, type: attribute)
- `get_job_info` (line 275, type: attribute)
- `len` (line 280, type: direct)
- `len` (line 286, type: direct)
- `len` (line 287, type: direct)
- `any` (line 296, type: direct)
- `any` (line 297, type: direct)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.test_one_click_file_download

Calls:
- `isoformat` (line 177, type: attribute)
- `now` (line 177, type: attribute)
- `object` (line 180, type: attribute)
- `download_file` (line 183, type: attribute)
- `assert_called_once_with` (line 194, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.test_printer_monitoring_start_stop

Calls:
- `object` (line 96, type: attribute)
- `connect` (line 99, type: attribute)
- `assert_called_once` (line 102, type: attribute)
- `object` (line 105, type: attribute)
- `disconnect` (line 108, type: attribute)
- `assert_called_once` (line 110, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialPrinterAPIEndpoints.test_printer_status_endpoint_real_time

Calls:
- `str` (line 63, type: direct)
- `uuid4` (line 63, type: direct)
- `isoformat` (line 70, type: attribute)
- `now` (line 70, type: attribute)
- `object` (line 73, type: attribute)
- `get_status` (line 76, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialPrinterConnectionRecovery.test_bambu_mqtt_connection_recovery

Calls:
- `patch` (line 306, type: direct)
- `BambuLabPrinter` (line 307, type: direct)
- `str` (line 308, type: direct)
- `uuid4` (line 308, type: direct)
- `object` (line 318, type: attribute)
- `isoformat` (line 323, type: attribute)
- `now` (line 323, type: attribute)
- `get_status` (line 327, type: attribute)

### tests\test_essential_printer_api.py:TestEssentialPrinterConnectionRecovery.test_prusa_http_connection_recovery

Calls:
- `PrusaPrinter` (line 338, type: direct)
- `str` (line 339, type: direct)
- `uuid4` (line 339, type: direct)
- `object` (line 346, type: attribute)
- `get_status` (line 354, type: attribute)
- `get_status` (line 359, type: attribute)

### tests\test_essential_printer_drivers.py:TestEssentialBambuLabDriverIntegration.mock_bambu_printer

Calls:
- `patch` (line 28, type: direct)
- `MagicMock` (line 30, type: direct)
- `MagicMock` (line 31, type: direct)
- `patch` (line 33, type: direct)
- `BambuLabPrinter` (line 34, type: direct)
- `str` (line 35, type: direct)
- `uuid4` (line 35, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialBambuLabDriverIntegration.mock_connect_with_retry

Calls:
- `append` (line 174, type: attribute)
- `len` (line 174, type: direct)
- `len` (line 175, type: direct)
- `PrinterConnectionError` (line 176, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialBambuLabDriverIntegration.test_bambu_file_listing_via_mqtt

Calls:
- `object` (line 138, type: attribute)
- `isoformat` (line 143, type: attribute)
- `fromtimestamp` (line 143, type: attribute)
- `list_files` (line 150, type: attribute)
- `len` (line 153, type: direct)
- `any` (line 157, type: direct)
- `any` (line 158, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialBambuLabDriverIntegration.test_bambu_mqtt_connection_initialization

Calls:
- `AsyncMock` (line 49, type: direct)
- `AsyncMock` (line 50, type: direct)
- `connect` (line 57, type: attribute)
- `assert_called_once` (line 61, type: attribute)
- `get_device_info` (line 64, type: attribute)

### tests\test_essential_printer_drivers.py:TestEssentialBambuLabDriverIntegration.test_bambu_mqtt_error_recovery

Calls:
- `object` (line 179, type: attribute)
- `raises` (line 181, type: attribute)
- `connect` (line 182, type: attribute)
- `raises` (line 184, type: attribute)
- `connect` (line 185, type: attribute)
- `connect` (line 188, type: attribute)
- `len` (line 190, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialBambuLabDriverIntegration.test_bambu_real_time_status_via_mqtt

Calls:
- `object` (line 91, type: attribute)
- `get_status` (line 105, type: attribute)

### tests\test_essential_printer_drivers.py:TestEssentialPrinterDriverComparison.classify_customer_type

Calls:
- `any` (line 520, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialPrinterDriverComparison.test_connection_recovery_consistency

Calls:
- `raises` (line 498, type: attribute)
- `PrinterConnectionError` (line 499, type: direct)
- `lower` (line 502, type: attribute)
- `str` (line 502, type: direct)
- `lower` (line 503, type: attribute)
- `str` (line 503, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialPrinterDriverComparison.test_german_business_data_integration

Calls:
- `classify_customer_type` (line 528, type: direct)
- `calculate_total_cost` (line 529, type: direct)
- `approx` (line 533, type: attribute)

### tests\test_essential_printer_drivers.py:TestEssentialPrinterDriverComparison.test_unified_status_interface

Calls:
- `patch` (line 429, type: direct)
- `BambuLabPrinter` (line 430, type: direct)
- `str` (line 431, type: direct)
- `uuid4` (line 431, type: direct)
- `PrusaPrinter` (line 438, type: direct)
- `str` (line 439, type: direct)
- `uuid4` (line 439, type: direct)
- `set` (line 470, type: direct)
- `keys` (line 470, type: attribute)
- `set` (line 471, type: direct)
- `keys` (line 471, type: attribute)
- `isinstance` (line 475, type: direct)
- `isinstance` (line 476, type: direct)
- `isinstance` (line 477, type: direct)
- `isinstance` (line 478, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialPrusaDriverIntegration.mock_poll_status

Calls:
- `min` (line 283, type: direct)
- `len` (line 283, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialPrusaDriverIntegration.mock_prusa_printer

Calls:
- `PrusaPrinter` (line 199, type: direct)
- `str` (line 200, type: direct)
- `uuid4` (line 200, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialPrusaDriverIntegration.test_prusa_30_second_polling_status

Calls:
- `object` (line 287, type: attribute)
- `get_status` (line 297, type: attribute)
- `sleep` (line 312, type: attribute)
- `get_status` (line 313, type: attribute)

### tests\test_essential_printer_drivers.py:TestEssentialPrusaDriverIntegration.test_prusa_file_download_http

Calls:
- `patch` (line 326, type: direct)
- `AsyncMock` (line 328, type: direct)
- `AsyncMock` (line 330, type: direct)
- `str` (line 331, type: direct)
- `len` (line 331, type: direct)
- `object` (line 334, type: attribute)
- `len` (line 338, type: direct)
- `decode` (line 340, type: attribute)
- `download_file` (line 343, type: attribute)
- `len` (line 348, type: direct)

### tests\test_essential_printer_drivers.py:TestEssentialPrusaDriverIntegration.test_prusa_http_api_connection

Calls:
- `patch` (line 224, type: direct)
- `AsyncMock` (line 225, type: direct)
- `AsyncMock` (line 227, type: direct)
- `object` (line 231, type: attribute)
- `check_connection` (line 239, type: attribute)

### tests\test_essential_printer_drivers.py:TestEssentialPrusaDriverIntegration.test_prusa_job_history_sync

Calls:
- `object` (line 383, type: attribute)
- `str` (line 390, type: direct)
- `uuid4` (line 390, type: direct)
- `isoformat` (line 393, type: attribute)
- `fromtimestamp` (line 393, type: attribute)
- `isoformat` (line 394, type: attribute)
- `fromtimestamp` (line 394, type: attribute)
- `any` (line 397, type: direct)
- `sync_job_history` (line 404, type: attribute)
- `len` (line 409, type: direct)
- `any` (line 418, type: direct)
- `any` (line 419, type: direct)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_analyze_gcode_file_disabled

Calls:
- `GcodeAnalyzer` (line 211, type: direct)
- `NamedTemporaryFile` (line 218, type: attribute)
- `write` (line 219, type: attribute)
- `analyze_gcode_file` (line 223, type: attribute)
- `unlink` (line 230, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_analyze_gcode_file_not_found

Calls:
- `GcodeAnalyzer` (line 199, type: direct)
- `analyze_gcode_file` (line 201, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_analyze_gcode_file_success

Calls:
- `GcodeAnalyzer` (line 169, type: direct)
- `NamedTemporaryFile` (line 180, type: attribute)
- `write` (line 181, type: attribute)
- `analyze_gcode_file` (line 185, type: attribute)
- `unlink` (line 195, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_find_print_start_disabled

Calls:
- `GcodeAnalyzer` (line 27, type: direct)
- `find_print_start_line` (line 35, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_find_print_start_extrusion_based

Calls:
- `GcodeAnalyzer` (line 68, type: direct)
- `find_print_start_line` (line 76, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_find_print_start_layer_marker

Calls:
- `GcodeAnalyzer` (line 40, type: direct)
- `find_print_start_line` (line 49, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_find_print_start_no_markers

Calls:
- `GcodeAnalyzer` (line 81, type: direct)
- `find_print_start_line` (line 89, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_find_print_start_type_marker

Calls:
- `GcodeAnalyzer` (line 54, type: direct)
- `find_print_start_line` (line 63, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_get_optimized_gcode_lines_disabled

Calls:
- `GcodeAnalyzer` (line 143, type: direct)
- `get_optimized_gcode_lines` (line 152, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_get_optimized_gcode_lines_no_optimization_possible

Calls:
- `GcodeAnalyzer` (line 157, type: direct)
- `get_optimized_gcode_lines` (line 164, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_get_optimized_gcode_lines_with_optimization

Calls:
- `GcodeAnalyzer` (line 122, type: direct)
- `get_optimized_gcode_lines` (line 132, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_heating_detection

Calls:
- `GcodeAnalyzer` (line 279, type: direct)
- `find_print_start_line` (line 285, type: attribute)
- `parametrize` (line 270, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_init_disabled

Calls:
- `GcodeAnalyzer` (line 22, type: direct)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_init_enabled

Calls:
- `GcodeAnalyzer` (line 17, type: direct)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_is_likely_print_move_edge_position

Calls:
- `GcodeAnalyzer` (line 102, type: direct)
- `_is_likely_print_move` (line 105, type: attribute)
- `_is_likely_print_move` (line 109, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_is_likely_print_move_normal_print

Calls:
- `GcodeAnalyzer` (line 114, type: direct)
- `_is_likely_print_move` (line 117, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_is_likely_print_move_small_extrusion

Calls:
- `GcodeAnalyzer` (line 94, type: direct)
- `_is_likely_print_move` (line 97, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_multiple_slicer_markers

Calls:
- `GcodeAnalyzer` (line 234, type: direct)
- `find_print_start_line` (line 253, type: attribute)

### tests\test_gcode_analyzer.py:TestGcodeAnalyzer.test_warmup_end_pattern_detection

Calls:
- `GcodeAnalyzer` (line 258, type: direct)
- `find_print_start_line` (line 266, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_get_formatted_time

Calls:
- `from_dict` (line 336, type: attribute)
- `create_sample_idea` (line 336, type: direct)
- `get_formatted_time` (line 337, type: attribute)
- `from_dict` (line 340, type: attribute)
- `create_sample_idea` (line 340, type: direct)
- `get_formatted_time` (line 341, type: attribute)
- `from_dict` (line 344, type: attribute)
- `create_sample_idea` (line 344, type: direct)
- `get_formatted_time` (line 345, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_idea_creation_from_dict

Calls:
- `create_sample_idea` (line 286, type: direct)
- `from_dict` (line 287, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_idea_to_dict

Calls:
- `create_sample_idea` (line 296, type: direct)
- `from_dict` (line 297, type: attribute)
- `to_dict` (line 298, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_idea_validation_invalid_priority

Calls:
- `create_sample_idea` (line 321, type: direct)
- `from_dict` (line 322, type: attribute)
- `validate` (line 324, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_idea_validation_invalid_status

Calls:
- `create_sample_idea` (line 328, type: direct)
- `from_dict` (line 329, type: attribute)
- `validate` (line 331, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_idea_validation_missing_title

Calls:
- `create_sample_idea` (line 313, type: direct)
- `from_dict` (line 315, type: attribute)
- `validate` (line 317, type: attribute)

### tests\test_ideas_service.py:TestIdeaModel.test_idea_validation_success

Calls:
- `create_sample_idea` (line 306, type: direct)
- `from_dict` (line 307, type: attribute)
- `validate` (line 309, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_cache_trending_success

Calls:
- `get_sample_trending_items` (line 196, type: attribute)
- `cache_trending` (line 199, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_cleanup_expired_trending

Calls:
- `cleanup_expired_trending` (line 275, type: attribute)
- `assert_called_once` (line 278, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_create_idea_missing_title

Calls:
- `create_sample_idea` (line 76, type: direct)
- `create_idea` (line 79, type: attribute)
- `assert_not_called` (line 82, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_create_idea_success

Calls:
- `create_sample_idea` (line 51, type: direct)
- `create_idea` (line 53, type: attribute)
- `assert_called_once` (line 57, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_create_idea_with_tags

Calls:
- `create_sample_idea` (line 62, type: direct)
- `create_idea` (line 67, type: attribute)
- `assert_called_once` (line 70, type: attribute)
- `assert_called_once_with` (line 71, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_delete_idea_success

Calls:
- `str` (line 157, type: direct)
- `uuid4` (line 157, type: attribute)
- `delete_idea` (line 159, type: attribute)
- `assert_called_once_with` (line 162, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_get_idea_not_found

Calls:
- `get_idea` (line 103, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_get_idea_success

Calls:
- `create_sample_idea` (line 87, type: direct)
- `get_idea` (line 91, type: attribute)
- `isinstance` (line 94, type: direct)

### tests\test_ideas_service.py:TestIdeaService.test_get_statistics

Calls:
- `get_statistics` (line 188, type: attribute)
- `assert_called_once` (line 191, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_get_trending

Calls:
- `get_sample_trending_items` (line 207, type: attribute)
- `get_trending` (line 210, type: attribute)
- `len` (line 212, type: direct)
- `len` (line 212, type: direct)
- `assert_called_once_with` (line 213, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_list_ideas_with_filters

Calls:
- `get_sample_ideas` (line 110, type: attribute)
- `list_ideas` (line 115, type: attribute)
- `len` (line 118, type: direct)
- `assert_called_once_with` (line 121, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_save_trending_as_idea

Calls:
- `create_sample_trending_item` (line 218, type: direct)
- `save_trending_as_idea` (line 221, type: attribute)
- `assert_called_once` (line 224, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_search_ideas

Calls:
- `AsyncMock` (line 252, type: direct)
- `search_ideas` (line 255, type: attribute)
- `len` (line 256, type: direct)
- `search_ideas` (line 260, type: attribute)
- `len` (line 261, type: direct)
- `search_ideas` (line 265, type: attribute)
- `len` (line 266, type: direct)
- `search_ideas` (line 269, type: attribute)
- `len` (line 270, type: direct)

### tests\test_ideas_service.py:TestIdeaService.test_update_idea_status

Calls:
- `str` (line 167, type: direct)
- `uuid4` (line 167, type: attribute)
- `update_idea_status` (line 170, type: attribute)
- `assert_called_once_with` (line 173, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_update_idea_success

Calls:
- `str` (line 133, type: direct)
- `uuid4` (line 133, type: attribute)
- `update_idea` (line 136, type: attribute)
- `assert_called_once_with` (line 139, type: attribute)

### tests\test_ideas_service.py:TestIdeaService.test_update_idea_with_tags

Calls:
- `str` (line 144, type: direct)
- `uuid4` (line 144, type: attribute)
- `update_idea` (line 148, type: attribute)
- `assert_called_once_with` (line 151, type: attribute)
- `assert_called_once_with` (line 152, type: attribute)

### tests\test_ideas_service.py:TestTrendingItemModel.test_is_expired_false

Calls:
- `create_sample_trending_item` (line 372, type: direct)
- `from_dict` (line 373, type: attribute)
- `is_expired` (line 375, type: attribute)

### tests\test_ideas_service.py:TestTrendingItemModel.test_is_expired_true

Calls:
- `replace` (line 379, type: attribute)
- `now` (line 379, type: attribute)
- `create_sample_trending_item` (line 380, type: direct)
- `isoformat` (line 381, type: attribute)
- `from_dict` (line 383, type: attribute)
- `is_expired` (line 385, type: attribute)

### tests\test_ideas_service.py:TestTrendingItemModel.test_trending_item_creation

Calls:
- `create_sample_trending_item` (line 353, type: direct)
- `from_dict` (line 354, type: attribute)

### tests\test_ideas_service.py:TestTrendingItemModel.test_trending_item_to_dict

Calls:
- `create_sample_trending_item` (line 362, type: direct)
- `from_dict` (line 363, type: attribute)
- `to_dict` (line 364, type: attribute)

### tests\test_ideas_service.py:idea_service

Calls:
- `IdeaService` (line 42, type: direct)

### tests\test_ideas_service.py:mock_database

Calls:
- `MagicMock` (line 21, type: direct)
- `AsyncMock` (line 22, type: direct)
- `AsyncMock` (line 23, type: direct)
- `AsyncMock` (line 24, type: direct)
- `AsyncMock` (line 25, type: direct)
- `AsyncMock` (line 26, type: direct)
- `AsyncMock` (line 27, type: direct)
- `AsyncMock` (line 28, type: direct)
- `AsyncMock` (line 29, type: direct)
- `AsyncMock` (line 30, type: direct)
- `AsyncMock` (line 31, type: direct)
- `AsyncMock` (line 32, type: direct)
- `AsyncMock` (line 33, type: direct)
- `AsyncMock` (line 34, type: direct)
- `AsyncMock` (line 35, type: direct)

### tests\test_printer_interface_conformance.py:test_bambu_printer_implements_interface

Calls:
- `skip` (line 38, type: attribute)
- `BambuLabPrinter` (line 39, type: direct)
- `hasattr` (line 41, type: direct)
- `getattr` (line 42, type: direct)
- `iscoroutinefunction` (line 43, type: attribute)

### tests\test_printer_interface_conformance.py:test_printer_interface_methods_signature

Calls:
- `hasattr` (line 21, type: direct)
- `getattr` (line 22, type: direct)
- `isfunction` (line 24, type: attribute)

### tests\test_printer_interface_conformance.py:test_prusa_printer_implements_interface

Calls:
- `PrusaPrinter` (line 29, type: direct)
- `hasattr` (line 31, type: direct)
- `getattr` (line 32, type: direct)
- `iscoroutinefunction` (line 33, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner.__init__

Calls:
- `Path` (line 20, type: direct)
- `Path` (line 20, type: direct)
- `mkdir` (line 26, type: attribute)
- `mkdir` (line 27, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner._create_test_documentation

Calls:
- `strftime` (line 352, type: attribute)
- `now` (line 352, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner._print_final_summary

Calls:
- `print` (line 617, type: direct)
- `print` (line 618, type: direct)
- `print` (line 619, type: direct)
- `print` (line 622, type: direct)
- `print` (line 625, type: direct)
- `print` (line 626, type: direct)
- `print` (line 627, type: direct)
- `print` (line 628, type: direct)
- `print` (line 631, type: direct)
- `print` (line 632, type: direct)
- `print` (line 633, type: direct)
- `print` (line 641, type: direct)
- `print` (line 643, type: direct)
- `print` (line 645, type: direct)
- `print` (line 646, type: direct)
- `print` (line 647, type: direct)

### tests\test_runner.py:PrinternizerTestRunner._process_backend_results

Calls:
- `print` (line 303, type: direct)
- `print` (line 306, type: direct)
- `print` (line 308, type: direct)
- `print` (line 309, type: direct)
- `print` (line 310, type: direct)

### tests\test_runner.py:PrinternizerTestRunner._process_benchmark_results

Calls:
- `print` (line 325, type: direct)
- `print` (line 328, type: direct)
- `exists` (line 332, type: attribute)
- `open` (line 333, type: direct)
- `load` (line 334, type: attribute)
- `print` (line 336, type: direct)
- `get` (line 337, type: attribute)
- `get` (line 338, type: attribute)
- `get` (line 339, type: attribute)
- `get` (line 339, type: attribute)
- `print` (line 340, type: direct)
- `print` (line 342, type: direct)

### tests\test_runner.py:PrinternizerTestRunner._process_frontend_results

Calls:
- `print` (line 314, type: direct)
- `print` (line 317, type: direct)
- `print` (line 319, type: direct)
- `print` (line 320, type: direct)
- `print` (line 321, type: direct)

### tests\test_runner.py:PrinternizerTestRunner.generate_coverage_report

Calls:
- `print` (line 151, type: direct)
- `isoformat` (line 158, type: attribute)
- `now` (line 158, type: attribute)
- `exists` (line 165, type: attribute)
- `open` (line 166, type: direct)
- `load` (line 167, type: attribute)
- `get` (line 169, type: attribute)
- `get` (line 169, type: attribute)
- `get` (line 170, type: attribute)
- `get` (line 170, type: attribute)
- `get` (line 171, type: attribute)
- `get` (line 171, type: attribute)
- `get` (line 172, type: attribute)
- `get` (line 172, type: attribute)
- `get` (line 173, type: attribute)
- `get` (line 173, type: attribute)
- `exists` (line 177, type: attribute)
- `open` (line 178, type: direct)
- `load` (line 179, type: attribute)
- `get` (line 191, type: attribute)
- `get` (line 192, type: attribute)
- `get` (line 193, type: attribute)
- `get` (line 194, type: attribute)
- `open` (line 209, type: direct)
- `dump` (line 210, type: attribute)
- `print` (line 212, type: direct)
- `print` (line 216, type: direct)
- `print` (line 217, type: direct)
- `print` (line 218, type: direct)
- `get` (line 218, type: attribute)
- `print` (line 219, type: direct)
- `get` (line 219, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner.generate_test_documentation

Calls:
- `print` (line 225, type: direct)
- `_create_test_documentation` (line 227, type: attribute)
- `open` (line 230, type: direct)
- `write` (line 231, type: attribute)
- `print` (line 233, type: direct)

### tests\test_runner.py:PrinternizerTestRunner.run_backend_tests

Calls:
- `print` (line 31, type: direct)
- `extend` (line 38, type: attribute)
- `extend` (line 57, type: attribute)
- `append` (line 61, type: attribute)
- `extend` (line 64, type: attribute)
- `time` (line 71, type: attribute)
- `run` (line 72, type: attribute)
- `time` (line 73, type: attribute)
- `_process_backend_results` (line 76, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner.run_frontend_tests

Calls:
- `print` (line 82, type: direct)
- `append` (line 92, type: attribute)
- `append` (line 104, type: attribute)
- `append` (line 108, type: attribute)
- `extend` (line 111, type: attribute)
- `str` (line 112, type: direct)
- `str` (line 113, type: direct)
- `time` (line 117, type: attribute)
- `run` (line 118, type: attribute)
- `time` (line 119, type: attribute)
- `_process_frontend_results` (line 122, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner.run_full_test_suite

Calls:
- `print` (line 239, type: direct)
- `print` (line 240, type: direct)
- `now` (line 240, type: attribute)
- `print` (line 241, type: direct)
- `print` (line 242, type: direct)
- `time` (line 245, type: attribute)
- `run_backend_tests` (line 255, type: attribute)
- `run_frontend_tests` (line 259, type: attribute)
- `print` (line 262, type: direct)
- `run_performance_benchmarks` (line 266, type: attribute)
- `print` (line 269, type: direct)
- `generate_coverage_report` (line 273, type: attribute)
- `print` (line 276, type: direct)
- `generate_test_documentation` (line 280, type: attribute)
- `print` (line 283, type: direct)
- `print` (line 286, type: direct)
- `time` (line 290, type: attribute)
- `_print_final_summary` (line 294, type: attribute)

### tests\test_runner.py:PrinternizerTestRunner.run_performance_benchmarks

Calls:
- `print` (line 128, type: direct)
- `print` (line 129, type: direct)
- `time` (line 140, type: attribute)
- `run` (line 141, type: attribute)
- `time` (line 142, type: attribute)
- `_process_benchmark_results` (line 145, type: attribute)

### tests\test_runner.py:main

Calls:
- `ArgumentParser` (line 652, type: attribute)
- `add_argument` (line 653, type: attribute)
- `add_argument` (line 654, type: attribute)
- `add_argument` (line 655, type: attribute)
- `add_argument` (line 656, type: attribute)
- `add_argument` (line 658, type: attribute)
- `add_argument` (line 659, type: attribute)
- `add_argument` (line 660, type: attribute)
- `add_argument` (line 661, type: attribute)
- `add_argument` (line 662, type: attribute)
- `add_argument` (line 663, type: attribute)
- `parse_args` (line 665, type: attribute)
- `PrinternizerTestRunner` (line 667, type: direct)
- `generate_coverage_report` (line 673, type: attribute)
- `generate_test_documentation` (line 675, type: attribute)
- `run_full_test_suite` (line 677, type: attribute)
- `run_backend_tests` (line 682, type: attribute)
- `run_frontend_tests` (line 687, type: attribute)
- `run_performance_benchmarks` (line 692, type: attribute)
- `run_full_test_suite` (line 695, type: attribute)
- `print` (line 698, type: direct)
- `print` (line 701, type: direct)
- `exit` (line 705, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_clean_title

Calls:
- `_clean_title` (line 117, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_close_session

Calls:
- `AsyncMock` (line 270, type: direct)
- `close` (line 272, type: attribute)
- `assert_called_once` (line 274, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_detect_platform_makerworld

Calls:
- `detect_platform` (line 28, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_detect_platform_printables

Calls:
- `detect_platform` (line 40, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_detect_platform_thingiverse

Calls:
- `detect_platform` (line 52, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_detect_platform_unknown

Calls:
- `detect_platform` (line 64, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_extract_creator_from_title

Calls:
- `extract_creator_from_title` (line 130, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_extract_model_id_makerworld

Calls:
- `extract_model_id` (line 77, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_extract_model_id_printables

Calls:
- `extract_model_id` (line 90, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_extract_model_id_thingiverse

Calls:
- `extract_model_id` (line 103, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_fetch_page_title_no_title_tag

Calls:
- `object` (line 255, type: attribute)
- `AsyncMock` (line 256, type: direct)
- `AsyncMock` (line 257, type: direct)
- `fetch_page_title` (line 263, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_fetch_page_title_success

Calls:
- `object` (line 238, type: attribute)
- `AsyncMock` (line 239, type: direct)
- `AsyncMock` (line 240, type: direct)
- `fetch_page_title` (line 246, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_get_platform_info

Calls:
- `get_platform_info` (line 165, type: attribute)
- `isinstance` (line 167, type: direct)
- `get_platform_info` (line 173, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_get_supported_platforms

Calls:
- `get_supported_platforms` (line 156, type: attribute)
- `isinstance` (line 159, type: direct)
- `all` (line 160, type: direct)
- `len` (line 161, type: direct)
- `len` (line 161, type: direct)

### tests\test_url_parser_service.py:TestUrlParserService.test_parse_url_http_error

Calls:
- `object` (line 205, type: attribute)
- `AsyncMock` (line 206, type: direct)
- `AsyncMock` (line 207, type: direct)
- `parse_url` (line 212, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_parse_url_invalid_url

Calls:
- `parse_url` (line 225, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_parse_url_success

Calls:
- `object` (line 183, type: attribute)
- `AsyncMock` (line 184, type: direct)
- `AsyncMock` (line 185, type: direct)
- `parse_url` (line 191, type: attribute)

### tests\test_url_parser_service.py:TestUrlParserService.test_validate_url

Calls:
- `validate_url` (line 149, type: attribute)
- `validate_url` (line 152, type: attribute)

### tests\test_url_parser_service.py:url_parser

Calls:
- `UrlParserService` (line 13, type: direct)

### tests\test_working_core.py:TestConfigurationValidation.test_job_creation_and_updates

Calls:
- `JobCreate` (line 182, type: direct)
- `JobUpdate` (line 192, type: direct)

### tests\test_working_core.py:TestConfigurationValidation.test_printer_config_updates

Calls:
- `PrinterConfig` (line 168, type: direct)

### tests\test_working_core.py:TestCoreModels.test_file_model_statuses

Calls:
- `File` (line 80, type: direct)
- `File` (line 93, type: direct)

### tests\test_working_core.py:TestCoreModels.test_job_model_business_logic

Calls:
- `Job` (line 50, type: direct)
- `Job` (line 66, type: direct)

### tests\test_working_core.py:TestCoreModels.test_printer_model_creation

Calls:
- `Printer` (line 24, type: direct)
- `Printer` (line 37, type: direct)

### tests\test_working_core.py:TestGermanBusinessLogic.classify_customer

Calls:
- `any` (line 131, type: direct)

### tests\test_working_core.py:TestGermanBusinessLogic.test_business_classification

Calls:
- `classify_customer` (line 134, type: direct)
- `classify_customer` (line 135, type: direct)
- `classify_customer` (line 136, type: direct)
- `classify_customer` (line 139, type: direct)
- `classify_customer` (line 140, type: direct)
- `classify_customer` (line 141, type: direct)

### tests\test_working_core.py:TestGermanBusinessLogic.test_file_naming_german_support

Calls:
- `split` (line 154, type: attribute)

### tests\test_working_core.py:TestGermanBusinessLogic.test_vat_calculations

Calls:
- `abs` (line 124, type: direct)

### verify_phase2_integration.py:check_file_contains

Calls:
- `read_text` (line 24, type: attribute)
- `print` (line 26, type: direct)
- `print` (line 29, type: direct)
- `print` (line 32, type: direct)

### verify_phase2_integration.py:check_file_exists

Calls:
- `exists` (line 13, type: attribute)
- `stat` (line 14, type: attribute)
- `print` (line 15, type: direct)
- `print` (line 18, type: direct)

### verify_phase2_integration.py:main

Calls:
- `print` (line 37, type: direct)
- `print` (line 38, type: direct)
- `print` (line 39, type: direct)
- `print` (line 40, type: direct)
- `Path` (line 42, type: direct)
- `print` (line 46, type: direct)
- `print` (line 47, type: direct)
- `check_file_exists` (line 56, type: direct)
- `print` (line 59, type: direct)
- `print` (line 62, type: direct)
- `print` (line 63, type: direct)
- `check_file_contains` (line 72, type: direct)
- `print` (line 75, type: direct)
- `print` (line 78, type: direct)
- `print` (line 79, type: direct)
- `check_file_contains` (line 89, type: direct)
- `print` (line 92, type: direct)
- `print` (line 95, type: direct)
- `print` (line 96, type: direct)
- `check_file_contains` (line 99, type: direct)
- `print` (line 104, type: direct)
- `print` (line 107, type: direct)
- `print` (line 108, type: direct)
- `check_file_contains` (line 111, type: direct)
- `print` (line 116, type: direct)
- `print` (line 119, type: direct)
- `print` (line 120, type: direct)
- `run` (line 124, type: attribute)
- `str` (line 125, type: direct)
- `print` (line 130, type: direct)
- `print` (line 132, type: direct)
- `print` (line 135, type: direct)
- `print` (line 137, type: direct)
- `print` (line 140, type: direct)
- `print` (line 142, type: direct)
- `print` (line 143, type: direct)
- `print` (line 144, type: direct)
- `print` (line 145, type: direct)
- `print` (line 146, type: direct)
- `print` (line 147, type: direct)
- `print` (line 148, type: direct)
- `print` (line 149, type: direct)
- `print` (line 152, type: direct)

