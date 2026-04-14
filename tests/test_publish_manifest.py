"""Tests for clipforge.publish_manifest — PublishManifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clipforge.publish_manifest import PublishManifest, VALID_PLATFORMS, VALID_STATUSES


# ── Basic instantiation ───────────────────────────────────────────────────────


def test_importable():
    assert PublishManifest is not None


def test_default_fields():
    m = PublishManifest(video_path="output/video.mp4")
    assert m.platform == "reels"
    assert m.status == "draft"
    assert m.priority == "normal"
    assert m.queue_name == "default"
    assert m.timezone == "UTC"
    assert m.manifest_id  # auto-generated UUID


def test_manifest_id_auto_generated():
    m1 = PublishManifest()
    m2 = PublishManifest()
    assert m1.manifest_id != m2.manifest_id


def test_custom_fields():
    m = PublishManifest(
        job_name="ep42",
        project_name="TechBrief",
        platform="tiktok",
        video_path="out/v.mp4",
        title="AI is wild",
        caption="Here's why...",
        hashtags="#AI #tiktok",
        status="ready",
        priority="high",
    )
    assert m.job_name == "ep42"
    assert m.project_name == "TechBrief"
    assert m.platform == "tiktok"
    assert m.title == "AI is wild"
    assert m.status == "ready"
    assert m.priority == "high"


# ── to_dict / from_dict roundtrip ─────────────────────────────────────────────


def test_to_dict_roundtrip():
    m = PublishManifest(
        job_name="test",
        platform="youtube-shorts",
        video_path="v.mp4",
        title="Hello",
        caption="World",
        hashtags="#test",
        publish_at="2026-05-01T18:00:00+00:00",
        campaign_name="spring",
        profile_ref="profile.json",
        template_ref="business",
        manual_review_required=True,
    )
    d = m.to_dict()
    m2 = PublishManifest.from_dict(d)
    assert m2.job_name == m.job_name
    assert m2.platform == m.platform
    assert m2.title == m.title
    assert m2.publish_at == m.publish_at
    assert m2.campaign_name == m.campaign_name
    assert m2.profile_ref == m.profile_ref
    assert m2.template_ref == m.template_ref
    assert m2.manual_review_required is True
    assert m2.manifest_id == m.manifest_id


def test_from_dict_extra_fields_preserved():
    d = {"video_path": "v.mp4", "my_custom_key": "my_value"}
    m = PublishManifest.from_dict(d)
    assert m.extra.get("my_custom_key") == "my_value"


def test_to_dict_extra_fields_round_trip():
    m = PublishManifest(video_path="v.mp4", extra={"source": "batch_run"})
    d = m.to_dict()
    assert d["source"] == "batch_run"
    m2 = PublishManifest.from_dict(d)
    assert m2.extra["source"] == "batch_run"


def test_variants_roundtrip():
    m = PublishManifest(
        video_path="v.mp4",
        title_variants=["T1", "T2"],
        cta_variants=["C1", "C2", "C3"],
    )
    d = m.to_dict()
    m2 = PublishManifest.from_dict(d)
    assert m2.title_variants == ["T1", "T2"]
    assert m2.cta_variants == ["C1", "C2", "C3"]


# ── save / load ───────────────────────────────────────────────────────────────


def test_save_creates_file(tmp_path):
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    out = tmp_path / "ep1.manifest.json"
    m.save(out)
    assert out.exists()


def test_load_roundtrip(tmp_path):
    m = PublishManifest(
        job_name="load-test",
        platform="youtube",
        video_path="v.mp4",
        title="My Title",
        notes="Some notes here",
    )
    p = tmp_path / "m.json"
    m.save(p)
    m2 = PublishManifest.load(p)
    assert m2.job_name == "load-test"
    assert m2.platform == "youtube"
    assert m2.title == "My Title"
    assert m2.notes == "Some notes here"
    assert m2.manifest_id == m.manifest_id


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PublishManifest.load(tmp_path / "does_not_exist.json")


def test_save_creates_parent_dirs(tmp_path):
    m = PublishManifest(video_path="v.mp4")
    deep = tmp_path / "a" / "b" / "c" / "m.json"
    m.save(deep)
    assert deep.exists()


def test_save_updates_updated_at(tmp_path):
    m = PublishManifest(video_path="v.mp4")
    original_updated = m.updated_at
    import time; time.sleep(0.01)
    m.save(tmp_path / "m.json")
    assert m.updated_at >= original_updated


# ── validate ──────────────────────────────────────────────────────────────────


def test_validate_missing_video_path():
    m = PublishManifest()
    errors = m.validate()
    assert any("video_path" in e for e in errors)


def test_validate_valid_manifest():
    m = PublishManifest(video_path="v.mp4", platform="reels")
    assert m.validate() == []


def test_validate_invalid_platform():
    m = PublishManifest(video_path="v.mp4", platform="snapchat")
    errors = m.validate()
    assert any("platform" in e for e in errors)


def test_validate_invalid_status():
    m = PublishManifest(video_path="v.mp4", status="unknown_status")
    errors = m.validate()
    assert any("status" in e for e in errors)


def test_validate_invalid_priority():
    m = PublishManifest(video_path="v.mp4", priority="urgent")
    errors = m.validate()
    assert any("priority" in e for e in errors)


def test_validate_invalid_publish_at():
    m = PublishManifest(video_path="v.mp4", publish_at="not-a-date")
    errors = m.validate()
    assert any("publish_at" in e for e in errors)


def test_validate_valid_publish_at():
    m = PublishManifest(video_path="v.mp4", publish_at="2026-05-01T18:00:00+00:00")
    assert m.validate() == []


def test_validate_valid_publish_at_zulu():
    m = PublishManifest(video_path="v.mp4", publish_at="2026-05-01T18:00:00Z")
    assert m.validate() == []


def test_is_ready_true():
    m = PublishManifest(video_path="v.mp4")
    assert m.is_ready() is True


def test_is_ready_false():
    m = PublishManifest(video_path="", platform="bad")
    assert m.is_ready() is False


def test_valid_platforms_set():
    assert "reels" in VALID_PLATFORMS
    assert "tiktok" in VALID_PLATFORMS
    assert "youtube" in VALID_PLATFORMS


def test_valid_statuses_set():
    for s in ("draft", "pending", "ready", "scheduled", "published", "failed"):
        assert s in VALID_STATUSES


def test_repr():
    m = PublishManifest(job_name="myj", platform="reels", status="ready")
    assert "myj" in repr(m)
    assert "reels" in repr(m)
