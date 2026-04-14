"""Tests for clipforge.publish_queue — PublishQueue."""

from __future__ import annotations

import pytest

from clipforge.publish_manifest import PublishManifest
from clipforge.publish_queue import PublishQueue


# ── Init / load ───────────────────────────────────────────────────────────────


def test_importable():
    assert PublishQueue is not None


def test_init_creates_dir(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    assert (tmp_path / "q").is_dir()


def test_init_creates_queue_json(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    assert (tmp_path / "q" / "queue.json").exists()


def test_init_creates_manifests_subdir(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    assert (tmp_path / "q" / "manifests").is_dir()


def test_init_default_name(tmp_path):
    q = PublishQueue.init(tmp_path / "my-queue")
    assert q.name == "my-queue"


def test_init_custom_name(tmp_path):
    q = PublishQueue.init(tmp_path / "q", name="Campaign A")
    assert q.name == "Campaign A"


def test_load_empty_queue(tmp_path):
    PublishQueue.init(tmp_path / "q")
    q2 = PublishQueue.load(tmp_path / "q")
    assert q2.name
    assert len(q2) == 0


def test_load_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PublishQueue.load(tmp_path / "no_such_dir")


def test_load_missing_queue_json_raises(tmp_path):
    (tmp_path / "q").mkdir()
    with pytest.raises(FileNotFoundError):
        PublishQueue.load(tmp_path / "q")


def test_repr(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    assert "PublishQueue" in repr(q)


# ── Append / get ──────────────────────────────────────────────────────────────


def test_append_increases_length(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    q.append(m)
    assert len(q) == 1


def test_append_saves_manifest_file(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    q.append(m)
    assert (tmp_path / "q" / "manifests" / f"{m.manifest_id}.json").exists()


def test_append_duplicate_raises(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    q.append(m)
    with pytest.raises(ValueError, match="already in the queue"):
        q.append(m)


def test_get_returns_manifest(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4", title="Hello")
    q.append(m)
    loaded = q.get(m.manifest_id)
    assert loaded.title == "Hello"
    assert loaded.job_name == "ep1"


def test_get_missing_raises_key_error(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    with pytest.raises(KeyError):
        q.get("nonexistent-id")


# ── list / filter ─────────────────────────────────────────────────────────────


def test_list_empty(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    assert q.list() == []


def test_list_returns_all(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    for i in range(3):
        q.append(PublishManifest(job_name=f"ep{i}", video_path="v.mp4"))
    assert len(q.list()) == 3


def test_filter_by_status(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    q.append(PublishManifest(job_name="a", video_path="v.mp4", status="draft"))
    q.append(PublishManifest(job_name="b", video_path="v.mp4", status="ready"))
    q.append(PublishManifest(job_name="c", video_path="v.mp4", status="draft"))
    drafts = q.filter_by_status("draft")
    assert len(drafts) == 2
    assert all(m.status == "draft" for m in drafts)


def test_filter_by_platform(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    q.append(PublishManifest(job_name="a", video_path="v.mp4", platform="reels"))
    q.append(PublishManifest(job_name="b", video_path="v.mp4", platform="tiktok"))
    reels = q.filter_by_platform("reels")
    assert len(reels) == 1
    assert reels[0].job_name == "a"


def test_filter_by_campaign(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    q.append(PublishManifest(job_name="a", video_path="v.mp4", campaign_name="spring"))
    q.append(PublishManifest(job_name="b", video_path="v.mp4", campaign_name="summer"))
    spring = q.filter_by_campaign("spring")
    assert len(spring) == 1
    assert spring[0].job_name == "a"


# ── update_status ─────────────────────────────────────────────────────────────


def test_update_status(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4", status="draft")
    q.append(m)
    q.update_status(m.manifest_id, "ready")
    reloaded = q.get(m.manifest_id)
    assert reloaded.status == "ready"


def test_update_status_invalid_raises(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    q.append(m)
    with pytest.raises(ValueError, match="Invalid status"):
        q.update_status(m.manifest_id, "nonexistent")


def test_update_status_missing_id_raises(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    with pytest.raises(KeyError):
        q.update_status("bad-id", "ready")


# ── remove ────────────────────────────────────────────────────────────────────


def test_remove_decreases_length(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="ep1", video_path="v.mp4")
    q.append(m)
    q.remove(m.manifest_id)
    assert len(q) == 0


def test_remove_missing_raises(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    with pytest.raises(KeyError):
        q.remove("bad-id")


# ── summary ───────────────────────────────────────────────────────────────────


def test_summary_empty(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    s = q.summary()
    assert s["total"] == 0
    assert isinstance(s["by_status"], dict)


def test_summary_counts_by_status(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    q.append(PublishManifest(job_name="a", video_path="v.mp4", status="draft"))
    q.append(PublishManifest(job_name="b", video_path="v.mp4", status="draft"))
    q.append(PublishManifest(job_name="c", video_path="v.mp4", status="ready"))
    s = q.summary()
    assert s["total"] == 3
    assert s["by_status"]["draft"] == 2
    assert s["by_status"]["ready"] == 1


# ── Persistence across reload ─────────────────────────────────────────────────


def test_persist_across_reload(tmp_path):
    q = PublishQueue.init(tmp_path / "q")
    m = PublishManifest(job_name="persist-test", video_path="v.mp4")
    q.append(m)

    q2 = PublishQueue.load(tmp_path / "q")
    assert len(q2) == 1
    reloaded = q2.get(m.manifest_id)
    assert reloaded.job_name == "persist-test"
