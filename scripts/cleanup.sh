#!/bin/bash
# Cleanup script for expired temp files and tokens
# Usage: ./scripts/cleanup.sh

set -e

cd "$(dirname "$0")/.."

TEMP_DIR="${TEMP_DIRECTORY:-/tmp/downloads}"
MAX_AGE="${TEMP_FILE_TTL:-86400}"

echo "Cleaning up temp files older than $MAX_AGE seconds in $TEMP_DIR..."

find "$TEMP_DIR" -type f -mmin +$((MAX_AGE / 60)) -delete 2>/dev/null || true

echo "Cleanup completed."