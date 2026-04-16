#!/usr/bin/env bash
# ClipForge v1.0 installer for Unix / macOS
set -e

echo "=== ClipForge v1.0 Installer ==="
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "[1/3] Creating virtual environment..."
  python3 -m venv .venv
else
  echo "[1/3] Virtual environment already exists, skipping."
fi

source .venv/bin/activate

# Choose install profile
# Default: core + TTS.  Pass --youtube to also install YouTube API libs.
EXTRAS="tts"
for arg in "$@"; do
  case $arg in
    --youtube) EXTRAS="tts,publish-youtube" ;;
    --full)    EXTRAS="full" ;;
  esac
done

echo "[2/3] Installing clipforge[$EXTRAS] and dependencies..."
pip install --upgrade pip --quiet
pip install -e ".[$EXTRAS]" --quiet

echo "[3/3] Done!"
echo ""
echo "---------------------------------------------------------------------"
echo "  ClipForge v1.0 installed with extras: [$EXTRAS]"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Activate the environment (if not already):"
echo "       source .venv/bin/activate"
echo ""
echo "  2. Copy and fill in your API keys:"
echo "       cp .env.example .env"
echo "       # Optionally set PEXELS_API_KEY, YOUTUBE_CREDENTIALS_PATH, etc."
echo ""
echo "  3. Verify your setup:"
echo "       clipforge doctor"
echo ""
echo "  4. Try a quick render:"
echo "       clipforge make --script-file examples/script_example.txt \\"
echo "                      --platform reels --audio-mode silent \\"
echo "                      --output output/demo.mp4"
echo ""
echo "  5. Interactive studio:"
echo "       clipforge studio"
echo "---------------------------------------------------------------------"
echo ""
echo "  Requires: FFmpeg on PATH  (https://ffmpeg.org/download.html)"
echo "  moviepy is pinned to 1.0.3 for rendering stability."
echo ""
echo "  YouTube publishing:"
echo "    bash install.sh --youtube"
echo "    # then set YOUTUBE_CREDENTIALS_PATH in .env"
echo ""
echo "  Upgrade:"
echo "    git pull && pip install -e '.[$EXTRAS]' --upgrade"
echo ""
echo "  Uninstall:"
echo "    bash uninstall.sh"
echo "---------------------------------------------------------------------"
