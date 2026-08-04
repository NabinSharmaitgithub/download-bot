# Development Setup

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (optional)
- Git
- Docker (optional)

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd download-bot
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -e ".[dev]"
pre-commit install
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your local values
```

Required for local development:
- `DATABASE_URL` - Local PostgreSQL connection
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `DOWNLOAD_LINK_HMAC_SECRET` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 5. Setup Database

```bash
# Create database
createdb download_bot

# Run migrations
alembic upgrade head
```

### 6. Run Application

```bash
# Terminal 1: FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Telegram bot (polling mode)
python -m app.bot
```

## Running Tests

```bash
# All tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Specific test file
pytest tests/test_config.py -v

# With specific markers
pytest -m "not integration" -v
```

## Code Quality

### Linting & Formatting

```bash
# Auto-fix
ruff check --fix .
black .
isort .

# Check only
ruff check .
black --check .
isort --check-only .
```

### Type Checking

```bash
mypy .
```

### Security Scanning

```bash
bandit -r app/
pip-audit
detect-secrets scan --baseline .secrets.baseline
```

### Pre-commit

```bash
# Run all hooks
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add_user_table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show history
alembic history
```

## Adding a New Provider

1. Create provider class in `app/providers/` implementing `BaseProvider`
2. Register in `app/providers/__init__.py`
3. Add URL patterns to detection logic
4. Add tests in `tests/providers/`

## Adding a New Language

1. Copy `locales/en.json` to `locales/<lang_code>.json`
2. Translate all string values
3. Test with `BOT_MODE=polling` and `/language` command

## Project Structure

```
download-bot/
├── .github/workflows/     # CI/CD pipelines
├── app/
│   ├── api/              # FastAPI routes
│   ├── bot/              # Telegram bot
│   ├── core/             # Config, logging, exceptions, i18n
│   ├── database/         # SQLAlchemy setup
│   ├── models/           # Database models
│   ├── providers/        # Download providers
│   ├── download/         # Download engine
│   ├── services/         # Business logic
│   ├── repositories/     # Data access
│   ├── middlewares/      # Bot middlewares
│   ├── keyboards/        # Inline keyboards
│   ├── handlers/         # Command handlers
│   └── utils/            # Utilities
├── tests/                # Test suite
├── locales/              # Translation files
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── alembic/              # Database migrations
├── pyproject.toml        # Project config
├── Dockerfile            # Multi-stage Docker build
├── .dockerignore
├── .env.example          # Environment template
├── README.md
└── todo.md
```

## Debugging

### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Bot",
      "type": "python",
      "request": "launch",
      "module": "app.bot",
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

### Logs

Logs are structured JSON. Use `jq` for pretty printing:

```bash
# Follow logs
tail -f logs/app.log | jq .

# Filter by level
grep '"level":"ERROR"' logs/app.log | jq .
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check connection
psql $DATABASE_URL -c "SELECT 1"
```

### Bot Not Starting

- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check bot is not already running elsewhere
- For webhook mode: ensure `WEBHOOK_URL` is accessible

### Import Errors

```bash
# Reinstall in development mode
pip install -e ".[dev]"
```

### Migration Failures

```bash
# Check current revision
alembic current

# Manual fix if needed
alembic stamp head
```

## Useful Commands

```bash
# Generate requirements.txt
pip freeze > requirements.txt

# Check outdated packages
pip list --outdated

# Run specific test with output
pytest tests/test_config.py::TestSettings::test_default_values -v -s

# Profile tests
pytest --profile-svg=profile.svg
```