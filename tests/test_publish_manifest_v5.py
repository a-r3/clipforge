"""Tests for V5 extensions to PublishManifest — record_attempt, as_publish_target."""

from __future__ import annotations

from clipforge.providers.publish.base import PublishResult, PublishTarget
from clipforge.publish_manifest import PublishManifest


def test_publish_attempts_default_empty():
    m = PublishManifest(video_path="v.mp4")
    assert m.publish_attempts == []


def test_record_attempt_appends():
    m = PublishManifest(video_path="v.mp4")
    result = PublishResult(success=True, provider="manual", platform="reels")
    m.record_attempt(result)
    assert len(m.publish_attempts) == 1


def test_record_attempt_stores_to_dict():
    m = PublishManifest(video_path="v.mp4")
    result = PublishResult(success=False, provider="youtube", error="timeout")
    m.record_attempt(result)
    entry = m.publish_attempts[0]
    assert entry["success"] is False
    assert entry["provider"] == "youtube"
    assert entry["error"] == "timeout"
    assert "attempted_at" in entry


def test_record_attempt_multiple():
    m = PublishManifest(video_path="v.mp4")
    m.record_attempt(PublishResult(success=False, error="first failure"))
    m.record_attempt(PublishResult(success=True))
    assert len(m.publish_attempts) == 2


def test_last_attempt_none_when_empty():
    m = PublishManifest(video_path="v.mp4")
    assert m.last_attempt() is None


def test_last_attempt_returns_most_recent():
    m = PublishManifest(video_path="v.mp4")
    m.record_attempt(PublishResult(success=False, error="fail1"))
    m.record_attempt(PublishResult(success=True, provider="youtube"))
    last = m.last_attempt()
    assert last["success"] is True
    assert last["provider"] == "youtube"


def test_publish_attempts_survive_save_load(tmp_path):
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    m.record_attempt(PublishResult(success=True, provider="manual", platform="reels"))
    p = tmp_path / "m.json"
    m.save(p)
    m2 = PublishManifest.load(p)
    assert len(m2.publish_attempts) == 1
    assert m2.publish_attempts[0]["provider"] == "manual"


def test_as_publish_target_basic():
    m = PublishManifest(
        video_path="out/v.mp4",
        title="Test Title",
        caption="Test caption",
        hashtags="#AI #reels",
        platform="reels",
        publish_at="2026-05-01T18:00:00Z",
    )
    t = m.as_publish_target()
    assert isinstance(t, PublishTarget)
    assert t.video_path == "out/v.mp4"
    assert t.title == "Test Title"
    assert t.caption == "Test caption"
    assert t.platform == "reels"
    assert t.schedule_at == "2026-05-01T18:00:00Z"


def test_as_publish_target_converts_hashtags_to_tags():
    m = PublishManifest(video_path="v.mp4", hashtags="#AI #reels #shorts")
    t = m.as_publish_target()
    assert "AI" in t.tags
    assert "reels" in t.tags
    assert "shorts" in t.tags


def test_as_publish_target_extra_carries_job_name():
    m = PublishManifest(job_name="ep42", video_path="v.mp4")
    t = m.as_publish_target()
    assert t.extra["job_name"] == "ep42"
    assert t.extra["manifest_id"] == m.manifest_id


def test_as_publish_target_extra_override():
    m = PublishManifest(video_path="v.mp4")
    t = m.as_publish_target(extra={"checklist_dir": "/tmp/cl"})
    assert t.extra["checklist_dir"] == "/tmp/cl"
