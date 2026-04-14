"""TikTok analytics collector — stub/manual.

TikTok's Content Posting API and Business API require special app review
and are not publicly available for third-party automation in V6.

This collector returns a stub record with ``data_source='stub'`` and
``fetch_error`` explaining that manual analytics entry is required.

Manual entry workflow::

    clipforge analytics fetch manifest.json --manual
    # Opens a prompt to enter metrics by hand

Future versions (V7+) will add real TikTok analytics once API access is stable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from clipforge.analytics.collector import BaseAnalyticsCollector
from clipforge.analytics.models import ContentAnalytics

if TYPE_CHECKING:
    from clipforge.publish_manifest import PublishManifest

_NOT_AVAILABLE_MSG = (
    "TikTok analytics are not available via API in V6. "
    "Use 'clipforge analytics fetch --manual' to enter metrics by hand, "
    "or check TikTok Creator Center for performance data."
)


class TikTokAnalyticsCollector(BaseAnalyticsCollector):
    """TikTok analytics — stub only.  Returns a manual-entry placeholder."""

    def is_available(self) -> bool:
        return False  # API not supported in V6

    def collector_name(self) -> str:
        return "tiktok"

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
