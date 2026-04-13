#!/usr/bin/env bash
# ClipForge installer for Unix/macOS
set -e

echo "=== ClipForge Installer ==="
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "[1/3] Creating virtual environment..."
  python3 -m venv .venv
else
  echo "[1/3] Virtual environment already exists, skipping."
fi

source .venv/bin/activate

# Install the package in editable mode with all runtime deps + TTS
echo "[2/3] Installing clipforge and dependencies..."
pip install --upgrade pip --quiet
pip install -e ".[tts]" --quiet

echo "[3/3] Done!"
echo ""
echo "---------------------------------------------------------------------"
echo "  Next steps:"
echo ""
echo "  1. Activate the environment:"
echo "       source .venv/bin/activate"
echo ""
echo "  2. Copy and fill in your API keys:"
echo "       cp .env.example .env"
echo "       # Add PEXELS_API_KEY and/or PIXABAY_API_KEY"
echo ""
echo "  3. Verify your setup:"
echo "       clipforge doctor"
echo ""
echo "  4. Try a quick render:"
echo "       clipforge make --script-file examples/script_example.txt \\"
echo "                      --platform reels --audio-mode silent \\"
echo "                      --output output/demo.mp4"
echo "---------------------------------------------------------------------"
echo ""
echo "  Requires: FFmpeg on PATH  (https://ffmpeg.org/download.html)"
echo "  moviepy is pinned to 1.0.3 for rendering stability."
echo "---------------------------------------------------------------------"
