"""social-pack command — generate social media content pack."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command("social-pack")
@click.option("--script-file", "-s", default=None, help="Path to script text file.")
@click.option("--script-text", "-t", default="", help="Inline script text.")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform.")
@click.option("--brand-name", "-b", default="", help="Brand name.")
@click.option("--save-json", default=None, metavar="PATH",
              help="Save social pack as a JSON file.")
@click.option("--save-txt", default=None, metavar="PATH",
              help="Save social pack as a plain-text file.")
def social_pack(
    script_file: str | None,
    script_text: str,
    platform: str,
    brand_name: str,
    save_json: str | None,
    save_txt: str | None,
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

    # Terminal preview
    click.echo(f"\nSocial Pack for {platform.upper()}")
    click.echo("=" * 50)
    click.echo(f"Title:\n  {pack['title']}\n")
    click.echo(f"Hook:\n  {pack['hook']}\n")
    click.echo(f"CTA:\n  {pack['cta']}\n")
    click.echo(f"Hashtags:\n  {pack['hashtags']}\n")
    click.echo(f"Caption:\n{pack['caption']}")

    # Save JSON
    if save_json:
        from clipforge.utils import save_json as _save_json, ensure_dir
        ensure_dir(Path(save_json).parent)
        _save_json(pack, save_json)
        click.echo(f"\nJSON saved to : {save_json}")

    # Save TXT
    if save_txt:
        from clipforge.utils import ensure_dir
        ensure_dir(Path(save_txt).parent)
        _write_txt(pack, save_txt)
        click.echo(f"TXT saved to  : {save_txt}")


def _write_txt(pack: dict, path: str) -> None:
    """Write a social pack dict to a plain-text file."""
    lines = [
        f"Platform : {pack.get('platform', '')}",
        f"Brand    : {pack.get('brand_name', '')}",
        "",
        f"TITLE",
        pack.get("title", ""),
        "",
        "HOOK",
        pack.get("hook", ""),
        "",
        "CTA",
        pack.get("cta", ""),
        "",
        "HASHTAGS",
        pack.get("hashtags", ""),
        "",
        "CAPTION",
        "-------",
        pack.get("caption", ""),
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
