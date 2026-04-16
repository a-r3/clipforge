"""Tests for V5 publish provider layer.

All network/API interactions are mocked — no live API calls.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from clipforge.providers.publish.base import (
    PublishNotAvailableError,
    PublishProvider,
    PublishResult,
    PublishTarget,
)
from clipforge.providers.publish.factory import PublishProviderFactory
from clipforge.providers.publish.manual_provider import ManualPublishProvider
from clipforge.providers.publish.youtube_provider import YouTubePublishProvider
from clipforge.publish_config import PublishConfig

# ── Helpers ───────────────────────────────────────────────────────────────────

def _target(**kw) -> PublishTarget:
    defaults = {
        "video_path": "video.mp4",
        "title": "Test Video",
        "caption": "Test caption",
        "platform": "youtube",
        "privacy": "public",
    }
    defaults.update(kw)
    return PublishTarget(**defaults)


# ── PublishResult V5 fields ───────────────────────────────────────────────────


def test_publish_result_new_fields():
    r = PublishResult(
        success=True,
        dry_run=True,
        provider="youtube",
        published_at="2026-05-01T18:00:00+00:00",
        retry_count=1,
        response_summary="All good",
        manual_action_required=False,
    )
    assert r.dry_run is True
    assert r.provider == "youtube"
    assert r.retry_count == 1


def test_publish_result_to_dict_roundtrip():
    r = PublishResult(
        success=True,
        dry_run=False,
        provider="manual",
        platform="reels",
        manual_action_required=True,
        response_summary="Checklist ready",
    )
    d = r.to_dict()
    r2 = PublishResult.from_dict(d)
    assert r2.success is True
    assert r2.provider == "manual"
    assert r2.manual_action_required is True
    assert r2.response_summary == "Checklist ready"


def test_publish_result_backwards_compat():
    """Existing code constructing PublishResult(success=True, post_url=…) still works."""
    r = PublishResult(success=True, post_url="https://example.com/post/1")
    assert r.success is True
    assert r.post_url == "https://example.com/post/1"
    assert r.dry_run is False   # default
    assert r.provider == ""     # default


# ── Base class validate_target / dry_run_publish ──────────────────────────────


def test_base_validate_target_missing_video():
    class MinimalProvider(PublishProvider):
        def publish(self, target):
            return PublishResult()

    p = MinimalProvider(api_key="key")
    errors = p.validate_target(PublishTarget())
    assert any("video_path" in e for e in errors)


def test_base_dry_run_publish_valid():
    class MinimalProvider(PublishProvider):
        def publish(self, target):
            return PublishResult()

    p = MinimalProvider(api_key="key")
    result = p.dry_run_publish(_target(video_path="v.mp4", platform="reels"))
    assert result.dry_run is True
    assert result.success is True


def test_base_dry_run_publish_invalid():
    class MinimalProvider(PublishProvider):
        def publish(self, target):
            return PublishResult()

    p = MinimalProvider(api_key="key")
    result = p.dry_run_publish(PublishTarget())  # no video_path
    assert result.dry_run is True
    assert result.success is False


# ── ManualPublishProvider ──────────────────────────────────────────────────────


def test_manual_provider_always_available():
    p = ManualPublishProvider()
    assert p.is_available() is True


def test_manual_provider_name():
    p = ManualPublishProvider()
    assert p.provider_name() == "manual"


def test_manual_validate_missing_video():
    p = ManualPublishProvider()
    errors = p.validate_target(PublishTarget())
    assert any("video_path" in e for e in errors)


def test_manual_validate_missing_video_file(tmp_path):
    p = ManualPublishProvider()
    target = PublishTarget(video_path=str(tmp_path / "no_such.mp4"), platform="reels", title="T")
    errors = p.validate_target(target)
    assert any("does not exist" in e for e in errors)


def test_manual_validate_valid(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = ManualPublishProvider()
    target = PublishTarget(video_path=str(video), platform="reels", title="Test")
    assert p.validate_target(target) == []


def test_manual_dry_run_valid(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = ManualPublishProvider()
    target = PublishTarget(video_path=str(video), platform="reels", title="Test")
    result = p.dry_run_publish(target)
    assert result.dry_run is True
    assert result.manual_action_required is True
    assert result.success is True  # validation passed


def test_manual_dry_run_invalid():
    p = ManualPublishProvider()
    result = p.dry_run_publish(PublishTarget())
    assert result.dry_run is True
    assert result.success is False


def test_manual_publish_returns_manual_action_required(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = ManualPublishProvider()
    target = PublishTarget(video_path=str(video), platform="reels", title="T")
    result = p.publish(target)
    assert result.success is False
    assert result.manual_action_required is True
    assert result.provider == "manual"


def test_manual_publish_writes_checklist_file(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = ManualPublishProvider()
    target = PublishTarget(
        video_path=str(video),
        platform="reels",
        title="Test title",
        caption="Test caption",
        extra={"checklist_dir": str(tmp_path / "checklists"), "job_name": "ep1"},
    )
    result = p.publish(target)
    assert result.manual_action_required is True
    checklist = tmp_path / "checklists" / "ep1_checklist.txt"
    assert checklist.exists()
    content = checklist.read_text()
    assert "REELS" in content
    assert "Test title" in content


def test_manual_publish_invalid_no_checklist(tmp_path):
    """publish() on an invalid target fails without writing a checklist."""
    p = ManualPublishProvider()
    result = p.publish(PublishTarget())  # no video_path
    assert result.success is False
    assert "Validation failed" in result.response_summary


def test_manual_checklist_contains_update_command(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = ManualPublishProvider()
    target = PublishTarget(
        video_path=str(video), platform="tiktok", title="T",
        extra={"checklist_dir": str(tmp_path), "job_name": "ep2"},
    )
    p.publish(target)
    content = (tmp_path / "ep2_checklist.txt").read_text()
    assert "clipforge queue status" in content


# ── YouTubePublishProvider — validation (no API calls) ────────────────────────


def test_youtube_provider_name():
    p = YouTubePublishProvider()
    assert p.provider_name() == "youtube"


def test_youtube_not_available_no_libs_no_creds():
    p = YouTubePublishProvider()
    # In test env, google libs likely not installed
    # Either way, no credentials file = not available
    assert p.is_available() is False


def test_youtube_validate_missing_video():
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(title="T", platform="youtube"))
    assert any("video_path" in e for e in errors)


def test_youtube_validate_missing_title(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(video_path=str(video), platform="youtube"))
    assert any("title" in e for e in errors)


def test_youtube_validate_title_too_long(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(
        video_path=str(video),
        title="X" * 101,
        platform="youtube",
    ))
    assert any("title" in e for e in errors)


def test_youtube_validate_title_max_ok(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(
        video_path=str(video),
        title="X" * 100,
        platform="youtube",
    ))
    assert errors == []


def test_youtube_validate_description_too_long(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(
        video_path=str(video),
        title="T",
        caption="X" * 5001,
        platform="youtube",
    ))
    assert any("description" in e for e in errors)


def test_youtube_validate_invalid_privacy(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(
        video_path=str(video),
        title="T",
        privacy="secret",
        platform="youtube",
    ))
    assert any("privacy" in e for e in errors)


def test_youtube_validate_invalid_schedule_at(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(
        video_path=str(video),
        title="T",
        schedule_at="not-a-date",
        platform="youtube",
    ))
    assert any("schedule_at" in e for e in errors)


def test_youtube_validate_valid(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    errors = p.validate_target(PublishTarget(
        video_path=str(video),
        title="Valid Title",
        caption="A short description.",
        platform="youtube",
        privacy="public",
    ))
    assert errors == []


# ── YouTubePublishProvider — dry-run ──────────────────────────────────────────


def test_youtube_dry_run_no_libs(tmp_path):
    """dry-run shows missing lib note when google libs not installed."""
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    result = p.dry_run_publish(PublishTarget(
        video_path=str(video), title="T", platform="youtube",
    ))
    assert result.dry_run is True
    # Either lib missing or creds missing makes overall_ok False
    assert "google-api-python-client" in result.response_summary or \
           "NOT FOUND" in result.response_summary


def test_youtube_dry_run_valid_when_mocked(tmp_path):
    """dry-run passes when libs and credentials are mocked as present."""
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    creds = tmp_path / "creds.json"
    creds.write_text('{"type": "service_account"}', encoding="utf-8")

    p = YouTubePublishProvider(credentials_path=str(creds))
    target = PublishTarget(video_path=str(video), title="T", platform="youtube")

    with patch.object(YouTubePublishProvider, "_google_libs_available", return_value=True):
        result = p.dry_run_publish(target)

    assert result.dry_run is True
    assert result.success is True


# ── YouTubePublishProvider — publish() raises when unavailable ────────────────


def test_youtube_publish_raises_when_no_libs(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    p = YouTubePublishProvider()
    with patch.object(YouTubePublishProvider, "_google_libs_available", return_value=False):
        with pytest.raises(PublishNotAvailableError, match="google-api-python-client"):
            p.publish(PublishTarget(video_path=str(video), title="T"))


def test_youtube_publish_raises_when_no_creds():
    p = YouTubePublishProvider(credentials_path="")
    with patch.object(YouTubePublishProvider, "_google_libs_available", return_value=True):
        with pytest.raises(PublishNotAvailableError, match="credentials"):
            p.publish(PublishTarget(video_path="v.mp4", title="T"))


def test_youtube_publish_returns_failure_on_validation_error(tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text('{"type": "service_account"}', encoding="utf-8")
    p = YouTubePublishProvider(credentials_path=str(creds))

    with patch.object(YouTubePublishProvider, "_google_libs_available", return_value=True):
        # no video_path — should fail validation, not raise
        result = p.publish(PublishTarget(title="T"))
    assert result.success is False
    assert "video_path" in result.error


def test_youtube_publish_mocked_success(tmp_path):
    """Full upload flow with _do_upload mocked to return a successful result."""
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake video content")
    creds = tmp_path / "creds.json"
    creds.write_text('{"type": "service_account"}', encoding="utf-8")

    p = YouTubePublishProvider(credentials_path=str(creds))
    target = PublishTarget(
        video_path=str(video),
        title="My Great Video",
        caption="Description here",
        platform="youtube",
        privacy="public",
    )

    fake_result = PublishResult(
        success=True,
        provider="youtube",
        platform="youtube",
        post_id="abc123",
        post_url="https://www.youtube.com/watch?v=abc123",
        published_at="2026-05-01T18:00:00+00:00",
        response_summary="Uploaded successfully. Video ID: abc123",
    )

    with patch.object(YouTubePublishProvider, "_google_libs_available", return_value=True):
        with patch.object(YouTubePublishProvider, "_do_upload", return_value=fake_result):
            result = p.publish(target)

    assert result.success is True
    assert result.post_id == "abc123"
    assert "abc123" in result.post_url
    assert result.provider == "youtube"
    assert result.dry_run is False


def test_youtube_publish_mocked_exception(tmp_path):
    """Exceptions during upload are caught and returned as failed result."""
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    creds = tmp_path / "creds.json"
    creds.write_text('{"type": "service_account"}', encoding="utf-8")

    p = YouTubePublishProvider(credentials_path=str(creds))
    target = PublishTarget(video_path=str(video), title="T", platform="youtube")

    with patch.object(YouTubePublishProvider, "_google_libs_available", return_value=True):
        with patch.object(
            YouTubePublishProvider, "_do_upload",
            side_effect=RuntimeError("connection timeout")
        ):
            result = p.publish(target)

    assert result.success is False
    assert "connection timeout" in result.error


# ── PublishProviderFactory ────────────────────────────────────────────────────


def test_factory_youtube_platform():
    provider = PublishProviderFactory.for_platform("youtube")
    assert isinstance(provider, YouTubePublishProvider)


def test_factory_youtube_shorts_platform():
    provider = PublishProviderFactory.for_platform("youtube-shorts")
    assert isinstance(provider, YouTubePublishProvider)


def test_factory_reels_defaults_to_manual():
    provider = PublishProviderFactory.for_platform("reels")
    assert isinstance(provider, ManualPublishProvider)


def test_factory_tiktok_defaults_to_manual():
    provider = PublishProviderFactory.for_platform("tiktok")
    assert isinstance(provider, ManualPublishProvider)


def test_factory_unknown_platform_falls_back_to_manual():
    provider = PublishProviderFactory.for_platform("snapchat")
    assert isinstance(provider, ManualPublishProvider)


def test_factory_config_override():
    config = PublishConfig(platform_providers={"reels": "youtube"})
    provider = PublishProviderFactory.for_platform("reels", config)
    assert isinstance(provider, YouTubePublishProvider)


def test_factory_for_manifest():
    from clipforge.publish_manifest import PublishManifest
    m = PublishManifest(video_path="v.mp4", platform="tiktok")
    provider = PublishProviderFactory.for_manifest(m)
    assert isinstance(provider, ManualPublishProvider)


def test_factory_available_providers():
    providers = PublishProviderFactory.available_providers()
    assert "manual" in providers
    assert "youtube" in providers


def test_factory_is_real_provider():
    assert PublishProviderFactory.is_real_provider("youtube") is True
    assert PublishProviderFactory.is_real_provider("manual") is False


# ── PublishConfig ─────────────────────────────────────────────────────────────


def test_publish_config_defaults():
    c = PublishConfig()
    assert c.default_provider == "manual"
    assert c.dry_run_default is False
    assert c.youtube_credentials_path == ""


def test_publish_config_from_env(monkeypatch):
    monkeypatch.setenv("YOUTUBE_CREDENTIALS_PATH", "/tmp/creds.json")
    monkeypatch.setenv("CLIPFORGE_PUBLISH_DRY_RUN", "1")
    monkeypatch.setenv("CLIPFORGE_DEFAULT_PROVIDER", "youtube")
    c = PublishConfig.from_env()
    assert c.youtube_credentials_path == "/tmp/creds.json"
    assert c.dry_run_default is True
    assert c.default_provider == "youtube"


def test_publish_config_save_load(tmp_path):
    c = PublishConfig(
        default_provider="youtube",
        dry_run_default=True,
        youtube_credentials_path="/path/to/creds.json",
        platform_providers={"reels": "manual"},
    )
    p = tmp_path / "publish.json"
    c.save(p)
    c2 = PublishConfig.load(p)
    assert c2.default_provider == "youtube"
    assert c2.dry_run_default is True
    assert c2.youtube_credentials_path == "/path/to/creds.json"
    assert c2.platform_providers == {"reels": "manual"}


def test_publish_config_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PublishConfig.load(tmp_path / "no_such.json")


def test_publish_config_load_or_default_no_file():
    c = PublishConfig.load_or_default(None)
    assert isinstance(c, PublishConfig)
    assert c.default_provider == "manual"


def test_publish_config_is_provider_enabled():
    c = PublishConfig(youtube_credentials_path="/tmp/creds.json")
    assert c.is_provider_enabled("manual") is True
    assert c.is_provider_enabled("youtube") is True


def test_publish_config_youtube_not_enabled_without_creds():
    c = PublishConfig()
    assert c.is_provider_enabled("youtube") is False


def test_publish_config_repr():
    c = PublishConfig()
    r = repr(c)
    assert "manual" in r
