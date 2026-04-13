"""
`autovideo social-pack` subcommand.

Generates a social media metadata package from a script file.
"""

import argparse
from pathlib import Path

from autovideo.social_pack import generate_social_pack


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo social-pack", description="Generate social media text and hashtags."
    )
    parser.add_argument(
        "--script-file",
        required=True,
        help="Path to the script file.",
    )
    parser.add_argument(
        "--platform",
        default="reels",
        help="Target platform identifier.",
    )
    parser.add_argument(
        "--brand-name",
        default="",
        help="Brand name to prefix the title.",
    )
    args = parser.parse_args(argv)
    script_text = Path(args.script_file).read_text(encoding="utf-8")
    pack = generate_social_pack(script_text, args.platform, args.brand_name)
    print(pack)
