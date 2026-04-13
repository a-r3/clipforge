"""social-pack command — generate social media content pack."""

from __future__ import annotations

import sys

import click


@click.command("social-pack")
@click.option("--script-file", "-s", default=None, help="Path to script text file.")
@click.option("--script-text", "-t", default="", help="Inline script text.")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform.")
@click.option("--brand-name", "-b", default="", help="Brand name.")
@click.option("--output", "-o", default=None, help="Save pack as JSON file.")
def social_pack(
    script_file: str | None,
    script_text: str,
    platform: str,
    brand_name: str,
    output: str | None,
) -> None:
    """Generate a social media content pack from a script."""
    import os

    text = script_text
    if script_file:
        if not os.path.exists(script_file):
            click.echo(f"Error: Script file not found: {script_file}", err=True)
            sys.exit(1)
        with open(script_file, encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        click.echo("Error: No script provided.", err=True)
        sys.exit(1)

    from clipforge.social_pack import generate_social_pack

    pack = generate_social_pack(text, platform=platform, brand_name=brand_name)

    click.echo(f"\nSocial Pack for {platform.upper()}")
    click.echo("=" * 50)
    click.echo(f"Title:\n  {pack['title']}\n")
    click.echo(f"Hook:\n  {pack['hook']}\n")
    click.echo(f"CTA:\n  {pack['cta']}\n")
    click.echo(f"Hashtags:\n  {pack['hashtags']}\n")
    click.echo(f"Caption:\n{pack['caption']}")

    if output:
        from clipforge.utils import save_json
        save_json(pack, output)
        click.echo(f"\nSaved to: {output}")
