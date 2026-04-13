"""
`autovideo wizard` subcommand.

Interactive assistant for configuring a new video project. This stub simply
prints a message indicating that the wizard is not yet implemented.
"""

import argparse


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo wizard", description="Interactive configuration wizard."
    )
    parser.parse_args(argv)
    print("Wizard mode is not implemented yet.")
