"""
`autovideo init-config` subcommand.

Generates a template configuration JSON file for building a video.
"""

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo init-config", description="Create a default configuration file."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the configuration JSON file.",
    )
    args = parser.parse_args(argv)
    output_path = Path(args.output)
    default_config = {
        "script_file": "examples/script_example.txt",
        "output": "output.mp4",
        "platform": "reels",
        "style": "clean",
        "audio_mode": "silent",
        "text_mode": "none",
    }
    output_path.write_text(json.dumps(default_config, indent=2), encoding="utf-8")
    print(f"Created configuration file at {output_path}")
