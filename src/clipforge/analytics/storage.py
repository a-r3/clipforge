"""AnalyticsStore — local JSON-based persistence for ContentAnalytics records.

Each record is stored as ``<store_dir>/<analytics_id>.json``.
Multiple records can exist for the same manifest (time series).

Usage::

    store = AnalyticsStore("./analytics_store")
    store.save(record)

    # Latest snapshot for a manifest
    latest = store.latest_for_manifest(manifest_id)

    # Time-series for a manifest
    history = store.for_manifest(manifest_id)

    # All records
    all_records = store.list()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clipforge.analytics.models import ContentAnalytics


class AnalyticsStore:
    """Local JSON-based store for ContentAnalytics records.

    Records are stored as individual ``<analytics_id>.json`` files.
    No index file is maintained — operations scan the directory.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self.path.mkdir(parents=True, exist_ok=True)

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(self, record: ContentAnalytics) -> Path:
        """Save a record to ``<store_dir>/<analytics_id>.json``.

        Returns the path the record was written to.
        """
        p = self.path / f"{record.analytics_id}.json"
        record.save(p)
        return p

    # ── Read ──────────────────────────────────────────────────────────────────

    def load(self, analytics_id: str) -> ContentAnalytics:
        """Load a record by its analytics_id.

        Raises FileNotFoundError if not found.
        """
        return ContentAnalytics.load(self.path / f"{analytics_id}.json")

    def list(self) -> list[ContentAnalytics]:
        """Return all records, sorted by fetched_at ascending."""
        records = []
        for p in sorted(self.path.glob("*.json")):
            try:
                records.append(ContentAnalytics.load(p))
            except Exception:
                pass  # skip corrupt files
        records.sort(key=lambda r: r.fetched_at)
        return records

    def for_manifest(self, manifest_id: str) -> list[ContentAnalytics]:
        """Return all records for *manifest_id*, sorted by fetched_at ascending."""
        return [r for r in self.list() if r.manifest_id == manifest_id]

    def latest_for_manifest(self, manifest_id: str) -> ContentAnalytics | None:
        """Return the most recent record for *manifest_id*, or None."""
        records = self.for_manifest(manifest_id)
        return records[-1] if records else None

    def for_platform(self, platform: str) -> list[ContentAnalytics]:
        """Return all records for *platform*."""
        return [r for r in self.list() if r.platform == platform]

    def for_campaign(self, campaign_name: str) -> list[ContentAnalytics]:
        """Return all records for *campaign_name*."""
        return [r for r in self.list() if r.campaign_name == campaign_name]

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(
        self,
        records: list[ContentAnalytics] | None = None,
    ) -> dict[str, Any]:
        """Return aggregate totals and averages for *records* (default: all).

        Returns a dict with keys: total_records, platforms, metrics (totals
        and averages), and by_platform breakdown.
        """
        recs = records if records is not None else self.list()
        if not recs:
            return {
                "total_records": 0,
                "platforms": [],
                "metrics": {},
                "by_platform": {},
            }

        totals = _sum_metrics(recs)
        n = len(recs)
        avgs = {k: round(v / n, 2) for k, v in totals.items()}
        platforms = sorted({r.platform for r in recs})

        by_platform: dict[str, Any] = {}
        for plat in platforms:
            plat_recs = [r for r in recs if r.platform == plat]
            t = _sum_metrics(plat_recs)
            by_platform[plat] = {
                "count": len(plat_recs),
                "totals": t,
                "averages": {k: round(v / len(plat_recs), 2) for k, v in t.items()},
            }

        return {
            "total_records": n,
            "platforms": platforms,
            "metrics": {
                "totals": totals,
                "averages": avgs,
            },
            "by_platform": by_platform,
        }

    def __len__(self) -> int:
        return sum(1 for _ in self.path.glob("*.json"))

    def __repr__(self) -> str:
        return f"AnalyticsStore(path={self.path!r}, records={len(self)})"


# ── Private helpers ───────────────────────────────────────────────────────────


def _sum_metrics(records: list[ContentAnalytics]) -> dict[str, Any]:
    """Sum numeric metrics across a list of records."""
    return {
        "views": sum(r.views for r in records),
        "likes": sum(r.likes for r in records),
        "comments": sum(r.comments for r in records),
        "shares": sum(r.shares for r in records),
        "impressions": sum(r.impressions for r in records),
        "reach": sum(r.reach for r in records),
        "ctr": round(sum(r.ctr for r in records), 4),
        "retention_pct": round(sum(r.retention_pct for r in records), 4),
        "engagement_rate": round(sum(r.engagement_rate for r in records), 4),
    }
