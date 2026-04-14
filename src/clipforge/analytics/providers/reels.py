"""Instagram Reels analytics collector — stub/manual.

Meta's Instagram Graph API provides analytics for Reels, but requires:
  - A Facebook Developer App
  - App Review approval for instagram_basic + instagram_content_publish scopes
  - A Professional / Creator account linked to a Facebook Page

These requirements are not met for automated third-party tools in V6.

This collector returns a stub with ``data_source='stub'`` and ``fetch_error``
explaining the limitation.  Use ``--manual`` mode to enter metrics by hand.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from clipforge.analytics.collector import BaseAnalyticsCollector
from clipforge.analytics.models import ContentAnalytics

if TYPE_CHECKING:
    from clipforge.publish_manifest import PublishManifest

_NOT_AVAILABLE_MSG = (
    "Instagram Reels analytics are not available via API in V6. "
    "Use 'clipforge analytics fetch --manual' to enter metrics by hand, "
    "or check Instagram Insights for performance data."
)


class ReelsAnalyticsCollector(BaseAnalyticsCollector):
    """Instagram Reels analytics — stub only."""

    def is_available(self) -> bool:
        return False  # API not supported in V6

    def collector_name(self) -> str:
        return "reels"

    def fetch(self, manifest: "PublishManifest") -> ContentAnalytics:
        last = manifest.last_attempt() or {}
        return ContentAnalytics(
            manifest_id=manifest.manifest_id,
            post_id=last.get("post_id", ""),
            post_url=last.get("post_url", ""),
            platform=manifest.platform,
            published_at=last.get("published_at", manifest.publish_at),
            job_name=manifest.job_name,
            campaign_name=manifest.campaign_name,
            data_source="stub",
            fetch_error=_NOT_AVAILABLE_MSG,
        )
