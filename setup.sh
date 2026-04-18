#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed." >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists, skipping creation."
fi

echo "Installing dependencies from requirements.txt..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r requirements.txt --quiet

echo ""
echo "Done. Activate the environment with:"
echo "  source $VENV_DIR/bin/activate"
