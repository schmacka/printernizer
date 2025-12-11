# Development

Welcome to the Printernizer development documentation! This section provides everything you need to contribute to the project.

## Quick Links

- **[Contributing Guide](contributing.md)** - How to contribute to Printernizer
- **[Development Workflow](workflow.md)** - Git workflow and development process
- **[Code Sync](code-sync.md)** - Understanding the code synchronization system
- **[Testing Guide](testing.md)** - How to write and run tests
- **[Debugging](debugging.md)** - Debugging tips and tools

## Getting Started with Development

### Prerequisites

- Python 3.8+
- Git
- Node.js (for frontend development)
- Docker (optional, for testing deployments)

### Setup Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/schmacka/printernizer.git
cd printernizer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 5. Run the application
python src/main.py
```

### Development Workflow

Printernizer uses a **two-branch model**:

- **`development`** - Integration and testing branch
  - All feature branches merge here first
  - Used for Docker testing deployments
  - Pre-release versions (e.g., `2.7.0-dev`)

- **`master`** - Production-ready branch
  - Only stable, tested code
  - Used for releases and Home Assistant add-on
  - Release versions only (e.g., `2.7.0`)

**Workflow:**
```
Feature branch → development (PR) → Docker test → master (PR) → Tag for release
```

See [Development Workflow](workflow.md) for complete details.

## Code Synchronization

**Single Source of Truth:** Edit code only in `/src/` and `/frontend/` directories.

**Home Assistant Add-on**: Maintained in separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository. Code automatically syncs via GitHub Actions when you push to `master` or `development` branch.

See [Code Sync](code-sync.md) for details.

## Project Structure

```
printernizer/
├── src/                    # Backend source code (EDIT HERE)
│   ├── api/               # FastAPI routers
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   ├── printers/          # Printer integrations
│   └── main.py            # Application entry point
├── frontend/              # Frontend source code (EDIT HERE)
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/                 # Test suite
├── docs/                  # Documentation (MkDocs)
├── printernizer/          # Home Assistant add-on (AUTO-SYNCED)
│   ├── src/              # Synced from /src/
│   └── frontend/         # Synced from /frontend/
├── docker/                # Docker configuration
└── scripts/               # Utility scripts
```

## Contributing Guidelines

### Branching Strategy

1. Create feature branch from `development`
2. Make changes and commit
3. Submit PR to `development`
4. After testing, merge to `master` for release

### Commit Messages

Follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
chore: Maintenance tasks
refactor: Code refactoring
test: Add tests
```

### Code Style

- **Python:** Black formatter, PEP 8
- **JavaScript:** ES6+, consistent formatting
- **Line length:** 100 characters
- **Type hints:** Required for Python code

### Testing

All contributions must include tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_printer_service.py
```

See [Testing Guide](testing.md) for details.

## Documentation

Update documentation when adding features:

1. Add docstrings to Python code
2. Update relevant .md files in `docs/`
3. Update CHANGELOG.md
4. Update API documentation if needed

## Release Process

See [RELEASE.md](https://github.com/schmacka/printernizer/blob/master/RELEASE.md) for the complete release process.

## Development Tools

### Interactive API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Database Browser

Use any SQLite browser to inspect the database:

```bash
sqlite3 data/printernizer.db
```

### Logging

Structured logging with different levels:

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("message", key="value")
logger.error("error", exc_info=True)
```

## Common Development Tasks

### Adding a New API Endpoint

1. Create/update router in `src/api/routers/`
2. Add business logic to service in `src/services/`
3. Update data models if needed in `src/models/`
4. Add tests in `tests/`
5. Update API documentation

### Adding Printer Support

1. Create new printer class in `src/printers/`
2. Extend `BasePrinter` interface
3. Implement required methods
4. Add configuration schema
5. Update documentation
6. Add tests

### Debugging

See [Debugging Guide](debugging.md) for:

- Setting up debuggers
- Common issues
- Logging best practices
- Performance profiling

## Getting Help

- **Questions:** [GitHub Discussions](https://github.com/schmacka/printernizer/discussions)
- **Bugs:** [GitHub Issues](https://github.com/schmacka/printernizer/issues)
- **Chat:** Check README for community links

## Resources

- [Architecture Overview](../architecture/index.md)
- [API Reference](../api-reference/index.md)
- [Testing Documentation](../testing/index.md)
- [CONTRIBUTING.md](contributing.md)
