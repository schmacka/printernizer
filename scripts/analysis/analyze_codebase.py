#!/usr/bin/env python3
"""
Codebase Function Analysis Script
Performs comprehensive AST-based analysis of all Python files to extract:
- Function definitions with signatures, decorators, docstrings
- Function calls and dependencies
- Import relationships
- Entry points
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re


class FunctionAnalyzer(ast.NodeVisitor):
    """AST visitor to extract function information and dependencies"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions = []
        self.imports = []
        self.function_calls = []
        self.current_function = None
        self.current_class = None

    def visit_Import(self, node):
        """Track import statements"""
        for alias in node.names:
            self.imports.append({
                'type': 'import',
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from...import statements"""
        module = node.module or ''
        for alias in node.names:
            self.imports.append({
                'type': 'from_import',
                'module': module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Track class context for methods"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Extract function definition information"""
        # Build signature
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Get decorators
        decorators = [ast.unparse(dec) for dec in node.decorator_list]

        # Get docstring
        docstring = ast.get_docstring(node) or ""

        # Get return annotation
        return_annotation = ""
        if node.returns:
            return_annotation = ast.unparse(node.returns)

        # Determine access level
        is_private = node.name.startswith('_') and not node.name.startswith('__')
        is_dunder = node.name.startswith('__') and node.name.endswith('__')
        access_level = 'dunder' if is_dunder else ('private' if is_private else 'public')

        # Determine if it's a method
        is_method = self.current_class is not None

        function_info = {
            'name': node.name,
            'full_name': f"{self.current_class}.{node.name}" if self.current_class else node.name,
            'class': self.current_class,
            'signature': f"({', '.join(args)})",
            'return_type': return_annotation,
            'decorators': decorators,
            'docstring': docstring,
            'line_start': node.lineno,
            'line_end': node.end_lineno,
            'access_level': access_level,
            'is_method': is_method,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'is_property': 'property' in decorators,
            'is_staticmethod': 'staticmethod' in decorators,
            'is_classmethod': 'classmethod' in decorators,
        }

        self.functions.append(function_info)

        # Track function calls within this function
        old_function = self.current_function
        self.current_function = function_info['full_name']
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        """Handle async functions"""
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        """Track function calls"""
        if self.current_function:
            # Try to extract the function name being called
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                self.function_calls.append({
                    'caller': self.current_function,
                    'callee': func_name,
                    'line': node.lineno,
                    'type': 'direct'
                })
            elif isinstance(node.func, ast.Attribute):
                # Handle method calls like obj.method()
                attr_name = node.func.attr
                self.function_calls.append({
                    'caller': self.current_function,
                    'callee': attr_name,
                    'line': node.lineno,
                    'type': 'attribute'
                })
        self.generic_visit(node)


def analyze_file(filepath: str) -> Dict:
    """Analyze a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=filepath)
        analyzer = FunctionAnalyzer(filepath)
        analyzer.visit(tree)

        return {
            'filepath': filepath,
            'functions': analyzer.functions,
            'imports': analyzer.imports,
            'function_calls': analyzer.function_calls,
            'error': None
        }
    except Exception as e:
        return {
            'filepath': filepath,
            'functions': [],
            'imports': [],
            'function_calls': [],
            'error': str(e)
        }


def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files excluding venv and .git"""
    python_files = []
    root_path = Path(root_dir)

    for py_file in root_path.rglob('*.py'):
        # Skip virtual environments and .git
        if any(part in py_file.parts for part in ['.venv', 'venv', '.git', '__pycache__']):
            continue
        python_files.append(str(py_file))

    return sorted(python_files)


def build_dependency_graph(all_results: List[Dict]) -> Dict:
    """Build function call dependency graph"""
    graph = defaultdict(list)

    for result in all_results:
        for call in result['function_calls']:
            caller = f"{result['filepath']}:{call['caller']}"
            callee = call['callee']
            graph[caller].append({
                'callee': callee,
                'line': call['line'],
                'type': call['type']
            })

    return dict(graph)


def find_entry_points(all_results: List[Dict]) -> List[Dict]:
    """Identify entry points in the codebase"""
    entry_points = []

    for result in all_results:
        filepath = result['filepath']

        # Check for main execution
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            content = ""

        if '__main__' in content:
            entry_points.append({
                'type': 'main',
                'file': filepath,
                'description': 'Script entry point (__main__)'
            })

        # Check for FastAPI routes
        for func in result['functions']:
            decorators = ' '.join(func['decorators'])
            if any(pattern in decorators for pattern in ['@app.', '@router.', '@get', '@post', '@put', '@delete', '@patch']):
                entry_points.append({
                    'type': 'api_endpoint',
                    'file': filepath,
                    'function': func['full_name'],
                    'line': func['line_start'],
                    'decorators': func['decorators']
                })

        # Check for CLI commands
        if 'click.command' in ' '.join(str(func['decorators']) for func in result['functions']):
            entry_points.append({
                'type': 'cli',
                'file': filepath,
                'description': 'CLI command'
            })

    return entry_points


def generate_function_inventory_report(all_results: List[Dict], output_file: str):
    """Generate markdown report of all functions"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Function Inventory Report\n\n")
        f.write(f"Generated: {Path(output_file).stat().st_mtime}\n\n")

        # Summary
        total_functions = sum(len(r['functions']) for r in all_results)
        total_files = len(all_results)
        f.write(f"## Summary\n\n")
        f.write(f"- Total Python files analyzed: {total_files}\n")
        f.write(f"- Total functions found: {total_functions}\n\n")

        # By file
        f.write("## Functions by File\n\n")
        for result in all_results:
            if result['error']:
                f.write(f"### {result['filepath']} ⚠️ ERROR\n")
                f.write(f"Error: {result['error']}\n\n")
                continue

            if not result['functions']:
                continue

            f.write(f"### {result['filepath']}\n\n")
            f.write(f"Functions: {len(result['functions'])}\n\n")

            f.write("| Function | Type | Access | Line | Signature | Decorators |\n")
            f.write("|----------|------|--------|------|-----------|------------|\n")

            for func in result['functions']:
                func_type = 'async' if func['is_async'] else 'method' if func['is_method'] else 'function'
                decorators = ', '.join(func['decorators']) if func['decorators'] else '-'
                f.write(f"| `{func['full_name']}` | {func_type} | {func['access_level']} | "
                       f"{func['line_start']} | `{func['signature']}` | {decorators} |\n")

            f.write("\n")

        # Statistics by category
        f.write("## Statistics\n\n")

        public_count = sum(1 for r in all_results for f in r['functions'] if f['access_level'] == 'public')
        private_count = sum(1 for r in all_results for f in r['functions'] if f['access_level'] == 'private')
        dunder_count = sum(1 for r in all_results for f in r['functions'] if f['access_level'] == 'dunder')

        f.write(f"- Public functions: {public_count}\n")
        f.write(f"- Private functions: {private_count}\n")
        f.write(f"- Dunder methods: {dunder_count}\n\n")

        async_count = sum(1 for r in all_results for func in r['functions'] if func['is_async'])
        property_count = sum(1 for r in all_results for func in r['functions'] if func['is_property'])
        static_count = sum(1 for r in all_results for func in r['functions'] if func['is_staticmethod'])

        f.write(f"- Async functions: {async_count}\n")
        f.write(f"- Properties: {property_count}\n")
        f.write(f"- Static methods: {static_count}\n")


def generate_dependency_report(dependency_graph: Dict, output_file: str):
    """Generate dependency analysis report"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Function Dependency Analysis\n\n")

        f.write(f"## Summary\n\n")
        f.write(f"- Total functions with dependencies: {len(dependency_graph)}\n")
        f.write(f"- Total dependency relationships: {sum(len(v) for v in dependency_graph.values())}\n\n")

        f.write("## Dependency Graph\n\n")
        for caller, callees in sorted(dependency_graph.items()):
            f.write(f"### {caller}\n\n")
            f.write("Calls:\n")
            for callee in callees:
                f.write(f"- `{callee['callee']}` (line {callee['line']}, type: {callee['type']})\n")
            f.write("\n")


def generate_entry_points_report(entry_points: List[Dict], output_file: str):
    """Generate entry points report"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Entry Points Analysis\n\n")

        f.write(f"## Summary\n\n")
        f.write(f"- Total entry points found: {len(entry_points)}\n\n")

        # Group by type
        by_type = defaultdict(list)
        for ep in entry_points:
            by_type[ep['type']].append(ep)

        for ep_type, eps in sorted(by_type.items()):
            f.write(f"## {ep_type.upper()} Entry Points\n\n")
            f.write(f"Count: {len(eps)}\n\n")

            for ep in eps:
                f.write(f"### {ep['file']}\n")
                if 'function' in ep:
                    f.write(f"- Function: `{ep['function']}` (line {ep['line']})\n")
                if 'decorators' in ep:
                    f.write(f"- Decorators: {', '.join(ep['decorators'])}\n")
                if 'description' in ep:
                    f.write(f"- Description: {ep['description']}\n")
                f.write("\n")


def main():
    """Main analysis execution"""
    print("Starting codebase analysis...")

    # Find all Python files
    root_dir = "."
    python_files = find_python_files(root_dir)
    print(f"Found {len(python_files)} Python files")

    # Analyze each file
    all_results = []
    for i, filepath in enumerate(python_files, 1):
        print(f"Analyzing [{i}/{len(python_files)}]: {filepath}")
        result = analyze_file(filepath)
        all_results.append(result)

    # Build dependency graph
    print("Building dependency graph...")
    dependency_graph = build_dependency_graph(all_results)

    # Find entry points
    print("Identifying entry points...")
    entry_points = find_entry_points(all_results)

    # Save raw JSON data
    output_dir = Path("docs/development/cleanup")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Saving raw data...")
    with open(output_dir / "function_analysis_raw.json", 'w') as f:
        json.dump({
            'files': all_results,
            'dependency_graph': dependency_graph,
            'entry_points': entry_points
        }, f, indent=2)

    # Generate reports
    print("Generating reports...")
    generate_function_inventory_report(all_results, output_dir / "01_function_inventory.md")
    generate_dependency_report(dependency_graph, output_dir / "02_dependency_analysis.md")
    generate_entry_points_report(entry_points, output_dir / "03_entry_points.md")

    print(f"\n[SUCCESS] Analysis complete!")
    print(f"Reports saved to: {output_dir}")
    print(f"- Function Inventory: 01_function_inventory.md")
    print(f"- Dependency Analysis: 02_dependency_analysis.md")
    print(f"- Entry Points: 03_entry_points.md")
    print(f"- Raw JSON data: function_analysis_raw.json")


if __name__ == "__main__":
    main()
