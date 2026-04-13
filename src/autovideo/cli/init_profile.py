"""
`autovideo init-profile` subcommand.

Creates a template channel profile JSON file for branding and customisation.
"""

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo init-profile", description="Create a default profile file."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the profile JSON file.",
    )
    args = parser.parse_args(argv)
    output_path = Path(args.output)
    default_profile = {
        "brand_name": "YourBrand",
        "logo_file": "assets/logo/placeholder.txt",
        "intro_text": "Welcome",
        "outro_text": "Thanks for watching",
        "voice_language": "az",
        "style": "clean",
    }
    output_path.write_text(json.dumps(default_profile, indent=2), encoding="utf-8")
    print(f"Created profile file at {output_path}")
