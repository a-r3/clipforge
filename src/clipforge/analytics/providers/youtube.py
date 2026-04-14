"""YouTube Analytics collector.

Uses the YouTube Analytics API v2 (``youtubeAnalytics.reports.query``) to
fetch per-video metrics.  Requires the same google-api-python-client stack
as the YouTube publish provider, **plus** the additional scope
``https://www.googleapis.com/auth/yt-analytics.readonly``.

Credential requirements:
  The credentials file must have been authorised for both
  ``youtube.upload`` (publish) AND ``yt-analytics.readonly`` (analytics).
  Service accounts with Domain-Wide Delegation can cover both scopes.

Auth::

    export YOUTUBE_CREDENTIALS_PATH=/path/to/credentials.json

Fetch::

    collector = YouTubeAnalyticsCollector(credentials_path="creds.json")
    record = collector.fetch(manifest)

If ``google-api-python-client`` is not installed or credentials are missing,
``is_available()`` returns False and ``fetch()`` returns a stub record with
``fetch_error`` set — it never raises.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from clipforge.analytics.collector import BaseAnalyticsCollector
from clipforge.analytics.models import ContentAnalytics

if TYPE_CHECKING:
    from clipforge.publish_manifest import PublishManifest

_ENV_CREDS = "YOUTUBE_CREDENTIALS_PATH"
_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"


class YouTubeAnalyticsCollector(BaseAnalyticsCollector):
    """Fetch video analytics from the YouTube Analytics API v2.

    Parameters
    ----------
    credentials_path:
        Path to Google credentials JSON (service account or OAuth2 token).
        Falls back to ``YOUTUBE_CREDENTIALS_PATH`` env var.
    days_back:
        How many days of history to query (default 30).  YouTube Analytics
        reports aggregate over a date range; we use this to set end_date=today,
        start_date=today-days_back.
    """

    def __init__(
        self,
        credentials_path: str = "",
        days_back: int = 30,
    ) -> None:
        self.credentials_path = credentials_path or os.environ.get(_ENV_CREDS, "")
        self.days_back = days_back

    def is_available(self) -> bool:
        if not self._google_libs_available():
            return False
        return bool(self.credentials_path and Path(self.credentials_path).exists())

    def collector_name(self) -> str:
        return "youtube"

    def fetch(self, manifest: "PublishManifest") -> ContentAnalytics:
        """Fetch analytics for *manifest* from YouTube.

        Returns a ``ContentAnalytics`` record.  On any failure, returns a
        record with ``data_source='stub'`` and ``fetch_error`` set.
        """
        last = manifest.last_attempt() or {}
        post_id = last.get("post_id", "")

        if not post_id:
            return self._stub(manifest, "No post_id found in manifest publish attempts")

        if not self.is_available():
            reason = (
                "google-api-python-client not installed"
                if not self._google_libs_available()
                else "credentials not configured"
            )
            return self._stub(manifest, f"YouTubeAnalyticsCollector not available: {reason}")

        try:
            return self._do_fetch(manifest, post_id, last)
        except Exception as exc:
            return self._stub(manifest, f"{type(exc).__name__}: {exc}")

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _google_libs_available() -> bool:
        try:
            import googleapiclient  # noqa: F401
            import google.auth  # noqa: F401
            return True
        except ImportError:
            return False

    def _build_analytics_client(self) -> Any:
        from googleapiclient.discovery import build
        import json

        creds_data = json.loads(Path(self.credentials_path).read_text(encoding="utf-8"))

        if creds_data.get("type") == "service_account":
            from google.oauth2 import service_account
            scopes = [_ANALYTICS_SCOPE, _UPLOAD_SCOPE]
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
        elif "token" in creds_data:
            import google.oauth2.credentials
            creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
                self.credentials_path,
                scopes=[_ANALYTICS_SCOPE],
            )
        else:
            raise RuntimeError(
                f"Unsupported credentials format in: {self.credentials_path}"
            )

        return build("youtubeAnalytics", "v2", credentials=creds)

    def _do_fetch(
        self,
        manifest: "PublishManifest",
        post_id: str,
        last_attempt: dict[str, Any],
    ) -> ContentAnalytics:
        """Perform the actual YouTube Analytics API call."""
        yt_analytics = self._build_analytics_client()

        today = datetime.now(timezone.utc).date()
        start_date = (today - timedelta(days=self.days_back)).isoformat()
        end_date = today.isoformat()

        # Core metrics query
        response = (
            yt_analytics.reports()
            .query(
                ids=f"channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,likes,dislikes,comments,shares,estimatedMinutesWatched,"
                        "averageViewDuration,averageViewPercentage,annotationClickThroughRate,"
                        "impressions,impressionsClickThroughRate",
                dimensions="video",
                filters=f"video=={post_id}",
                maxResults=1,
            )
            .execute()
        )

        rows = response.get("rows", [])
        if not rows:
            return self._stub(manifest, f"No data returned for video {post_id}")

        # Column headers → index map
        headers = [h["name"] for h in response.get("columnHeaders", [])]

        def _get(name: str, default: Any = 0) -> Any:
            try:
                return rows[0][headers.index(name)]
            except (ValueError, IndexError):
                return default

        views = int(_get("views"))
        likes = int(_get("likes"))
        comments = int(_get("comments"))
        shares = int(_get("shares"))
        impressions = int(_get("impressions"))
        ctr = float(_get("impressionsClickThroughRate", 0.0))
        retention_pct = float(_get("averageViewPercentage", 0.0))
        avg_view_s = float(_get("averageViewDuration", 0.0))
        eng = round((likes + comments + shares) / max(1, views) * 100, 4)

        return ContentAnalytics(
            manifest_id=manifest.manifest_id,
            post_id=post_id,
            post_url=last_attempt.get("post_url", f"https://www.youtube.com/watch?v={post_id}"),
            platform=manifest.platform,
            published_at=last_attempt.get("published_at", manifest.publish_at),
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
            impressions=impressions,
            ctr=ctr,
            retention_pct=retention_pct,
            avg_view_duration_s=avg_view_s,
            engagement_rate=eng,
            job_name=manifest.job_name,
            campaign_name=manifest.campaign_name,
            template_ref=manifest.template_ref,
            profile_ref=manifest.profile_ref,
            data_source="api",
        )

    def _stub(self, manifest: "PublishManifest", error: str) -> ContentAnalytics:
        last = manifest.last_attempt() or {}
        return ContentAnalytics(
            manifest_id=manifest.manifest_id,
            post_id=last.get("post_id", ""),
            post_url=last.get("post_url", ""),
            platform=manifest.platform,
            published_at=last.get("published_at", manifest.publish_at),
            job_name=manifest.job_name,
            campaign_name=manifest.campaign_name,
            template_ref=manifest.template_ref,
            profile_ref=manifest.profile_ref,
            data_source="stub",
            fetch_error=error,
        )
