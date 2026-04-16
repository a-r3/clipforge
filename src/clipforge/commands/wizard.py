"""wizard command — interactive configuration wizard."""

from __future__ import annotations

import click

_PLATFORM_LABELS = {
    "reels": "Instagram Reels (9:16 vertical)",
    "tiktok": "TikTok (9:16 vertical)",
    "youtube-shorts": "YouTube Shorts (9:16 vertical)",
    "youtube": "YouTube (16:9 landscape)",
    "landscape": "Landscape / generic (16:9)",
}

_AUDIO_LABELS = {
    "silent": "No audio",
    "music": "Background music (you provide an .mp3 file)",
    "voiceover": "Auto-generated voiceover (pyttsx3)",
    "voiceover+music": "Voiceover + background music",
}


@click.command("wizard")
@click.option("--output", "-o", default="config.json", show_default=True,
              help="Where to save the generated config file.")
@click.option("--quick", is_flag=True, default=False,
              help="Quick mode: only ask the 3 essential questions.")
def wizard(output: str, quick: bool) -> None:
    """Interactive setup wizard — create a config file in under a minute.

    Asks a few questions and writes a ready-to-use config.json.
    Then run:  clipforge make --config config.json

    Use --quick to answer only the essentials and skip optional settings.
    """

    click.echo()
    click.echo("  ClipForge Setup Wizard")
    click.echo("  " + "─" * 38)
    click.echo("  Press Enter to accept the [default] for each question.")
    click.echo()

    # ── Essential questions ──────────────────────────────────────────────
    click.echo("  ESSENTIAL")
    click.echo()

    script_file = click.prompt(
        "  1. Script file path",
        default="examples/script_example.txt",
    )

    click.echo()
    click.echo("  Platform options:")
    for key, label in _PLATFORM_LABELS.items():
        click.echo(f"    {key:<18} {label}")
    platform = click.prompt(
        "\n  2. Target platform",
        default="reels",
        type=click.Choice(list(_PLATFORM_LABELS.keys()), case_sensitive=False),
    )

    video_output = click.prompt(
        "\n  3. Output video path",
        default="output/video.mp4",
    )

    if quick:
        # Quick mode: fill everything else with smart defaults
        config = _build_config(
            script_file=script_file,
            video_output=video_output,
            platform=platform,
            style=_smart_style(platform),
            audio_mode="silent",
            text_mode="subtitle",
            subtitle_mode=_smart_subtitle_mode(platform),
            music_file="",
            brand_name="",
            logo_file="",
            ai_mode="off",
        )
        _save_and_finish(config, output)
        return

    # ── Optional extras ──────────────────────────────────────────────────
    click.echo()
    click.echo("  OPTIONAL EXTRAS  (press Enter to skip)")
    click.echo()

    brand_name = click.prompt("  Brand name (shown in overlays)", default="")

    click.echo()
    click.echo("  Audio options:")
    for key, label in _AUDIO_LABELS.items():
        click.echo(f"    {key:<20} {label}")
    audio_mode = click.prompt(
        "\n  Audio mode",
        default="silent",
        type=click.Choice(list(_AUDIO_LABELS.keys()), case_sensitive=False),
    )

    music_file = ""
    if audio_mode in ("music", "voiceover+music"):
        music_file = click.prompt(
            "  Music file path (.mp3/.wav)",
            default="assets/music/background.mp3",
        )

    click.echo()
    click.echo("  Style options: clean, bold, minimal, cinematic")
    style = click.prompt(
        "  Visual style",
        default=_smart_style(platform),
        type=click.Choice(["clean", "bold", "minimal", "cinematic"], case_sensitive=False),
    )

    # ── Advanced (optional) ──────────────────────────────────────────────
    click.echo()
    click.echo("  ADVANCED  (press Enter to skip all — safe defaults will be used)")
    click.echo()

    show_advanced = click.confirm("  Configure advanced options?", default=False)

    subtitle_mode = _smart_subtitle_mode(platform)
    text_mode = "subtitle"
    logo_file = ""
    ai_mode = "off"

    if show_advanced:
        click.echo()
        text_mode = click.prompt(
            "  Text mode (subtitle / title_cards / none)",
            default="subtitle",
            type=click.Choice(["none", "subtitle", "title_cards"], case_sensitive=False),
        )
        if text_mode == "subtitle":
            subtitle_mode = click.prompt(
                "  Subtitle animation (static / typewriter / word-by-word)",
                default=_smart_subtitle_mode(platform),
                type=click.Choice(["static", "typewriter", "word-by-word"], case_sensitive=False),
            )
        logo_file = click.prompt("  Logo file path (leave blank for none)", default="")
        ai_mode = click.prompt(
            "  AI mode (off / assist / full)",
            default="off",
            type=click.Choice(["off", "assist", "full"], case_sensitive=False),
        )

    config = _build_config(
        script_file=script_file,
        video_output=video_output,
        platform=platform,
        style=style,
        audio_mode=audio_mode,
        text_mode=text_mode,
        subtitle_mode=subtitle_mode,
        music_file=music_file,
        brand_name=brand_name,
        logo_file=logo_file,
        ai_mode=ai_mode,
    )
    _save_and_finish(config, output)


def _smart_style(platform: str) -> str:
    return "bold" if platform in ("reels", "tiktok") else "clean"


def _smart_subtitle_mode(platform: str) -> str:
    return "word-by-word" if platform in ("reels", "tiktok") else "static"


def _build_config(
    *,
    script_file: str,
    video_output: str,
    platform: str,
    style: str,
    audio_mode: str,
    text_mode: str,
    subtitle_mode: str,
    music_file: str,
    brand_name: str,
    logo_file: str,
    ai_mode: str,
) -> dict:
    return {
        "script_file": script_file,
        "output": video_output,
        "platform": platform,
        "style": style,
        "audio_mode": audio_mode,
        "text_mode": text_mode,
        "subtitle_mode": subtitle_mode,
        "music_file": music_file,
        "music_volume": 0.12,
        "auto_voice": audio_mode in ("voiceover", "voiceover+music"),
        "voice_language": "en",
        "intro_text": "",
        "outro_text": "Follow for more" if brand_name else "",
        "brand_name": brand_name,
        "logo_file": logo_file,
        "watermark_position": "bottom-right",
        "ai_mode": ai_mode,
        "ai_provider": "",
        "ai_model": "",
        "max_scenes": 15,
    }


def _save_and_finish(config: dict, output: str) -> None:
    from clipforge.utils import save_json
    save_json(config, output)
    click.echo()
    click.echo("  ─" * 20)
    click.echo(f"  Config saved to: {output}")
    click.echo()
    click.echo("  Next steps:")
    click.echo(f"    Preview the plan : clipforge make --config {output} --dry-run")
    click.echo(f"    Build your video : clipforge make --config {output}")
    click.echo()
