"""Tests for the batch runner module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from clipforge.batch_runner import BatchRunner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_batch(tmp_path: Path, jobs: list) -> Path:
    f = tmp_path / "batch.json"
    f.write_text(json.dumps(jobs), encoding="utf-8")
    return f


def _write_script(tmp_path: Path, name: str = "script.txt") -> Path:
    s = tmp_path / name
    s.write_text(
        "AI is changing the way businesses work today.\n\n"
        "Teams using intelligent tools outperform competitors.",
        encoding="utf-8",
    )
    return s


# ---------------------------------------------------------------------------
# load_batch
# ---------------------------------------------------------------------------

def test_load_batch_list(tmp_path):
    jobs = [{"output": "a.mp4"}, {"output": "b.mp4"}]
    f = _write_batch(tmp_path, jobs)
    runner = BatchRunner()
    result = runner.load_batch(f)
    assert result == jobs


def test_load_batch_object_with_jobs_key(tmp_path):
    data = {"jobs": [{"output": "a.mp4"}]}
    f = tmp_path / "batch.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    runner = BatchRunner()
    result = runner.load_batch(f)
    assert result == [{"output": "a.mp4"}]


def test_load_batch_missing_file(tmp_path):
    runner = BatchRunner()
    result = runner.load_batch(tmp_path / "nonexistent.json")
    assert result == []


def test_load_batch_empty_list(tmp_path):
    f = _write_batch(tmp_path, [])
    runner = BatchRunner()
    assert runner.load_batch(f) == []


# ---------------------------------------------------------------------------
# dry_run
# ---------------------------------------------------------------------------

def test_dry_run_skips_render(tmp_path):
    script = _write_script(tmp_path)
    jobs = [
        {"script_file": str(script), "output": str(tmp_path / "a.mp4")},
        {"script_file": str(script), "output": str(tmp_path / "b.mp4")},
    ]
    f = _write_batch(tmp_path, jobs)
    runner = BatchRunner()
    summary = runner.run(f, dry_run=True)
    assert summary["total"] == 2
    assert summary["succeeded"] == 2
    assert summary["failed"] == 0
    # Output files must NOT be created in dry run
    assert not (tmp_path / "a.mp4").exists()
    assert not (tmp_path / "b.mp4").exists()


# ---------------------------------------------------------------------------
# continue on error
# ---------------------------------------------------------------------------

def test_continue_on_error_processes_all_jobs(tmp_path):
    script = _write_script(tmp_path)
    jobs = [
        {"script_file": str(script), "output": str(tmp_path / "a.mp4")},
        {"script_file": "/nonexistent/bad_script.txt", "output": str(tmp_path / "b.mp4")},
        {"script_file": str(script), "output": str(tmp_path / "c.mp4")},
    ]
    f = _write_batch(tmp_path, jobs)
    runner = BatchRunner(on_error="continue")

    # Mock _run_job so only the bad script raises
    def selective_run(job, idx):
        if "bad_script" in job.get("script_file", ""):
            raise FileNotFoundError("Script file not found")
        # For good jobs, mock the builder
        from clipforge.builder import BuildSummary
        BuildSummary(scene_count=2, stock_hits=0, fallbacks=2,
                     total_duration=10.0, output_path=job["output"])
        # We need to create the output file to simulate success
        Path(job["output"]).touch()
        return {"scenes": 2, "output": job["output"]}

    with patch.object(runner, "_run_job", side_effect=selective_run):
        summary = runner.run(f)

    assert summary["total"] == 3
    assert summary["succeeded"] == 2
    assert summary["failed"] == 1
    assert len(summary["errors"]) == 1


def test_stop_on_error_halts_early(tmp_path):
    script = _write_script(tmp_path)
    jobs = [
        {"script_file": "/bad/script.txt", "output": str(tmp_path / "a.mp4")},
        {"script_file": str(script), "output": str(tmp_path / "b.mp4")},
        {"script_file": str(script), "output": str(tmp_path / "c.mp4")},
    ]
    f = _write_batch(tmp_path, jobs)
    runner = BatchRunner(on_error="stop")

    call_count = [0]

    def fake_run(job, idx):
        call_count[0] += 1
        if "bad" in job.get("script_file", ""):
            raise FileNotFoundError("not found")
        return {"scenes": 1, "output": job["output"]}

    with patch.object(runner, "_run_job", side_effect=fake_run):
        summary = runner.run(f)

    assert summary["failed"] >= 1
    assert call_count[0] == 1  # stopped after first failure


# ---------------------------------------------------------------------------
# summary structure
# ---------------------------------------------------------------------------

def test_summary_keys_present(tmp_path):
    f = _write_batch(tmp_path, [])
    runner = BatchRunner()
    summary = runner.run(f)
    for key in ("total", "succeeded", "failed", "errors"):
        assert key in summary


def test_empty_batch_returns_zero_counts(tmp_path):
    f = _write_batch(tmp_path, [])
    runner = BatchRunner()
    summary = runner.run(f)
    assert summary["total"] == 0
    assert summary["succeeded"] == 0
    assert summary["failed"] == 0
    assert summary["errors"] == []
