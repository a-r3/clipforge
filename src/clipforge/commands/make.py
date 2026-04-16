"""make command — the main video creation pipeline."""

from __future__ import annotations

import sys

import click


@click.command("make")
@click.option("--script-file", "-s", default=None,
              help="Path to your script text file.")
@click.option("--config", "-c", "config_file", default=None,
              help="Path to a JSON config file (see clipforge init-config).")
@click.option("--output", "-o", default=None,
              help="Output video path. Default: output/video.mp4")
@click.option("--platform", "-p", default=None,
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Target platform. Sets aspect ratio and smart defaults. Default: reels")
@click.option("--preset", default=None,
              help="Apply a named style preset (clean, bold, minimal, cinematic). "
                   "Run 'clipforge presets' to see all options.")
@click.option("--style", default=None,
              help="Visual style: clean, bold, minimal, or cinematic.")
@click.option("--audio-mode", default=None,
              type=click.Choice(["silent", "music", "voiceover", "voiceover+music"]),
              help="Audio: silent | music | voiceover | voiceover+music")
@click.option("--text-mode", default=None,
              type=click.Choice(["none", "subtitle", "title_cards"]),
              help="Text overlay: none | subtitle | title_cards")
@click.option("--subtitle-mode", default=None,
              type=click.Choice(["static", "typewriter", "word-by-word"]),
              help="Subtitle style: static | typewriter | word-by-word")
@click.option("--music-file", default=None,
              help="Path to a background music file (.mp3/.wav).")
@click.option("--brand-name", default=None,
              help="Your brand name (shown in social pack and overlays).")
@click.option("--profile", default=None,
              help="Path to a brand profile JSON (see clipforge init-profile).")
@click.option("--optimization-report", default=None,
              help="Optional optimization report JSON to review before rendering.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview the scene plan without rendering the video.")
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
    profile: str | None,
    optimization_report: str | None,
    dry_run: bool,
) -> None:
    """Build a short video from a script.

    Minimal usage:

      clipforge make --script-file script.txt

    With a config file:

      clipforge make --config myconfig.json

    Dry-run to preview the plan without rendering:

      clipforge make --script-file script.txt --dry-run
    """
    from clipforge.config_loader import ConfigLoader, load_config
    from clipforge.scene_planner import ScenePlanner
    from clipforge.script_parser import ScriptParser

    # Build overrides from CLI flags (None values are stripped inside load_config)
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

    # Apply brand profile (fills missing keys without overriding explicit values)
    if profile:
        import os
        if not os.path.exists(profile):
            click.echo(f"Error: Profile file not found: {profile}", err=True)
            sys.exit(1)
        from clipforge.profile import BrandProfile
        bp = BrandProfile.load(profile)
        config = bp.apply_to_config(config)
        click.echo(f"Profile applied : {profile} (brand: {bp.brand_name or 'unnamed'})")

    if optimization_report:
        import os
        if not os.path.exists(optimization_report):
            click.echo(f"Error: Optimization report file not found: {optimization_report}", err=True)
            sys.exit(1)
        from clipforge.optimize.models import OptimizationReport
        report = OptimizationReport.load(optimization_report)
        _echo_optimization_notes(report.next_video_brief)

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
            click.echo(f"Preset applied  : {preset}")
        except KeyError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

    # Find script text
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
            "Error: No script provided.\n"
            "  Use --script-file path/to/script.txt\n"
            "  Or set script_file in a config JSON (see clipforge init-config).",
            err=True,
        )
        sys.exit(1)

    # Parse script
    parser = ScriptParser(max_scenes=config.get("max_scenes", 15))
    scenes = parser.parse(script_text)
    scene_dicts = [s.to_dict() for s in scenes]

    # Show what was auto-selected so the user knows what's happening
    _echo_selected_settings(config)
    click.echo(f"Scenes parsed   : {len(scenes)}")

    # Plan scenes
    from clipforge.ai.factory import AIFactory
    ai_provider = AIFactory.from_config(config)
    planner = ScenePlanner(ai_mode=config.get("ai_mode", "off"), ai_provider=ai_provider)
    planned = planner.plan(scene_dicts)

    if dry_run:
        _print_dry_run(planned, config)
        return

    # Build video
    output_path = config.get("output", "output/video.mp4")
    click.echo("\nRendering video ...")

    try:
        from clipforge.builder import VideoBuilder
        builder = VideoBuilder()
        summary = builder.build(planned, config, output_path)
        summary.print()
    except Exception as exc:
        click.echo(f"\nError building video: {exc}", err=True)
        sys.exit(1)


def _echo_selected_settings(config: dict) -> None:
    """Print the key settings being used, clearly marking auto-selected ones."""
    platform = config.get("platform", "reels")
    style = config.get("style", "clean")
    audio = config.get("audio_mode", "silent")
    text = config.get("text_mode", "subtitle")
    subtitle = config.get("subtitle_mode", "static")

    click.echo(
        f"Platform        : {platform}  |  "
        f"style={style}  audio={audio}  text={text}/{subtitle}"
    )


def _print_dry_run(planned: list, config: dict) -> None:
    """Print a dry-run scene plan."""
    click.echo("\nDry run — planned scenes:")
    total = 0.0
    for i, scene in enumerate(planned, 1):
        dur = scene["duration"]
        total += dur
        conf = scene.get("confidence", 0.0)
        conf_str = f" conf={conf:.0%}" if conf else ""
        click.echo(
            f"  Scene {i:2d}: [{scene['visual_type']:12s}] "
            f"{scene.get('primary_query', scene['query'])!r:<40s} "
            f"({dur:.1f}s{conf_str})"
        )
    click.echo(
        f"\nTotal : {len(planned)} scene(s), ~{total:.1f}s"
        f"  platform={config.get('platform','reels')}"
        f"  audio={config.get('audio_mode','silent')}"
        f"  text={config.get('text_mode','none')}"
    )
    click.echo("\nRun without --dry-run to render the video.")


def _echo_optimization_notes(brief: dict) -> None:
    """Print optimization guidance before building."""
    if not brief:
        return
    click.echo("Optimization notes:")
    if brief.get("platform"):
        click.echo(f"  Platform goal : {brief['platform']}")
    if brief.get("template_ref"):
        click.echo(f"  Template goal : {brief['template_ref']}")
    if brief.get("title_direction"):
        click.echo(f"  Title         : {brief['title_direction']}")
    if brief.get("hook_direction"):
        click.echo(f"  Hook          : {brief['hook_direction']}")
    if brief.get("thumbnail_direction"):
        click.echo(f"  Thumbnail     : {brief['thumbnail_direction']}")
    click.echo()
