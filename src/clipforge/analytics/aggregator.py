"""Analytics aggregator — summary, comparison, and time-series helpers.

Usage::

    from clipforge.analytics.aggregator import AnalyticsAggregator

    agg = AnalyticsAggregator(records)

    summary   = agg.summary()
    by_plat   = agg.by_platform()
    by_tmpl   = agg.by_template()
    by_camp   = agg.by_campaign()
    delta     = agg.compare(records_a, records_b)
    top_views = agg.top_by("views", n=5)
    series    = agg.time_series(bucket="day")
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from clipforge.analytics.models import ContentAnalytics

_METRIC_KEYS = [
    "views", "likes", "comments", "shares",
    "impressions", "reach", "ctr",
    "retention_pct", "avg_view_duration_s", "engagement_rate",
]


class AnalyticsAggregator:
    """Aggregate and compare a collection of ContentAnalytics records."""

    def __init__(self, records: list[ContentAnalytics]) -> None:
        self.records = records

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Return aggregate totals + averages over all records."""
        if not self.records:
            return {"count": 0, "totals": {}, "averages": {}}
        return {
            "count": len(self.records),
            "totals": _totals(self.records),
            "averages": _averages(self.records),
        }

    # ── Group-by helpers ──────────────────────────────────────────────────────

    def by_platform(self) -> dict[str, dict[str, Any]]:
        """Return summary broken down by platform."""
        return self._group_by(lambda r: r.platform or "unknown")

    def by_template(self) -> dict[str, dict[str, Any]]:
        """Return summary broken down by template_ref."""
        return self._group_by(lambda r: r.template_ref or "(no template)")

    def by_campaign(self) -> dict[str, dict[str, Any]]:
        """Return summary broken down by campaign_name."""
        return self._group_by(lambda r: r.campaign_name or "(no campaign)")

    def _group_by(self, key_fn: Any) -> dict[str, dict[str, Any]]:
        groups: dict[str, list[ContentAnalytics]] = defaultdict(list)
        for r in self.records:
            groups[key_fn(r)].append(r)
        return {
            k: {"count": len(recs), "totals": _totals(recs), "averages": _averages(recs)}
            for k, recs in sorted(groups.items())
        }

    # ── Top N ─────────────────────────────────────────────────────────────────

    def top_by(self, metric: str, n: int = 5) -> list[ContentAnalytics]:
        """Return the top *n* records sorted by *metric* descending."""
        return sorted(
            self.records,
            key=lambda r: float(getattr(r, metric, 0) or 0),
            reverse=True,
        )[:n]

    # ── Compare ───────────────────────────────────────────────────────────────

    @staticmethod
    def compare(
        records_a: list[ContentAnalytics],
        records_b: list[ContentAnalytics],
        label_a: str = "A",
        label_b: str = "B",
    ) -> dict[str, Any]:
        """Compare two groups of records and return delta metrics.

        Positive delta means B outperforms A.
        """
        if not records_a and not records_b:
            return {}
        avg_a = _averages(records_a) if records_a else {k: 0.0 for k in _METRIC_KEYS}
        avg_b = _averages(records_b) if records_b else {k: 0.0 for k in _METRIC_KEYS}

        delta = {}
        for k in _METRIC_KEYS:
            va = avg_a.get(k, 0.0)
            vb = avg_b.get(k, 0.0)
            abs_delta = round(vb - va, 4)
            pct_delta = round((vb - va) / max(abs(va), 0.001) * 100, 2)
            delta[k] = {
                label_a: va,
                label_b: vb,
                "delta": abs_delta,
                "delta_pct": pct_delta,
                "winner": label_b if abs_delta > 0 else (label_a if abs_delta < 0 else "tie"),
            }
        return {
            "count_a": len(records_a),
            "count_b": len(records_b),
            "metrics": delta,
        }

    # ── Time series ───────────────────────────────────────────────────────────

    def time_series(self, bucket: str = "day") -> list[dict[str, Any]]:
        """Return records aggregated into time buckets.

        Parameters
        ----------
        bucket:
            ``"day"``, ``"week"``, or ``"month"``.

        Returns
        -------
        list of ``{"period": str, "count": int, "totals": dict, "averages": dict}``
        sorted by period ascending.
        """
        buckets: dict[str, list[ContentAnalytics]] = defaultdict(list)
        for r in self.records:
            key = _bucket_key(r.fetched_at, bucket)
            buckets[key].append(r)
        return [
            {
                "period": k,
                "count": len(recs),
                "totals": _totals(recs),
                "averages": _averages(recs),
            }
            for k, recs in sorted(buckets.items())
        ]


# ── Private helpers ───────────────────────────────────────────────────────────


def _totals(records: list[ContentAnalytics]) -> dict[str, Any]:
    return {k: round(sum(float(getattr(r, k, 0) or 0) for r in records), 4)
            for k in _METRIC_KEYS}


def _averages(records: list[ContentAnalytics]) -> dict[str, Any]:
    if not records:
        return {k: 0.0 for k in _METRIC_KEYS}
    n = len(records)
    return {k: round(sum(float(getattr(r, k, 0) or 0) for r in records) / n, 4)
            for k in _METRIC_KEYS}


def _bucket_key(iso_dt: str, bucket: str) -> str:
    """Convert an ISO-8601 string to a bucket key string."""
    try:
        dt = datetime.fromisoformat(iso_dt.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return "unknown"
    if bucket == "day":
        return dt.strftime("%Y-%m-%d")
    if bucket == "week":
        # ISO week: year-Www
        return dt.strftime("%G-W%V")
    if bucket == "month":
        return dt.strftime("%Y-%m")
    return dt.strftime("%Y-%m-%d")
