# Commit Message Conventions

## Format

Follow the **Conventional Commits** specification.

```
<type>: <description>

[optional body]
```

## Types

| Type | Use For |
|------|---------|
| `feat` | New features |
| `fix` | Bug fixes |
| `docs` | Documentation changes |
| `test` | Test additions or changes |
| `refactor` | Code refactoring (no behavior change) |
| `chore` | Maintenance tasks, version bumps |
| `style` | Formatting, whitespace (no code change) |
| `perf` | Performance improvements |

## Examples

```bash
# New feature
git commit -m "feat: Add timelapse generation for print jobs"

# Bug fix
git commit -m "fix: Resolve MQTT connection timeout on Bambu printers"

# Documentation
git commit -m "docs: Update API endpoint documentation"

# Version bump
git commit -m "chore: Bump version to 2.9.1"

# Refactoring
git commit -m "refactor: Extract printer status logic to dedicated service"
```

## Best Practices

- Use imperative mood ("Add feature" not "Added feature")
- Keep first line under 72 characters
- Reference issues when applicable: `fix: Resolve timeout (#123)`
- Be specific about what changed

## References

- Contributing guide: `CONTRIBUTING.md`
- Conventional Commits: https://www.conventionalcommits.org/
