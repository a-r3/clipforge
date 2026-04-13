"""wizard command — interactive configuration wizard."""

from __future__ import annotations

import click


@click.command("wizard")
@click.option("--output", "-o", default="config.json", show_default=True, help="Output config file path.")
def wizard(output: str) -> None:
    """Interactive wizard to create a ClipForge config file."""
    from clipforge.utils import save_json

    click.echo("ClipForge Setup Wizard")
    click.echo("=" * 40)
    click.echo("Answer the prompts to create your config. Press Enter to accept defaults.\n")

    script_file = click.prompt("Script file path", default="examples/script_example.txt")
    video_output = click.prompt("Output video path", default="output/video.mp4")
    platform = click.prompt(
        "Platform", default="reels",
        type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
    )
    style = click.prompt(
        "Style", default="clean",
        type=click.Choice(["clean", "bold", "minimal", "cinematic"]),
    )
    audio_mode = click.prompt(
        "Audio mode", default="silent",
        type=click.Choice(["silent", "music", "voiceover", "voiceover+music"]),
    )
    text_mode = click.prompt(
        "Text mode", default="subtitle",
        type=click.Choice(["none", "subtitle", "title_cards"]),
    )
    subtitle_mode = click.prompt(
        "Subtitle animation", default="static",
        type=click.Choice(["static", "typewriter", "word-by-word"]),
    )
    music_file = click.prompt("Music file path (leave blank for none)", default="")
    ai_mode = click.prompt(
        "AI mode", default="off",
        type=click.Choice(["off", "assist", "full"]),
    )
    brand_name = click.prompt("Brand name (leave blank for none)", default="")
    logo_file = click.prompt("Logo file path (leave blank for none)", default="")

    config = {
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
        "outro_text": "Follow for more",
        "logo_file": logo_file,
        "watermark_position": "top-right",
        "ai_mode": ai_mode,
        "ai_provider": "",
        "ai_model": "",
        "max_scenes": 15,
        "brand_name": brand_name,
    }

    save_json(config, output)
    click.echo(f"\nConfig saved to: {output}")
    click.echo("Run: clipforge make --config " + output)
