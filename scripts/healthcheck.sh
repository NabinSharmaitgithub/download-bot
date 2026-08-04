#!/bin/bash
# Health check script for Render
# Usage: ./scripts/healthcheck.sh

set -e

cd "$(dirname "$0")/.."

URL="${HEALTHCHECK_URL:-http://localhost:8000/health}"
TIMEOUT="${HEALTHCHECK_TIMEOUT:-10}"

echo "Checking health at $URL..."

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$URL" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "Health check passed (HTTP $HTTP_CODE)"
    exit 0
else
    echo "Health check failed (HTTP $HTTP_CODE)"
    exit 1
fi