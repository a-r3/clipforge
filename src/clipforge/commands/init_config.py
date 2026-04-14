"""init-config command — create a starter config JSON file."""

from __future__ import annotations

import sys

import click


# Required / commonly changed fields only. Advanced fields are optional.
_ESSENTIAL_CONFIG = {
    "script_file": "examples/script_example.txt",
    "output": "output/video.mp4",
    "platform": "reels",
    "brand_name": "",
    "style": "clean",
    "audio_mode": "silent",
    "text_mode": "subtitle",
    "subtitle_mode": "static",
}

# Advanced fields shown in the config but with safe defaults
_ADVANCED_CONFIG = {
    "music_file": "",
    "music_volume": 0.12,
    "auto_voice": False,
    "voice_language": "en",
    "intro_text": "",
    "outro_text": "",
    "logo_file": "",
    "watermark_position": "bottom-right",
    "ai_mode": "off",
    "ai_provider": "",
    "ai_model": "",
    "max_scenes": 15,
}


@click.command("init-config")
@click.option("--output", "-o", default="config.json", show_default=True,
              help="Where to save the config file.")
@click.option("--platform", "-p", default="reels", show_default=True,
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform (sets aspect ratio and smart defaults).")
@click.option("--minimal", is_flag=True, default=False,
              help="Write only the essential fields (shorter file).")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite an existing file.")
def init_config(output: str, platform: str, minimal: bool, force: bool) -> None:
    """Create a starter config JSON file.

    Edit the file to customise your video, then run:

      clipforge make --config config.json

    Or use the wizard for a guided setup:

      clipforge wizard
    """
    import os
    from clipforge.utils import save_json

    if os.path.exists(output) and not force:
        click.echo(f"  File already exists: {output}")
        click.echo(f"  Use --force to overwrite, or choose a different --output path.")
        sys.exit(1)

    config = dict(_ESSENTIAL_CONFIG)
    config["platform"] = platform
    # Apply smart style/subtitle defaults for the chosen platform
    if platform in ("reels", "tiktok"):
        config["style"] = "bold"
        config["subtitle_mode"] = "word-by-word"

    if not minimal:
        config.update(_ADVANCED_CONFIG)

    save_json(config, output)
    click.echo(f"\n  Config written to: {output}")
    click.echo(f"  Platform: {platform}")
    click.echo()
    click.echo("  Next steps:")
    click.echo(f"    Edit the file, then: clipforge make --config {output}")
    click.echo(f"    Or preview first:    clipforge make --config {output} --dry-run")
    click.echo()
