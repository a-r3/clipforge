"""social-pack command — generate social media content pack."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command("social-pack")
@click.option("--script-file", "-s", default=None,
              help="Path to your script text file.")
@click.option("--script-text", "-t", default="",
              help="Inline script text (alternative to --script-file).")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform. Default: reels")
@click.option("--brand-name", "-b", default="",
              help="Your brand name (included in title and CTAs).")
@click.option("--show-variants", is_flag=True, default=False,
              help="Show alternative title/hook/CTA options.")
@click.option("--save-json", default=None, metavar="PATH",
              help="Save the full pack to a JSON file.")
@click.option("--save-txt", default=None, metavar="PATH",
              help="Save the full pack to a plain-text file.")
def social_pack(
    script_file: str | None,
    script_text: str,
    platform: str,
    brand_name: str,
    show_variants: bool,
    save_json: str | None,
    save_txt: str | None,
) -> None:
    """Generate a social media content pack from your script.

    Produces a ready-to-use title, hook, CTA, hashtags, and caption.

    Examples:

      clipforge social-pack --script-file script.txt --platform reels

      clipforge social-pack --script-file script.txt --brand-name MyBrand \\
          --save-json output/social.json --save-txt output/social.txt
    """
    import os

    text = script_text
    if script_file:
        if not os.path.exists(script_file):
            click.echo(f"Error: Script file not found: {script_file}", err=True)
            sys.exit(1)
        with open(script_file, encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        click.echo(
            "Error: No script provided.\n"
            "  Use --script-file path/to/script.txt\n"
            "  Or pass inline text with --script-text '...'",
            err=True,
        )
        sys.exit(1)

    from clipforge.social_pack import generate_social_pack

    pack = generate_social_pack(text, platform=platform, brand_name=brand_name)

    # ── Clean primary output ─────────────────────────────────────────────
    click.echo()
    click.echo(f"  Social Pack — {platform.upper()}")
    click.echo("  " + "─" * 40)
    click.echo(f"  Title     : {pack['title']}")
    click.echo(f"  Hook      : {pack['hook']}")
    click.echo(f"  CTA       : {pack['cta']}")
    click.echo(f"  Hashtags  : {pack['hashtags']}")
    click.echo()
    click.echo("  Caption:")
    for line in pack["caption"].splitlines():
        click.echo(f"  {line}")

    # ── Optional variants section ────────────────────────────────────────
    if show_variants:
        click.echo()
        click.echo("  " + "─" * 40)
        click.echo("  VARIANTS  (alternative options for A/B testing)")
        click.echo()

        title_variants = pack.get("title_variants", [])
        if len(title_variants) > 1:
            click.echo("  Title options:")
            for i, t in enumerate(title_variants, 1):
                click.echo(f"    {i}. {t}")

        hook_variants = pack.get("hook_variants", [])
        if len(hook_variants) > 1:
            click.echo("  Hook options:")
            for i, h in enumerate(hook_variants, 1):
                click.echo(f"    {i}. {h}")

        cta_variants = pack.get("cta_variants", [])
        if len(cta_variants) > 1:
            click.echo("  CTA options:")
            for i, c in enumerate(cta_variants, 1):
                click.echo(f"    {i}. {c}")

    # ── Save files ───────────────────────────────────────────────────────
    if save_json:
        from clipforge.utils import ensure_dir
        from clipforge.utils import save_json as _save_json
        ensure_dir(Path(save_json).parent)
        _save_json(pack, save_json)
        click.echo(f"\n  JSON saved  : {save_json}")

    if save_txt:
        from clipforge.utils import ensure_dir
        ensure_dir(Path(save_txt).parent)
        _write_txt(pack, save_txt)
        click.echo(f"  TXT saved   : {save_txt}")

    click.echo()


def _write_txt(pack: dict, path: str) -> None:
    """Write a social pack dict to a structured plain-text file."""
    lines = [
        f"Platform : {pack.get('platform', '')}",
        f"Brand    : {pack.get('brand_name', '')}",
        "",
        "TITLE",
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
    # Append variants if present
    title_variants = pack.get("title_variants", [])
    hook_variants = pack.get("hook_variants", [])
    cta_variants = pack.get("cta_variants", [])
    if len(title_variants) > 1 or len(hook_variants) > 1 or len(cta_variants) > 1:
        lines += ["", "VARIANTS", "--------"]
        if len(title_variants) > 1:
            lines.append("Title options:")
            lines.extend(f"  {t}" for t in title_variants)
        if len(hook_variants) > 1:
            lines.append("Hook options:")
            lines.extend(f"  {h}" for h in hook_variants)
        if len(cta_variants) > 1:
            lines.append("CTA options:")
            lines.extend(f"  {c}" for c in cta_variants)

    Path(path).write_text("\n".join(lines), encoding="utf-8")
