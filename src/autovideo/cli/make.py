"""
`autovideo make` subcommand.

This command builds a video from a script file. It is a thin wrapper around
the core builder functionality.
"""

import argparse
import sys
from pathlib import Path

from autovideo.script_parser import split_script_into_scenes
from autovideo.builder import make_video


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo make", description="Build a video from a script file."
    )
    parser.add_argument(
        "--script-file",
        required=True,
        help="Path to the script file (text).",
    )
    parser.add_argument(
        "--output",
        default="output.mp4",
        help="Path to save the generated video.",
    )
    args = parser.parse_args(argv)
    script_path = Path(args.script_file)
    if not script_path.exists():
        print(f"Script file not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    script_text = script_path.read_text(encoding="utf-8")
    # In a full implementation, scenes would be used for planning.
    split_script_into_scenes(script_text)
    output_path = make_video(script_text, out_name=args.output)
    print(f"Video created at {output_path}")
