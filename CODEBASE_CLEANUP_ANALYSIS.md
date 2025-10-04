# Codebase Cleanup Analysis Guide

## Overview
This document provides a systematic approach to identify and clean up duplicate and unused functions in the Printernizer codebase. The analysis is divided into four phases to ensure thorough coverage and minimize the risk of breaking changes.

Document everything in /docs/development/cleanup

## Phase 1: Inventory and Mapping

### 1.1 Create Function Inventory
**Objective:** Build a comprehensive catalog of all functions in the codebase

**Tasks:**
- [ ] Scan all Python files in `src/`, `scripts/`, `tests/` directories
- [ ] Extract function definitions with:
  - Function name and signature
  - File path and line number
  - Docstring/comments (if present)
  - Decorator information (@staticmethod, @property, etc.)
  - Access level (public/private based on naming convention)

**Tools to use:**
- `grep -r "def " --include="*.py"` for basic function discovery
- AST parsing for detailed signature analysis
- Code analysis tools like `vulture` or custom scripts

### 1.2 Map Function Dependencies
**Objective:** Understand the call relationships between functions

**Tasks:**
- [ ] Identify function calls within each file
- [ ] Map cross-file function imports and usage
- [ ] Create dependency graph showing:
  - Which functions call which other functions
  - Import relationships between modules
  - Circular dependencies (if any)
- [ ] Identify entry points (functions called from main, routes, CLI)

**Output:** 
- Dependency matrix or graph
- List of potential circular dependencies

## Phase 2: Duplicate Detection

### 2.1 Identify Potential Duplicates
**Objective:** Find functions that may be duplicating functionality

**Search Criteria:**
- [ ] **Identical names:** Functions with exact same name in different files
- [ ] **Similar names:** Functions with similar naming patterns (e.g., `process_file`, `handle_file`, `manage_file`)
- [ ] **Identical signatures:** Functions with same parameters but different names
- [ ] **Similar logic patterns:** Functions performing similar operations (manual review required)

**Common duplicate patterns to look for:**
- File processing utilities
- Database connection/query functions
- Validation functions
- Error handling functions
- Configuration loading functions

### 2.2 Analyze Duplicate Severity
**Objective:** Categorize duplicates by type and consolidation complexity

**Categories:**

**🔴 Exact Duplicates (High Priority)**
- Identical implementation
- Same input/output behavior
- Safe to merge immediately

**🟡 Functional Duplicates (Medium Priority)**
- Same behavior, different implementation
- May have performance or style differences
- Require careful evaluation before merging

**🟠 Partial Duplicates (Low Priority)**
- Overlapping functionality
- Shared code blocks within larger functions
- Consider extracting common parts to utilities

## Phase 3: Usage Analysis

### 3.1 Find Unused Functions
**Objective:** Identify functions that are no longer needed

**Detection Methods:**
- [ ] Static analysis to find functions never called
- [ ] Search for function references across entire codebase
- [ ] Check for functions only called by other unused functions (dead code chains)
- [ ] Identify test-only functions that may be obsolete

**Special Considerations:**
- Functions used in templates or configuration files
- Functions called via reflection or dynamic imports
- API endpoints that might be called externally
- Functions used in scripts or CLI commands

### 3.2 Analyze Usage Patterns
**Objective:** Identify functions with questionable usage patterns

**Pattern Analysis:**
- [ ] **Single-use functions:** Called only once (potential for inlining)
- [ ] **Low-usage functions:** Called very rarely (< 3 times)
- [ ] **Legacy functions:** Commented as deprecated or TODO
- [ ] **Redundant wrappers:** Simple functions that just call other functions

## Phase 4: Documentation and Action Plan

### 4.1 Document Findings
**Objective:** Create comprehensive cleanup report

**Report Structure:**

#### 4.1.1 Executive Summary
- Total functions analyzed
- Number of duplicates found by category
- Number of unused functions identified
- Estimated cleanup impact

#### 4.1.2 Duplicate Functions Report
```markdown
| Function Name | File 1 | File 2 | Type | Complexity | Priority |
|---------------|--------|--------|------|------------|----------|
| process_gcode | src/gcode.py:45 | scripts/processor.py:12 | Exact | Low | High |
```

#### 4.1.3 Unused Functions Report
```markdown
| Function Name | File | Last Modified | Risk Level | Recommendation |
|---------------|------|---------------|------------|----------------|
| old_parser | src/legacy.py:123 | 2024-01-15 | Low | Remove |
```

#### 4.1.4 Low Usage Functions Report
```markdown
| Function Name | File | Usage Count | Recommendation |
|---------------|------|-------------|----------------|
| debug_helper | src/utils.py:67 | 1 | Consider inlining |
```

### 4.2 Create Cleanup Recommendations
**Objective:** Provide actionable steps for codebase improvement

#### 4.2.1 Immediate Actions (Low Risk)
- [ ] Remove unused functions with no external dependencies
- [ ] Merge exact duplicate functions
- [ ] Remove dead code chains

#### 4.2.2 Medium Priority Actions
- [ ] Consolidate functional duplicates (requires testing)
- [ ] Inline single-use functions where appropriate
- [ ] Extract common functionality from partial duplicates

#### 4.2.3 Long-term Improvements
- [ ] Refactor modules with high duplication
- [ ] Establish coding standards to prevent future duplication
- [ ] Implement linting rules to catch duplicates early

## Implementation Guidelines

### 4.3 Safety Measures
**Before making changes:**
- [ ] Ensure comprehensive test coverage for affected functions
- [ ] Create backup branch for rollback capability
- [ ] Review with team members for external usage concerns
- [ ] Check for dynamic function calls or reflection usage

### 4.4 Testing Strategy
**For each cleanup operation:**
- [ ] Run existing test suite
- [ ] Add tests for consolidated functions if missing
- [ ] Perform integration testing for critical paths
- [ ] Monitor application behavior after deployment

### 4.5 Documentation Updates
**After cleanup:**
- [ ] Update API documentation if public functions changed
- [ ] Update internal documentation and comments
- [ ] Record cleanup decisions for future reference
- [ ] Update CHANGELOG.md with cleanup summary

## Tools and Scripts

### Recommended Tools
- **vulture**: Dead code finder for Python
- **pyflakes**: Static analysis for unused imports/variables
- **radon**: Code complexity analysis
- **ast**: Python AST parsing for detailed analysis
- **grep/ripgrep**: Pattern searching across codebase

### Custom Analysis Scripts
Consider creating project-specific scripts for:
- Function signature extraction
- Cross-reference analysis
- Duplicate detection with domain-specific rules
- Usage frequency counting

## Success Metrics

### Quantitative Measures
- [ ] Reduction in total lines of code
- [ ] Decrease in cyclomatic complexity
- [ ] Reduction in duplicate code percentage
- [ ] Fewer linting warnings/errors

### Qualitative Measures
- [ ] Improved code maintainability
- [ ] Clearer module responsibilities
- [ ] Better test coverage ratios
- [ ] Enhanced developer productivity

---

## Execution Checklist

### Phase 1: Discovery
- [ ] Function inventory complete
- [ ] Dependency mapping done
- [ ] Initial analysis documented

### Phase 2: Duplicate Analysis
- [ ] Duplicate detection complete
- [ ] Severity categorization done
- [ ] Consolidation plan created

### Phase 3: Usage Analysis
- [ ] Unused function identification complete
- [ ] Usage pattern analysis done
- [ ] Removal risk assessment complete

### Phase 4: Cleanup Execution
- [ ] Cleanup plan approved
- [ ] Safety measures in place
- [ ] Changes implemented and tested
- [ ] Documentation updated

---

**Note:** This analysis should be performed iteratively. Start with high-confidence, low-risk changes and gradually work toward more complex refactoring as confidence in the codebase understanding increases.