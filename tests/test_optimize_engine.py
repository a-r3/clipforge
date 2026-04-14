"""Tests for Optimizer engine — all analysis passes and edge cases."""

from __future__ import annotations

import pytest

from clipforge.analytics.models import ContentAnalytics
from clipforge.optimize.engine import Optimizer
from clipforge.optimize.models import OptimizationReport


# ── Helpers ───────────────────────────────────────────────────────────────────


def _rec(
    platform="youtube",
    views=1000,
    likes=50,
    comments=10,
    shares=5,
    impressions=5000,
    ctr=3.0,
    retention_pct=50.0,
    engagement_rate=6.5,
    template_ref="tmpl-a",
    campaign_name="Q1",
    data_source="api",
    published_at="2024-06-10T14:00:00+00:00",
    fetched_at="2024-06-11T10:00:00+00:00",
    **kwargs,
) -> ContentAnalytics:
    return ContentAnalytics(
        platform=platform,
        views=views,
        likes=likes,
        comments=comments,
        shares=shares,
        impressions=impressions,
        ctr=ctr,
        retention_pct=retention_pct,
        engagement_rate=engagement_rate,
        template_ref=template_ref,
        campaign_name=campaign_name,
        data_source=data_source,
        published_at=published_at,
        fetched_at=fetched_at,
        **kwargs,
    )


# ── Construction ──────────────────────────────────────────────────────────────


def test_optimizer_excludes_stub_records():
    records = [
        _rec(data_source="api"),
        _rec(data_source="stub"),
        _rec(data_source="mock"),
    ]
    opt = Optimizer(records)
    assert len(opt.records) == 2  # stub excluded


def test_optimizer_empty_records():
    opt = Optimizer([])
    report = opt.analyze()
    assert report.is_empty()
    assert report.source_records == 0
    assert report.recommendations == []


# ── analyze output structure ──────────────────────────────────────────────────


def test_analyze_returns_report():
    records = [_rec() for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert isinstance(report, OptimizationReport)
    assert report.source_records == 5


def test_analyze_summary_metrics_populated():
    records = [_rec(views=1000, ctr=3.0, retention_pct=50.0, engagement_rate=6.5)
               for _ in range(4)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.summary_metrics["views"] == pytest.approx(1000.0)
    assert report.summary_metrics["ctr"] == pytest.approx(3.0)


def test_analyze_recommendations_sorted_by_severity():
    """High-severity recommendations must appear before medium/low."""
    # Give low CTR (high severity) and some data variance
    records = [_rec(ctr=0.5, retention_pct=15.0) for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    if len(report.recommendations) >= 2:
        order = {"high": 0, "medium": 1, "low": 2}
        severities = [order[r.severity] for r in report.recommendations]
        assert severities == sorted(severities)


def test_analyze_filters_platform():
    records = [
        _rec(platform="youtube"),
        _rec(platform="tiktok"),
        _rec(platform="youtube"),
    ]
    opt = Optimizer(records)
    report = opt.analyze(platform="youtube")
    assert report.source_records == 2


def test_analyze_filters_campaign():
    records = [
        _rec(campaign_name="Q1"),
        _rec(campaign_name="Q2"),
        _rec(campaign_name="Q1"),
    ]
    opt = Optimizer(records)
    report = opt.analyze(campaign="Q1")
    assert report.source_records == 2


def test_analyze_filters_last_n():
    records = [
        _rec(fetched_at=f"2024-0{i+1}-01T00:00:00+00:00") for i in range(6)
    ]
    opt = Optimizer(records)
    report = opt.analyze(last_n=3)
    assert report.source_records == 3


def test_analyze_filters_applied_stored():
    records = [_rec(platform="youtube") for _ in range(3)]
    opt = Optimizer(records)
    report = opt.analyze(platform="youtube", campaign="Q1")
    assert report.filters_applied.get("platform") == "youtube"
    assert report.filters_applied.get("campaign") == "Q1"


def test_analyze_no_match_returns_empty():
    records = [_rec(platform="youtube")]
    opt = Optimizer(records)
    report = opt.analyze(platform="tiktok")
    assert report.is_empty()


# ── Benchmark checks ──────────────────────────────────────────────────────────


def test_low_ctr_triggers_recommendation():
    # YouTube benchmark min = 2.0%; feed 0.8%
    records = [_rec(platform="youtube", ctr=0.8) for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    ctr_recs = report.by_category("ctr")
    assert len(ctr_recs) >= 1
    assert any("CTR" in r.title for r in ctr_recs)


def test_good_ctr_triggers_sustain_recommendation():
    # ≥ benchmark max = 10% → "sustain" low-severity rec
    records = [_rec(platform="youtube", ctr=12.0) for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    ctr_recs = report.by_category("ctr")
    assert any(r.severity == "low" for r in ctr_recs)


def test_low_retention_triggers_recommendation():
    # YouTube benchmark min = 30%; feed 10%
    records = [_rec(platform="youtube", retention_pct=10.0) for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    ret_recs = report.by_category("retention")
    assert len(ret_recs) >= 1
    assert ret_recs[0].severity in ("high", "medium")


def test_good_metrics_no_benchmark_alert():
    # CTR=5%, retention=55% — both within YouTube range → no benchmark alert
    records = [_rec(platform="youtube", ctr=5.0, retention_pct=55.0) for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    ctr_alerts = [r for r in report.by_category("ctr") if r.severity in ("high", "medium")]
    ret_alerts = [r for r in report.by_category("retention") if r.severity in ("high", "medium")]
    assert len(ctr_alerts) == 0
    assert len(ret_alerts) == 0


def test_insufficient_sample_suppresses_benchmark():
    # Only 2 records — below _MIN_SAMPLE=3
    records = [_rec(platform="youtube", ctr=0.5)] * 2
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("ctr") == []


# ── Timing analysis ───────────────────────────────────────────────────────────


def test_timing_best_day_recommendation():
    # 3 Mondays (high views) + 3 Fridays (low views)
    monday_recs = [
        _rec(views=5000, published_at="2024-01-01T10:00:00+00:00",
             fetched_at=f"2024-01-0{i+1}T10:00:00+00:00")
        for i in range(3)
    ]
    friday_recs = [
        _rec(views=500, published_at="2024-01-05T10:00:00+00:00",
             fetched_at=f"2024-01-1{i+2}T10:00:00+00:00")
        for i in range(3)
    ]
    opt = Optimizer(monday_recs + friday_recs)
    report = opt.analyze()
    timing_recs = report.by_category("timing")
    # Should find Monday is best
    assert any("Monday" in r.title for r in timing_recs)


def test_timing_insufficient_data_no_rec():
    # Only 2 records total — timing needs ≥ MIN_SAMPLE * 2 = 6
    records = [_rec() for _ in range(2)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("timing") == []


def test_timing_no_published_at_skipped():
    records = [_rec(published_at="") for _ in range(8)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("timing") == []


# ── Template analysis ─────────────────────────────────────────────────────────


def test_template_best_template_recommended():
    good = [_rec(template_ref="tmpl-good", engagement_rate=15.0,
                 fetched_at=f"2024-0{i+1}-01T00:00:00+00:00") for i in range(3)]
    bad = [_rec(template_ref="tmpl-bad", engagement_rate=2.0,
                fetched_at=f"2024-0{i+4}-01T00:00:00+00:00") for i in range(3)]
    opt = Optimizer(good + bad)
    report = opt.analyze()
    tmpl_recs = report.by_category("template")
    assert len(tmpl_recs) >= 1
    assert any("tmpl-good" in r.title for r in tmpl_recs)


def test_template_single_template_no_rec():
    records = [_rec(template_ref="only-one") for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("template") == []


def test_template_small_groups_no_rec():
    # Each template only has 1 record — below _MIN_GROUP_SAMPLE=2
    records = [_rec(template_ref=f"tmpl-{i}") for i in range(4)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("template") == []


def test_template_close_performance_no_high_rec():
    # <15% delta — should produce no medium/high template rec
    same_ish = (
        [_rec(template_ref="A", engagement_rate=10.0)] * 2 +
        [_rec(template_ref="B", engagement_rate=10.5)] * 2
    )
    opt = Optimizer(same_ish)
    report = opt.analyze()
    high_med = [r for r in report.by_category("template")
                if r.severity in ("high", "medium")]
    assert len(high_med) == 0


# ── Platform analysis ─────────────────────────────────────────────────────────


def test_platform_best_platform_recommended():
    yt = [_rec(platform="youtube", engagement_rate=12.0) for _ in range(3)]
    tk = [_rec(platform="tiktok", engagement_rate=2.0) for _ in range(3)]
    opt = Optimizer(yt + tk)
    report = opt.analyze()
    plat_recs = report.by_category("platform")
    assert len(plat_recs) >= 1
    assert any("youtube" in r.title.lower() for r in plat_recs)


def test_platform_single_platform_no_rec():
    records = [_rec(platform="youtube") for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("platform") == []


# ── Campaign analysis ─────────────────────────────────────────────────────────


def test_campaign_best_campaign_recommended():
    q1 = [_rec(campaign_name="Q1", engagement_rate=20.0) for _ in range(3)]
    q2 = [_rec(campaign_name="Q2", engagement_rate=3.0) for _ in range(3)]
    opt = Optimizer(q1 + q2)
    report = opt.analyze()
    eng_recs = report.by_category("engagement")
    assert len(eng_recs) >= 1
    assert any("Q1" in r.title for r in eng_recs)


def test_campaign_no_named_campaigns_no_rec():
    records = [_rec(campaign_name="") for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("engagement") == []


# ── Trend analysis ────────────────────────────────────────────────────────────


def test_trend_improving():
    first_half = [
        _rec(engagement_rate=3.0, fetched_at=f"2024-01-0{i+1}T00:00:00+00:00")
        for i in range(4)
    ]
    second_half = [
        _rec(engagement_rate=9.0, fetched_at=f"2024-01-{i+10}T00:00:00+00:00")
        for i in range(4)
    ]
    opt = Optimizer(first_half + second_half)
    report = opt.analyze()
    assert report.trend == "improving"
    assert report.trend_pct > 0


def test_trend_declining():
    first_half = [
        _rec(engagement_rate=15.0, fetched_at=f"2024-01-0{i+1}T00:00:00+00:00")
        for i in range(4)
    ]
    second_half = [
        _rec(engagement_rate=4.0, fetched_at=f"2024-01-{i+10}T00:00:00+00:00")
        for i in range(4)
    ]
    opt = Optimizer(first_half + second_half)
    report = opt.analyze()
    assert report.trend == "declining"
    assert report.trend_pct < 0
    trend_recs = report.by_category("trend")
    assert len(trend_recs) >= 1
    decline_rec = trend_recs[0]
    assert decline_rec.severity in ("high", "medium")


def test_trend_stable():
    records = [
        _rec(engagement_rate=5.0, fetched_at=f"2024-01-0{i+1}T00:00:00+00:00")
        for i in range(8)
    ]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.trend == "stable"


def test_trend_insufficient_data():
    records = [_rec() for _ in range(3)]  # < 6 required
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.trend == "insufficient_data"


# ── Frequency analysis ────────────────────────────────────────────────────────


def test_frequency_long_gap_flagged():
    # Gap of 30 days between first and second publish
    records = [
        _rec(published_at="2024-01-01T00:00:00+00:00",
             fetched_at="2024-01-02T00:00:00+00:00"),
        _rec(published_at="2024-01-31T00:00:00+00:00",
             fetched_at="2024-02-01T00:00:00+00:00"),
        _rec(published_at="2024-02-07T00:00:00+00:00",
             fetched_at="2024-02-08T00:00:00+00:00"),
        _rec(published_at="2024-02-14T00:00:00+00:00",
             fetched_at="2024-02-15T00:00:00+00:00"),
        _rec(published_at="2024-02-21T00:00:00+00:00",
             fetched_at="2024-02-22T00:00:00+00:00"),
    ]
    opt = Optimizer(records)
    report = opt.analyze()
    freq_recs = report.by_category("frequency")
    assert len(freq_recs) >= 1
    assert any(r.severity == "medium" for r in freq_recs)


def test_frequency_consistent_posting_positive():
    # Every 2 days for 6 records → avg_gap ≤ 3, positive rec
    records = [
        _rec(
            published_at=f"2024-01-{(i * 2 + 1):02d}T00:00:00+00:00",
            fetched_at=f"2024-01-{(i * 2 + 2):02d}T00:00:00+00:00",
        )
        for i in range(6)
    ]
    opt = Optimizer(records)
    report = opt.analyze()
    freq_recs = report.by_category("frequency")
    assert any(r.severity == "low" for r in freq_recs)


def test_frequency_insufficient_data_no_rec():
    records = [_rec() for _ in range(2)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.by_category("frequency") == []


# ── Top performers ────────────────────────────────────────────────────────────


def test_top_performers_by_views():
    records = [_rec(views=100), _rec(views=9999), _rec(views=500)]
    opt = Optimizer(records)
    report = opt.analyze()
    assert report.top_performers["top_by_views"]["views"] == 9999


def test_top_performers_by_template():
    records = [
        _rec(template_ref="tmpl-a", views=100),
        _rec(template_ref="tmpl-b", views=500),
    ]
    opt = Optimizer(records)
    report = opt.analyze()
    assert "tmpl-a" in report.top_performers["by_template"]
    assert "tmpl-b" in report.top_performers["by_template"]


def test_top_performers_empty_when_no_records():
    opt = Optimizer([])
    report = opt.analyze()
    assert report.top_performers == {}


# ── Manifest schema safety ────────────────────────────────────────────────────


def test_recommendations_do_not_modify_records():
    """Optimizer must be a pure reader — records unchanged after analyze()."""
    records = [_rec(views=1000, ctr=0.5) for _ in range(5)]
    original_views = [r.views for r in records]
    opt = Optimizer(records)
    opt.analyze()
    assert [r.views for r in records] == original_views


def test_report_to_dict_does_not_violate_schema():
    """OptimizationReport.to_dict() must be JSON-serialisable."""
    import json
    records = [_rec() for _ in range(5)]
    opt = Optimizer(records)
    report = opt.analyze()
    d = report.to_dict()
    # Should not raise
    serialised = json.dumps(d)
    assert len(serialised) > 0
