---
paths: src/api/routers/**/*.py
---

# API Routing Standards

## Trailing Slash Policy

FastAPI is configured with `redirect_slashes=False` to prevent conflicts with StaticFiles mounted at root.

## Mandatory Pattern

**NEVER use `"/"` as the endpoint path in router decorators.**
**ALWAYS use `""` (empty string) for root resource endpoints.**

## Correct Patterns

```python
# Root endpoints - use empty string
@router.get("")           # GET /api/v1/printers
@router.post("")          # POST /api/v1/printers

# Path parameters - include leading slash
@router.get("/{id}")      # GET /api/v1/printers/abc123
@router.put("/{id}")      # PUT /api/v1/printers/abc123
@router.delete("/{id}")   # DELETE /api/v1/printers/abc123

# Nested paths
@router.get("/{id}/files")  # GET /api/v1/printers/abc123/files
```

## Incorrect Patterns

```python
# DO NOT use trailing slash for root
@router.get("/")          # Creates /api/v1/printers/ - causes 405 errors
@router.post("/")         # Wrong!
```

## Why This Matters

Using `"/"` instead of `""` creates routes that require a trailing slash, which:
- Returns 405 Method Not Allowed for requests without trailing slash
- Inconsistent with REST conventions
- Breaks frontend API calls

## Configuration

```python
# main.py line ~600
app = FastAPI(
    ...
    redirect_slashes=False  # Critical setting
)
```

## References

- Git history: commits ddf53ea, 34680e6
- Branch: fix/disable-redirect-slashes
- Main configuration: `src/main.py`
