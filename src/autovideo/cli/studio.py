"""
`autovideo studio` subcommand.

Launches an interactive console or GUI for advanced editing. This stub simply
notifies the user that the feature is not yet implemented.
"""

import argparse


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo studio", description="Interactive studio (not implemented)."
    )
    parser.parse_args(argv)
    print("Studio mode is not implemented yet.")
