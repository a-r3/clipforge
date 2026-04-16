"""Tests for analytics collectors — MockAnalyticsCollector and YouTubeAnalyticsCollector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from clipforge.analytics.collector import MockAnalyticsCollector
from clipforge.analytics.models import ContentAnalytics

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_manifest(
    manifest_id="m-1",
    platform="youtube",
    job_name="test-job",
    campaign_name="Q1",
    template_ref="tmpl-1",
    profile_ref="",
    publish_at="2024-01-01T00:00:00+00:00",
    publish_attempts=None,
):
    m = MagicMock()
    m.manifest_id = manifest_id
    m.platform = platform
    m.job_name = job_name
    m.campaign_name = campaign_name
    m.template_ref = template_ref
    m.profile_ref = profile_ref
    m.publish_at = publish_at
    m.last_attempt.return_value = publish_attempts or {}
    return m


# ── MockAnalyticsCollector ────────────────────────────────────────────────────


def test_mock_collector_is_available():
    assert MockAnalyticsCollector().is_available() is True


def test_mock_collector_name():
    assert MockAnalyticsCollector().collector_name() == "mock"


def test_mock_collector_returns_content_analytics():
    collector = MockAnalyticsCollector(seed=42)
    m = _make_manifest()
    rec = collector.fetch(m)
    assert isinstance(rec, ContentAnalytics)
    assert rec.platform == "youtube"
    assert rec.manifest_id == "m-1"
    assert rec.data_source == "mock"


def test_mock_collector_deterministic_with_seed():
    m = _make_manifest()
    r1 = MockAnalyticsCollector(seed=99).fetch(m)
    r2 = MockAnalyticsCollector(seed=99).fetch(m)
    assert r1.views == r2.views
    assert r1.likes == r2.likes
    assert r1.ctr == r2.ctr


def test_mock_collector_different_seeds_differ():
    m = _make_manifest()
    r1 = MockAnalyticsCollector(seed=1).fetch(m)
    r2 = MockAnalyticsCollector(seed=2).fetch(m)
    # Very unlikely to produce identical values
    assert r1.views != r2.views or r1.likes != r2.likes


def test_mock_collector_overrides():
    m = _make_manifest()
    rec = MockAnalyticsCollector(seed=0, views=12345, likes=999).fetch(m)
    assert rec.views == 12345
    assert rec.likes == 999


def test_mock_collector_no_fetch_error():
    m = _make_manifest()
    rec = MockAnalyticsCollector().fetch(m)
    assert rec.fetch_error == ""


def test_mock_collector_engagement_rate_positive():
    m = _make_manifest()
    rec = MockAnalyticsCollector(seed=1).fetch(m)
    assert rec.engagement_rate >= 0


def test_mock_collector_provenance_from_manifest():
    m = _make_manifest(
        campaign_name="summer",
        template_ref="tmpl-x",
        publish_attempts={"post_id": "vid-abc", "post_url": "http://yt.com/v=vid-abc"},
    )
    rec = MockAnalyticsCollector(seed=7).fetch(m)
    assert rec.campaign_name == "summer"
    assert rec.template_ref == "tmpl-x"
    assert rec.post_id == "vid-abc"


# ── YouTubeAnalyticsCollector (mocked) ────────────────────────────────────────


def test_youtube_collector_is_available_false_when_no_creds():
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    collector = YouTubeAnalyticsCollector(credentials_path="")
    assert collector.is_available() is False


def test_youtube_collector_is_available_false_when_file_missing(tmp_path):
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    collector = YouTubeAnalyticsCollector(credentials_path=str(tmp_path / "missing.json"))
    assert collector.is_available() is False


def test_youtube_collector_stub_when_no_post_id():
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    m = _make_manifest(publish_attempts={})
    collector = YouTubeAnalyticsCollector(credentials_path="")
    rec = collector.fetch(m)
    assert rec.data_source == "stub"
    assert rec.fetch_error != ""


def test_youtube_collector_stub_when_unavailable():
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    m = _make_manifest(publish_attempts={"post_id": "vid-123"})
    collector = YouTubeAnalyticsCollector(credentials_path="")
    rec = collector.fetch(m)
    assert rec.data_source == "stub"
    assert "not available" in rec.fetch_error


def test_youtube_collector_stub_on_api_exception(tmp_path):
    """If _do_fetch raises any exception, fetch() returns a stub."""
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector

    creds_file = tmp_path / "creds.json"
    creds_file.write_text("{}", encoding="utf-8")

    m = _make_manifest(publish_attempts={"post_id": "vid-abc"})
    collector = YouTubeAnalyticsCollector(credentials_path=str(creds_file))

    with patch.object(collector, "is_available", return_value=True), \
         patch.object(collector, "_do_fetch", side_effect=RuntimeError("API error")):
        rec = collector.fetch(m)

    assert rec.data_source == "stub"
    assert "RuntimeError" in rec.fetch_error


def test_youtube_collector_do_fetch_maps_metrics(tmp_path):
    """_do_fetch correctly maps API response columns to ContentAnalytics fields."""
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector

    creds_file = tmp_path / "creds.json"
    creds_file.write_text("{}", encoding="utf-8")

    m = _make_manifest(
        publish_attempts={"post_id": "vid-xyz", "post_url": "https://yt.com/watch?v=vid-xyz"},
    )
    collector = YouTubeAnalyticsCollector(credentials_path=str(creds_file))

    mock_response = {
        "columnHeaders": [
            {"name": "video"},
            {"name": "views"},
            {"name": "likes"},
            {"name": "dislikes"},
            {"name": "comments"},
            {"name": "shares"},
            {"name": "estimatedMinutesWatched"},
            {"name": "averageViewDuration"},
            {"name": "averageViewPercentage"},
            {"name": "impressions"},
            {"name": "impressionsClickThroughRate"},
        ],
        "rows": [["vid-xyz", 5000, 200, 10, 50, 30, 12500, 150, 60.0, 8000, 3.5]],
    }

    mock_yt = MagicMock()
    mock_yt.reports.return_value.query.return_value.execute.return_value = mock_response

    with patch.object(collector, "_build_analytics_client", return_value=mock_yt):
        rec = collector._do_fetch(m, "vid-xyz", {"post_url": "https://yt.com/watch?v=vid-xyz"})

    assert rec.views == 5000
    assert rec.likes == 200
    assert rec.comments == 50
    assert rec.shares == 30
    assert rec.impressions == 8000
    assert rec.ctr == pytest.approx(3.5)
    assert rec.retention_pct == pytest.approx(60.0)
    assert rec.avg_view_duration_s == pytest.approx(150.0)
    assert rec.data_source == "api"


# ── Stub collectors ───────────────────────────────────────────────────────────


def test_tiktok_collector_is_available_false():
    from clipforge.analytics.providers.tiktok import TikTokAnalyticsCollector
    assert TikTokAnalyticsCollector().is_available() is False


def test_tiktok_collector_returns_stub():
    from clipforge.analytics.providers.tiktok import TikTokAnalyticsCollector
    m = _make_manifest(platform="tiktok")
    rec = TikTokAnalyticsCollector().fetch(m)
    assert rec.data_source == "stub"
    assert rec.fetch_error != ""


def test_reels_collector_is_available_false():
    from clipforge.analytics.providers.reels import ReelsAnalyticsCollector
    assert ReelsAnalyticsCollector().is_available() is False


def test_reels_collector_returns_stub():
    from clipforge.analytics.providers.reels import ReelsAnalyticsCollector
    m = _make_manifest(platform="reels")
    rec = ReelsAnalyticsCollector().fetch(m)
    assert rec.data_source == "stub"
    assert rec.fetch_error != ""


# ── Factory ───────────────────────────────────────────────────────────────────


def test_factory_youtube_platform():
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    c = AnalyticsCollectorFactory.for_platform("youtube")
    assert isinstance(c, YouTubeAnalyticsCollector)


def test_factory_youtube_shorts_platform():
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    c = AnalyticsCollectorFactory.for_platform("youtube-shorts")
    assert isinstance(c, YouTubeAnalyticsCollector)


def test_factory_tiktok_platform():
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.analytics.providers.tiktok import TikTokAnalyticsCollector
    c = AnalyticsCollectorFactory.for_platform("tiktok")
    assert isinstance(c, TikTokAnalyticsCollector)


def test_factory_reels_platform():
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.analytics.providers.reels import ReelsAnalyticsCollector
    c = AnalyticsCollectorFactory.for_platform("reels")
    assert isinstance(c, ReelsAnalyticsCollector)


def test_factory_unknown_platform_returns_mock():
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    c = AnalyticsCollectorFactory.for_platform("landscape")
    assert isinstance(c, MockAnalyticsCollector)


def test_factory_passes_credentials_to_youtube():
    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
    from clipforge.publish_config import PublishConfig

    config = PublishConfig(youtube_credentials_path="/tmp/creds.json")
    c = AnalyticsCollectorFactory.for_platform("youtube", config)
    assert isinstance(c, YouTubeAnalyticsCollector)
    assert c.credentials_path == "/tmp/creds.json"
