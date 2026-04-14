"""ContentAnalytics — data model for per-video performance metrics.

One ``ContentAnalytics`` record captures the metrics snapshot for a single
published video at a point in time.  Multiple snapshots can be stored for the
same manifest (one per fetch).

All numeric fields default to 0 / 0.0 so absent data doesn't cause errors.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_DATA_SOURCES = {"api", "mock", "manual", "stub"}


@dataclass
class ContentAnalytics:
    """Performance metrics snapshot for a single published video.

    Fields
    ------
    Identity
        ``analytics_id`` — UUID for this record.
        ``manifest_id`` — back-reference to the :class:`PublishManifest`.
        ``post_id`` — platform post / video ID.
        ``post_url`` — public URL to the post.
        ``platform`` — platform name (youtube, tiktok, reels, …).

    Timing
        ``fetched_at`` — ISO-8601 when these stats were fetched.
        ``published_at`` — ISO-8601 when the video was published.

    Core metrics
        ``views``, ``likes``, ``comments``, ``shares``, ``impressions``,
        ``reach`` — raw counts.

    Engagement derived
        ``ctr`` — click-through rate (%).
        ``retention_pct`` — average view duration as % of video length.
        ``avg_view_duration_s`` — average view duration in seconds.
        ``engagement_rate`` — (likes + comments + shares) / views * 100.

    Provenance
        ``job_name``, ``campaign_name``, ``template_ref``, ``profile_ref``
        — copied from the manifest for query convenience.

    Source tracking
        ``data_source`` — "api" | "mock" | "manual" | "stub".
        ``fetch_error`` — non-empty when the fetch partially failed.
        ``extra`` — arbitrary additional fields.
    """

    # Identity
    analytics_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    manifest_id: str = ""
    post_id: str = ""
    post_url: str = ""
    platform: str = ""

    # Timing
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: str = ""

    # Core metrics
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int = 0
    reach: int = 0

    # Engagement derived
    ctr: float = 0.0               # click-through rate %
    retention_pct: float = 0.0     # average retention %
    avg_view_duration_s: float = 0.0
    engagement_rate: float = 0.0   # (likes+comments+shares)/views * 100

    # Provenance (copied from manifest for convenience)
    job_name: str = ""
    campaign_name: str = ""
    template_ref: str = ""
    profile_ref: str = ""

    # Source tracking
    data_source: str = "api"       # "api" | "mock" | "manual" | "stub"
    fetch_error: str = ""

    extra: dict[str, Any] = field(default_factory=dict)

    # ── Computed helpers ──────────────────────────────────────────────────────

    def compute_engagement_rate(self) -> float:
        """Return (likes + comments + shares) / views * 100, or 0 if no views."""
        if self.views <= 0:
            return 0.0
        return round((self.likes + self.comments + self.shares) / self.views * 100, 4)

    def is_real(self) -> bool:
        """True if this record came from a real API call (not mock/stub)."""
        return self.data_source == "api"

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "analytics_id": self.analytics_id,
            "manifest_id": self.manifest_id,
            "post_id": self.post_id,
            "post_url": self.post_url,
            "platform": self.platform,
            "fetched_at": self.fetched_at,
            "published_at": self.published_at,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "impressions": self.impressions,
            "reach": self.reach,
            "ctr": self.ctr,
            "retention_pct": self.retention_pct,
            "avg_view_duration_s": self.avg_view_duration_s,
            "engagement_rate": self.engagement_rate,
            "job_name": self.job_name,
            "campaign_name": self.campaign_name,
            "template_ref": self.template_ref,
            "profile_ref": self.profile_ref,
            "data_source": self.data_source,
            "fetch_error": self.fetch_error,
        }
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentAnalytics":
        known = {
            "analytics_id", "manifest_id", "post_id", "post_url", "platform",
            "fetched_at", "published_at",
            "views", "likes", "comments", "shares", "impressions", "reach",
            "ctr", "retention_pct", "avg_view_duration_s", "engagement_rate",
            "job_name", "campaign_name", "template_ref", "profile_ref",
            "data_source", "fetch_error",
        }
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            analytics_id=data.get("analytics_id", str(uuid.uuid4())),
            manifest_id=data.get("manifest_id", ""),
            post_id=data.get("post_id", ""),
            post_url=data.get("post_url", ""),
            platform=data.get("platform", ""),
            fetched_at=data.get("fetched_at", ""),
            published_at=data.get("published_at", ""),
            views=data.get("views", 0),
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            shares=data.get("shares", 0),
            impressions=data.get("impressions", 0),
            reach=data.get("reach", 0),
            ctr=data.get("ctr", 0.0),
            retention_pct=data.get("retention_pct", 0.0),
            avg_view_duration_s=data.get("avg_view_duration_s", 0.0),
            engagement_rate=data.get("engagement_rate", 0.0),
            job_name=data.get("job_name", ""),
            campaign_name=data.get("campaign_name", ""),
            template_ref=data.get("template_ref", ""),
            profile_ref=data.get("profile_ref", ""),
            data_source=data.get("data_source", "api"),
            fetch_error=data.get("fetch_error", ""),
            extra=extra,
        )

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ContentAnalytics":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Analytics record not found: {path}")
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))

    def __repr__(self) -> str:
        return (
            f"ContentAnalytics(platform={self.platform!r}, views={self.views}, "
            f"likes={self.likes}, source={self.data_source!r})"
        )
