#!/usr/bin/env bash
# ClipForge uninstaller for Unix / macOS
set -e

echo "=== ClipForge Uninstaller ==="
echo ""
echo "This will:"
echo "  - Deactivate and remove the .venv virtual environment"
echo "  - Remove the clipforge package from any active environment"
echo ""
echo "It will NOT remove:"
echo "  - Your script files or video outputs"
echo "  - Your .env file or API keys"
echo "  - Your analytics_store, publish_queue, or project folders"
echo ""
read -r -p "Continue? [y/N] " confirm
case "$confirm" in
  [yY][eE][sS]|[yY]) ;;
  *) echo "Cancelled."; exit 0 ;;
esac

# Remove package from active env (if any)
if command -v pip &>/dev/null; then
  pip uninstall clipforge -y 2>/dev/null || true
fi

# Remove virtual environment
if [ -d ".venv" ]; then
  echo "Removing .venv..."
  rm -rf .venv
  echo "Done."
else
  echo "No .venv directory found."
fi

echo ""
echo "ClipForge has been uninstalled."
echo "Your project files, outputs, and .env are untouched."
