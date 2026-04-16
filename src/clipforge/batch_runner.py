"""Batch runner for ClipForge.

Processes multiple video jobs from a batch JSON file, continuing on
failures and printing a clear per-job status and final summary.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from clipforge.utils import load_json

logger = logging.getLogger(__name__)


class BatchRunner:
    """Run multiple ClipForge jobs from a batch configuration file."""

    def __init__(self, on_error: str = "continue") -> None:
        """Initialize the batch runner.

        Args:
            on_error: How to handle job errors. ``"continue"`` (default) or ``"stop"``.
        """
        self.on_error = on_error

    def load_batch(self, batch_file: str | Path) -> list[dict[str, Any]]:
        """Load jobs from a batch JSON file.

        Accepts either a JSON array of job dicts, or a JSON object with a
        ``"jobs"`` key containing the array.
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
            dry_run: If True, validate jobs but do not render.

        Returns:
            Summary dict with keys: total, succeeded, failed, errors.
        """
        jobs = self.load_batch(batch_file)
        total = len(jobs)

        if total == 0:
            print("Batch: no jobs found.")
            return {"total": 0, "succeeded": 0, "failed": 0, "errors": []}

        mode_label = " [dry run]" if dry_run else ""
        print(f"\nBatch{mode_label}: {total} job(s)")
        print("-" * 52)

        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for i, job in enumerate(jobs, 1):
            job_output = job.get("output", f"batch_job_{i}.mp4")
            label = f"[{i}/{total}] {Path(job_output).name}"
            print(f"  {label:<35s}", end="", flush=True)

            if dry_run:
                print("SKIP")
                succeeded += 1
                continue

            t0 = time.monotonic()
            try:
                result_info = self._run_job(job, i)
                elapsed = time.monotonic() - t0
                scenes = result_info.get("scenes", "?")
                print(f"OK  ({scenes} scenes, {elapsed:.1f}s)")
                succeeded += 1
            except Exception as exc:
                elapsed = time.monotonic() - t0
                msg = str(exc)
                print(f"FAIL ({elapsed:.1f}s)")
                print(f"       → {msg}")
                logger.error("Job %d (%s) failed: %s", i, job_output, msg)
                errors.append({"job": i, "output": job_output, "error": msg})
                failed += 1
                if self.on_error == "stop":
                    print("  Stopping batch (--stop-on-error).")
                    break

        summary = {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors,
        }
        self._print_summary(summary)
        return summary

    def _run_job(self, job: dict[str, Any], index: int) -> dict[str, Any]:
        """Run a single job and return a dict with render info.

        Raises an exception on failure.
        """
        from clipforge.builder import VideoBuilder
        from clipforge.config_loader import load_config
        from clipforge.scene_planner import ScenePlanner
        from clipforge.script_parser import ScriptParser

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
        summary = builder.build(planned, config, output)

        return {"scenes": summary.scene_count, "output": output}

    def _print_summary(self, summary: dict[str, Any]) -> None:
        """Print a human-readable batch summary."""
        total = summary["total"]
        ok = summary["succeeded"]
        fail = summary["failed"]
        skipped = total - ok - fail

        print("-" * 52)
        status = "complete" if fail == 0 else "complete with errors"
        parts = [f"{ok}/{total} succeeded"]
        if fail:
            parts.append(f"{fail} failed")
        if skipped:
            parts.append(f"{skipped} skipped")
        print(f"Batch {status}: {', '.join(parts)}")

        if summary["errors"]:
            print("\nFailed jobs:")
            for err in summary["errors"]:
                out = Path(err["output"]).name
                print(f"  Job {err['job']:2d}  {out:<30s}  {err['error']}")
