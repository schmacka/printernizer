# Project Conventions

## Language

- **Logging**: English
- **GUI/Frontend**: English
- **Reports**: English
- **Code comments**: English

## Business Focus

Printernizer distinguishes between:
- **Business orders**: Customer prints for commercial purposes
- **Private models**: Personal/hobby prints

This affects analytics and reporting features.

## Primary Use Case

Enterprise-grade 3D printer fleet management with:
- Automated job monitoring
- File organization
- Business analytics
- Multi-printer support (Bambu Lab, Prusa)

## Supported Printers

| Manufacturer | Models | Protocol |
|--------------|--------|----------|
| Bambu Lab | A1, A1 Mini, P1S, X1C | MQTT |
| Prusa | Core One | HTTP API |

## Error Response Format

All API errors follow this structure:

```json
{
  "status": "error",
  "message": "User-friendly error message",
  "error_code": "PRINTER_NOT_FOUND",
  "details": { ... },
  "timestamp": "2025-01-08T15:30:00Z"
}
```

## File Organization

```
/src/              # Backend source code
/frontend/         # Frontend source code
/migrations/       # Database migrations
/tests/            # Test suite
/docs/             # Documentation
/.claude/          # Claude Code configuration
```

## References

- Error handling: `src/utils/errors.py`
- Printer base: `src/printers/base.py`
