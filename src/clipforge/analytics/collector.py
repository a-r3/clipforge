"""Analytics collector — abstract base and mock implementation.

Usage::

    from clipforge.analytics.collector import MockAnalyticsCollector

    collector = MockAnalyticsCollector()
    record = collector.fetch(manifest)
    print(record.views)

All collectors share the same interface: ``fetch(manifest) -> ContentAnalytics``.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from clipforge.analytics.models import ContentAnalytics

if TYPE_CHECKING:
    from clipforge.publish_manifest import PublishManifest


class BaseAnalyticsCollector(ABC):
    """Abstract base for analytics collectors.

    Implementations must override ``fetch()``.
    ``is_available()`` should return False when the provider is not configured
    (missing credentials, library not installed, etc.).
    """

    @abstractmethod
    def fetch(self, manifest: "PublishManifest") -> ContentAnalytics:
        """Fetch current analytics for the given manifest's published post.

        Must return a :class:`ContentAnalytics` record even on failure —
        set ``fetch_error`` and leave metrics at 0.
        """

    def is_available(self) -> bool:
        """Return True if this collector is configured and ready to fetch."""
        return True

    def collector_name(self) -> str:
        return type(self).__name__.lower().replace("analyticscollector", "").replace("collector", "")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(available={self.is_available()})"


class MockAnalyticsCollector(BaseAnalyticsCollector):
    """Mock analytics collector for testing and CI.

    Returns deterministic or randomly seeded fake metrics.
    Never makes real API calls.

    Parameters
    ----------
    seed:
        Integer seed for reproducible randomness.  None = random each time.
    views, likes, …:
        Override specific metric values (useful in tests).
    """

    def __init__(
        self,
        seed: int | None = None,
        views: int | None = None,
        likes: int | None = None,
        comments: int | None = None,
        shares: int | None = None,
        impressions: int | None = None,
        reach: int | None = None,
        ctr: float | None = None,
        retention_pct: float | None = None,
    ) -> None:
        self._seed = seed
        self._overrides: dict[str, Any] = {}
        if views is not None:
            self._overrides["views"] = views
        if likes is not None:
            self._overrides["likes"] = likes
        if comments is not None:
            self._overrides["comments"] = comments
        if shares is not None:
            self._overrides["shares"] = shares
        if impressions is not None:
            self._overrides["impressions"] = impressions
        if reach is not None:
            self._overrides["reach"] = reach
        if ctr is not None:
            self._overrides["ctr"] = ctr
        if retention_pct is not None:
            self._overrides["retention_pct"] = retention_pct

    def collector_name(self) -> str:
        return "mock"

    def fetch(self, manifest: "PublishManifest") -> ContentAnalytics:
        """Return mock analytics for *manifest*."""
        rng = random.Random(self._seed)

        views = self._overrides.get("views", rng.randint(500, 50_000))
        likes = self._overrides.get("likes", rng.randint(10, max(11, views // 20)))
        comments = self._overrides.get("comments", rng.randint(0, max(1, views // 100)))
        shares = self._overrides.get("shares", rng.randint(0, max(1, views // 50)))
        impressions = self._overrides.get("impressions", int(views * rng.uniform(1.2, 3.0)))
        reach = self._overrides.get("reach", int(impressions * rng.uniform(0.5, 0.9)))
        ctr = self._overrides.get("ctr", round(views / max(1, impressions) * 100, 2))
        retention_pct = self._overrides.get("retention_pct", round(rng.uniform(20.0, 75.0), 1))
        avg_view_s = round(retention_pct / 100 * rng.uniform(30, 120), 1)
        eng = round((likes + comments + shares) / max(1, views) * 100, 4)

        # Pull provenance from manifest
        last = manifest.last_attempt() or {}

        return ContentAnalytics(
            manifest_id=manifest.manifest_id,
            post_id=last.get("post_id", "mock-post-id"),
            post_url=last.get("post_url", ""),
            platform=manifest.platform,
            published_at=last.get("published_at", manifest.publish_at),
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
            impressions=impressions,
            reach=reach,
            ctr=ctr,
            retention_pct=retention_pct,
            avg_view_duration_s=avg_view_s,
            engagement_rate=eng,
            job_name=manifest.job_name,
            campaign_name=manifest.campaign_name,
            template_ref=manifest.template_ref,
            profile_ref=manifest.profile_ref,
            data_source="mock",
        )
