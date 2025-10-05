#!/usr/bin/env python3
"""
Phase 3: Usage Analysis Script
Performs deep usage pattern analysis to identify:
- Dead code chains (unused functions calling other unused functions)
- Single-use functions (candidates for inlining)
- Low-usage functions (< 3 calls)
- Redundant wrapper functions
- Legacy/deprecated functions
- Dynamic function calls and reflection usage
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter


class UsageAnalyzer:
    """Analyzes function usage patterns across the codebase"""

    def __init__(self, analysis_data_path: str, duplicate_data_path: str):
        """Load Phase 1 and Phase 2 analysis data"""
        with open(analysis_data_path, 'r') as f:
            self.phase1_data = json.load(f)

        with open(duplicate_data_path, 'r') as f:
            self.phase2_data = json.load(f)

        self.all_functions = {}  # name -> [function_info]
        self.call_graph = defaultdict(set)  # caller -> {callees}
        self.reverse_call_graph = defaultdict(set)  # callee -> {callers}
        self.function_locations = {}  # full_name -> file_info

        self._build_indices()

    def _build_indices(self):
        """Build function and call graph indices"""
        # Index all functions
        for file_data in self.phase1_data['files']:
            filepath = file_data['filepath']

            for func in file_data['functions']:
                func_info = {
                    'file': filepath,
                    **func
                }

                # Store by name
                if func['name'] not in self.all_functions:
                    self.all_functions[func['name']] = []
                self.all_functions[func['name']].append(func_info)

                # Store location
                full_key = f"{filepath}:{func['full_name']}"
                self.function_locations[full_key] = func_info

            # Build call graphs
            for call in file_data.get('function_calls', []):
                caller = f"{filepath}:{call['caller']}"
                callee = call['callee']

                self.call_graph[caller].add(callee)
                self.reverse_call_graph[callee].add(caller)

    def find_dead_code_chains(self) -> List[Dict]:
        """Find chains of unused functions that only call other unused functions"""
        unused_set = {f['function'] for f in self.phase2_data.get('unused_functions', [])}

        dead_chains = []
        visited = set()

        def find_chain(func_name: str, chain: List[str]) -> Optional[List[str]]:
            """Recursively find dead code chains"""
            if func_name in visited:
                return None

            visited.add(func_name)
            current_chain = chain + [func_name]

            # Get what this function calls
            callees = set()
            for caller_key in self.call_graph:
                if caller_key.endswith(f":{func_name}"):
                    callees.update(self.call_graph[caller_key])

            # If all callees are also unused, it's a dead chain
            if callees and callees.issubset(unused_set):
                # Continue chain
                for callee in callees:
                    sub_chain = find_chain(callee, current_chain)
                    if sub_chain:
                        return sub_chain
                return current_chain
            elif not callees:
                # Leaf node
                return current_chain

            return None

        # Find chains starting from unused functions
        for unused_func in unused_set:
            if unused_func not in visited:
                chain = find_chain(unused_func, [])
                if chain and len(chain) > 1:
                    dead_chains.append({
                        'chain': chain,
                        'length': len(chain),
                        'root': chain[0],
                        'severity': 'high' if len(chain) > 3 else 'medium'
                    })

        return sorted(dead_chains, key=lambda x: x['length'], reverse=True)

    def analyze_usage_frequency(self) -> Dict[str, List[Dict]]:
        """Categorize functions by usage frequency"""
        call_counts = Counter()

        # Count all calls
        for callees in self.call_graph.values():
            for callee in callees:
                call_counts[callee] += 1

        # Categorize
        results = {
            'unused': [],
            'single_use': [],
            'low_use': [],  # 2-3 calls
            'moderate_use': [],  # 4-10 calls
            'high_use': []  # 10+ calls
        }

        for func_name, func_list in self.all_functions.items():
            count = call_counts.get(func_name, 0)

            for func_info in func_list:
                # Skip test files, private methods, entry points
                if self._should_skip_usage_analysis(func_info):
                    continue

                entry = {
                    'function': func_info['full_name'],
                    'file': func_info['file'],
                    'line': func_info['line_start'],
                    'call_count': count,
                    'is_async': func_info['is_async'],
                    'access_level': func_info['access_level']
                }

                if count == 0:
                    results['unused'].append(entry)
                elif count == 1:
                    results['single_use'].append(entry)
                elif count <= 3:
                    results['low_use'].append(entry)
                elif count <= 10:
                    results['moderate_use'].append(entry)
                else:
                    results['high_use'].append(entry)

        return results

    def find_wrapper_functions(self) -> List[Dict]:
        """Find simple wrapper functions that just delegate to other functions"""
        wrappers = []

        for file_data in self.phase1_data['files']:
            filepath = file_data['filepath']

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()

                tree = ast.parse(source, filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if self._is_simple_wrapper(node):
                            target = self._get_wrapper_target(node)
                            wrappers.append({
                                'wrapper': node.name,
                                'file': filepath,
                                'line': node.lineno,
                                'wraps': target,
                                'type': 'async' if isinstance(node, ast.AsyncFunctionDef) else 'sync',
                                'recommendation': 'Consider inlining or documenting purpose'
                            })
            except:
                continue

        return wrappers

    def find_legacy_functions(self) -> List[Dict]:
        """Find functions marked as deprecated, TODO, or legacy"""
        legacy = []

        for file_data in self.phase1_data['files']:
            for func in file_data['functions']:
                docstring = func.get('docstring', '').lower()

                # Check for legacy markers
                markers = {
                    'deprecated': 'DEPRECATED' in docstring.upper(),
                    'todo': 'TODO' in docstring.upper() or 'FIXME' in docstring.upper(),
                    'legacy': 'legacy' in docstring,
                    'old': 'old implementation' in docstring or 'obsolete' in docstring
                }

                if any(markers.values()):
                    legacy.append({
                        'function': func['full_name'],
                        'file': file_data['filepath'],
                        'line': func['line_start'],
                        'markers': [k for k, v in markers.items() if v],
                        'docstring_snippet': docstring[:200] if docstring else '',
                        'severity': 'high' if markers['deprecated'] else 'medium'
                    })

        return legacy

    def detect_dynamic_calls(self) -> List[Dict]:
        """Detect potential dynamic function calls (getattr, eval, exec, etc.)"""
        dynamic_patterns = []

        for file_data in self.phase1_data['files']:
            filepath = file_data['filepath']

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()

                # Search for dynamic call patterns
                patterns = {
                    'getattr': r'getattr\s*\(',
                    'setattr': r'setattr\s*\(',
                    'eval': r'\beval\s*\(',
                    'exec': r'\bexec\s*\(',
                    '__import__': r'__import__\s*\(',
                    'importlib': r'importlib\.',
                    'globals()': r'globals\s*\(\)',
                    'locals()': r'locals\s*\(\)'
                }

                found_patterns = []
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, source):
                        # Find line numbers
                        lines = source.split('\n')
                        line_nums = [i+1 for i, line in enumerate(lines) if re.search(pattern, line)]
                        found_patterns.append({
                            'pattern': pattern_name,
                            'lines': line_nums[:5]  # First 5 occurrences
                        })

                if found_patterns:
                    dynamic_patterns.append({
                        'file': filepath,
                        'patterns': found_patterns,
                        'note': 'May contain dynamic function calls not detected by static analysis'
                    })
            except:
                continue

        return dynamic_patterns

    def analyze_api_endpoints(self) -> Dict[str, List[Dict]]:
        """Analyze API endpoints and their usage patterns"""
        endpoints = {
            'http': [],
            'websocket': []
        }

        for file_data in self.phase1_data['files']:
            if 'api/routers' not in file_data['filepath']:
                continue

            for func in file_data['functions']:
                decorators = ' '.join(func.get('decorators', []))

                # HTTP endpoints
                http_methods = ['@app.get', '@app.post', '@app.put', '@app.delete', '@app.patch',
                               '@router.get', '@router.post', '@router.put', '@router.delete', '@router.patch']

                for method in http_methods:
                    if method in decorators:
                        endpoints['http'].append({
                            'endpoint': func['name'],
                            'method': method.split('.')[-1].upper(),
                            'file': file_data['filepath'],
                            'line': func['line_start'],
                            'is_async': func['is_async'],
                            'decorators': func['decorators']
                        })
                        break

                # WebSocket endpoints
                if '@app.websocket' in decorators or '@router.websocket' in decorators:
                    endpoints['websocket'].append({
                        'endpoint': func['name'],
                        'file': file_data['filepath'],
                        'line': func['line_start'],
                        'is_async': func['is_async']
                    })

        return endpoints

    def identify_test_only_functions(self) -> List[Dict]:
        """Find functions only used in tests"""
        test_only = []

        for func_name, callers in self.reverse_call_graph.items():
            if not callers:
                continue

            # Check if all callers are test files
            all_test_files = all('test_' in caller or '/tests/' in caller for caller in callers)

            if all_test_files and len(callers) > 0:
                # Get function info
                func_list = self.all_functions.get(func_name, [])
                for func_info in func_list:
                    # Skip if already in test file
                    if 'test_' in func_info['file'] or '/tests/' in func_info['file']:
                        continue

                    test_only.append({
                        'function': func_info['full_name'],
                        'file': func_info['file'],
                        'line': func_info['line_start'],
                        'used_by_tests': list(callers),
                        'recommendation': 'Consider moving to test utilities'
                    })

        return test_only

    def _should_skip_usage_analysis(self, func_info: Dict) -> bool:
        """Determine if function should be skipped in usage analysis"""
        # Skip test files
        if 'test_' in func_info['file'] or '/tests/' in func_info['file']:
            return True

        # Skip dunder methods
        if func_info['access_level'] == 'dunder':
            return True

        # Skip properties
        if func_info.get('is_property'):
            return True

        # Skip likely entry points
        if func_info['name'] in ['main', 'run', 'start', 'execute']:
            return True

        return False

    def _is_simple_wrapper(self, node: ast.FunctionDef) -> bool:
        """Check if function is a simple wrapper (1-2 statements, mostly a call)"""
        # Count meaningful statements
        statements = [s for s in node.body if not isinstance(s, ast.Pass)]

        if len(statements) != 1:
            return False

        stmt = statements[0]

        # Check if it's a return statement with a call
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
            return True

        # Check if it's just a call (no return)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return True

        return False

    def _get_wrapper_target(self, node: ast.FunctionDef) -> str:
        """Get the name of the function being wrapped"""
        stmt = [s for s in node.body if not isinstance(s, ast.Pass)][0]

        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        else:
            return "unknown"

        if isinstance(call.func, ast.Name):
            return call.func.id
        elif isinstance(call.func, ast.Attribute):
            return call.func.attr

        return "unknown"


def generate_usage_report(analyzer: UsageAnalyzer, output_dir: Path):
    """Generate comprehensive usage analysis report"""

    print("Finding dead code chains...")
    dead_chains = analyzer.find_dead_code_chains()

    print("Analyzing usage frequency...")
    usage_freq = analyzer.analyze_usage_frequency()

    print("Finding wrapper functions...")
    wrappers = analyzer.find_wrapper_functions()

    print("Finding legacy/deprecated functions...")
    legacy = analyzer.find_legacy_functions()

    print("Detecting dynamic function calls...")
    dynamic_calls = analyzer.detect_dynamic_calls()

    print("Analyzing API endpoints...")
    api_endpoints = analyzer.analyze_api_endpoints()

    print("Identifying test-only functions...")
    test_only = analyzer.identify_test_only_functions()

    # Generate markdown report
    output_file = output_dir / "05_usage_analysis.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Phase 3: Usage Analysis Report\n\n")
        f.write("**Generated**: Phase 3 Analysis\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Dead Code Chains**: {len(dead_chains)}\n")
        f.write(f"- **Unused Functions**: {len(usage_freq['unused'])}\n")
        f.write(f"- **Single-Use Functions**: {len(usage_freq['single_use'])}\n")
        f.write(f"- **Low-Use Functions** (2-3 calls): {len(usage_freq['low_use'])}\n")
        f.write(f"- **Wrapper Functions**: {len(wrappers)}\n")
        f.write(f"- **Legacy/Deprecated**: {len(legacy)}\n")
        f.write(f"- **Test-Only Functions**: {len(test_only)}\n")
        f.write(f"- **Files with Dynamic Calls**: {len(dynamic_calls)}\n")
        f.write(f"- **HTTP API Endpoints**: {len(api_endpoints['http'])}\n")
        f.write(f"- **WebSocket Endpoints**: {len(api_endpoints['websocket'])}\n\n")

        # Dead Code Chains
        f.write("## 🔴 Dead Code Chains (High Priority)\n\n")
        f.write("Chains of unused functions that only call other unused functions.\n\n")

        if dead_chains:
            for chain in dead_chains[:10]:
                f.write(f"### Chain starting with `{chain['root']}` ({chain['length']} functions)\n\n")
                f.write(f"**Severity**: {chain['severity'].upper()}\n\n")
                f.write("Call chain:\n")
                for i, func in enumerate(chain['chain']):
                    indent = "  " * i
                    f.write(f"{indent}- `{func}`\n")
                f.write("\n")
        else:
            f.write("No dead code chains detected.\n\n")

        # Usage Frequency Analysis
        f.write("## 📊 Usage Frequency Analysis\n\n")

        f.write("### Unused Functions\n\n")
        f.write(f"Total: {len(usage_freq['unused'])}\n\n")
        if usage_freq['unused'][:20]:
            f.write("| Function | File | Line | Access |\n")
            f.write("|----------|------|------|--------|\n")
            for func in usage_freq['unused'][:20]:
                f.write(f"| `{func['function']}` | {func['file']} | {func['line']} | {func['access_level']} |\n")
            f.write("\n")

        f.write("### Single-Use Functions\n\n")
        f.write(f"Total: {len(usage_freq['single_use'])}\n\n")
        f.write("Functions called exactly once - candidates for inlining.\n\n")
        if usage_freq['single_use'][:15]:
            f.write("| Function | File | Line | Type |\n")
            f.write("|----------|------|------|------|\n")
            for func in usage_freq['single_use'][:15]:
                func_type = 'async' if func['is_async'] else 'sync'
                f.write(f"| `{func['function']}` | {func['file']} | {func['line']} | {func_type} |\n")
            f.write("\n")

        f.write("### Low-Use Functions (2-3 calls)\n\n")
        f.write(f"Total: {len(usage_freq['low_use'])}\n\n")
        if usage_freq['low_use'][:15]:
            f.write("| Function | File | Line | Calls |\n")
            f.write("|----------|------|------|-------|\n")
            for func in usage_freq['low_use'][:15]:
                f.write(f"| `{func['function']}` | {func['file']} | {func['line']} | {func['call_count']} |\n")
            f.write("\n")

        # Wrapper Functions
        f.write("## 🔄 Wrapper Functions\n\n")
        f.write("Simple functions that just delegate to other functions.\n\n")

        if wrappers:
            f.write("| Wrapper | Wraps | File | Line | Type |\n")
            f.write("|---------|-------|------|------|------|\n")
            for wrapper in wrappers[:20]:
                f.write(f"| `{wrapper['wrapper']}` | `{wrapper['wraps']}` | {wrapper['file']} | {wrapper['line']} | {wrapper['type']} |\n")
            f.write("\n")
        else:
            f.write("No simple wrapper functions detected.\n\n")

        # Legacy/Deprecated Functions
        f.write("## ⚠️ Legacy/Deprecated Functions\n\n")
        f.write("Functions marked as deprecated, TODO, or legacy in docstrings.\n\n")

        if legacy:
            for func in legacy:
                f.write(f"### `{func['function']}`\n\n")
                f.write(f"**File**: {func['file']}:{func['line']}\n\n")
                f.write(f"**Markers**: {', '.join(func['markers'])}\n\n")
                f.write(f"**Severity**: {func['severity'].upper()}\n\n")
                if func['docstring_snippet']:
                    f.write(f"**Docstring**: {func['docstring_snippet']}\n\n")
        else:
            f.write("No legacy/deprecated functions found.\n\n")

        # Test-Only Functions
        f.write("## 🧪 Test-Only Functions\n\n")
        f.write("Functions in production code only called by tests.\n\n")

        if test_only:
            f.write("| Function | File | Line | Used By |\n")
            f.write("|----------|------|------|----------|\n")
            for func in test_only[:15]:
                used_by = f"{len(func['used_by_tests'])} tests"
                f.write(f"| `{func['function']}` | {func['file']} | {func['line']} | {used_by} |\n")
            f.write("\n")
        else:
            f.write("No test-only functions detected.\n\n")

        # Dynamic Calls
        f.write("## 🔮 Dynamic Function Calls\n\n")
        f.write("Files containing dynamic calls (getattr, eval, etc.) that may hide function usage.\n\n")

        if dynamic_calls:
            for item in dynamic_calls:
                f.write(f"### {item['file']}\n\n")
                for pattern in item['patterns']:
                    lines_str = ', '.join(map(str, pattern['lines']))
                    f.write(f"- **{pattern['pattern']}**: lines {lines_str}\n")
                f.write(f"\n*{item['note']}*\n\n")
        else:
            f.write("No dynamic function calls detected.\n\n")

        # API Endpoints
        f.write("## 🌐 API Endpoints Inventory\n\n")

        f.write("### HTTP Endpoints\n\n")
        f.write(f"Total: {len(api_endpoints['http'])}\n\n")
        if api_endpoints['http']:
            f.write("| Endpoint | Method | File | Line | Async |\n")
            f.write("|----------|--------|------|------|-------|\n")
            for ep in api_endpoints['http']:
                async_str = 'Yes' if ep['is_async'] else 'No'
                f.write(f"| `{ep['endpoint']}` | {ep['method']} | {ep['file']} | {ep['line']} | {async_str} |\n")
            f.write("\n")

        f.write("### WebSocket Endpoints\n\n")
        f.write(f"Total: {len(api_endpoints['websocket'])}\n\n")
        if api_endpoints['websocket']:
            f.write("| Endpoint | File | Line |\n")
            f.write("|----------|------|------|\n")
            for ep in api_endpoints['websocket']:
                f.write(f"| `{ep['endpoint']}` | {ep['file']} | {ep['line']} |\n")
            f.write("\n")

        # Usage Statistics
        f.write("## 📈 Usage Distribution\n\n")
        f.write("| Category | Count | Percentage |\n")
        f.write("|----------|-------|------------|\n")

        total_analyzed = sum(len(v) for v in usage_freq.values())
        for category, funcs in usage_freq.items():
            pct = (len(funcs) / total_analyzed * 100) if total_analyzed > 0 else 0
            f.write(f"| {category.replace('_', ' ').title()} | {len(funcs)} | {pct:.1f}% |\n")
        f.write("\n")

    # Save raw usage data
    with open(output_dir / "usage_analysis_raw.json", 'w') as f:
        json.dump({
            'dead_chains': dead_chains,
            'usage_frequency': usage_freq,
            'wrappers': wrappers,
            'legacy_functions': legacy,
            'dynamic_calls': dynamic_calls,
            'api_endpoints': api_endpoints,
            'test_only_functions': test_only
        }, f, indent=2)

    return {
        'dead_chains': len(dead_chains),
        'unused': len(usage_freq['unused']),
        'single_use': len(usage_freq['single_use']),
        'low_use': len(usage_freq['low_use']),
        'wrappers': len(wrappers),
        'legacy': len(legacy),
        'test_only': len(test_only),
        'dynamic_files': len(dynamic_calls),
        'http_endpoints': len(api_endpoints['http']),
        'websocket_endpoints': len(api_endpoints['websocket'])
    }


def main():
    """Main execution for Phase 3"""
    print("Phase 3: Usage Analysis Starting...")
    print("=" * 60)

    # Load data
    phase1_file = Path("docs/development/cleanup/function_analysis_raw.json")
    phase2_file = Path("docs/development/cleanup/duplicate_analysis_raw.json")

    if not phase1_file.exists():
        print(f"Error: Phase 1 data not found at {phase1_file}")
        return

    if not phase2_file.exists():
        print(f"Error: Phase 2 data not found at {phase2_file}")
        return

    # Initialize analyzer
    print(f"\nLoading analysis data...")
    analyzer = UsageAnalyzer(str(phase1_file), str(phase2_file))
    print(f"Loaded {len(analyzer.all_functions)} unique function names")

    # Generate reports
    output_dir = Path("docs/development/cleanup")
    print(f"\nGenerating usage analysis reports...")
    stats = generate_usage_report(analyzer, output_dir)

    # Summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 3: Usage Analysis Complete!")
    print("=" * 60)
    print(f"\nFindings:")
    print(f"  - Dead code chains: {stats['dead_chains']}")
    print(f"  - Unused functions: {stats['unused']}")
    print(f"  - Single-use functions: {stats['single_use']}")
    print(f"  - Low-use functions: {stats['low_use']}")
    print(f"  - Wrapper functions: {stats['wrappers']}")
    print(f"  - Legacy/deprecated: {stats['legacy']}")
    print(f"  - Test-only functions: {stats['test_only']}")
    print(f"  - Files with dynamic calls: {stats['dynamic_files']}")
    print(f"  - HTTP endpoints: {stats['http_endpoints']}")
    print(f"  - WebSocket endpoints: {stats['websocket_endpoints']}")
    print(f"\nReports saved to: {output_dir}")
    print(f"  - 05_usage_analysis.md")
    print(f"  - usage_analysis_raw.json")


if __name__ == "__main__":
    main()
