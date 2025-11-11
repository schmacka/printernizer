# Contributing to Printernizer

Thank you for your interest in contributing to Printernizer! This document outlines the process for contributing to this professional 3D printer management system.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/printernizer.git
   cd printernizer
   ```
3. **Set up your development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow the existing code style and conventions
- Write tests for new functionality
- Update documentation as needed
- Ensure your code works with both Bambu Lab A1 and Prusa Core One printers

### 3. Test Your Changes
```bash
# Run the test suite
python -m pytest

# Run with coverage
python -m pytest --cov=src tests/

# Test specific components
python -m pytest tests/backend/
```

### 4. Code Quality Checks
```bash
# Format code (if black is available)
black src/ tests/

# Type checking (if mypy is available)
mypy src/

# Manual code review using the checklist in docs/development/
```

### 5. Commit Your Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions
- `refactor:` for code refactoring

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots for UI changes
- Testing notes

## Development Guidelines

### Code Style
- Follow existing Python conventions
- Use type hints where appropriate
- Write clear, descriptive variable and function names
- Add docstrings for public functions and classes

### Testing
- Write unit tests for new functionality
- Include integration tests for printer communication
- Test error handling and edge cases
- Maintain good test coverage

### Documentation
- Update README.md if needed
- Add docstrings to new functions
- Update API documentation
- Include examples for new features

## Areas for Contribution

### High Priority
- **3D Preview System** - STL/3MF/G-Code visualization
- **Additional Printer Support** - Other 3D printer integrations
- **Performance Optimization** - Database queries, file handling
- **Test Coverage** - Expand test suite coverage

### Medium Priority
- **UI/UX Improvements** - Frontend enhancements
- **Documentation** - User guides, API docs
- **Monitoring** - Advanced metrics and alerting
- **Internationalization** - Additional language support

### Low Priority
- **Code Quality** - Refactoring and cleanup
- **Development Tools** - Improved dev experience
- **Examples** - Sample configurations and use cases

## Printer Integration Guidelines

When adding support for new 3D printers:

1. **Extend the base printer class** in `src/printers/base.py`
2. **Implement all required methods** with proper error handling
3. **Follow the existing patterns** from Bambu Lab and Prusa implementations
4. **Add comprehensive tests** for the new printer type
5. **Update documentation** with setup instructions

## Security Considerations

- Never commit API keys or sensitive credentials
- Follow secure coding practices
- Report security issues privately to sebastian@porcus3d.de
- Use environment variables for configuration

## Release Process

For maintainers creating releases:

- See [RELEASE.md](RELEASE.md) for the complete release workflow
- Includes versioning standards, tagging, and automated GitHub releases
- GitHub Actions automatically creates releases when tags are pushed

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing GitHub issues
- **Questions**: Start a GitHub Discussion
- **Contact**: sebastian@porcus3d.de for complex questions

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments section

## License

By contributing to Printernizer, you agree that your contributions will be licensed under the AGPL-3.0 license. For commercial licensing questions, contact sebastian@porcus3d.de.

Thank you for helping make Printernizer better! 🚀