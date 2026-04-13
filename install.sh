#!/usr/bin/env bash
# Simple installation script for Unix systems.
set -e

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

echo "Installation complete. Activate the virtual environment with:"
echo "source .venv/bin/activate"
echo "Then run 'autovideo --help' to see available commands."