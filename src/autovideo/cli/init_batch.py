"""
`autovideo init-batch` subcommand.

Creates a template batch job configuration file. Each job corresponds to a
single video.
"""

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo init-batch", description="Create a batch configuration template."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the batch configuration JSON file.",
    )
    args = parser.parse_args(argv)
    output_path = Path(args.output)
    default_batch = {
        "jobs": [
            {
                "script_file": "examples/script_example.txt",
                "output": "output/demo.mp4",
                "platform": "reels",
                "style": "clean",
            }
        ]
    }
    output_path.write_text(json.dumps(default_batch, indent=2), encoding="utf-8")
    print(f"Created batch configuration file at {output_path}")
