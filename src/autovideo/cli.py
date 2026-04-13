"""Entry point for the `autovideo` command.

This module defines the main function which dispatches to individual
subcommand handlers defined in the `autovideo.cli` subpackage.  The CLI uses
argparse to parse command line arguments and load configuration files.
"""

import argparse
import importlib
import sys


def main(argv: list[str] | None = None) -> None:
    """Parse command line arguments and invoke the requested subcommand.

    If no subcommand is provided, display usage information.
    """
    parser = argparse.ArgumentParser(prog="autovideo", description="Auto Scenario Video Builder CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Define known subcommands; they map to modules in autovideo.cli
    commands = [
        "make",
        "scenes",
        "doctor",
        "presets",
        "wizard",
        "init-config",
        "init-batch",
        "batch",
        "social-pack",
        "export-bundle",
        "init-profile",
        "thumbnail",
        "studio",
    ]

    for cmd in commands:
        subparsers.add_parser(cmd, help=f"See `autovideo {cmd} --help` for details")

    args, remainder = parser.parse_known_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Dynamically import the subcommand module and call its main() function
    module_name = args.command.replace('-', '_')  # convert hyphens to underscore
    try:
        module = importlib.import_module(f"autovideo.cli.{module_name}")
    except ModuleNotFoundError:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)

    if hasattr(module, "main"):
        module.main(remainder)
    else:
        print(f"Subcommand '{args.command}' is not implemented yet.")


if __name__ == "__main__":
    main()