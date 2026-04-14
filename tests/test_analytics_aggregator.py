"""Tests for AnalyticsAggregator — summary, compare, time_series, group-by, top_by."""

from __future__ import annotations

import pytest

from clipforge.analytics.aggregator import AnalyticsAggregator, _bucket_key
from clipforge.analytics.models import ContentAnalytics


# ── Helpers ───────────────────────────────────────────────────────────────────


def _rec(**kwargs) -> ContentAnalytics:
    defaults = {
        "platform": "youtube",
        "manifest_id": "m-1",
        "views": 100,
        "likes": 10,
        "comments": 5,
        "shares": 2,
        "impressions": 200,
        "reach": 150,
        "ctr": 2.5,
        "retention_pct": 50.0,
        "avg_view_duration_s": 30.0,
        "engagement_rate": 17.0,
        "fetched_at": "2024-06-15T10:00:00+00:00",
        "campaign_name": "summer",
        "template_ref": "tmpl-a",
    }
    defaults.update(kwargs)
    return ContentAnalytics(**defaults)


# ── summary ───────────────────────────────────────────────────────────────────


def test_summary_empty():
    agg = AnalyticsAggregator([])
    result = agg.summary()
    assert result["count"] == 0
    assert result["totals"] == {}
    assert result["averages"] == {}


def test_summary_single():
    agg = AnalyticsAggregator([_rec(views=1000, likes=50)])
    result = agg.summary()
    assert result["count"] == 1
    assert result["totals"]["views"] == 1000
    assert result["averages"]["views"] == pytest.approx(1000.0)


def test_summary_multiple():
    records = [_rec(views=100), _rec(views=200), _rec(views=300)]
    agg = AnalyticsAggregator(records)
    result = agg.summary()
    assert result["count"] == 3
    assert result["totals"]["views"] == 600
    assert result["averages"]["views"] == pytest.approx(200.0)


# ── by_platform ───────────────────────────────────────────────────────────────


def test_by_platform():
    records = [
        _rec(platform="youtube", views=100),
        _rec(platform="youtube", views=200),
        _rec(platform="tiktok", views=50),
    ]
    agg = AnalyticsAggregator(records)
    result = agg.by_platform()
    assert "youtube" in result
    assert "tiktok" in result
    assert result["youtube"]["count"] == 2
    assert result["youtube"]["totals"]["views"] == 300
    assert result["tiktok"]["count"] == 1


def test_by_platform_unknown():
    records = [_rec(platform=None)]
    agg = AnalyticsAggregator(records)
    result = agg.by_platform()
    assert "unknown" in result


# ── by_template ───────────────────────────────────────────────────────────────


def test_by_template():
    records = [
        _rec(template_ref="tmpl-a", views=100),
        _rec(template_ref="tmpl-b", views=200),
        _rec(template_ref="tmpl-a", views=50),
    ]
    agg = AnalyticsAggregator(records)
    result = agg.by_template()
    assert result["tmpl-a"]["count"] == 2
    assert result["tmpl-b"]["count"] == 1


def test_by_template_none():
    records = [_rec(template_ref=None)]
    agg = AnalyticsAggregator(records)
    result = agg.by_template()
    assert "(no template)" in result


# ── by_campaign ───────────────────────────────────────────────────────────────


def test_by_campaign():
    records = [
        _rec(campaign_name="Q1", views=100),
        _rec(campaign_name="Q2", views=200),
    ]
    agg = AnalyticsAggregator(records)
    result = agg.by_campaign()
    assert "Q1" in result
    assert "Q2" in result


def test_by_campaign_none():
    records = [_rec(campaign_name=None)]
    agg = AnalyticsAggregator(records)
    result = agg.by_campaign()
    assert "(no campaign)" in result


# ── top_by ────────────────────────────────────────────────────────────────────


def test_top_by_views():
    records = [_rec(views=v) for v in [10, 500, 50, 200, 1000, 300]]
    agg = AnalyticsAggregator(records)
    top = agg.top_by("views", n=3)
    assert len(top) == 3
    assert top[0].views == 1000
    assert top[1].views == 500
    assert top[2].views == 300


def test_top_by_n_larger_than_records():
    records = [_rec(views=v) for v in [10, 20]]
    agg = AnalyticsAggregator(records)
    top = agg.top_by("views", n=10)
    assert len(top) == 2


def test_top_by_default_n():
    records = [_rec(views=v) for v in range(10)]
    agg = AnalyticsAggregator(records)
    top = agg.top_by("views")
    assert len(top) == 5


def test_top_by_missing_metric():
    records = [_rec()]
    agg = AnalyticsAggregator(records)
    top = agg.top_by("nonexistent_metric", n=1)
    assert len(top) == 1  # returns record, 0 for missing attribute


# ── compare ───────────────────────────────────────────────────────────────────


def test_compare_empty():
    result = AnalyticsAggregator.compare([], [])
    assert result == {}


def test_compare_basic():
    a = [_rec(views=100, likes=10, comments=5, shares=2, engagement_rate=17.0)]
    b = [_rec(views=200, likes=20, comments=8, shares=5, engagement_rate=16.5)]
    result = AnalyticsAggregator.compare(a, b)
    assert result["count_a"] == 1
    assert result["count_b"] == 1
    views = result["metrics"]["views"]
    assert views["A"] == pytest.approx(100.0)
    assert views["B"] == pytest.approx(200.0)
    assert views["delta"] == pytest.approx(100.0)
    assert views["winner"] == "B"


def test_compare_a_wins():
    a = [_rec(views=500)]
    b = [_rec(views=100)]
    result = AnalyticsAggregator.compare(a, b, label_a="control", label_b="variant")
    views = result["metrics"]["views"]
    assert views["winner"] == "control"
    assert views["delta"] < 0


def test_compare_tie():
    a = [_rec(views=100)]
    b = [_rec(views=100)]
    result = AnalyticsAggregator.compare(a, b)
    assert result["metrics"]["views"]["winner"] == "tie"


def test_compare_b_empty():
    a = [_rec(views=200)]
    result = AnalyticsAggregator.compare(a, [])
    assert result["metrics"]["views"]["B"] == 0.0
    assert result["metrics"]["views"]["winner"] == "A"


def test_compare_custom_labels():
    a = [_rec(views=100)]
    b = [_rec(views=200)]
    result = AnalyticsAggregator.compare(a, b, label_a="old", label_b="new")
    assert "old" in result["metrics"]["views"]
    assert "new" in result["metrics"]["views"]


# ── time_series ───────────────────────────────────────────────────────────────


def test_time_series_day_bucket():
    records = [
        _rec(fetched_at="2024-01-01T10:00:00+00:00", views=100),
        _rec(fetched_at="2024-01-01T15:00:00+00:00", views=200),
        _rec(fetched_at="2024-01-02T08:00:00+00:00", views=50),
    ]
    agg = AnalyticsAggregator(records)
    series = agg.time_series(bucket="day")
    assert len(series) == 2
    assert series[0]["period"] == "2024-01-01"
    assert series[0]["count"] == 2
    assert series[0]["totals"]["views"] == 300
    assert series[1]["period"] == "2024-01-02"
    assert series[1]["count"] == 1


def test_time_series_week_bucket():
    records = [
        _rec(fetched_at="2024-01-01T00:00:00+00:00"),  # 2024-W01
        _rec(fetched_at="2024-01-08T00:00:00+00:00"),  # 2024-W02
    ]
    agg = AnalyticsAggregator(records)
    series = agg.time_series(bucket="week")
    assert len(series) == 2
    assert series[0]["period"].startswith("2024-W")


def test_time_series_month_bucket():
    records = [
        _rec(fetched_at="2024-01-15T00:00:00+00:00"),
        _rec(fetched_at="2024-01-20T00:00:00+00:00"),
        _rec(fetched_at="2024-02-05T00:00:00+00:00"),
    ]
    agg = AnalyticsAggregator(records)
    series = agg.time_series(bucket="month")
    assert len(series) == 2
    assert series[0]["period"] == "2024-01"
    assert series[0]["count"] == 2


def test_time_series_invalid_date_buckets_to_unknown():
    records = [_rec(fetched_at="not-a-date")]
    agg = AnalyticsAggregator(records)
    series = agg.time_series()
    assert series[0]["period"] == "unknown"


def test_time_series_sorted_ascending():
    records = [
        _rec(fetched_at="2024-03-01T00:00:00+00:00"),
        _rec(fetched_at="2024-01-01T00:00:00+00:00"),
        _rec(fetched_at="2024-02-01T00:00:00+00:00"),
    ]
    agg = AnalyticsAggregator(records)
    series = agg.time_series(bucket="month")
    periods = [s["period"] for s in series]
    assert periods == sorted(periods)


# ── _bucket_key ───────────────────────────────────────────────────────────────


def test_bucket_key_day():
    assert _bucket_key("2024-06-15T10:30:00+00:00", "day") == "2024-06-15"


def test_bucket_key_week():
    key = _bucket_key("2024-01-08T00:00:00+00:00", "week")
    assert key.startswith("2024-W")


def test_bucket_key_month():
    assert _bucket_key("2024-06-15T10:00:00+00:00", "month") == "2024-06"


def test_bucket_key_invalid():
    assert _bucket_key("bad-date", "day") == "unknown"


def test_bucket_key_unknown_bucket_defaults_to_day():
    key = _bucket_key("2024-06-15T10:00:00+00:00", "hour")
    assert key == "2024-06-15"  # falls through to default strftime("%Y-%m-%d")
