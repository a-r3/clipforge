"""Tests for OptimizationReport and Recommendation models."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from clipforge.optimize.models import OptimizationReport, Recommendation


# ── Recommendation ────────────────────────────────────────────────────────────


def test_recommendation_defaults():
    r = Recommendation(
        category="timing",
        severity="high",
        title="Post on Mondays",
        description="Mondays show 40% more views.",
    )
    assert r.current_value == ""
    assert r.suggested_value == ""
    assert r.evidence == {}
    assert r.confidence == 1.0


def test_recommendation_to_dict():
    r = Recommendation(
        category="ctr",
        severity="medium",
        title="Low CTR",
        description="Below benchmark.",
        current_value="1.2%",
        suggested_value="≥2.0%",
        evidence={"avg_ctr": 1.2},
        confidence=0.8,
    )
    d = r.to_dict()
    assert d["category"] == "ctr"
    assert d["severity"] == "medium"
    assert d["evidence"]["avg_ctr"] == 1.2
    assert d["confidence"] == pytest.approx(0.8, abs=0.01)


def test_recommendation_round_trip():
    r = Recommendation(
        category="template",
        severity="low",
        title="Use tmpl-a",
        description="Better engagement.",
        suggested_value="tmpl-a",
        confidence=0.6,
    )
    d = r.to_dict()
    r2 = Recommendation.from_dict(d)
    assert r2.category == r.category
    assert r2.severity == r.severity
    assert r2.title == r.title
    assert r2.confidence == pytest.approx(r.confidence, abs=0.01)


def test_recommendation_from_dict_defaults():
    r = Recommendation.from_dict({})
    assert r.category == ""
    assert r.severity == "low"
    assert r.confidence == 1.0


# ── OptimizationReport ────────────────────────────────────────────────────────


def test_report_defaults():
    report = OptimizationReport()
    assert report.source_records == 0
    assert report.trend == "insufficient_data"
    assert report.recommendations == []
    assert uuid.UUID(report.report_id)
    assert report.generated_at


def test_report_is_empty():
    assert OptimizationReport().is_empty() is True
    assert OptimizationReport(source_records=5).is_empty() is False


def test_report_high_priority():
    recs = [
        Recommendation(category="ctr", severity="high", title="H", description=""),
        Recommendation(category="ctr", severity="medium", title="M", description=""),
        Recommendation(category="ctr", severity="low", title="L", description=""),
    ]
    report = OptimizationReport(source_records=10, recommendations=recs)
    hp = report.high_priority()
    assert len(hp) == 1
    assert hp[0].severity == "high"


def test_report_by_category():
    recs = [
        Recommendation(category="timing", severity="high", title="T1", description=""),
        Recommendation(category="ctr", severity="medium", title="T2", description=""),
        Recommendation(category="timing", severity="low", title="T3", description=""),
    ]
    report = OptimizationReport(source_records=10, recommendations=recs)
    timing_recs = report.by_category("timing")
    assert len(timing_recs) == 2
    assert report.by_category("template") == []


def test_report_to_dict():
    report = OptimizationReport(
        source_records=15,
        trend="improving",
        trend_pct=22.5,
        recommendations=[
            Recommendation(category="ctr", severity="high", title="T", description="")
        ],
    )
    d = report.to_dict()
    assert d["source_records"] == 15
    assert d["trend"] == "improving"
    assert d["trend_pct"] == pytest.approx(22.5)
    assert len(d["recommendations"]) == 1


def test_report_round_trip():
    recs = [
        Recommendation(category="timing", severity="medium", title="T", description="D",
                       evidence={"key": "val"}, confidence=0.75),
    ]
    report = OptimizationReport(
        source_records=10,
        trend="stable",
        trend_pct=3.1,
        filters_applied={"platform": "youtube"},
        recommendations=recs,
        top_performers={"top_by_views": {"views": 5000}},
        summary_metrics={"views": 1234.0},
    )
    d = report.to_dict()
    r2 = OptimizationReport.from_dict(d)
    assert r2.report_id == report.report_id
    assert r2.source_records == 10
    assert r2.trend == "stable"
    assert r2.filters_applied == {"platform": "youtube"}
    assert len(r2.recommendations) == 1
    assert r2.recommendations[0].category == "timing"
    assert r2.top_performers["top_by_views"]["views"] == 5000


def test_report_save_and_load(tmp_path):
    report = OptimizationReport(
        source_records=8,
        trend="improving",
        recommendations=[
            Recommendation(category="ctr", severity="high", title="X", description="Y"),
        ],
    )
    path = tmp_path / "report.json"
    report.save(path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["source_records"] == 8

    loaded = OptimizationReport.load(path)
    assert loaded.report_id == report.report_id
    assert loaded.trend == "improving"
    assert len(loaded.recommendations) == 1


def test_report_load_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        OptimizationReport.load(tmp_path / "missing.json")


def test_report_save_creates_parent_dirs(tmp_path):
    report = OptimizationReport(source_records=1)
    path = tmp_path / "a" / "b" / "report.json"
    report.save(path)
    assert path.exists()
