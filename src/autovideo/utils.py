"""Utility functions for the Auto Scenario Video Builder.

This module includes helpers for loading environment variables, checking
external dependencies like FFmpeg, and printing available presets.  These
functions are invoked by the CLI commands and other modules.
"""

from __future__ import annotations

import os
import subprocess
from typing import List

from dotenv import load_dotenv


def load_env() -> dict[str, str]:
    """Load environment variables from a `.env` file.

    Returns a dictionary of environment variables. If no `.env` file
    exists, returns an empty dictionary.
    """
    load_dotenv()
    return dict(os.environ)


def check_ffmpeg() -> bool:
    """Return True if FFmpeg is installed and available on the system PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


# Backwards‑compatible alias used by tests
def is_ffmpeg_available() -> bool:
    """Alias for check_ffmpeg()."""
    return check_ffmpeg()


def missing_api_keys() -> List[str]:
    """Return a list of missing API keys required for stock media downloads."""
    env = load_env()
    missing: List[str] = []
    if not env.get("PEXELS_API_KEY") and not env.get("PIXABAY_API_KEY"):
        missing.append("PEXELS_API_KEY or PIXABAY_API_KEY")
    return missing


def doctor() -> None:
    """Print diagnostic information about the environment and dependencies."""
    ok = True
    print("Running autovideo doctor...\n")
    if check_ffmpeg():
        print("[OK] FFmpeg found.")
    else:
        print("[ERROR] FFmpeg not found on PATH.")
        ok = False
    missing = missing_api_keys()
    if missing:
        print(f"[WARNING] Missing API keys: {', '.join(missing)}")
    else:
        print("[OK] Stock media API keys found.")
    if not os.path.exists(".env"):
        print("[WARNING] .env file not found.")
    else:
        print("[OK] .env file found.")
    if ok:
        print("\nYour environment looks ready.")
    else:
        print("\nPlease install FFmpeg and configure API keys as needed.")


def print_presets() -> None:
    """Print available presets for audio, text and subtitle modes."""
    print("Audio modes: silent, music, voiceover, voiceover+music")
    print("Text modes: none, subtitle, title_cards")
    print("Subtitle modes: static, typewriter, word-by-word")
    print("Platforms: reels, tiktok, youtube-shorts, landscape")