"""Scenes command — parse a script and show scene breakdown."""

from __future__ import annotations

import sys

import click


@click.command("scenes")
@click.option("--script-file", "-s", required=False, help="Path to script text file.")
@click.option("--script-text", "-t", default="", help="Inline script text.")
@click.option("--max-scenes", default=15, show_default=True, help="Maximum scenes to parse.")
@click.option("--json-output", is_flag=True, default=False, help="Output as JSON.")
def scenes(
    script_file: str | None,
    script_text: str,
    max_scenes: int,
    json_output: bool,
) -> None:
    """Parse a script and display the scene breakdown."""
    from clipforge.script_parser import ScriptParser

    # Load script
    text = script_text
    if script_file:
        import os
        if not os.path.exists(script_file):
            click.echo(f"Error: Script file not found: {script_file}", err=True)
            sys.exit(1)
        with open(script_file, encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        click.echo("Error: No script text provided. Use --script-file or --script-text.", err=True)
        sys.exit(1)

    parser = ScriptParser(max_scenes=max_scenes)
    parsed_scenes = parser.parse(text)

    if json_output:
        import json
        data = [s.to_dict() for s in parsed_scenes]
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"Script parsed into {len(parsed_scenes)} scene(s):\n")
    for scene in parsed_scenes:
        click.echo(f"Scene {scene.index + 1}:")
        click.echo(f"  Duration : ~{scene.estimated_duration:.1f}s")
        click.echo(f"  Visual   : {scene.visual_intent}")
        click.echo(f"  Keywords : {', '.join(scene.keywords[:5])}")
        click.echo(f"  Text     : {scene.text[:80]}{'...' if len(scene.text) > 80 else ''}")
        click.echo()
