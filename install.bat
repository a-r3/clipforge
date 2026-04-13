@echo off
REM ClipForge installer for Windows
echo === ClipForge Installer ===
echo.

IF NOT EXIST ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
) ELSE (
    echo [1/3] Virtual environment already exists, skipping.
)

CALL .venv\Scripts\activate.bat

echo [2/3] Installing clipforge and dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -e ".[tts]" --quiet

echo [3/3] Done!
echo.
echo ---------------------------------------------------------------------
echo   Next steps:
echo.
echo   1. Activate the environment:
echo        .venv\Scripts\activate.bat
echo.
echo   2. Copy and fill in your API keys:
echo        copy .env.example .env
echo        (Add PEXELS_API_KEY and/or PIXABAY_API_KEY)
echo.
echo   3. Verify your setup:
echo        clipforge doctor
echo.
echo   4. Try a quick render:
echo        clipforge make --script-file examples/script_example.txt ^
echo                       --platform reels --audio-mode silent ^
echo                       --output output\demo.mp4
echo ---------------------------------------------------------------------
echo.
echo   Requires: FFmpeg on PATH  (https://ffmpeg.org/download.html)
echo   moviepy is pinned to 1.0.3 for rendering stability.
echo ---------------------------------------------------------------------
