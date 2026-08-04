#!/bin/bash
# Start the application
# Usage: ./scripts/start.sh [api|bot|both]

set -e

MODE=${1:-both}

cd "$(dirname "$0")/.."

# Validate required environment variables
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

echo "Starting in mode: $MODE"

case $MODE in
    api)
        echo "Starting FastAPI server..."
        exec uvicorn app.main:app --host "${FASTAPI_HOST:-0.0.0.0}" --port "${FASTAPI_PORT:-8000}"
        ;;
    bot)
        echo "Starting Telegram bot..."
        exec python -m app.bot
        ;;
    both)
        echo "Starting both FastAPI and Telegram bot..."
        # Run migrations first
        alembic upgrade head
        
        # Start FastAPI in background
        uvicorn app.main:app --host "${FASTAPI_HOST:-0.0.0.0}" --port "${FASTAPI_PORT:-8000}" &
        API_PID=$!
        
        # Start bot
        python -m app.bot &
        BOT_PID=$!
        
        # Wait for either process to exit
        wait -n $API_PID $BOT_PID
        EXIT_CODE=$?
        
        # Kill the other process
        kill $API_PID $BOT_PID 2>/dev/null || true
        
        exit $EXIT_CODE
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Usage: $0 [api|bot|both]"
        exit 1
        ;;
esac