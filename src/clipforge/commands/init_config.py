"""init-config command — create a starter config JSON file."""

from __future__ import annotations

import sys

import click


_DEFAULT_CONFIG = {
    "script_file": "examples/script_example.txt",
    "output": "output/video.mp4",
    "platform": "reels",
    "style": "clean",
    "audio_mode": "silent",
    "text_mode": "subtitle",
    "subtitle_mode": "static",
    "music_file": "",
    "music_volume": 0.12,
    "auto_voice": False,
    "voice_language": "en",
    "intro_text": "",
    "outro_text": "",
    "logo_file": "",
    "watermark_position": "top-right",
    "ai_mode": "off",
    "ai_provider": "",
    "ai_model": "",
    "max_scenes": 15,
    "brand_name": "",
}


@click.command("init-config")
@click.option("--output", "-o", default="config.json", show_default=True, help="Output config file path.")
@click.option("--platform", "-p", default="reels", show_default=True,
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform.")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing file.")
def init_config(output: str, platform: str, force: bool) -> None:
    """Create a starter ClipForge config JSON file."""
    import os
    from clipforge.utils import save_json

    if os.path.exists(output) and not force:
        click.echo(f"File already exists: {output}. Use --force to overwrite.")
        sys.exit(1)

    config = dict(_DEFAULT_CONFIG)
    config["platform"] = platform

    save_json(config, output)
    click.echo(f"Config written to: {output}")
    click.echo("Edit the file to customise your video settings.")
