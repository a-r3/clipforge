"""batch command — run a batch jobs file."""

from __future__ import annotations

import sys

import click


@click.command("batch")
@click.option("--batch-file", "-b", required=True, help="Path to batch JSON file.")
@click.option("--dry-run", is_flag=True, default=False, help="Validate jobs without running.")
@click.option("--stop-on-error", is_flag=True, default=False, help="Stop on first failure.")
def batch(batch_file: str, dry_run: bool, stop_on_error: bool) -> None:
    """Run multiple video jobs from a batch JSON file."""
    import os
    if not os.path.exists(batch_file):
        click.echo(f"Error: Batch file not found: {batch_file}", err=True)
        sys.exit(1)

    from clipforge.batch_runner import BatchRunner

    on_error = "stop" if stop_on_error else "continue"
    runner = BatchRunner(on_error=on_error)

    summary = runner.run(batch_file, dry_run=dry_run)

    if summary["failed"] > 0:
        sys.exit(1)
