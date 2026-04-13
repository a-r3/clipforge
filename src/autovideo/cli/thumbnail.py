"""
`autovideo thumbnail` subcommand.

Generates a thumbnail image. This stub simply prints the provided arguments.
"""

import argparse


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo thumbnail", description="Create a thumbnail image (stub)."
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Text to display on the thumbnail.",
    )
    parser.add_argument(
        "--platform",
        default="reels",
        help="Target platform preset.",
    )
    parser.add_argument(
        "--brand-name",
        default="",
        help="Optional brand name to include.",
    )
    parser.add_argument(
        "--output",
        default="thumbnail.jpg",
        help="Output path for the thumbnail image.",
    )
    args = parser.parse_args(argv)
    print(
        f"Would generate a thumbnail with text '{args.text}' for {args.platform} as {args.output} (not implemented)."
    )
