#!/bin/bash
# Run the application with all services
# Usage: ./scripts/run.sh

set -e

cd "$(dirname "$0")/.."

source .venv/bin/activate

# Validate environment
required_vars=(
    "DATABASE_URL"
    "TELEGRAM_BOT_TOKEN"
    "SECRET_KEY"
    "DOWNLOAD_LINK_HMAC_SECRET"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Required environment variable $var is not set"
        exit 1
    fi
done

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start services
echo "Starting FastAPI server..."
uvicorn app.main:app --host "${FASTAPI_HOST:-0.0.0.0}" --port "${FASTAPI_PORT:-8000}" &
API_PID=$!

echo "Starting Telegram bot..."
python -m app.bot &
BOT_PID=$!

echo "Starting cleanup service..."
python -c "
import asyncio
from app.download import cleanup_service
asyncio.run(cleanup_service.start())
" &
CLEANUP_PID=$!

# Wait for any process to exit
wait -n $API_PID $BOT_PID $CLEANUP_PID
EXIT_CODE=$?

# Kill remaining processes
kill $API_PID $BOT_PID $CLEANUP_PID 2>/dev/null || true

exit $EXIT_CODE