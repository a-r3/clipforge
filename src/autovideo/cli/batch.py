"""
`autovideo batch` subcommand.

Reads a batch configuration file and lists the output filenames that would be
generated. The actual rendering is not performed in this stub implementation.
"""

import argparse
import json
from pathlib import Path

from autovideo.batch_runner import run_batch


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autovideo batch", description="Process multiple video jobs from a batch file."
    )
    parser.add_argument(
        "--batch-file",
        required=True,
        help="Path to the batch configuration file.",
    )
    args = parser.parse_args(argv)
    batch_path = Path(args.batch_file)
    config = json.loads(batch_path.read_text(encoding="utf-8"))
    outputs = run_batch(config)
    for out in outputs:
        print(out)
