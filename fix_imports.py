#!/usr/bin/env python3
"""Fix all imports in src directory to use src. prefix"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single Python file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix standard imports
    patterns = [
        (r'^from (api|database|services|utils|models|printers)\.', r'from src.\1.'),
        (r'^from (api|database|services|utils|models|printers) import', r'from src.\1 import'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in: {filepath}")
        return True
    return False

def main():
    src_dir = Path(__file__).parent / 'src'
    fixed_count = 0

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                if fix_imports_in_file(filepath):
                    fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()