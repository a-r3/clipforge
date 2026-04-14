"""AnalyticsCollectorFactory — select the right collector for a platform.

Usage::

    from clipforge.analytics.factory import AnalyticsCollectorFactory
    from clipforge.publish_config import PublishConfig

    config = PublishConfig.load_or_default("publish_config.json")
    collector = AnalyticsCollectorFactory.for_platform("youtube", config)
    record = collector.fetch(manifest)

Platform mapping (V6):
    youtube, youtube-shorts  →  YouTubeAnalyticsCollector  (real API if available)
    reels                    →  ReelsAnalyticsCollector     (stub only)
    tiktok                   →  TikTokAnalyticsCollector    (stub only)
    landscape, <anything>    →  MockAnalyticsCollector      (safe default)

If the real collector for a platform reports ``is_available() == False``,
the factory does NOT automatically fall back — it returns the stub collector
as-is.  The CLI / caller decides whether to attempt manual entry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from clipforge.analytics.collector import BaseAnalyticsCollector, MockAnalyticsCollector

if TYPE_CHECKING:
    from clipforge.publish_config import PublishConfig

# Platform → collector name
_DEFAULT_COLLECTORS: dict[str, str] = {
    "youtube": "youtube",
    "youtube-shorts": "youtube",
    "reels": "reels",
    "tiktok": "tiktok",
}


class AnalyticsCollectorFactory:
    """Create analytics collectors by platform name."""

    @staticmethod
    def for_platform(
        platform: str,
        config: "PublishConfig | None" = None,
    ) -> BaseAnalyticsCollector:
        """Return the appropriate collector for *platform*.

        Parameters
        ----------
        platform:
            Platform string, e.g. ``"youtube"``, ``"tiktok"``, ``"reels"``.
        config:
            Optional :class:`~clipforge.publish_config.PublishConfig`.
            Used to pass credentials to the YouTube collector.

        Returns
        -------
        A :class:`~clipforge.analytics.collector.BaseAnalyticsCollector`
        instance — never raises.
        """
        name = _DEFAULT_COLLECTORS.get(platform.lower(), "mock")
        return AnalyticsCollectorFactory._build(name, config)

    @staticmethod
    def _build(
        name: str,
        config: "PublishConfig | None",
    ) -> BaseAnalyticsCollector:
        if name == "youtube":
            from clipforge.analytics.providers.youtube import YouTubeAnalyticsCollector
            creds = (config.youtube_credentials_path if config else "") or ""
            return YouTubeAnalyticsCollector(credentials_path=creds)

        if name == "tiktok":
            from clipforge.analytics.providers.tiktok import TikTokAnalyticsCollector
            return TikTokAnalyticsCollector()

        if name == "reels":
            from clipforge.analytics.providers.reels import ReelsAnalyticsCollector
            return ReelsAnalyticsCollector()

        # Fallback: safe mock
        return MockAnalyticsCollector()

    @staticmethod
    def available_platforms() -> list[str]:
        """Return platforms that have a registered (possibly stub) collector."""
        return sorted(_DEFAULT_COLLECTORS.keys())
