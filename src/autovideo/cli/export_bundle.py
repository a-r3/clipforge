"""
`autovideo export-bundle` subcommand.

Packages the video file and associated social metadata into a single folder.
This stub prints the intended behaviour.
"""

import argparse


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo export-bundle", description="Package video and social metadata together."
    )
    parser.add_argument(
        "--video-file",
        required=True,
        help="Path to the video file.",
    )
    parser.add_argument(
        "--social-json",
        required=True,
        help="Path to the social pack JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default="export",
        help="Directory to write the packaged bundle.",
    )
    args = parser.parse_args(argv)
    print(
        f"Would package {args.video_file} and {args.social_json} into {args.output_dir} (not implemented)."
    )
