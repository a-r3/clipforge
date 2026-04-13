"""make command — the main video creation pipeline."""

from __future__ import annotations

import sys

import click


@click.command("make")
@click.option("--script-file", "-s", default=None, help="Path to script text file.")
@click.option("--config", "-c", "config_file", default=None, help="Path to config JSON file.")
@click.option("--output", "-o", default=None, help="Output video path (e.g. output/video.mp4).")
@click.option("--platform", "-p", default=None,
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform.")
@click.option("--preset", default=None, help="Apply a named preset.")
@click.option("--style", default=None, help="Visual style (clean, bold, minimal, cinematic).")
@click.option("--audio-mode", default=None,
              type=click.Choice(["silent", "music", "voiceover", "voiceover+music"]),
              help="Audio mode.")
@click.option("--text-mode", default=None,
              type=click.Choice(["none", "subtitle", "title_cards"]),
              help="Text overlay mode.")
@click.option("--subtitle-mode", default=None,
              type=click.Choice(["static", "typewriter", "word-by-word"]),
              help="Subtitle animation mode.")
@click.option("--music-file", default=None, help="Path to background music file.")
@click.option("--brand-name", default=None, help="Brand name for overlays.")
@click.option("--dry-run", is_flag=True, default=False, help="Parse and plan without rendering.")
def make(
    script_file: str | None,
    config_file: str | None,
    output: str | None,
    platform: str | None,
    preset: str | None,
    style: str | None,
    audio_mode: str | None,
    text_mode: str | None,
    subtitle_mode: str | None,
    music_file: str | None,
    brand_name: str | None,
    dry_run: bool,
) -> None:
    """Build a short video from a script."""
    from clipforge.config_loader import load_config, ConfigLoader
    from clipforge.script_parser import ScriptParser
    from clipforge.scene_planner import ScenePlanner

    # Build config
    overrides = {
        k: v for k, v in {
            "script_file": script_file,
            "output": output,
            "platform": platform,
            "style": style,
            "audio_mode": audio_mode,
            "text_mode": text_mode,
            "subtitle_mode": subtitle_mode,
            "music_file": music_file,
            "brand_name": brand_name,
        }.items()
        if v is not None
    }

    config = load_config(config_file, overrides)

    # Validate config
    errors = ConfigLoader().validate(config)
    if errors:
        for err in errors:
            click.echo(f"Config error: {err}", err=True)
        sys.exit(1)

    # Apply preset if specified
    if preset:
        from clipforge.presets import Presets
        p = Presets()
        try:
            config = p.apply_preset(config, preset)
        except KeyError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # Find script
    script_path = config.get("script_file", "")
    script_text = config.get("script_text", "")

    if script_path and not script_text:
        import os
        if not os.path.exists(script_path):
            click.echo(f"Error: Script file not found: {script_path}", err=True)
            sys.exit(1)
        with open(script_path, encoding="utf-8") as f:
            script_text = f.read()

    if not script_text.strip():
        click.echo(
            "Error: No script provided. Use --script-file or set script_file in config.",
            err=True,
        )
        sys.exit(1)

    # Parse script
    parser = ScriptParser(max_scenes=config.get("max_scenes", 15))
    scenes = parser.parse(script_text)
    scene_dicts = [s.to_dict() for s in scenes]

    click.echo(f"Parsed {len(scenes)} scene(s).")

    # Plan scenes
    planner = ScenePlanner(ai_mode=config.get("ai_mode", "off"))
    planned = planner.plan(scene_dicts)

    if dry_run:
        _print_dry_run(planned, config)
        return

    # Build video
    output_path = config.get("output", "output/video.mp4")
    click.echo(f"Building video  -> {output_path}")

    try:
        from clipforge.builder import VideoBuilder
        builder = VideoBuilder()
        summary = builder.build(planned, config, output_path)
        summary.print()
    except Exception as exc:
        click.echo(f"Error building video: {exc}", err=True)
        sys.exit(1)


def _print_dry_run(planned: list, config: dict) -> None:
    """Print a dry-run scene plan."""
    click.echo("Dry run — planned scenes:")
    total = 0.0
    for i, scene in enumerate(planned, 1):
        dur = scene["duration"]
        total += dur
        click.echo(
            f"  Scene {i:2d}: [{scene['visual_type']:12s}] {scene['query']!r:<40s} ({dur:.1f}s)"
        )
    click.echo(
        f"\nTotal: {len(planned)} scene(s), ~{total:.1f}s  |  "
        f"audio={config.get('audio_mode','silent')}  "
        f"text={config.get('text_mode','none')}  "
        f"platform={config.get('platform','reels')}"
    )
