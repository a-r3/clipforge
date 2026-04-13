"""init-batch command — create a starter batch JSON file."""

from __future__ import annotations

import sys

import click


_BATCH_TEMPLATE = {
    "jobs": [
        {
            "script_file": "examples/script_example.txt",
            "output": "output/video_1.mp4",
            "platform": "reels",
            "style": "clean",
            "audio_mode": "silent",
            "text_mode": "subtitle",
        },
        {
            "script_file": "examples/script_example.txt",
            "output": "output/video_2.mp4",
            "platform": "tiktok",
            "style": "bold",
            "audio_mode": "music",
            "text_mode": "title_cards",
        },
    ]
}


@click.command("init-batch")
@click.option("--output", "-o", default="batch.json", show_default=True, help="Output batch file path.")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing file.")
def init_batch(output: str, force: bool) -> None:
    """Create a starter batch jobs JSON file."""
    import os
    from clipforge.utils import save_json

    if os.path.exists(output) and not force:
        click.echo(f"File already exists: {output}. Use --force to overwrite.")
        sys.exit(1)

    save_json(_BATCH_TEMPLATE, output)
    click.echo(f"Batch file written to: {output}")
    click.echo("Edit the file to add your batch jobs.")
