#!/bin/bash
# Setup script for initial project setup
# Usage: ./scripts/setup.sh

set -e

cd "$(dirname "$0")/.."

echo "Setting up download-bot..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Create .env from example
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
fi

# Create required directories
mkdir -p /data/downloads /tmp/downloads /var/log/app

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Run: alembic upgrade head"
echo "3. Run: python -m pytest"
echo "4. Run: uvicorn app.main:app --reload"