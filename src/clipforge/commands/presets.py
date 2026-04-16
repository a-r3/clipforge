"""Presets command — list available presets."""

from __future__ import annotations

import click

_PRESET_DESCRIPTIONS = {
    "clean": "Light background music, static subtitles, clean fonts. Good all-rounder.",
    "bold": "Title cards, prominent text, music. Best for Reels / TikTok hooks.",
    "minimal": "No text overlay, no audio. Pure visuals — for cinematic b-roll.",
    "cinematic": "Word-by-word subtitles, voiceover + music. Storytelling style.",
}


@click.command("presets")
@click.option("--preset", "-p", default=None,
              help="Show full details for a specific preset.")
def presets_cmd(preset: str | None) -> None:
    """List available style presets.

    Presets bundle style + text + audio settings into a single name.
    Apply one with:

      clipforge make --script-file script.txt --preset bold

    Or set it in your config.json:

      { "preset": "cinematic" }
    """
    from clipforge.presets import Presets

    p = Presets()
    available = p.list_presets()

    if preset:
        try:
            data = p.get_preset(preset)
            click.echo(f"\n  Preset: {preset}")
            desc = _PRESET_DESCRIPTIONS.get(preset, "")
            if desc:
                click.echo(f"  {desc}")
            click.echo("  " + "─" * 36)
            for key, value in data.items():
                click.echo(f"  {key:<20} {value}")
        except KeyError as exc:
            click.echo(f"Error: {exc}", err=True)
        return

    click.echo("\n  Available presets:\n")
    for name in available:
        try:
            data = p.get_preset(name)
            style = data.get("style", name)
            text_mode = data.get("text_mode", "subtitle")
            audio_mode = data.get("audio_mode", "silent")
            desc = _PRESET_DESCRIPTIONS.get(name, "")
            click.echo(f"  {name:<12} style={style:<10} text={text_mode:<12} audio={audio_mode}")
            if desc:
                click.echo(f"             {desc}")
        except Exception:
            click.echo(f"  {name}")
        click.echo()

    click.echo("  Apply: clipforge make --preset <name>")
    click.echo("  Info:  clipforge presets --preset <name>")
    click.echo()
