"""init-profile command — create a profile JSON file."""

from __future__ import annotations

import sys

import click


_PROFILE_TEMPLATE = {
    "brand_name": "MyBrand",
    "logo_file": "assets/logo/logo.png",
    "watermark_position": "top-right",
    "default_platform": "reels",
    "default_style": "clean",
    "default_audio_mode": "music",
    "default_text_mode": "subtitle",
    "default_subtitle_mode": "static",
    "music_file": "assets/music/background.mp3",
    "music_volume": 0.12,
    "intro_text": "",
    "outro_text": "Follow for more",
    "voice_language": "en",
    "auto_voice": False,
    "ai_mode": "off",
    "ai_provider": "",
}


@click.command("init-profile")
@click.option("--output", "-o", default="profile.json", show_default=True, help="Output profile file path.")
@click.option("--brand-name", "-b", default="MyBrand", help="Brand name.")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing file.")
def init_profile(output: str, brand_name: str, force: bool) -> None:
    """Create a starter channel profile JSON file."""
    import os
    from clipforge.utils import save_json

    if os.path.exists(output) and not force:
        click.echo(f"File already exists: {output}. Use --force to overwrite.")
        sys.exit(1)

    profile = dict(_PROFILE_TEMPLATE)
    profile["brand_name"] = brand_name

    save_json(profile, output)
    click.echo(f"Profile written to: {output}")
    click.echo("Edit the file to set your channel defaults.")
