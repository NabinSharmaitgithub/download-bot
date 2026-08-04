# Architecture Overview

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Telegram Users                           │
└─────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Telegram Bot (aiogram 3.x)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Middlewares: Logging, i18n, DB Session, User Reg,      │   │
│  │ Rate Limit, Flood Protection, Error Handling            │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Routers & Handlers: /start, /help, /settings,          │   │
│  │ /history, /queue, /status, /cancel, /about,            │   │
│  │ /language, /admin, callbacks                           │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────┬────────────────────────────────────────┘
                           │
           ┌────────┴─────────┐
           ▼               ▼               ▼
┌────────────┐ ┌─────────┐ ┌────────────┐
│   FastAPI        │ │  Database   │ │  Download        │
│  (Web Service)   │ │ (PostgreSQL)│ │  Engine          │
│                  │ │             │ │                  │
│ • Health checks  │ │ • Users     │ │ • Queue Manager  │
│ • Metrics        │ │ • Downloads │ │ • Progress Track │
│ • Signed URLs    │ │ • Queue     │ │ • Temp Storage   │
│ • Webhook        │ │ • Settings  │ │ • File Delivery  │
└────────────┘ └─────────┘ └────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Provider Plugins                             │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐      │
│  │ YouTube  │ │Google Drive│ │ Dropbox  │ │  TeraBox   │      │
│  │ (yt-dlp) │ │            │ │          │ │            │      │
│  └─────────┘ └──────────┘ └─────────┘ └──────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration (`app/core/config.py`)

- **Pydantic Settings** with environment-specific validation
- Supports development, testing, production environments
- Validates all required variables at startup
- Type-safe with field validators

### 2. Logging (`app/core/logging.py`)

- **Structured JSON logging** via structlog + python-json-logger
- Context variables: request_id, user_id, download_id
- Automatic secret redaction (tokens, passwords, keys)
- Configurable format (JSON/console) and level

### 3. Exception Handling (`app/core/exceptions.py`)

- Hierarchical exception classes with HTTP status codes
- Automatic mapping to user-friendly responses
- Never exposes stack traces or internal details
- Centralized exception handlers in FastAPI

### 4. Localization (`app/core/localization.py`)

- JSON-based translation files per locale
- Automatic fallback to default locale
- Parameterized translations with `.format()`
- Lazy loading, middleware integration

### 5. Database Layer (`app/database/`)

- **SQLAlchemy 2.x async** with asyncpg/aiosqlite
- Connection pooling with configurable limits
- Session management with transaction support
- Alembic for migrations

### 6. Models (`app/models/`)

- **DeclarativeBase** with TimestampMixin
- Models: User, Download, DownloadHistory, Queue, Settings, AdminLog, Statistics
- Proper indexes, foreign keys, constraints
- Enum types for status fields

### 7. Repository Pattern (`app/repositories/`)

- Abstract base repository with CRUD + pagination/filtering/sorting
- Concrete implementations per model
- Framework-independent, easily testable
- Dependency injection ready

### 8. Telegram Bot (`app/bot/`)

- **aiogram 3.x** with Dispatcher, Router, FSM
- Middleware chain for cross-cutting concerns
- Command handlers with localization
- Callback query framework with validation
- Graceful startup/shutdown with lifespan

### 9. FastAPI Service (`app/main.py`, `app/api/`)

- Health endpoints: `/health`, `/ready`, `/metrics`
- Prometheus metrics middleware
- Exception handlers for all custom exceptions
- Webhook endpoint for Telegram updates

### 10. Download Engine (`app/download/`)

- **DownloadManager**: Start/pause/cancel/track downloads
- **QueueManager**: Per-user queues, priorities, persistence
- **ProgressTracker**: Real-time progress with callbacks
- **TempStorage**: Secure temp files, cleanup, recovery
- **FileDelivery**: Direct Telegram upload or signed URLs
- **CleanupService**: Background scheduler for expired files

### 11. Provider Plugins (`app/providers/`)

- **BaseProvider** abstract interface
- Provider identification, URL validation, metadata extraction
- Folder traversal, download preparation, error mapping
- Independent, replaceable implementations

## Data Flow

### Download Request Flow

```
User sends URL
      │
      ▼
Message Handler → Provider Detection → Validation
      │
      ▼
Queue Manager ← Add to queue (with priority)
      │
      ▼
Download Manager → Provider → Download Preparation
      │
      ▼
Progress Tracker → Callbacks → Telegram Updates
      │
      ▼
Temp Storage → File Complete
      │
      ▼
File Delivery → Telegram Upload OR Signed URL
      │
      ▼
History Record → Notification
```

### Webhook Flow (Production)

```
Telegram → FastAPI /webhook → Dispatcher → Middlewares → Handlers
                                    │
                                    ▼
                              Database Session
                                    │
                                    ▼
                              Response → Telegram
```

## Security Considerations

### Secrets Management
- All secrets via environment variables
- Never logged (automatic redaction in logging)
- HMAC-SHA256 for signed URLs
- Minimum key lengths enforced

### Input Validation
- Pydantic models for all API inputs
- Callback data validation and signing
- URL validation per provider
- File path sanitization

### Access Control
- Admin-only commands with user ID verification
- User isolation in queue/download operations
- Owner verification for file downloads

### Network Security
- HTTPS-ready (Render terminates TLS)
- Rate limiting and flood protection
- Secure temporary file handling
- No SSRF vulnerabilities

## Scalability

### Horizontal Scaling
- Stateless FastAPI workers (multiple replicas)
- Shared PostgreSQL database
- Redis for FSM storage and caching
- Background worker for downloads

### Database Optimization
- Connection pooling
- Proper indexes on frequently queried columns
- Async queries throughout
- Pagination for large result sets

### Download Concurrency
- Per-user configurable limits
- Global queue with priorities
- Streaming downloads (no full file in memory)
- Backpressure handling

## Deployment Architecture (Render)

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Render Platform                        │
│  ┌───────────────────┐    ┌──────────────────────┐  │
│  │   Web Service       │    │   Background Worker         │  │
│  │   (FastAPI)         │    │   (Telegram Bot + Downloads)│  │
│  │                     │    │                             │  │
│  │ • /health           │    │ • Polling/Webhook           │  │
│  │ • /ready            │    │ • Download Queue            │  │
│  │ • /metrics          │    │ • Cleanup Scheduler         │  │
│  │ • /webhook          │    │                             │  │
│  │ • Signed URLs       │    │                             │  │
│  └──────────┬─────────┘    └──────────────┬──────────┘  │
│             │                              │                  │
│             └─────────┬──────────┘                  │
│                            ▼                                   │
│                   ┌──────────────┐                     │
│                   │  PostgreSQL         │                     │
│                   │  (Managed)          │                     │
│                   └──────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Metrics (Prometheus)
- HTTP request count/latency by endpoint
- Active downloads, queue length
- Database connection pool usage
- Custom business metrics

### Health Checks
- `/health` - Basic liveness
- `/ready` - Readiness (DB, config valid)
- Docker HEALTHCHECK

### Logging
- Structured JSON with correlation IDs
- Error tracking with context
- Audit logging for admin actions

### Alerting (Recommended)
- High error rates
- Queue backlog growth
- Disk space warnings
- Failed downloads spike