"""templates command — list and apply content template packs."""

from __future__ import annotations

import sys

import click


@click.group("templates")
def templates_cmd() -> None:
    """Manage content template packs.

    Templates are starting-point configurations for common content types:
    business, AI, motivation, educational.

    Examples:

      clipforge templates list
      clipforge templates show business
      clipforge templates apply business --output config.json
      clipforge templates sample business
    """


@templates_cmd.command("list")
def templates_list() -> None:
    """List all available content template packs."""
    from clipforge.templates import TemplateManager
    mgr = TemplateManager()
    packs = mgr.list_templates()

    if not packs:
        click.echo("  No templates found.")
        return

    click.echo()
    click.echo("  Available template packs:\n")
    for t in packs:
        name = t.get("name", "?")
        label = t.get("label", name)
        desc = t.get("description", "")
        platform = t.get("platform", "reels")
        style = t.get("style", "clean")
        audio = t.get("audio_mode", "silent")
        click.echo(f"  {name:<14} {label}")
        click.echo(f"               platform={platform}  style={style}  audio={audio}")
        if desc:
            click.echo(f"               {desc}")
        click.echo()

    click.echo("  Apply: clipforge templates apply <name> --output config.json")
    click.echo()


@templates_cmd.command("show")
@click.argument("name")
def templates_show(name: str) -> None:
    """Show details for a template pack."""
    from clipforge.templates import TemplateManager
    mgr = TemplateManager()
    try:
        t = mgr.get(name)
    except KeyError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    click.echo()
    click.echo(f"  Template: {t.get('label', name)}")
    click.echo("  " + "─" * 40)
    config_keys = [
        "platform", "style", "audio_mode", "text_mode", "subtitle_mode",
        "music_volume", "max_scenes", "outro_text",
    ]
    for key in config_keys:
        if key in t:
            click.echo(f"  {key:<20} {t[key]}")

    tags = t.get("suggested_hashtags", [])
    if tags:
        click.echo(f"  {'suggested_hashtags':<20} {' '.join(tags)}")

    click.echo()
    sample = t.get("sample_script", "")
    if sample:
        click.echo("  Sample script (first 120 chars):")
        click.echo(f"    {sample[:120]}{'...' if len(sample) > 120 else ''}")
    click.echo()


@templates_cmd.command("apply")
@click.argument("name")
@click.option("--output", "-o", default="config.json", show_default=True,
              help="Where to write the generated config file.")
@click.option("--script-file", "-s", default=None,
              help="Script file to include in the config.")
@click.option("--brand-name", "-b", default="",
              help="Brand name to include in the config.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite an existing file.")
def templates_apply(name: str, output: str, script_file: str | None, brand_name: str, force: bool) -> None:
    """Generate a config file from a template pack.

    Example:

      clipforge templates apply business --output business.json --brand-name MyBrand
    """
    import os
    from clipforge.templates import TemplateManager
    from clipforge.utils import save_json

    if os.path.exists(output) and not force:
        click.echo(f"  File already exists: {output}  (use --force to overwrite)")
        sys.exit(1)

    mgr = TemplateManager()
    try:
        template = mgr.get(name)
    except KeyError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    config: dict = {}
    for key in ("platform", "style", "audio_mode", "text_mode", "subtitle_mode",
                "music_volume", "max_scenes", "intro_text", "outro_text"):
        if key in template:
            config[key] = template[key]

    config["script_file"] = script_file or "examples/script_example.txt"
    config["output"] = "output/video.mp4"
    config["brand_name"] = brand_name
    config["music_file"] = ""
    config["ai_mode"] = "off"
    config["ai_provider"] = ""

    save_json(config, output)
    click.echo()
    click.echo(f"  Config written from template '{name}' → {output}")
    click.echo(f"  Platform : {config['platform']}  style={config['style']}  audio={config['audio_mode']}")
    click.echo()
    click.echo(f"  Next: clipforge make --config {output}")
    click.echo()


@templates_cmd.command("sample")
@click.argument("name")
@click.option("--output", "-o", default=None,
              help="Write sample script to a file instead of printing it.")
def templates_sample(name: str, output: str | None) -> None:
    """Print or save the sample script for a template pack.

    Example:

      clipforge templates sample motivation --output script.txt
    """
    from clipforge.templates import TemplateManager
    mgr = TemplateManager()
    try:
        script = mgr.get_sample_script(name)
    except KeyError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    if not script:
        click.echo(f"  No sample script for template '{name}'.")
        return

    if output:
        from pathlib import Path
        Path(output).write_text(script, encoding="utf-8")
        click.echo(f"  Sample script written to: {output}")
    else:
        click.echo()
        click.echo(f"  Sample script for '{name}':")
        click.echo("  " + "─" * 40)
        for line in script.splitlines():
            click.echo(f"  {line}")
        click.echo()
