@echo off
REM ClipForge v1.0 installer for Windows
REM Usage: install.bat           (core + TTS)
REM        install.bat --youtube (core + TTS + YouTube API)
REM        install.bat --full    (all extras)
echo === ClipForge v1.0 Installer ===
echo.

SET EXTRAS=tts
IF "%1"=="--youtube" SET EXTRAS=tts,publish-youtube
IF "%1"=="--full"    SET EXTRAS=full

IF NOT EXIST ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
) ELSE (
    echo [1/3] Virtual environment already exists, skipping.
)

CALL .venv\Scripts\activate.bat

echo [2/3] Installing clipforge[%EXTRAS%] and dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -e ".[%EXTRAS%]" --quiet

echo [3/3] Done!
echo.
echo ---------------------------------------------------------------------
echo   ClipForge v1.0 installed with extras: [%EXTRAS%]
echo.
echo   Next steps:
echo.
echo   1. Activate the environment:
echo        .venv\Scripts\activate.bat
echo.
echo   2. Copy and fill in your API keys:
echo        copy .env.example .env
echo.
echo   3. Verify your setup:
echo        clipforge doctor
echo.
echo   4. Try a quick render:
echo        clipforge make --script-file examples\script_example.txt ^
echo                       --platform reels --audio-mode silent ^
echo                       --output output\demo.mp4
echo.
echo   5. Interactive studio:
echo        clipforge studio
echo ---------------------------------------------------------------------
echo.
echo   Requires: FFmpeg on PATH  (https://ffmpeg.org/download.html)
echo   moviepy is pinned to 1.0.3 for rendering stability.
echo.
echo   YouTube publishing:
echo     install.bat --youtube
echo     then set YOUTUBE_CREDENTIALS_PATH in .env
echo.
echo   Uninstall:
echo     pip uninstall clipforge -y
echo     rmdir /s /q .venv
echo ---------------------------------------------------------------------
