"""
`autovideo presets` subcommand.

Lists the available platforms and styles defined in the data presets.
"""

import argparse

from autovideo.presets import list_platforms, list_styles


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo presets", description="List available platforms and styles."
    )
    parser.parse_args(argv)
    platforms = ", ".join(list_platforms())
    styles = ", ".join(list_styles())
    print(f"Platforms: {platforms}")
    print(f"Styles: {styles}")
