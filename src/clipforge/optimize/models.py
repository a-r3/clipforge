"""Optimization data models — Recommendation and OptimizationReport.

Usage::

    from clipforge.optimize.models import Recommendation, OptimizationReport

    rec = Recommendation(
        category="timing",
        severity="high",
        title="Post on Thursdays",
        description="Thursday posts average 42% more views than other days.",
        suggested_value="Thursday",
        evidence={"thursday_avg_views": 12300, "overall_avg_views": 8660},
        confidence=0.85,
    )

    report = OptimizationReport(source_records=24, recommendations=[rec])
    report.save("optimization_notes.json")
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Valid recommendation categories
CATEGORIES = {
    "timing",      # best day / hour to publish
    "template",    # which template performs best
    "platform",    # which platform returns best results
    "retention",   # retention % is below platform norm
    "ctr",         # click-through rate is below / above norm
    "engagement",  # engagement rate analysis
    "trend",       # improving / declining over time
    "frequency",   # publishing cadence signals
}

SEVERITIES = {"high", "medium", "low"}


@dataclass
class Recommendation:
    """A single actionable optimization suggestion.

    Fields
    ------
    category:
        One of ``CATEGORIES`` — groups recommendations by topic.
    severity:
        ``"high"`` = significant improvement possible, act on it.
        ``"medium"`` = moderate impact or limited data.
        ``"low"`` = informational / small delta.
    title:
        One-line summary (shown in CLI and Studio).
    description:
        Detailed explanation with supporting numbers.
    current_value:
        What the data shows you're doing now (may be empty).
    suggested_value:
        Concrete recommended change (may be empty).
    evidence:
        Supporting metrics dict, e.g. ``{"avg_ctr": 1.2, "benchmark_min": 2.0}``.
    confidence:
        0.0–1.0.  Lower when sample size is small or variance is high.
    """

    category: str
    severity: str
    title: str
    description: str
    current_value: str = ""
    suggested_value: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 3),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recommendation":
        return cls(
            category=data.get("category", ""),
            severity=data.get("severity", "low"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            current_value=data.get("current_value", ""),
            suggested_value=data.get("suggested_value", ""),
            evidence=data.get("evidence", {}),
            confidence=float(data.get("confidence", 1.0)),
        )

    def __repr__(self) -> str:
        return f"Recommendation({self.severity!r}, {self.category!r}, {self.title!r})"


@dataclass
class OptimizationReport:
    """Full optimization analysis result.

    Fields
    ------
    report_id:
        UUID for this report.
    generated_at:
        ISO-8601 timestamp.
    source_records:
        Number of analytics records analysed.
    filters_applied:
        Dict of any platform / campaign / template / last_n filters used.
    recommendations:
        Sorted list of :class:`Recommendation` objects (high → low severity).
    top_performers:
        Dict of best-performing keys by dimension
        (``by_template``, ``by_platform``, ``by_campaign``).
    trend:
        ``"improving"`` | ``"declining"`` | ``"stable"`` | ``"insufficient_data"``.
    trend_pct:
        Percentage change between first-half and second-half of data
        (positive = improving).  0.0 when insufficient data.
    summary_metrics:
        Overall averages for key metrics across all records analysed.
    next_video_brief:
        Structured advisory brief for the next video: platform, template,
        timing window, and creative direction hints derived from the report.
    """

    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_records: int = 0
    filters_applied: dict[str, Any] = field(default_factory=dict)
    recommendations: list[Recommendation] = field(default_factory=list)
    top_performers: dict[str, Any] = field(default_factory=dict)
    trend: str = "insufficient_data"
    trend_pct: float = 0.0
    summary_metrics: dict[str, Any] = field(default_factory=dict)
    next_video_brief: dict[str, Any] = field(default_factory=dict)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def high_priority(self) -> list[Recommendation]:
        """Return only ``severity='high'`` recommendations."""
        return [r for r in self.recommendations if r.severity == "high"]

    def by_category(self, category: str) -> list[Recommendation]:
        """Return all recommendations for a given category."""
        return [r for r in self.recommendations if r.category == category]

    def is_empty(self) -> bool:
        return self.source_records == 0

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "source_records": self.source_records,
            "filters_applied": self.filters_applied,
            "trend": self.trend,
            "trend_pct": round(self.trend_pct, 2),
            "summary_metrics": self.summary_metrics,
            "top_performers": self.top_performers,
            "next_video_brief": self.next_video_brief,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationReport":
        return cls(
            report_id=data.get("report_id", str(uuid.uuid4())),
            generated_at=data.get("generated_at", ""),
            source_records=data.get("source_records", 0),
            filters_applied=data.get("filters_applied", {}),
            recommendations=[
                Recommendation.from_dict(r) for r in data.get("recommendations", [])
            ],
            top_performers=data.get("top_performers", {}),
            trend=data.get("trend", "insufficient_data"),
            trend_pct=float(data.get("trend_pct", 0.0)),
            summary_metrics=data.get("summary_metrics", {}),
            next_video_brief=data.get("next_video_brief", {}),
        )

    def save(self, path: str | Path) -> None:
        """Write the report to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "OptimizationReport":
        """Load a previously saved report from JSON."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Optimization report not found: {path}")
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))

    def __repr__(self) -> str:
        return (
            f"OptimizationReport(records={self.source_records}, "
            f"recs={len(self.recommendations)}, trend={self.trend!r})"
        )
