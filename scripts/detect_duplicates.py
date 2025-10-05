#!/usr/bin/env python3
"""
Phase 2: Duplicate Detection Script
Analyzes the codebase to identify duplicate and similar functions using:
- Exact name matching across files
- Similar name pattern detection
- Signature similarity analysis
- Code structure similarity (AST-based)
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib


class CodeSimilarityAnalyzer:
    """Analyzes code similarity using multiple techniques"""

    def __init__(self, analysis_data_path: str):
        """Load the Phase 1 analysis data"""
        with open(analysis_data_path, 'r') as f:
            self.data = json.load(f)

        self.all_functions = []
        self.functions_by_name = defaultdict(list)
        self.functions_by_signature = defaultdict(list)
        self._index_functions()

    def _index_functions(self):
        """Build indexes for quick lookup"""
        for file_data in self.data['files']:
            filepath = file_data['filepath']
            for func in file_data['functions']:
                func_info = {
                    'file': filepath,
                    **func
                }
                self.all_functions.append(func_info)

                # Index by name
                self.functions_by_name[func['name']].append(func_info)

                # Index by signature
                sig_key = f"{func['name']}{func['signature']}"
                self.functions_by_signature[sig_key].append(func_info)

    def find_exact_name_duplicates(self) -> List[Dict]:
        """Find functions with exact same name in different files"""
        duplicates = []

        for name, funcs in self.functions_by_name.items():
            if len(funcs) > 1:
                # Filter out methods from same class (not duplicates)
                unique_locations = {}
                for func in funcs:
                    key = f"{func['file']}:{func.get('class', '')}"
                    if key not in unique_locations:
                        unique_locations[key] = func

                if len(unique_locations) > 1:
                    duplicates.append({
                        'type': 'exact_name',
                        'name': name,
                        'count': len(unique_locations),
                        'locations': list(unique_locations.values()),
                        'severity': 'high' if not name.startswith('_') else 'medium'
                    })

        return sorted(duplicates, key=lambda x: x['count'], reverse=True)

    def find_similar_names(self, threshold: float = 0.8) -> List[Dict]:
        """Find functions with similar names using fuzzy matching"""
        similar_groups = []
        processed = set()

        function_names = [f for f in self.all_functions if f['access_level'] == 'public']

        for i, func1 in enumerate(function_names):
            if func1['full_name'] in processed:
                continue

            similar = [func1]
            for func2 in function_names[i+1:]:
                if func2['full_name'] in processed:
                    continue

                # Skip if same file
                if func1['file'] == func2['file']:
                    continue

                # Calculate name similarity
                similarity = self._name_similarity(func1['name'], func2['name'])

                if similarity >= threshold:
                    similar.append(func2)
                    processed.add(func2['full_name'])

            if len(similar) > 1:
                processed.add(func1['full_name'])
                similar_groups.append({
                    'type': 'similar_names',
                    'pattern': self._extract_common_pattern([f['name'] for f in similar]),
                    'count': len(similar),
                    'functions': similar,
                    'severity': 'medium'
                })

        return sorted(similar_groups, key=lambda x: x['count'], reverse=True)

    def find_identical_signatures(self) -> List[Dict]:
        """Find functions with identical signatures but different names"""
        duplicates = []

        for sig_key, funcs in self.functions_by_signature.items():
            if len(funcs) > 1:
                duplicates.append({
                    'type': 'identical_signature',
                    'signature': funcs[0]['signature'],
                    'return_type': funcs[0].get('return_type', ''),
                    'count': len(funcs),
                    'functions': funcs,
                    'severity': 'low'
                })

        return sorted(duplicates, key=lambda x: x['count'], reverse=True)

    def analyze_code_structure_similarity(self, file_path: str) -> Dict:
        """Analyze AST structure similarity for functions in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            function_hashes = {}

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Create simplified AST hash (structure-based)
                    structure_hash = self._hash_ast_structure(node)
                    function_hashes[node.name] = structure_hash

            return function_hashes
        except:
            return {}

    def find_structural_duplicates(self, min_group_size: int = 2) -> List[Dict]:
        """Find functions with similar AST structures"""
        structure_groups = defaultdict(list)

        # Group files by directory for focused analysis
        files_by_dir = defaultdict(list)
        for file_data in self.data['files']:
            dir_path = str(Path(file_data['filepath']).parent)
            files_by_dir[dir_path].append(file_data['filepath'])

        # Analyze each directory
        for dir_path, files in files_by_dir.items():
            for filepath in files:
                hashes = self.analyze_code_structure_similarity(filepath)
                for func_name, struct_hash in hashes.items():
                    structure_groups[struct_hash].append({
                        'file': filepath,
                        'function': func_name
                    })

        # Find groups with duplicates
        duplicates = []
        for struct_hash, funcs in structure_groups.items():
            if len(funcs) >= min_group_size:
                # Filter out same file
                unique_files = {}
                for func in funcs:
                    if func['file'] not in unique_files:
                        unique_files[func['file']] = []
                    unique_files[func['file']].append(func['function'])

                if len(unique_files) > 1:
                    duplicates.append({
                        'type': 'structural_similarity',
                        'structure_hash': struct_hash[:8],
                        'count': len(funcs),
                        'functions': funcs,
                        'severity': 'high'
                    })

        return sorted(duplicates, key=lambda x: x['count'], reverse=True)

    def find_single_use_functions(self) -> List[Dict]:
        """Find functions that are only called once (candidates for inlining)"""
        # Build call count map
        call_counts = defaultdict(int)

        for file_data in self.data['files']:
            for call in file_data.get('function_calls', []):
                call_counts[call['callee']] += 1

        single_use = []
        for func in self.all_functions:
            if func['access_level'] == 'public' and not func['is_method']:
                count = call_counts.get(func['name'], 0)
                if count == 1:
                    single_use.append({
                        'function': func['full_name'],
                        'file': func['file'],
                        'line': func['line_start'],
                        'signature': func['signature'],
                        'call_count': count
                    })

        return single_use

    def find_unused_functions(self) -> List[Dict]:
        """Find functions that appear to be unused"""
        # Build set of all called functions
        called_functions = set()

        for file_data in self.data['files']:
            for call in file_data.get('function_calls', []):
                called_functions.add(call['callee'])

        # Find functions that are never called
        unused = []
        for func in self.all_functions:
            # Skip private functions, test functions, and special methods
            if func['access_level'] == 'private':
                continue
            if func['access_level'] == 'dunder':
                continue
            if 'test_' in func['file']:
                continue
            if func['is_property'] or func['is_staticmethod'] or func['is_classmethod']:
                continue

            # Check if it's called
            if func['name'] not in called_functions:
                # Double-check it's not an entry point or API endpoint
                if not self._is_likely_entry_point(func):
                    unused.append({
                        'function': func['full_name'],
                        'file': func['file'],
                        'line': func['line_start'],
                        'signature': func['signature'],
                        'is_async': func['is_async'],
                        'decorators': func.get('decorators', [])
                    })

        return unused

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two function names"""
        # Normalize names (remove underscores, convert to lowercase)
        n1 = name1.lower().replace('_', '')
        n2 = name2.lower().replace('_', '')

        return SequenceMatcher(None, n1, n2).ratio()

    def _extract_common_pattern(self, names: List[str]) -> str:
        """Extract common pattern from similar names"""
        if not names:
            return ""

        # Find longest common substring
        common = names[0]
        for name in names[1:]:
            matcher = SequenceMatcher(None, common, name)
            match = matcher.find_longest_match(0, len(common), 0, len(name))
            if match.size > 0:
                common = common[match.a:match.a + match.size]

        return common if len(common) > 3 else f"[{', '.join(names[:3])}...]"

    def _hash_ast_structure(self, node: ast.AST) -> str:
        """Create a hash of AST structure (ignoring variable names)"""
        def serialize_node(n):
            if isinstance(n, ast.AST):
                # Include node type but not names/values
                fields = []
                for field, value in ast.iter_fields(n):
                    if field in ['name', 'id', 'arg', 'attr', 's', 'n']:
                        continue  # Skip identifiers and literals
                    fields.append(serialize_node(value))
                return f"{n.__class__.__name__}({','.join(fields)})"
            elif isinstance(n, list):
                return f"[{','.join(serialize_node(item) for item in n)}]"
            else:
                return str(type(n).__name__)

        structure = serialize_node(node)
        return hashlib.md5(structure.encode()).hexdigest()

    def _is_likely_entry_point(self, func: Dict) -> bool:
        """Check if function is likely an entry point"""
        # Check for main
        if func['name'] == 'main':
            return True

        # Check for common decorator patterns
        decorators = ' '.join(func.get('decorators', []))

        # FastAPI/API endpoints
        api_patterns = [
            '@app.', '@router.',
            '@get', '@post', '@put', '@delete', '@patch',
            '.get(', '.post(', '.put(', '.delete(', '.patch(',
            'websocket'
        ]
        if any(pattern in decorators.lower() for pattern in api_patterns):
            return True

        # CLI commands
        if '@click' in decorators:
            return True

        # API routers - also check file path
        if 'api/routers' in func.get('file', '') or 'api\\routers' in func.get('file', ''):
            return True

        return False


def generate_duplicate_report(analyzer: CodeSimilarityAnalyzer, output_dir: Path):
    """Generate comprehensive duplicate detection report"""

    print("Finding exact name duplicates...")
    exact_duplicates = analyzer.find_exact_name_duplicates()

    print("Finding similar names...")
    similar_names = analyzer.find_similar_names(threshold=0.75)

    print("Finding identical signatures...")
    identical_sigs = analyzer.find_identical_signatures()

    print("Finding structural duplicates...")
    structural_dups = analyzer.find_structural_duplicates()

    print("Finding single-use functions...")
    single_use = analyzer.find_single_use_functions()

    print("Finding unused functions...")
    unused = analyzer.find_unused_functions()

    # Generate markdown report
    output_file = output_dir / "04_duplicate_detection.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Phase 2: Duplicate Detection Report\n\n")
        f.write("**Generated**: Phase 2 Analysis\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Exact Name Duplicates**: {len(exact_duplicates)}\n")
        f.write(f"- **Similar Name Groups**: {len(similar_names)}\n")
        f.write(f"- **Identical Signature Groups**: {len(identical_sigs)}\n")
        f.write(f"- **Structural Duplicates**: {len(structural_dups)}\n")
        f.write(f"- **Single-Use Functions**: {len(single_use)}\n")
        f.write(f"- **Potentially Unused Functions**: {len(unused)}\n\n")

        # Exact Name Duplicates
        f.write("## 🔴 Exact Name Duplicates (High Priority)\n\n")
        f.write("Functions with identical names in different files.\n\n")

        if exact_duplicates:
            for dup in exact_duplicates[:20]:  # Top 20
                f.write(f"### `{dup['name']}` ({dup['count']} occurrences)\n\n")
                f.write(f"**Severity**: {dup['severity'].upper()}\n\n")
                f.write("| File | Line | Signature | Class | Access |\n")
                f.write("|------|------|-----------|-------|--------|\n")
                for loc in dup['locations']:
                    class_name = loc.get('class', '-')
                    f.write(f"| {loc['file']} | {loc['line_start']} | `{loc['signature']}` | {class_name} | {loc['access_level']} |\n")
                f.write("\n")
        else:
            f.write("No exact name duplicates found.\n\n")

        # Similar Names
        f.write("## 🟡 Similar Name Patterns (Medium Priority)\n\n")
        f.write("Functions with similar names that may indicate duplicate functionality.\n\n")

        if similar_names:
            for group in similar_names[:15]:  # Top 15
                f.write(f"### Pattern: `{group['pattern']}` ({group['count']} functions)\n\n")
                f.write("| Function | File | Line |\n")
                f.write("|----------|------|------|\n")
                for func in group['functions']:
                    f.write(f"| `{func['name']}` | {func['file']} | {func['line_start']} |\n")
                f.write("\n")
        else:
            f.write("No similar name patterns found.\n\n")

        # Identical Signatures
        f.write("## 🟠 Identical Signatures (Low Priority)\n\n")
        f.write("Functions with same signatures but different names.\n\n")

        if identical_sigs:
            for sig in identical_sigs[:10]:  # Top 10
                f.write(f"### Signature: `{sig['signature']}`\n\n")
                f.write("| Function | File | Line |\n")
                f.write("|----------|------|------|\n")
                for func in sig['functions']:
                    f.write(f"| `{func['full_name']}` | {func['file']} | {func['line_start']} |\n")
                f.write("\n")
        else:
            f.write("No identical signature groups found.\n\n")

        # Structural Duplicates
        f.write("## 🔴 Structural Duplicates (High Priority)\n\n")
        f.write("Functions with similar AST structures indicating duplicate logic.\n\n")

        if structural_dups:
            for dup in structural_dups[:10]:  # Top 10
                f.write(f"### Structure Hash: `{dup['structure_hash']}` ({dup['count']} functions)\n\n")
                f.write("| Function | File |\n")
                f.write("|----------|------|\n")
                for func in dup['functions']:
                    f.write(f"| `{func['function']}` | {func['file']} |\n")
                f.write("\n")
        else:
            f.write("No structural duplicates found.\n\n")

        # Single-Use Functions
        f.write("## 📊 Single-Use Functions\n\n")
        f.write("Functions called only once - candidates for inlining.\n\n")

        if single_use:
            f.write("| Function | File | Line | Signature |\n")
            f.write("|----------|------|------|----------|\n")
            for func in single_use[:30]:  # Top 30
                f.write(f"| `{func['function']}` | {func['file']} | {func['line']} | `{func['signature']}` |\n")
            f.write("\n")
        else:
            f.write("No single-use functions found.\n\n")

        # Unused Functions
        f.write("## 🗑️ Potentially Unused Functions\n\n")
        f.write("Functions that appear to have no callers in the codebase.\n\n")
        f.write("**Note**: May include entry points, API endpoints, or dynamically called functions.\n\n")

        if unused:
            f.write("| Function | File | Line | Async | Decorators |\n")
            f.write("|----------|------|------|-------|------------|\n")
            for func in unused[:50]:  # Top 50
                is_async = 'Yes' if func['is_async'] else 'No'
                decorators = ', '.join(func['decorators']) if func['decorators'] else '-'
                f.write(f"| `{func['function']}` | {func['file']} | {func['line']} | {is_async} | {decorators} |\n")
            f.write("\n")
        else:
            f.write("No unused functions detected.\n\n")

    # Save raw duplicate data
    with open(output_dir / "duplicate_analysis_raw.json", 'w') as f:
        json.dump({
            'exact_duplicates': exact_duplicates,
            'similar_names': similar_names,
            'identical_signatures': identical_sigs,
            'structural_duplicates': structural_dups,
            'single_use_functions': single_use,
            'unused_functions': unused
        }, f, indent=2)

    return {
        'exact_duplicates': len(exact_duplicates),
        'similar_names': len(similar_names),
        'identical_signatures': len(identical_sigs),
        'structural_duplicates': len(structural_dups),
        'single_use': len(single_use),
        'unused': len(unused)
    }


def main():
    """Main execution for Phase 2"""
    print("Phase 2: Duplicate Detection Starting...")
    print("=" * 60)

    # Load Phase 1 data
    analysis_file = Path("docs/development/cleanup/function_analysis_raw.json")
    if not analysis_file.exists():
        print(f"Error: Phase 1 analysis data not found at {analysis_file}")
        print("Please run Phase 1 analysis first (scripts/analyze_codebase.py)")
        return

    # Initialize analyzer
    print(f"\nLoading Phase 1 data from {analysis_file}...")
    analyzer = CodeSimilarityAnalyzer(str(analysis_file))
    print(f"Loaded {len(analyzer.all_functions)} functions from {len(analyzer.data['files'])} files")

    # Generate reports
    output_dir = Path("docs/development/cleanup")
    print(f"\nGenerating duplicate detection reports...")
    stats = generate_duplicate_report(analyzer, output_dir)

    # Summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 2: Duplicate Detection Complete!")
    print("=" * 60)
    print(f"\nFindings:")
    print(f"  - Exact name duplicates: {stats['exact_duplicates']}")
    print(f"  - Similar name groups: {stats['similar_names']}")
    print(f"  - Identical signatures: {stats['identical_signatures']}")
    print(f"  - Structural duplicates: {stats['structural_duplicates']}")
    print(f"  - Single-use functions: {stats['single_use']}")
    print(f"  - Potentially unused: {stats['unused']}")
    print(f"\nReports saved to: {output_dir}")
    print(f"  - 04_duplicate_detection.md")
    print(f"  - duplicate_analysis_raw.json")


if __name__ == "__main__":
    main()
