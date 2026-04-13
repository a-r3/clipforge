"""Presets command — list available presets."""

from __future__ import annotations

import click


@click.command("presets")
@click.option("--preset", "-p", default=None, help="Show details for a specific preset.")
def presets_cmd(preset: str | None) -> None:
    """List available ClipForge presets."""
    from clipforge.presets import Presets

    p = Presets()
    available = p.list_presets()

    if preset:
        try:
            data = p.get_preset(preset)
            click.echo(f"Preset: {preset}")
            click.echo("-" * 30)
            for key, value in data.items():
                click.echo(f"  {key}: {value}")
        except KeyError as exc:
            click.echo(f"Error: {exc}", err=True)
        return

    click.echo("Available presets:\n")
    for name in available:
        try:
            data = p.get_preset(name)
            style = data.get("style", name)
            text_mode = data.get("text_mode", "subtitle")
            audio_mode = data.get("audio_mode", "silent")
            click.echo(f"  {name:<12} style={style}, text={text_mode}, audio={audio_mode}")
        except Exception:
            click.echo(f"  {name}")

    click.echo(f"\nUse with: clipforge make --preset <name>")
