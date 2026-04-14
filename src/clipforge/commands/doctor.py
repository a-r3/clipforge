"""Doctor command — check system requirements for ClipForge."""

from __future__ import annotations

import os
import subprocess
import sys

import click


def _ok(msg: str) -> None:
    click.echo(f"  [OK]    {msg}")


def _warn(msg: str) -> None:
    click.echo(f"  [WARN]  {msg}")


def _error(msg: str) -> None:
    click.echo(f"  [ERROR] {msg}")



@click.command("doctor")
@click.option("--config", "config_file", default=None,
              help="Also validate a specific config file.")
def doctor(config_file: str | None) -> None:
    """Check that your system is ready to use ClipForge.

    Checks Python version, FFmpeg, .env file, API keys, and packages.
    Run this after installation, or whenever something seems broken.

    Examples:

      clipforge doctor
      clipforge doctor --config myconfig.json
    """
    click.echo("\n  ClipForge Doctor")
    click.echo("  " + "─" * 38)
    all_ok = True

    click.echo()
    # 1. Python version
    version = sys.version_info
    if version >= (3, 10):
        _ok(f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        _error(f"Python {version.major}.{version.minor}.{version.micro} — requires 3.10+")
        all_ok = False

    # 2. FFmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            first_line = result.stdout.decode(errors="ignore").split("\n")[0]
            _ok(f"FFmpeg found: {first_line[:60]}")
        else:
            _error("FFmpeg returned non-zero exit code.")
            all_ok = False
    except FileNotFoundError:
        _error("FFmpeg not found on PATH. Install from https://ffmpeg.org/")
        all_ok = False
    except Exception as exc:
        _warn(f"Could not check FFmpeg: {exc}")

    # 3. .env file
    if os.path.exists(".env"):
        _ok(".env file found.")
    else:
        _warn(".env file not found. Copy .env.example to .env and fill in keys.")

    # 4. API keys
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "")

    if pexels_key:
        _ok(f"PEXELS_API_KEY set ({pexels_key[:4]}***)")
    else:
        _warn("PEXELS_API_KEY not set. Stock video from Pexels will not work.")

    if pixabay_key:
        _ok(f"PIXABAY_API_KEY set ({pixabay_key[:4]}***)")
    else:
        _warn("PIXABAY_API_KEY not set. Stock media from Pixabay will not work.")

    # 5. Check config file if provided
    if config_file:
        if os.path.exists(config_file):
            _ok(f"Config file found: {config_file}")
            try:
                from clipforge.config_loader import load_config
                config = load_config(config_file)

                music_file = config.get("music_file", "")
                if music_file:
                    if os.path.exists(music_file):
                        _ok(f"Music file found: {music_file}")
                    else:
                        _warn(f"Music file not found: {music_file}")

                logo_file = config.get("logo_file", "")
                if logo_file:
                    if os.path.exists(logo_file):
                        _ok(f"Logo file found: {logo_file}")
                    else:
                        _warn(f"Logo file not found: {logo_file}")

                ai_mode = config.get("ai_mode", "off")
                if ai_mode != "off":
                    ai_provider = config.get("ai_provider", "")
                    if ai_provider:
                        env_key = f"{ai_provider.upper()}_API_KEY"
                        if os.environ.get(env_key):
                            _ok(f"AI provider '{ai_provider}' key found ({env_key}).")
                        else:
                            _warn(f"AI mode '{ai_mode}' enabled but {env_key} not set.")
            except Exception as exc:
                _warn(f"Could not parse config: {exc}")
        else:
            _error(f"Config file not found: {config_file}")
            all_ok = False

    # 6. Required directories
    for directory in ["output", "assets"]:
        if os.path.isdir(directory):
            _ok(f"Directory '{directory}/' exists.")
        else:
            _warn(f"Directory '{directory}/' not found (will be created on first run).")

    # 7. Optional packages
    for pkg, pip_name in [
        ("moviepy", "moviepy"),
        ("PIL", "Pillow"),
        ("rich", "rich"),
        ("pyttsx3", "pyttsx3"),
    ]:
        try:
            __import__(pkg)
            _ok(f"Package '{pip_name}' installed.")
        except ImportError:
            _warn(f"Package '{pip_name}' not installed (optional: pip install {pip_name}).")

    click.echo("\n  " + "─" * 38)
    if all_ok:
        click.echo("  All checks passed. ClipForge is ready!\n")
        click.echo("  Quick start:")
        click.echo("    clipforge wizard                    # create a config interactively")
        click.echo("    clipforge make --script-file script.txt --dry-run  # preview")
        click.echo("    clipforge make --script-file script.txt            # build video")
    else:
        click.echo("  Some checks failed. See [ERROR] and [WARN] lines above.")
        click.echo()
        click.echo("  Common fixes:")
        click.echo("    FFmpeg missing  → sudo apt install ffmpeg  (or brew install ffmpeg)")
        click.echo("    .env missing    → cp .env.example .env  (then add your API keys)")
        click.echo("    Package missing → pip install -e '.[tts]'  (or pip install clipforge)")
    click.echo()
