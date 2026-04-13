"""
`autovideo scenes` subcommand.

Lists scenes extracted from a script file. Useful to verify how a script is
segmented before building a video.
"""

import argparse
import sys
from pathlib import Path

from autovideo.script_parser import split_script_into_scenes


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo scenes", description="List scenes extracted from a script."
    )
    parser.add_argument(
        "--script-file",
        required=True,
        help="Path to the script file.",
    )
    args = parser.parse_args(argv)
    script_path = Path(args.script_file)
    if not script_path.exists():
        print(f"Script file not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    script_text = script_path.read_text(encoding="utf-8")
    scenes = split_script_into_scenes(script_text)
    for idx, scene in enumerate(scenes, 1):
        print(f"{idx}. {scene}")
