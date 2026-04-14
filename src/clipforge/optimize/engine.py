"""Optimization engine — analyse ContentAnalytics records and emit recommendations.

All analysis is purely statistical — no LLM calls, no external services.
Recommendations are grounded in measurable metric deltas from your own data.

Usage::

    from clipforge.optimize.engine import Optimizer
    from clipforge.analytics.storage import AnalyticsStore

    store = AnalyticsStore("./analytics_store")
    records = store.list()

    opt = Optimizer(records)
    report = opt.analyze(platform="youtube", last_n=30)

    for rec in report.high_priority():
        print(rec.title, "—", rec.description)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from clipforge.analytics.models import ContentAnalytics
from clipforge.optimize.models import OptimizationReport, Recommendation

# ── Benchmark ranges (platform → (min, max) for "healthy" values) ─────────────

_CTR_BENCHMARKS: dict[str, tuple[float, float]] = {
    "youtube":        (2.0, 10.0),
    "youtube-shorts": (1.0,  8.0),
    "tiktok":         (0.5,  5.0),
    "reels":          (0.5,  5.0),
}
_CTR_DEFAULT = (1.0, 8.0)  # fallback for unknown platforms

_RETENTION_BENCHMARKS: dict[str, tuple[float, float]] = {
    "youtube":        (30.0, 70.0),
    "youtube-shorts": (60.0, 90.0),
    "tiktok":         (40.0, 80.0),
    "reels":          (40.0, 80.0),
}
_RETENTION_DEFAULT = (30.0, 70.0)

# Minimum records to emit statistically meaningful recommendations
_MIN_SAMPLE = 3
_MIN_TIMING_SAMPLE = 2   # per day/hour bucket
_MIN_GROUP_SAMPLE = 2    # per template/platform/campaign group

# Thresholds for flagging a recommendation as "high" vs "medium"
_HIGH_DELTA_PCT = 30.0   # group A outperforms B by ≥30% → high
_MED_DELTA_PCT  = 15.0   # ≥15% → medium; below → low

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
              "Friday", "Saturday", "Sunday"]


class Optimizer:
    """Analyse a collection of ContentAnalytics records and produce an OptimizationReport.

    Parameters
    ----------
    records:
        List of :class:`~clipforge.analytics.models.ContentAnalytics` records to analyse.
        Stub records (``data_source == 'stub'``) are excluded automatically.
    """

    def __init__(self, records: list[ContentAnalytics]) -> None:
        # Exclude stubs — they carry no real metric signal
        self.records = [r for r in records if r.data_source != "stub"]

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        platform: str = "",
        campaign: str = "",
        template: str = "",
        last_n: int = 0,
    ) -> OptimizationReport:
        """Run all analysis passes and return a structured :class:`OptimizationReport`.

        Parameters
        ----------
        platform:
            If set, filter records to this platform only.
        campaign:
            If set, filter records to this campaign only.
        template:
            If set, filter records to this template_ref only.
        last_n:
            If > 0, use only the most recent *last_n* records (by fetched_at).

        Returns
        -------
        :class:`~clipforge.optimize.models.OptimizationReport`
        """
        filtered = self._filter(platform, campaign, template, last_n)

        filters: dict[str, Any] = {}
        if platform:
            filters["platform"] = platform
        if campaign:
            filters["campaign"] = campaign
        if template:
            filters["template"] = template
        if last_n:
            filters["last_n"] = last_n

        if not filtered:
            return OptimizationReport(
                source_records=0,
                filters_applied=filters,
                trend="insufficient_data",
                recommendations=[],
            )

        recs: list[Recommendation] = []
        recs.extend(self._check_benchmarks(filtered))
        recs.extend(self._analyze_timing(filtered))
        recs.extend(self._analyze_templates(filtered))
        recs.extend(self._analyze_platforms(filtered))
        recs.extend(self._analyze_campaigns(filtered))
        recs.extend(self._analyze_trend(filtered))
        recs.extend(self._analyze_frequency(filtered))

        # Sort: high → medium → low, stable within each tier
        _order = {"high": 0, "medium": 1, "low": 2}
        recs.sort(key=lambda r: _order.get(r.severity, 3))

        trend, trend_pct = self._compute_trend(filtered)

        return OptimizationReport(
            source_records=len(filtered),
            filters_applied=filters,
            recommendations=recs,
            top_performers=self._top_performers(filtered),
            trend=trend,
            trend_pct=trend_pct,
            summary_metrics=_summary_metrics(filtered),
        )

    # ── Filtering ─────────────────────────────────────────────────────────────

    def _filter(
        self,
        platform: str,
        campaign: str,
        template: str,
        last_n: int,
    ) -> list[ContentAnalytics]:
        out = list(self.records)
        if platform:
            out = [r for r in out if r.platform == platform]
        if campaign:
            out = [r for r in out if r.campaign_name == campaign]
        if template:
            out = [r for r in out if r.template_ref == template]
        if last_n > 0:
            out = sorted(out, key=lambda r: r.fetched_at)[-last_n:]
        return out

    # ── Benchmark checks ──────────────────────────────────────────────────────

    def _check_benchmarks(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Check CTR and retention against platform norms."""
        recs: list[Recommendation] = []
        if len(records) < _MIN_SAMPLE:
            return recs

        by_platform: dict[str, list[ContentAnalytics]] = defaultdict(list)
        for r in records:
            by_platform[r.platform or "unknown"].append(r)

        for plat, group in by_platform.items():
            if len(group) < _MIN_SAMPLE:
                continue

            avg_ctr = _avg(group, "ctr")
            avg_ret = _avg(group, "retention_pct")

            ctr_min, ctr_max = _CTR_BENCHMARKS.get(plat, _CTR_DEFAULT)
            ret_min, ret_max = _RETENTION_BENCHMARKS.get(plat, _RETENTION_DEFAULT)

            # CTR below floor
            if avg_ctr > 0 and avg_ctr < ctr_min:
                gap = ctr_min - avg_ctr
                severity = "high" if gap > 2.0 else "medium"
                recs.append(Recommendation(
                    category="ctr",
                    severity=severity,
                    title=f"CTR below target on {plat}",
                    description=(
                        f"Average CTR is {avg_ctr:.1f}%, below the typical {ctr_min}–{ctr_max}% "
                        f"range for {plat}. Low CTR usually means thumbnails or titles are not "
                        f"compelling enough in the feed. Test bolder thumbnails, stronger "
                        f"numbers/emotions in titles, or time-sensitive hooks."
                    ),
                    current_value=f"{avg_ctr:.1f}%",
                    suggested_value=f"≥{ctr_min:.0f}%",
                    evidence={
                        "avg_ctr": round(avg_ctr, 2),
                        "benchmark_min": ctr_min,
                        "benchmark_max": ctr_max,
                        "platform": plat,
                        "sample": len(group),
                    },
                    confidence=min(1.0, len(group) / 10),
                ))

            # CTR above ceiling (informational)
            elif avg_ctr >= ctr_max:
                recs.append(Recommendation(
                    category="ctr",
                    severity="low",
                    title=f"Strong CTR on {plat} — sustain it",
                    description=(
                        f"Average CTR of {avg_ctr:.1f}% is above the typical {ctr_max:.0f}% ceiling "
                        f"for {plat}. Your thumbnails and titles are working well — keep the same "
                        f"visual style and hook patterns."
                    ),
                    current_value=f"{avg_ctr:.1f}%",
                    evidence={
                        "avg_ctr": round(avg_ctr, 2),
                        "benchmark_max": ctr_max,
                        "platform": plat,
                        "sample": len(group),
                    },
                    confidence=min(1.0, len(group) / 10),
                ))

            # Retention below floor
            if avg_ret > 0 and avg_ret < ret_min:
                gap = ret_min - avg_ret
                severity = "high" if gap > 20 else "medium"
                recs.append(Recommendation(
                    category="retention",
                    severity=severity,
                    title=f"Low retention on {plat}",
                    description=(
                        f"Average retention of {avg_ret:.1f}% is below the typical {ret_min}–{ret_max}% "
                        f"range for {plat}. Viewers are dropping off early. Strengthen the opening "
                        f"hook (first 3 seconds), cut slow scenes, and front-load your best content. "
                        f"Consider reducing video length."
                    ),
                    current_value=f"{avg_ret:.1f}%",
                    suggested_value=f"≥{ret_min:.0f}%",
                    evidence={
                        "avg_retention_pct": round(avg_ret, 1),
                        "benchmark_min": ret_min,
                        "benchmark_max": ret_max,
                        "platform": plat,
                        "sample": len(group),
                    },
                    confidence=min(1.0, len(group) / 10),
                ))

        return recs

    # ── Timing analysis ───────────────────────────────────────────────────────

    def _analyze_timing(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Find best day-of-week and hour-of-day for publishing."""
        recs: list[Recommendation] = []
        if len(records) < _MIN_SAMPLE * 2:
            return recs

        dated = [r for r in records if _parse_dt(r.published_at) is not None]
        if len(dated) < _MIN_SAMPLE:
            return recs

        # Day of week
        by_day: dict[int, list[ContentAnalytics]] = defaultdict(list)
        for r in dated:
            dt = _parse_dt(r.published_at)
            if dt is not None:
                by_day[dt.weekday()].append(r)

        day_avgs = {
            day: _avg(group, "views")
            for day, group in by_day.items()
            if len(group) >= _MIN_TIMING_SAMPLE
        }
        if len(day_avgs) >= 2:
            best_day = max(day_avgs, key=lambda d: day_avgs[d])
            overall_avg = _avg(records, "views")
            best_avg = day_avgs[best_day]
            if overall_avg > 0:
                delta_pct = (best_avg - overall_avg) / overall_avg * 100
                if delta_pct >= _MED_DELTA_PCT:
                    severity = "high" if delta_pct >= _HIGH_DELTA_PCT else "medium"
                    recs.append(Recommendation(
                        category="timing",
                        severity=severity,
                        title=f"Post on {_DAY_NAMES[best_day]}s for more views",
                        description=(
                            f"Videos published on {_DAY_NAMES[best_day]}s average "
                            f"{best_avg:,.0f} views — {delta_pct:.0f}% above your "
                            f"overall average of {overall_avg:,.0f}. "
                            f"Schedule future posts on {_DAY_NAMES[best_day]}s."
                        ),
                        current_value="mixed days",
                        suggested_value=_DAY_NAMES[best_day],
                        evidence={
                            "best_day": _DAY_NAMES[best_day],
                            "best_day_avg_views": round(best_avg, 0),
                            "overall_avg_views": round(overall_avg, 0),
                            "delta_pct": round(delta_pct, 1),
                            "sample_on_best_day": len(by_day[best_day]),
                        },
                        confidence=min(1.0, len(by_day[best_day]) / 5),
                    ))

        # Hour of day
        by_hour: dict[int, list[ContentAnalytics]] = defaultdict(list)
        for r in dated:
            dt = _parse_dt(r.published_at)
            if dt is not None:
                by_hour[dt.hour].append(r)

        hour_avgs = {
            h: _avg(group, "engagement_rate")
            for h, group in by_hour.items()
            if len(group) >= _MIN_TIMING_SAMPLE
        }
        if len(hour_avgs) >= 2:
            best_hour = max(hour_avgs, key=lambda h: hour_avgs[h])
            overall_eng = _avg(records, "engagement_rate")
            best_eng = hour_avgs[best_hour]
            if overall_eng > 0:
                delta_pct = (best_eng - overall_eng) / overall_eng * 100
                if delta_pct >= _MED_DELTA_PCT:
                    severity = "high" if delta_pct >= _HIGH_DELTA_PCT else "medium"
                    recs.append(Recommendation(
                        category="timing",
                        severity=severity,
                        title=f"Publish around {best_hour:02d}:00 for higher engagement",
                        description=(
                            f"Posts published around {best_hour:02d}:00 UTC show "
                            f"{best_eng:.2f}% engagement — {delta_pct:.0f}% above your "
                            f"average of {overall_eng:.2f}%. "
                            f"Try scheduling content in that window."
                        ),
                        current_value="mixed hours",
                        suggested_value=f"{best_hour:02d}:00 UTC",
                        evidence={
                            "best_hour_utc": best_hour,
                            "best_hour_avg_engagement": round(best_eng, 3),
                            "overall_avg_engagement": round(overall_eng, 3),
                            "delta_pct": round(delta_pct, 1),
                            "sample_at_best_hour": len(by_hour[best_hour]),
                        },
                        confidence=min(1.0, len(by_hour[best_hour]) / 5),
                    ))

        return recs

    # ── Template analysis ─────────────────────────────────────────────────────

    def _analyze_templates(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Compare performance across template_ref values."""
        recs: list[Recommendation] = []

        groups = _group_by(records, lambda r: r.template_ref or "(no template)")
        groups = {k: v for k, v in groups.items() if len(v) >= _MIN_GROUP_SAMPLE}

        if len(groups) < 2:
            return recs

        # Compare by engagement_rate
        eng_by_tmpl = {tmpl: _avg(g, "engagement_rate") for tmpl, g in groups.items()}
        ctr_by_tmpl = {tmpl: _avg(g, "ctr") for tmpl, g in groups.items()}

        best_tmpl = max(eng_by_tmpl, key=lambda t: eng_by_tmpl[t])
        worst_tmpl = min(eng_by_tmpl, key=lambda t: eng_by_tmpl[t])

        best_eng = eng_by_tmpl[best_tmpl]
        worst_eng = eng_by_tmpl[worst_tmpl]

        if worst_eng > 0:
            delta_pct = (best_eng - worst_eng) / worst_eng * 100
        else:
            delta_pct = 0.0

        if delta_pct >= _MED_DELTA_PCT and best_tmpl != "(no template)":
            severity = "high" if delta_pct >= _HIGH_DELTA_PCT else "medium"
            recs.append(Recommendation(
                category="template",
                severity=severity,
                title=f"Template '{best_tmpl}' drives {delta_pct:.0f}% more engagement",
                description=(
                    f"Videos using template '{best_tmpl}' achieve {best_eng:.2f}% engagement, "
                    f"compared to {worst_eng:.2f}% for '{worst_tmpl}' — a {delta_pct:.0f}% "
                    f"improvement. Prioritise '{best_tmpl}' for upcoming content."
                ),
                current_value=f"mixed templates (best: {best_tmpl}, worst: {worst_tmpl})",
                suggested_value=best_tmpl,
                evidence={
                    "best_template": best_tmpl,
                    "best_avg_engagement": round(best_eng, 3),
                    "worst_template": worst_tmpl,
                    "worst_avg_engagement": round(worst_eng, 3),
                    "delta_pct": round(delta_pct, 1),
                    "engagement_by_template": {k: round(v, 3) for k, v in eng_by_tmpl.items()},
                    "ctr_by_template": {k: round(v, 2) for k, v in ctr_by_tmpl.items()},
                },
                confidence=min(1.0, min(len(g) for g in groups.values()) / 5),
            ))

        return recs

    # ── Platform analysis ─────────────────────────────────────────────────────

    def _analyze_platforms(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Compare performance across platforms when multi-platform data exists."""
        recs: list[Recommendation] = []

        groups = _group_by(records, lambda r: r.platform or "unknown")
        groups = {k: v for k, v in groups.items() if len(v) >= _MIN_GROUP_SAMPLE}

        if len(groups) < 2:
            return recs

        eng_by_plat = {plat: _avg(g, "engagement_rate") for plat, g in groups.items()}
        views_by_plat = {plat: _avg(g, "views") for plat, g in groups.items()}

        best_plat = max(eng_by_plat, key=lambda p: eng_by_plat[p])
        worst_plat = min(eng_by_plat, key=lambda p: eng_by_plat[p])

        best_eng = eng_by_plat[best_plat]
        worst_eng = eng_by_plat[worst_plat]

        if worst_eng > 0:
            delta_pct = (best_eng - worst_eng) / worst_eng * 100
        else:
            delta_pct = 0.0

        if delta_pct >= _MED_DELTA_PCT:
            severity = "high" if delta_pct >= _HIGH_DELTA_PCT else "medium"
            recs.append(Recommendation(
                category="platform",
                severity=severity,
                title=f"{best_plat} generates {delta_pct:.0f}% more engagement",
                description=(
                    f"{best_plat} achieves {best_eng:.2f}% engagement rate vs "
                    f"{worst_eng:.2f}% on {worst_plat}. If you're resource-constrained, "
                    f"prioritise {best_plat} for maximum impact."
                ),
                current_value=f"publishing on {', '.join(sorted(groups.keys()))}",
                suggested_value=f"focus on {best_plat}",
                evidence={
                    "best_platform": best_plat,
                    "best_avg_engagement": round(best_eng, 3),
                    "worst_platform": worst_plat,
                    "worst_avg_engagement": round(worst_eng, 3),
                    "delta_pct": round(delta_pct, 1),
                    "engagement_by_platform": {k: round(v, 3) for k, v in eng_by_plat.items()},
                    "avg_views_by_platform": {k: round(v, 0) for k, v in views_by_plat.items()},
                },
                confidence=min(1.0, min(len(g) for g in groups.values()) / 5),
            ))

        return recs

    # ── Campaign analysis ─────────────────────────────────────────────────────

    def _analyze_campaigns(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Surface the best-performing campaign structure."""
        recs: list[Recommendation] = []

        named = [r for r in records if r.campaign_name]
        groups = _group_by(named, lambda r: r.campaign_name)
        groups = {k: v for k, v in groups.items() if len(v) >= _MIN_GROUP_SAMPLE}

        if len(groups) < 2:
            return recs

        eng_by_camp = {c: _avg(g, "engagement_rate") for c, g in groups.items()}
        best_camp = max(eng_by_camp, key=lambda c: eng_by_camp[c])
        worst_camp = min(eng_by_camp, key=lambda c: eng_by_camp[c])

        best_eng = eng_by_camp[best_camp]
        worst_eng = eng_by_camp[worst_camp]

        if worst_eng <= 0:
            return recs

        delta_pct = (best_eng - worst_eng) / worst_eng * 100
        if delta_pct >= _MED_DELTA_PCT:
            severity = "high" if delta_pct >= _HIGH_DELTA_PCT else "medium"
            recs.append(Recommendation(
                category="engagement",
                severity=severity,
                title=f"Campaign '{best_camp}' outperforms others",
                description=(
                    f"Campaign '{best_camp}' achieves {best_eng:.2f}% engagement, "
                    f"{delta_pct:.0f}% above '{worst_camp}' ({worst_eng:.2f}%). "
                    f"Analyse what made '{best_camp}' effective — topic, format, posting "
                    f"frequency — and replicate those patterns."
                ),
                current_value=worst_camp,
                suggested_value=f"replicate '{best_camp}' patterns",
                evidence={
                    "best_campaign": best_camp,
                    "best_avg_engagement": round(best_eng, 3),
                    "worst_campaign": worst_camp,
                    "worst_avg_engagement": round(worst_eng, 3),
                    "delta_pct": round(delta_pct, 1),
                    "engagement_by_campaign": {k: round(v, 3) for k, v in eng_by_camp.items()},
                },
                confidence=min(1.0, min(len(g) for g in groups.values()) / 5),
            ))

        return recs

    # ── Trend analysis ────────────────────────────────────────────────────────

    def _analyze_trend(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Compare first-half vs second-half performance to surface momentum."""
        recs: list[Recommendation] = []
        if len(records) < 6:
            return recs

        sorted_recs = sorted(records, key=lambda r: r.fetched_at)
        mid = len(sorted_recs) // 2
        first_half = sorted_recs[:mid]
        second_half = sorted_recs[mid:]

        avg_eng_a = _avg(first_half, "engagement_rate")
        avg_eng_b = _avg(second_half, "engagement_rate")
        avg_views_a = _avg(first_half, "views")
        avg_views_b = _avg(second_half, "views")

        if avg_eng_a <= 0:
            return recs

        eng_delta = (avg_eng_b - avg_eng_a) / avg_eng_a * 100
        views_delta = (avg_views_b - avg_views_a) / max(1, avg_views_a) * 100

        if eng_delta >= 10:
            recs.append(Recommendation(
                category="trend",
                severity="low",
                title="Engagement is trending upward",
                description=(
                    f"Recent videos show {avg_eng_b:.2f}% engagement vs {avg_eng_a:.2f}% "
                    f"in earlier ones — a {eng_delta:.0f}% improvement. Your content strategy "
                    f"is gaining traction. Stay consistent and double down on what's working."
                ),
                evidence={
                    "recent_avg_engagement": round(avg_eng_b, 3),
                    "earlier_avg_engagement": round(avg_eng_a, 3),
                    "engagement_delta_pct": round(eng_delta, 1),
                    "views_delta_pct": round(views_delta, 1),
                },
                confidence=min(1.0, len(records) / 20),
            ))
        elif eng_delta <= -10:
            severity = "high" if eng_delta <= -25 else "medium"
            recs.append(Recommendation(
                category="trend",
                severity=severity,
                title="Engagement is declining — refresh your approach",
                description=(
                    f"Recent videos show {avg_eng_b:.2f}% engagement vs {avg_eng_a:.2f}% "
                    f"in earlier ones — a {abs(eng_delta):.0f}% decline. Consider changing "
                    f"your hook style, posting frequency, or topic focus. Review your "
                    f"top-performing content for patterns to reuse."
                ),
                evidence={
                    "recent_avg_engagement": round(avg_eng_b, 3),
                    "earlier_avg_engagement": round(avg_eng_a, 3),
                    "engagement_delta_pct": round(eng_delta, 1),
                    "views_delta_pct": round(views_delta, 1),
                },
                confidence=min(1.0, len(records) / 20),
            ))

        return recs

    # ── Frequency analysis ────────────────────────────────────────────────────

    def _analyze_frequency(self, records: list[ContentAnalytics]) -> list[Recommendation]:
        """Check whether gaps between posts correlate with lower engagement."""
        recs: list[Recommendation] = []
        if len(records) < 5:
            return recs

        dated = [r for r in records if _parse_dt(r.published_at) is not None]
        dated.sort(key=lambda r: r.published_at)
        if len(dated) < 4:
            return recs

        gaps_days: list[float] = []
        for i in range(1, len(dated)):
            a = _parse_dt(dated[i - 1].published_at)
            b = _parse_dt(dated[i].published_at)
            if a and b:
                gaps_days.append((b - a).total_seconds() / 86400)

        if not gaps_days:
            return recs

        avg_gap = sum(gaps_days) / len(gaps_days)
        max_gap = max(gaps_days)

        if max_gap > 21:  # 3-week gap is notable
            recs.append(Recommendation(
                category="frequency",
                severity="medium",
                title=f"Longest publishing gap is {max_gap:.0f} days",
                description=(
                    f"There is a gap of {max_gap:.0f} days between two videos in this data. "
                    f"Algorithms on most platforms favour consistent posting. "
                    f"Aim for a regular cadence — even once a week is better than "
                    f"bursts with long gaps. Your average gap is {avg_gap:.0f} days."
                ),
                evidence={
                    "avg_gap_days": round(avg_gap, 1),
                    "max_gap_days": round(max_gap, 1),
                    "num_intervals": len(gaps_days),
                },
                confidence=0.7,
            ))
        elif avg_gap <= 3 and len(dated) >= 6:
            recs.append(Recommendation(
                category="frequency",
                severity="low",
                title="Consistent high-frequency posting",
                description=(
                    f"Average gap between posts is {avg_gap:.1f} days — "
                    f"excellent for algorithm visibility. Keep the cadence up."
                ),
                evidence={"avg_gap_days": round(avg_gap, 1)},
                confidence=0.8,
            ))

        return recs

    # ── Trend helper ──────────────────────────────────────────────────────────

    def _compute_trend(self, records: list[ContentAnalytics]) -> tuple[str, float]:
        """Return (trend_label, pct_change) comparing first vs second half."""
        if len(records) < 6:
            return "insufficient_data", 0.0

        sorted_recs = sorted(records, key=lambda r: r.fetched_at)
        mid = len(sorted_recs) // 2
        avg_a = _avg(sorted_recs[:mid], "engagement_rate")
        avg_b = _avg(sorted_recs[mid:], "engagement_rate")

        if avg_a <= 0:
            return "insufficient_data", 0.0

        pct = (avg_b - avg_a) / avg_a * 100
        if pct >= 10:
            return "improving", round(pct, 1)
        if pct <= -10:
            return "declining", round(pct, 1)
        return "stable", round(pct, 1)

    # ── Top performers ────────────────────────────────────────────────────────

    def _top_performers(self, records: list[ContentAnalytics]) -> dict[str, Any]:
        """Return best-by-views record + grouped averages."""
        if not records:
            return {}

        top_rec = max(records, key=lambda r: r.views)

        def _group_avgs(key_fn):
            groups = _group_by(records, key_fn)
            return {
                k: {
                    "count": len(g),
                    "avg_views": round(_avg(g, "views"), 0),
                    "avg_engagement": round(_avg(g, "engagement_rate"), 3),
                    "avg_ctr": round(_avg(g, "ctr"), 2),
                }
                for k, g in sorted(groups.items())
                if len(g) >= 1
            }

        return {
            "top_by_views": {
                "manifest_id": top_rec.manifest_id,
                "job_name": top_rec.job_name,
                "platform": top_rec.platform,
                "views": top_rec.views,
                "engagement_rate": top_rec.engagement_rate,
                "published_at": top_rec.published_at[:10] if top_rec.published_at else "",
            },
            "by_template": _group_avgs(lambda r: r.template_ref or "(no template)"),
            "by_platform": _group_avgs(lambda r: r.platform or "unknown"),
            "by_campaign": _group_avgs(lambda r: r.campaign_name or "(no campaign)"),
        }


# ── Private helpers ───────────────────────────────────────────────────────────


def _avg(records: list[ContentAnalytics], metric: str) -> float:
    if not records:
        return 0.0
    vals = [float(getattr(r, metric, 0) or 0) for r in records]
    return sum(vals) / len(vals)


def _group_by(
    records: list[ContentAnalytics],
    key_fn: Any,
) -> dict[str, list[ContentAnalytics]]:
    out: dict[str, list[ContentAnalytics]] = defaultdict(list)
    for r in records:
        out[key_fn(r)].append(r)
    return dict(out)


def _parse_dt(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _summary_metrics(records: list[ContentAnalytics]) -> dict[str, Any]:
    if not records:
        return {}
    n = len(records)
    metrics = ["views", "likes", "comments", "shares", "impressions",
               "ctr", "retention_pct", "engagement_rate"]
    return {
        m: round(sum(float(getattr(r, m, 0) or 0) for r in records) / n, 3)
        for m in metrics
    }
