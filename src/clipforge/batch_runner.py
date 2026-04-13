"""Batch runner for ClipForge.

Processes multiple video jobs from a batch JSON file, continuing on
failures and printing a summary.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from clipforge.utils import load_json, ensure_dir

logger = logging.getLogger(__name__)


class BatchRunner:
    """Run multiple ClipForge jobs from a batch configuration file."""

    def __init__(self, on_error: str = "continue") -> None:
        """Initialize the batch runner.

        Args:
            on_error: How to handle job errors. 'continue' (default) or 'stop'.
        """
        self.on_error = on_error

    def load_batch(self, batch_file: str | Path) -> list[dict[str, Any]]:
        """Load jobs from a batch JSON file.

        The file should be a JSON array of job config dicts, or a JSON object
        with a ``jobs`` key containing the array.

        Returns a list of job dicts.
        """
        data = load_json(batch_file)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("jobs", [])
        return []

    def run(self, batch_file: str | Path, dry_run: bool = False) -> dict[str, Any]:
        """Process all jobs in *batch_file*.

        Args:
            batch_file: Path to the batch JSON file.
            dry_run: If True, validate jobs but do not run them.

        Returns:
            Summary dict with keys: total, succeeded, failed, errors.
        """
        jobs = self.load_batch(batch_file)
        total = len(jobs)
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        logger.info("Starting batch: %d job(s)", total)
        print(f"Batch: {total} job(s) to process")

        for i, job in enumerate(jobs, 1):
            job_name = job.get("output", f"job-{i}")
            print(f"  [{i}/{total}] {job_name} ...", end=" ", flush=True)

            if dry_run:
                print("SKIPPED (dry run)")
                succeeded += 1
                continue

            try:
                self._run_job(job, i)
                print("OK")
                succeeded += 1
            except Exception as exc:
                msg = str(exc)
                print(f"FAILED: {msg}")
                logger.error("Job %d failed: %s", i, msg)
                errors.append({"job": i, "output": job_name, "error": msg})
                failed += 1
                if self.on_error == "stop":
                    break

        summary = {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors,
        }

        self._print_summary(summary)
        return summary

    def _run_job(self, job: dict[str, Any], index: int) -> None:
        """Run a single job dict.

        Raises an exception on failure (which the caller catches).
        """
        from clipforge.config_loader import load_config
        from clipforge.script_parser import ScriptParser
        from clipforge.scene_planner import ScenePlanner
        from clipforge.builder import VideoBuilder

        # Build config for this job
        config_file = job.get("config_file")
        config = load_config(config_file, overrides=job)

        # Read script
        script_file = config.get("script_file", "")
        script_text = config.get("script_text", "")
        if script_file and not script_text:
            script_path = Path(script_file)
            if not script_path.exists():
                raise FileNotFoundError(f"Script file not found: {script_file}")
            script_text = script_path.read_text(encoding="utf-8")

        if not script_text:
            raise ValueError("No script_file or script_text in job config.")

        parser = ScriptParser()
        scenes = [s.to_dict() for s in parser.parse(script_text)]

        planner = ScenePlanner(ai_mode=config.get("ai_mode", "off"))
        planned = planner.plan(scenes)

        output = config.get("output", f"output/batch_{index}.mp4")
        builder = VideoBuilder()
        builder.build(planned, config, output)

    def _print_summary(self, summary: dict[str, Any]) -> None:
        """Print a human-readable batch summary."""
        print(f"\nBatch complete: {summary['succeeded']}/{summary['total']} succeeded, "
              f"{summary['failed']} failed.")
        if summary["errors"]:
            print("Errors:")
            for err in summary["errors"]:
                print(f"  Job {err['job']} ({err['output']}): {err['error']}")
