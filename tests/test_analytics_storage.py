"""Tests for AnalyticsStore — save/load/list/filter/summary."""

from __future__ import annotations

import pytest

from clipforge.analytics.models import ContentAnalytics
from clipforge.analytics.storage import AnalyticsStore


def _make(platform="youtube", manifest_id="m-1", views=100, **kwargs) -> ContentAnalytics:
    return ContentAnalytics(
        platform=platform,
        manifest_id=manifest_id,
        views=views,
        **kwargs,
    )


# ── Basic save / load ─────────────────────────────────────────────────────────


def test_save_returns_path(tmp_path):
    store = AnalyticsStore(tmp_path)
    rec = _make()
    p = store.save(rec)
    assert p.exists()
    assert p.name == f"{rec.analytics_id}.json"


def test_load_by_id(tmp_path):
    store = AnalyticsStore(tmp_path)
    rec = _make(views=42)
    store.save(rec)
    loaded = store.load(rec.analytics_id)
    assert loaded.views == 42


def test_load_not_found(tmp_path):
    store = AnalyticsStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.load("nonexistent-id")


def test_len(tmp_path):
    store = AnalyticsStore(tmp_path)
    assert len(store) == 0
    store.save(_make())
    store.save(_make())
    assert len(store) == 2


# ── list ──────────────────────────────────────────────────────────────────────


def test_list_sorted_by_fetched_at(tmp_path):
    store = AnalyticsStore(tmp_path)
    r1 = _make(fetched_at="2024-01-01T00:00:00+00:00")
    r2 = _make(fetched_at="2024-03-01T00:00:00+00:00")
    r3 = _make(fetched_at="2024-02-01T00:00:00+00:00")
    for r in [r1, r2, r3]:
        store.save(r)
    records = store.list()
    assert [r.analytics_id for r in records] == [r1.analytics_id, r3.analytics_id, r2.analytics_id]


def test_list_empty(tmp_path):
    store = AnalyticsStore(tmp_path)
    assert store.list() == []


def test_list_skips_corrupt_files(tmp_path):
    store = AnalyticsStore(tmp_path)
    (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
    store.save(_make())
    records = store.list()
    assert len(records) == 1


# ── for_manifest ──────────────────────────────────────────────────────────────


def test_for_manifest(tmp_path):
    store = AnalyticsStore(tmp_path)
    store.save(_make(manifest_id="m-1"))
    store.save(_make(manifest_id="m-1"))
    store.save(_make(manifest_id="m-2"))
    assert len(store.for_manifest("m-1")) == 2
    assert len(store.for_manifest("m-2")) == 1
    assert store.for_manifest("m-3") == []


def test_latest_for_manifest(tmp_path):
    store = AnalyticsStore(tmp_path)
    r1 = _make(manifest_id="m-1", fetched_at="2024-01-01T00:00:00+00:00")
    r2 = _make(manifest_id="m-1", fetched_at="2024-02-01T00:00:00+00:00")
    store.save(r1)
    store.save(r2)
    latest = store.latest_for_manifest("m-1")
    assert latest is not None
    assert latest.analytics_id == r2.analytics_id


def test_latest_for_manifest_none(tmp_path):
    store = AnalyticsStore(tmp_path)
    assert store.latest_for_manifest("missing") is None


# ── for_platform / for_campaign ───────────────────────────────────────────────


def test_for_platform(tmp_path):
    store = AnalyticsStore(tmp_path)
    store.save(_make(platform="youtube"))
    store.save(_make(platform="youtube"))
    store.save(_make(platform="tiktok"))
    assert len(store.for_platform("youtube")) == 2
    assert len(store.for_platform("tiktok")) == 1


def test_for_campaign(tmp_path):
    store = AnalyticsStore(tmp_path)
    store.save(_make(campaign_name="Q1"))
    store.save(_make(campaign_name="Q2"))
    store.save(_make(campaign_name="Q1"))
    assert len(store.for_campaign("Q1")) == 2


# ── summary ───────────────────────────────────────────────────────────────────


def test_summary_empty(tmp_path):
    store = AnalyticsStore(tmp_path)
    result = store.summary()
    assert result["total_records"] == 0
    assert result["platforms"] == []


def test_summary_totals_and_averages(tmp_path):
    store = AnalyticsStore(tmp_path)
    store.save(_make(platform="youtube", views=100, likes=10))
    store.save(_make(platform="youtube", views=200, likes=20))
    result = store.summary()
    assert result["total_records"] == 2
    assert result["metrics"]["totals"]["views"] == 300
    assert result["metrics"]["averages"]["views"] == 150


def test_summary_by_platform(tmp_path):
    store = AnalyticsStore(tmp_path)
    store.save(_make(platform="youtube", views=100))
    store.save(_make(platform="tiktok", views=200))
    result = store.summary()
    assert "youtube" in result["by_platform"]
    assert "tiktok" in result["by_platform"]
    assert result["by_platform"]["youtube"]["count"] == 1
    assert result["by_platform"]["tiktok"]["totals"]["views"] == 200
