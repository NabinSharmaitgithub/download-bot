# Download Bot

A production-ready Telegram bot for downloading content from multiple providers (YouTube, Google Drive, Dropbox, TeraBox) with queue management, progress tracking, and secure file delivery.

## Features

- **Multi-provider support**: YouTube, Google Drive, Dropbox, TeraBox
- **Queue management**: Per-user queues with priority and concurrency control
- **Progress tracking**: Real-time download progress with speed and ETA
- **Secure file delivery**: Direct Telegram upload or signed URLs for large files
- **Localization**: English and Nepali (extensible)
- **Admin panel**: User management, broadcasting, system monitoring
- **Production-ready**: Structured logging, health checks, metrics, graceful shutdown

## Architecture

```
├── app/
│   ├── api/           # FastAPI routes (health, metrics, downloads)
│   ├── bot/           # Telegram bot (handlers, middlewares, routers)
│   ├── core/          # Config, logging, exceptions, localization
│   ├── database/      # SQLAlchemy async, sessions, migrations
│   ├── models/        # Database models
│   ├── providers/     # Provider plugins (YouTube, Drive, etc.)
│   ├── download/      # Download engine, queue, progress
│   ├── services/      # Business logic services
│   ├── repositories/  # Data access layer
│   ├── middlewares/   # Bot middlewares
│   ├── keyboards/     # Inline keyboard builders
│   ├── handlers/      # Command/callback handlers
│   └── utils/         # Utilities
├── tests/             # Unit & integration tests
├── locales/           # Translation files (JSON)
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis (optional, for FSM storage)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd download-bot
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the application**:
   ```bash
   # Development (polling mode)
   python -m uvicorn app.main:app --reload

   # Or run bot only
   python -m app.bot
   ```

### Docker

```bash
docker build -t download-bot .
docker run --env-file .env download-bot
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|----------|
| `APP_ENV` | Environment (development/testing/production) | No | development |
| `DEBUG` | Enable debug mode | No | false |
| `LOG_LEVEL` | Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) | No | INFO |
| `LOG_FORMAT` | Log format (json/console) | No | json |
| `FASTAPI_HOST` | FastAPI host | No | 0.0.0.0 |
| `FASTAPI_PORT` | FastAPI port | No | 8000 |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `DATABASE_POOL_SIZE` | Connection pool size | No | 10 |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | No | 20 |
| `REDIS_URL` | Redis connection string | No | - |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | Yes | - |
| `BOT_MODE` | Bot mode (polling/webhook) | No | polling |
| `WEBHOOK_URL` | Webhook URL (required for webhook mode) | No* | - |
| `WEBHOOK_PATH` | Webhook path | No | /webhook |
| `WEBHOOK_SECRET` | Webhook secret token | No | - |
| `TG_MAX_UPLOAD_SIZE` | Max Telegram upload size (bytes) | No | 50MB |
| `DOWNLOAD_DIRECTORY` | Completed downloads directory | No | /data/downloads |
| `TEMP_DIRECTORY` | Temporary files directory | No | /tmp/downloads |
| `DOWNLOAD_LINK_EXPIRATION` | Signed URL expiration (seconds) | No | 3600 |
| `DOWNLOAD_LINK_HMAC_SECRET` | HMAC secret for signed URLs (min 32 chars) | Yes | - |
| `MAX_CONCURRENT_DOWNLOADS` | Max concurrent downloads per user | No | 3 |
| `MAX_QUEUE_SIZE` | Max queue size per user | No | 100 |
| `CLEANUP_INTERVAL` | Cleanup job interval (seconds) | No | 3600 |
| `TEMP_FILE_TTL` | Temp file TTL (seconds) | No | 86400 |
| `ADMIN_USER_IDS` | Comma-separated admin Telegram IDs | No | - |
| `SECRET_KEY` | Application secret key (min 32 chars) | Yes | - |

*Required when `BOT_MODE=webhook`

## Deployment on Render

### 1. Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Create a new PostgreSQL database
3. Note the `DATABASE_URL` (internal connection string)

### 2. Create Web Service

1. Create new Web Service
2. Connect your repository
3. Configure:
   - **Build Command**: `pip install -e ".[dev]"`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add all required variables from above
4. Deploy

### 3. Create Background Worker

1. Create new Background Worker
2. Connect same repository
3. Configure:
   - **Build Command**: `pip install -e ".[dev]"`
   - **Start Command**: `python -m app.bot`
   - **Environment Variables**: Same as Web Service
3. Deploy

### 4. Configure Webhook (Optional)

If using webhook mode:
1. Set `BOT_MODE=webhook`
2. Set `WEBHOOK_URL=https://your-web-service.onrender.com`
3. The webhook will be auto-configured on startup

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/settings` | Configure preferences |
| `/history` | View download history |
| `/queue` | View download queue |
| `/status` | Check download status |
| `/cancel` | Cancel current download |
| `/about` | About the bot |
| `/language` | Change language |
| `/admin` | Admin panel (admins only) |

## Development

### Code Quality

```bash
# Format
ruff check --fix .
black .
isort .

# Type check
mypy .

# Tests
pytest --cov=app

# Security
bandit -r app/
pip-audit
detect-secrets scan
```

### Pre-commit Hooks

```bash
pre-commit install
```

### Adding a New Language

1. Copy `locales/en.json` to `locales/<lang_code>.json`
2. Translate all values
3. Add language code to `Localization.available_locales`

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Project Structure Details

### Core Modules

- **config.py**: Pydantic Settings with validation for all environments
- **logging.py**: Structured JSON logging with context (request_id, user_id, download_id)
- **exceptions.py**: Exception hierarchy with HTTP status code mapping
- **localization.py**: i18n framework with JSON files, fallback, parameterization

### Bot Framework

- **middlewares.py**: Logging, localization, DB session, user registration, rate limiting, flood protection, error handling
- **routers.py**: Command router registration
- **handlers/**: Individual command handlers

### API

- **main.py**: FastAPI app with lifespan, middleware, exception handlers
- **routes.py**: API endpoints (/health, /ready, /metrics, /api/info)

## Security

- All secrets via environment variables
- HMAC-SHA256 signed download URLs
- Rate limiting and flood protection
- Input validation and sanitization
- No sensitive data in logs
- Non-root Docker user
- Parameterized SQL queries only

## Monitoring

- **Health**: `GET /health`
- **Readiness**: `GET /ready`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Structured logs**: JSON format with context

## License

MIT License - see LICENSE file for details.