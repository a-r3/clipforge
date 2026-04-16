"""init-profile command — create a brand profile JSON file."""

from __future__ import annotations

import sys

import click


@click.command("init-profile")
@click.option("--output", "-o", default="profile.json", show_default=True,
              help="Where to save the profile file.")
@click.option("--brand-name", "-b", default="MyBrand",
              help="Your brand or channel name.")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Default platform for your channel.")
@click.option("--style", default=None,
              type=click.Choice(["clean", "bold", "minimal", "cinematic"]),
              help="Default visual style. Auto-selected from platform if omitted.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite an existing profile file.")
def init_profile(output: str, brand_name: str, platform: str, style: str | None, force: bool) -> None:
    """Create a brand profile — save your channel defaults once, reuse everywhere.

    A profile stores your brand name, platform, style, and other preferences.
    Apply it to any build with:

      clipforge make --script-file script.txt --profile profile.json

    Examples:

      clipforge init-profile --brand-name TechBrief --platform reels
      clipforge init-profile --output mybrand.json --brand-name MyBrand --style bold
    """
    import os

    from clipforge.profile import BrandProfile

    if os.path.exists(output) and not force:
        click.echo(f"  File already exists: {output}")
        click.echo("  Use --force to overwrite, or choose a different --output path.")
        sys.exit(1)

    # Auto-pick style from platform if not given
    if style is None:
        style = "bold" if platform in ("reels", "tiktok") else "clean"

    profile = BrandProfile(
        brand_name=brand_name,
        platform=platform,
        style=style,
        audio_mode="silent",
        text_mode="subtitle",
        subtitle_mode="word-by-word" if platform in ("reels", "tiktok") else "static",
        music_file="",
        music_volume=0.12,
        intro_text=brand_name,
        outro_text="Follow for more",
        watermark_text=brand_name,
        watermark_position="bottom-right",
        watermark_opacity=0.7,
        watermark_size=24,
        ai_mode="off",
        ai_provider="",
        ai_model="",
        logo_file="",
    )
    profile.save(output)

    click.echo()
    click.echo(f"  Profile saved to: {output}")
    click.echo()
    click.echo(f"  Brand   : {brand_name}")
    click.echo(f"  Platform: {platform}  |  style={style}")
    click.echo()
    click.echo("  To use this profile in any build:")
    click.echo(f"    clipforge make --script-file script.txt --profile {output}")
    click.echo()
    click.echo(f"  Edit {output} to customise watermark, music, AI mode, and more.")
    click.echo()
