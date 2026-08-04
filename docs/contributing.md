# Contributing Guide

Thank you for contributing to Download Bot! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Follow the project's coding standards
- Write tests for new features
- Update documentation as needed

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Run tests and quality checks
6. Submit a pull request

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

Examples:
```
feat(bot): add /language command
fix(download): handle network timeout gracefully
docs(api): update environment variables list
```

### Pull Request Process

1. Ensure all CI checks pass
2. Update CHANGELOG.md (if applicable)
3. Request review from maintainers
4. Address review comments
5. Squash and merge

## Code Standards

### Python Style

- **Ruff** for linting (replaces flake8, isort, pyupgrade)
- **Black** for formatting (line length 100)
- **isort** for import sorting (Black profile)
- **mypy** for type checking (strict mode)

Run locally:
```bash
ruff check --fix .
black .
isort .
mypy .
```

### Type Hints

- All functions must have type hints
- Use `from __future__ import annotations`
- Prefer `list[str]` over `List[str]` (Python 3.9+)
- Use `TypedDict` for dict structures

### Async Code

- All I/O operations must be async
- Use `async with` for context managers
- Avoid blocking calls in async functions
- Use `asyncio.gather` for concurrent operations

### Error Handling

- Use custom exceptions from `app.core.exceptions`
- Never use bare `except:`
- Log exceptions with context
- Return user-friendly error messages

### Logging

- Use `get_logger(__name__)` at module level
- Include context: `logger.info("action", key=value)`
- Never log secrets (automatic redaction)
- Use appropriate log levels

### Testing

- Target ≥80% coverage (Milestone 1), ≥85% (Milestone 2), ≥90% (Milestones 3+)
- Write unit tests for business logic
- Write integration tests for API/database
- Use fixtures for common setup
- Mock external dependencies

Test structure:
```python
class TestFeatureName:
    def test_specific_behavior(self):
        # Arrange
        # Act
        # Assert
```

### Documentation

- Update README.md for user-facing changes
- Update docs/architecture.md for structural changes
- Add docstrings for public APIs
- Keep .env.example current

## Project Structure

```
app/
├── api/           # FastAPI routes
├── bot/           # Telegram bot
├── core/          # Config, logging, exceptions, i18n
├── database/      # SQLAlchemy setup
├── models/        # Database models
├── providers/     # Download providers
├── download/      # Download engine
├── services/      # Business logic
├── repositories/  # Data access
├── middlewares/   # Bot middlewares
├── keyboards/     # Inline keyboards
├── handlers/      # Command handlers
└── utils/         # Utilities
```

## Adding Features

### New Command

1. Create handler in `app/bot/handlers/`
2. Register in `app/bot/routers.py`
3. Add translations to `locales/en.json` and `locales/ne.json`
4. Write tests in `tests/test_handlers/`

### New Provider

1. Implement `BaseProvider` in `app/providers/`
2. Register in `app/providers/__init__.py`
3. Add URL detection patterns
4. Write unit tests with mocked responses

### New Model

1. Create model in `app/models/`
2. Add repository in `app/repositories/`
3. Create Alembic migration
4. Update ER diagram in docs

### New API Endpoint

1. Add route in `app/api/routes.py`
2. Add Pydantic models for request/response
3. Write integration tests
4. Update OpenAPI docs (auto-generated)

## Quality Gates

All PRs must pass:

- ✅ Ruff (linting)
- ✅ Black (formatting)
- ✅ isort (imports)
- ✅ mypy (type checking)
- ✅ pytest (tests)
- ✅ pytest-cov (coverage)
- ✅ Bandit (security)
- ✅ pip-audit (dependencies)
- ✅ detect-secrets (secrets)

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. GitHub Actions builds and deploys
5. Verify deployment

## Getting Help

- Check existing issues and PRs
- Read documentation in `docs/`
- Ask questions in discussions
- Contact maintainers

## Recognition

Contributors will be acknowledged in:
- CHANGELOG.md
- README.md contributors section
- Release notes