"""Tests for ContentAnalytics model — serialisation, save/load, helpers."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from clipforge.analytics.models import ContentAnalytics


# ── Defaults and construction ─────────────────────────────────────────────────


def test_default_fields():
    rec = ContentAnalytics()
    assert rec.views == 0
    assert rec.likes == 0
    assert rec.data_source == "api"
    assert rec.fetch_error == ""
    assert rec.platform == ""
    assert uuid.UUID(rec.analytics_id)  # valid UUID
    assert rec.fetched_at  # non-empty ISO string


def test_explicit_fields():
    rec = ContentAnalytics(
        manifest_id="m-1",
        post_id="vid-123",
        platform="youtube",
        views=1000,
        likes=50,
        comments=10,
        shares=5,
        data_source="api",
    )
    assert rec.manifest_id == "m-1"
    assert rec.post_id == "vid-123"
    assert rec.views == 1000


# ── Computed helpers ──────────────────────────────────────────────────────────


def test_compute_engagement_rate_no_views():
    rec = ContentAnalytics(views=0, likes=10)
    assert rec.compute_engagement_rate() == 0.0


def test_compute_engagement_rate():
    rec = ContentAnalytics(views=100, likes=5, comments=2, shares=3)
    assert rec.compute_engagement_rate() == pytest.approx(10.0)


def test_is_real_api():
    assert ContentAnalytics(data_source="api").is_real() is True


def test_is_real_mock():
    assert ContentAnalytics(data_source="mock").is_real() is False


def test_is_real_stub():
    assert ContentAnalytics(data_source="stub").is_real() is False


def test_is_real_manual():
    assert ContentAnalytics(data_source="manual").is_real() is False


# ── Serialisation ─────────────────────────────────────────────────────────────


def test_to_dict_keys():
    rec = ContentAnalytics(platform="tiktok", views=200)
    d = rec.to_dict()
    assert d["platform"] == "tiktok"
    assert d["views"] == 200
    assert "analytics_id" in d
    assert "fetched_at" in d


def test_round_trip():
    rec = ContentAnalytics(
        manifest_id="m-abc",
        platform="reels",
        views=999,
        likes=40,
        ctr=3.14,
        data_source="manual",
        fetch_error="",
    )
    d = rec.to_dict()
    rec2 = ContentAnalytics.from_dict(d)
    assert rec2.analytics_id == rec.analytics_id
    assert rec2.manifest_id == rec.manifest_id
    assert rec2.views == rec.views
    assert rec2.ctr == rec.ctr
    assert rec2.data_source == rec.data_source


def test_from_dict_extra_fields_preserved():
    d = {
        "analytics_id": str(uuid.uuid4()),
        "platform": "youtube",
        "views": 1,
        "custom_key": "custom_value",
    }
    rec = ContentAnalytics.from_dict(d)
    assert rec.extra.get("custom_key") == "custom_value"


def test_to_dict_extra_fields_included():
    rec = ContentAnalytics(extra={"foo": "bar"})
    d = rec.to_dict()
    assert d.get("foo") == "bar"


# ── Save / load ───────────────────────────────────────────────────────────────


def test_save_and_load(tmp_path):
    rec = ContentAnalytics(platform="youtube", views=500, likes=25)
    path = tmp_path / "analytics.json"
    rec.save(path)

    assert path.exists()
    loaded = ContentAnalytics.load(path)
    assert loaded.analytics_id == rec.analytics_id
    assert loaded.views == 500
    assert loaded.likes == 25


def test_load_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        ContentAnalytics.load(tmp_path / "nonexistent.json")


def test_save_creates_parent_dirs(tmp_path):
    rec = ContentAnalytics(views=1)
    path = tmp_path / "a" / "b" / "record.json"
    rec.save(path)
    assert path.exists()
