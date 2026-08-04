#!/bin/bash
# Run database migrations
# Usage: ./scripts/migrate.sh [upgrade|downgrade|revision|current|history]

set -e

COMMAND=${1:-upgrade}

cd "$(dirname "$0")/.."

echo "Running alembic $COMMAND..."

case $COMMAND in
    upgrade)
        alembic upgrade head
        ;;
    downgrade)
        alembic downgrade -1
        ;;
    revision)
        alembic revision --autogenerate -m "${2:-auto_migration}"
        ;;
    current)
        alembic current
        ;;
    history)
        alembic history
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Usage: $0 [upgrade|downgrade|revision|current|history]"
        exit 1
        ;;
esac

echo "Done."