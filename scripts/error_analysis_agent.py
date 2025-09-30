#!/usr/bin/env python3
"""
Error Analysis Agent - Automated Log Analysis and Fix Workflow
Follows the workflow established in the error analysis process
"""

import re
import sys
import argparse
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class ErrorAnalysisAgent:
    """
    Automated agent for analyzing server logs and identifying issues.

    Workflow:
    1. Read and parse log file
    2. Categorize errors (import, runtime, warnings, tracebacks)
    3. Perform root cause analysis
    4. Generate recommendations
    5. Create detailed report
    """

    def __init__(self, log_file_path):
        self.log_file_path = Path(log_file_path)
        self.lines = []
        self.error_categories = {
            'import_errors': defaultdict(list),
            'warnings': defaultdict(list),
            'errors': defaultdict(list),
            'tracebacks': [],
            'info': []
        }

        # Pattern matching
        self.patterns = {
            'module_not_found': r"ModuleNotFoundError: No module named '(\w+)'",
            'warning': r"WARNING:\s+(.+)",
            'json_error': r'"event":\s*"(Failed[^"]+)"',
            'json_warning': r'"level":\s*"warning".*"event":\s*"([^"]+)"',
        }

    def load_log(self):
        """Load log file into memory."""
        if not self.log_file_path.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_file_path}")

        with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = f.readlines()

        print(f"✓ Loaded {len(self.lines)} lines from {self.log_file_path.name}")

    def parse_errors(self):
        """Parse and categorize all errors from the log."""
        current_traceback = []
        in_traceback = False

        for i, line in enumerate(self.lines, 1):
            # Track tracebacks
            if 'Traceback (most recent call last)' in line:
                in_traceback = True
                current_traceback = [(i, line.strip())]
            elif in_traceback:
                current_traceback.append((i, line.strip()))
                # End of traceback - look for the error type
                if line.strip() and not line.startswith(' ') and 'Error' in line:
                    self.error_categories['tracebacks'].append(current_traceback)
                    in_traceback = False
                    current_traceback = []

            # ModuleNotFoundError
            match = re.search(self.patterns['module_not_found'], line)
            if match:
                module_name = match.group(1)
                self.error_categories['import_errors'][module_name].append(i)

            # Warnings
            match = re.search(self.patterns['warning'], line)
            if match:
                warning_msg = match.group(1)
                self.error_categories['warnings'][warning_msg].append(i)

            # JSON formatted errors
            match = re.search(self.patterns['json_error'], line)
            if match:
                error_msg = match.group(1)
                self.error_categories['errors'][error_msg].append(i)

            # JSON formatted warnings
            match = re.search(self.patterns['json_warning'], line)
            if match:
                warning_msg = match.group(1)
                self.error_categories['warnings'][warning_msg].append(i)

            # Info messages
            if 'INFO:' in line:
                self.error_categories['info'].append((i, line.strip()))

        print(f"✓ Parsed log and categorized errors")

    def analyze_root_cause(self):
        """Perform root cause analysis based on detected errors."""
        total_import_errors = sum(len(v) for v in self.error_categories['import_errors'].values())
        total_errors = sum(len(v) for v in self.error_categories['errors'].values())
        total_warnings = sum(len(v) for v in self.error_categories['warnings'].values())

        analysis = {
            'status': 'unknown',
            'severity': 'none',
            'issues': [],
            'recommendations': [],
            'proposed_fixes': []
        }

        if total_import_errors > 0:
            analysis['status'] = 'critical'
            analysis['severity'] = 'high'
            analysis['issues'].append({
                'type': 'import_error',
                'description': 'ModuleNotFoundError preventing server startup',
                'count': total_import_errors,
                'impact': 'Server fails to start (100% startup failure rate)'
            })
            analysis['recommendations'].extend([
                'Update run.bat to use: python -m src.main',
                "Update main.py uvicorn call to: uvicorn.run('src.main:app')",
                'Ensure PYTHONPATH includes project root'
            ])

            # Proposed automated fixes
            analysis['proposed_fixes'].append({
                'file': 'run.bat',
                'description': 'Update startup script to use module path',
                'action': 'replace_content',
                'search': 'cd src\npython main.py',
                'replace': 'set ENVIRONMENT=development\npython -m src.main'
            })
            analysis['proposed_fixes'].append({
                'file': 'src/main.py',
                'description': 'Fix uvicorn module reference',
                'action': 'replace_content',
                'search': 'uvicorn.run("main:app"',
                'replace': 'uvicorn.run("src.main:app"'
            })
        elif total_errors > 0 or total_warnings > 0:
            analysis['status'] = 'degraded'
            analysis['severity'] = 'medium' if total_errors > 0 else 'low'

            if total_errors > 0:
                for error, line_nums in self.error_categories['errors'].items():
                    analysis['issues'].append({
                        'type': 'runtime_error',
                        'description': error,
                        'count': len(line_nums),
                        'impact': 'Feature degradation, not blocking startup'
                    })
                analysis['recommendations'].append('Investigate and fix runtime errors for affected features')

            if total_warnings > 0:
                for warning, line_nums in self.error_categories['warnings'].items():
                    analysis['issues'].append({
                        'type': 'warning',
                        'description': warning,
                        'count': len(line_nums),
                        'impact': 'Minor issues, system continues to operate'
                    })
                analysis['recommendations'].append('Review warnings for potential improvements')
        else:
            analysis['status'] = 'healthy'
            analysis['severity'] = 'none'
            analysis['recommendations'].append('System is healthy - no action required!')

        return analysis

    def generate_report(self, output_format='console'):
        """Generate comprehensive error analysis report."""
        analysis = self.analyze_root_cause()

        total_import_errors = sum(len(v) for v in self.error_categories['import_errors'].values())
        total_errors = sum(len(v) for v in self.error_categories['errors'].values())
        total_warnings = sum(len(v) for v in self.error_categories['warnings'].values())
        total_tracebacks = len(self.error_categories['tracebacks'])
        total_info = len(self.error_categories['info'])

        if output_format == 'console':
            self._print_console_report(analysis, total_import_errors, total_errors,
                                      total_warnings, total_tracebacks, total_info)
        elif output_format == 'json':
            return self._generate_json_report(analysis, total_import_errors, total_errors,
                                             total_warnings, total_tracebacks, total_info)
        elif output_format == 'markdown':
            return self._generate_markdown_report(analysis, total_import_errors, total_errors,
                                                  total_warnings, total_tracebacks, total_info)

    def _print_console_report(self, analysis, total_import_errors, total_errors,
                             total_warnings, total_tracebacks, total_info):
        """Print report to console."""
        print('\n' + '='*60)
        print('ERROR ANALYSIS AGENT REPORT'.center(60))
        print('='*60 + '\n')

        # Timestamp
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log file: {self.log_file_path.name}\n")

        # Status Badge
        status_badges = {
            'healthy': '✅ HEALTHY',
            'degraded': '⚠️  DEGRADED',
            'critical': '🔴 CRITICAL'
        }
        print(f"Status: {status_badges.get(analysis['status'], '❓ UNKNOWN')}\n")

        # Import Errors
        if self.error_categories['import_errors']:
            print('🔴 IMPORT ERRORS')
            print('-' * 60)
            for module, line_nums in self.error_categories['import_errors'].items():
                print(f"  ModuleNotFoundError: No module named '{module}'")
                print(f"    Occurrences: {len(line_nums)} (lines: {', '.join(map(str, line_nums))})")
            print()

        # Runtime Errors
        if self.error_categories['errors']:
            print('❌ RUNTIME ERRORS')
            print('-' * 60)
            for error, line_nums in self.error_categories['errors'].items():
                print(f"  {error}")
                print(f"    Occurrences: {len(line_nums)} (lines: {', '.join(map(str, line_nums))})")
            print()

        # Warnings
        if self.error_categories['warnings']:
            print('⚠️  WARNINGS')
            print('-' * 60)
            for warning, line_nums in self.error_categories['warnings'].items():
                print(f"  {warning}")
                print(f"    Occurrences: {len(line_nums)} (lines: {', '.join(map(str, line_nums))})")
            print()

        # Traceback Summary
        if self.error_categories['tracebacks']:
            print('📋 TRACEBACK SUMMARY')
            print('-' * 60)
            print(f"  Total tracebacks found: {len(self.error_categories['tracebacks'])}")
            print(f"  First traceback starts at line: {self.error_categories['tracebacks'][0][0][0]}")
            print(f"  Last traceback starts at line: {self.error_categories['tracebacks'][-1][0][0]}")
            print()

        # Statistics
        print('📊 STATISTICS')
        print('-' * 60)
        print(f"  Total lines in log: {len(self.lines)}")
        print(f"  Import errors: {total_import_errors}")
        print(f"  Runtime errors: {total_errors}")
        print(f"  Warnings: {total_warnings}")
        print(f"  Tracebacks: {total_tracebacks}")
        print(f"  Info messages: {total_info}")
        print()

        # Root Cause Analysis
        print('🔍 ROOT CAUSE ANALYSIS')
        print('-' * 60)
        if analysis['issues']:
            for issue in analysis['issues']:
                print(f"  {issue['type'].upper()}: {issue['description']}")
                print(f"    Impact: {issue['impact']}")
                print()
        else:
            print("  ✅ No critical issues detected!")
            print("  Server is running cleanly without errors or warnings.")
        print()

        # Recommendations
        print('💡 RECOMMENDATIONS')
        print('-' * 60)
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
        print('\n' + '='*60 + '\n')

    def _generate_json_report(self, analysis, total_import_errors, total_errors,
                             total_warnings, total_tracebacks, total_info):
        """Generate JSON format report."""
        import json

        return json.dumps({
            'timestamp': datetime.now().isoformat(),
            'log_file': str(self.log_file_path),
            'status': analysis['status'],
            'severity': analysis['severity'],
            'statistics': {
                'total_lines': len(self.lines),
                'import_errors': total_import_errors,
                'runtime_errors': total_errors,
                'warnings': total_warnings,
                'tracebacks': total_tracebacks,
                'info_messages': total_info
            },
            'issues': analysis['issues'],
            'recommendations': analysis['recommendations']
        }, indent=2)

    def _generate_markdown_report(self, analysis, total_import_errors, total_errors,
                                  total_warnings, total_tracebacks, total_info):
        """Generate Markdown format report."""
        status_badges = {
            'healthy': '✅ HEALTHY',
            'degraded': '⚠️ DEGRADED',
            'critical': '🔴 CRITICAL'
        }

        md = f"""# Error Analysis Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Log File**: `{self.log_file_path.name}`
**Status**: {status_badges.get(analysis['status'], '❓ UNKNOWN')}

## Statistics

- Total lines: {len(self.lines)}
- Import errors: {total_import_errors}
- Runtime errors: {total_errors}
- Warnings: {total_warnings}
- Tracebacks: {total_tracebacks}
- Info messages: {total_info}

## Issues Detected

"""
        if analysis['issues']:
            for issue in analysis['issues']:
                md += f"### {issue['type'].replace('_', ' ').title()}\n\n"
                md += f"- **Description**: {issue['description']}\n"
                md += f"- **Count**: {issue['count']}\n"
                md += f"- **Impact**: {issue['impact']}\n\n"
        else:
            md += "✅ No issues detected!\n\n"

        md += "## Recommendations\n\n"
        for i, rec in enumerate(analysis['recommendations'], 1):
            md += f"{i}. {rec}\n"

        return md

    def apply_fixes(self, analysis, dry_run=True):
        """Apply proposed fixes to files (with dry-run mode)."""
        if not analysis['proposed_fixes']:
            print("\n📋 No automated fixes available for detected issues.")
            return False

        print("\n🔧 PROPOSED FIXES")
        print('='*60)

        for i, fix in enumerate(analysis['proposed_fixes'], 1):
            print(f"\n{i}. {fix['description']}")
            print(f"   File: {fix['file']}")
            print(f"   Action: {fix['action']}")

            if fix['action'] == 'replace_content':
                print(f"   Search for:")
                print(f"     {repr(fix['search'][:60])}...")
                print(f"   Replace with:")
                print(f"     {repr(fix['replace'][:60])}...")

        if dry_run:
            print("\n" + "="*60)
            print("\n⚠️  DRY RUN MODE - No files were modified")
            print("   Run with --apply-fixes to actually apply changes")
            return False

        # Prompt for confirmation
        print("\n" + "="*60)
        response = input("\n❓ Apply these fixes? (yes/no): ").strip().lower()

        if response not in ['yes', 'y']:
            print("❌ Fixes not applied - user cancelled")
            return False

        # Apply fixes
        print("\n🔧 Applying fixes...\n")
        fixes_applied = 0

        for fix in analysis['proposed_fixes']:
            try:
                file_path = Path(fix['file'])
                if not file_path.exists():
                    print(f"⚠️  Skipping {fix['file']} - file not found")
                    continue

                # Read file
                content = file_path.read_text(encoding='utf-8')

                # Apply fix
                if fix['action'] == 'replace_content':
                    if fix['search'] in content:
                        new_content = content.replace(fix['search'], fix['replace'])
                        file_path.write_text(new_content, encoding='utf-8')
                        print(f"✓ Applied fix to {fix['file']}")
                        fixes_applied += 1
                    else:
                        print(f"⚠️  Could not find search pattern in {fix['file']}")

            except Exception as e:
                print(f"❌ Error applying fix to {fix['file']}: {e}")

        print(f"\n✓ Applied {fixes_applied}/{len(analysis['proposed_fixes'])} fixes")
        return fixes_applied > 0

    def run(self, output_format='console', plan_mode=True, apply_fixes=False):
        """
        Execute the complete error analysis workflow.

        Args:
            output_format: Report format (console, json, markdown)
            plan_mode: If True, show proposed fixes without applying (default)
            apply_fixes: If True, apply fixes after user confirmation
        """
        try:
            print("\n🤖 Error Analysis Agent Starting...\n")

            if plan_mode and not apply_fixes:
                print("📋 Running in PLAN MODE - will propose fixes without applying\n")
            elif apply_fixes:
                print("🔧 Running in FIX MODE - will apply fixes after confirmation\n")

            # Step 1: Load log file
            self.load_log()

            # Step 2: Parse errors
            self.parse_errors()

            # Step 3: Analyze root cause
            analysis = self.analyze_root_cause()

            # Step 4: Generate report
            report = self.generate_report(output_format=output_format)

            if output_format != 'console':
                return report

            # Step 5: Plan mode - show proposed fixes
            if plan_mode and analysis['proposed_fixes']:
                self.apply_fixes(analysis, dry_run=not apply_fixes)

            print("\n✓ Analysis complete!")
            return analysis

        except Exception as e:
            print(f"\n❌ Error during analysis: {e}")
            raise


def main():
    """Main entry point for the error analysis agent."""
    parser = argparse.ArgumentParser(
        description='Automated Error Analysis Agent for Server Logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s server.log                    # Analyze server.log
  %(prog)s server.log -f json            # Generate JSON report
  %(prog)s server.log -f markdown -o report.md  # Save markdown report
        """
    )

    parser.add_argument('log_file', help='Path to the log file to analyze')
    parser.add_argument('-f', '--format', choices=['console', 'json', 'markdown'],
                       default='console', help='Output format (default: console)')
    parser.add_argument('-o', '--output', help='Output file path (for json/markdown formats)')

    args = parser.parse_args()

    # Create and run agent
    agent = ErrorAnalysisAgent(args.log_file)
    result = agent.run(output_format=args.format)

    # Save to file if specified
    if args.output and result:
        output_path = Path(args.output)
        output_path.write_text(result, encoding='utf-8')
        print(f"\n✓ Report saved to: {output_path}")


if __name__ == '__main__':
    main()