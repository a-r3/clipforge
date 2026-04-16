"""Publish manifest — structured record for a publishable content item.

A publish manifest captures everything needed to describe, validate, and
eventually publish a piece of content: paths, social metadata, scheduling,
and provenance (which profile/template was used).

Manifests are stored as JSON files.  They are human-readable and can be
edited by hand before adding to a queue.

Usage::

    from clipforge.publish_manifest import PublishManifest

    m = PublishManifest(
        job_name="episode-42",
        platform="reels",
        video_path="output/video.mp4",
        title="AI is changing everything",
        caption="Here's how AI will reshape your workflow...",
        hashtags="#AI #productivity #reels",
    )
    m.save("manifests/episode-42.json")

    # Load back
    m2 = PublishManifest.load("manifests/episode-42.json")
    errors = m2.validate()
    if errors:
        for e in errors:
            print("  !", e)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from datetime import timezone as _tz
from pathlib import Path
from typing import Any

# ── Valid values ──────────────────────────────────────────────────────────────

VALID_PLATFORMS = {"reels", "tiktok", "youtube-shorts", "youtube", "landscape"}

VALID_STATUSES = {
    "draft",
    "pending",
    "ready",
    "scheduled",
    "manual_action_required",
    "published",
    "failed",
    "archived",
}

VALID_PRIORITIES = {"low", "normal", "high"}


# ── Main class ────────────────────────────────────────────────────────────────


class PublishManifest:
    """A structured record describing a publishable content item.

    Fields are grouped into four areas:

    * **Identity** — manifest_id, job_name, project_name
    * **Content** — platform, video_path, thumbnail_path, script_path
    * **Social metadata** — title, caption, hashtags, cta, hook
    * **Scheduling** — publish_at, timezone, campaign_name, queue_name,
      priority, publish_target, manual_review_required, status
    * **Provenance** — profile_ref, template_ref, brand_name
    * **Housekeeping** — notes, created_at, updated_at, extra
    """

    def __init__(
        self,
        *,
        # Identity
        manifest_id: str = "",
        job_name: str = "",
        project_name: str = "",
        # Content
        platform: str = "reels",
        video_path: str = "",
        thumbnail_path: str = "",
        script_path: str = "",
        bundle_dir: str = "",
        # Social metadata
        title: str = "",
        caption: str = "",
        hashtags: str = "",
        cta: str = "",
        hook: str = "",
        title_variants: list[str] | None = None,
        caption_variants: list[str] | None = None,
        cta_variants: list[str] | None = None,
        # Scheduling
        publish_at: str = "",          # ISO-8601 UTC, empty = unscheduled
        timezone: str = "UTC",
        campaign_name: str = "",
        queue_name: str = "default",
        priority: str = "normal",
        publish_target: str = "",      # e.g. "instagram_main", "tiktok_brand"
        manual_review_required: bool = False,
        status: str = "draft",
        # Provenance
        profile_ref: str = "",         # profile JSON path or name
        template_ref: str = "",        # template name
        brand_name: str = "",
        # Housekeeping
        notes: str = "",
        created_at: str = "",
        updated_at: str = "",
        extra: dict[str, Any] | None = None,
        # V5 — publish attempt history
        publish_attempts: list[dict[str, Any]] | None = None,
    ) -> None:
        now = datetime.now(_tz.utc).isoformat()

        self.manifest_id = manifest_id or str(uuid.uuid4())
        self.job_name = job_name
        self.project_name = project_name

        self.platform = platform
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.script_path = script_path
        self.bundle_dir = bundle_dir

        self.title = title
        self.caption = caption
        self.hashtags = hashtags
        self.cta = cta
        self.hook = hook
        self.title_variants: list[str] = title_variants or []
        self.caption_variants: list[str] = caption_variants or []
        self.cta_variants: list[str] = cta_variants or []

        self.publish_at = publish_at
        self.timezone = timezone
        self.campaign_name = campaign_name
        self.queue_name = queue_name
        self.priority = priority
        self.publish_target = publish_target
        self.manual_review_required = manual_review_required
        self.status = status

        self.profile_ref = profile_ref
        self.template_ref = template_ref
        self.brand_name = brand_name

        self.notes = notes
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.extra: dict[str, Any] = extra or {}
        self.publish_attempts: list[dict[str, Any]] = publish_attempts or []

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict."""
        d: dict[str, Any] = {
            "manifest_id": self.manifest_id,
            "job_name": self.job_name,
            "project_name": self.project_name,
            "platform": self.platform,
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "script_path": self.script_path,
            "bundle_dir": self.bundle_dir,
            "title": self.title,
            "caption": self.caption,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "hook": self.hook,
            "title_variants": self.title_variants,
            "caption_variants": self.caption_variants,
            "cta_variants": self.cta_variants,
            "publish_at": self.publish_at,
            "timezone": self.timezone,
            "campaign_name": self.campaign_name,
            "queue_name": self.queue_name,
            "priority": self.priority,
            "publish_target": self.publish_target,
            "manual_review_required": self.manual_review_required,
            "status": self.status,
            "profile_ref": self.profile_ref,
            "template_ref": self.template_ref,
            "brand_name": self.brand_name,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "publish_attempts": self.publish_attempts,
        }
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublishManifest":
        """Create a ``PublishManifest`` from a plain dict."""
        known = {
            "manifest_id", "job_name", "project_name",
            "platform", "video_path", "thumbnail_path", "script_path", "bundle_dir",
            "title", "caption", "hashtags", "cta", "hook",
            "title_variants", "caption_variants", "cta_variants",
            "publish_at", "timezone", "campaign_name", "queue_name",
            "priority", "publish_target", "manual_review_required", "status",
            "profile_ref", "template_ref", "brand_name",
            "notes", "created_at", "updated_at", "publish_attempts",
        }
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            manifest_id=data.get("manifest_id", ""),
            job_name=data.get("job_name", ""),
            project_name=data.get("project_name", ""),
            platform=data.get("platform", "reels"),
            video_path=data.get("video_path", ""),
            thumbnail_path=data.get("thumbnail_path", ""),
            script_path=data.get("script_path", ""),
            bundle_dir=data.get("bundle_dir", ""),
            title=data.get("title", ""),
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", ""),
            cta=data.get("cta", ""),
            hook=data.get("hook", ""),
            title_variants=data.get("title_variants", []),
            caption_variants=data.get("caption_variants", []),
            cta_variants=data.get("cta_variants", []),
            publish_at=data.get("publish_at", ""),
            timezone=data.get("timezone", "UTC"),
            campaign_name=data.get("campaign_name", ""),
            queue_name=data.get("queue_name", "default"),
            priority=data.get("priority", "normal"),
            publish_target=data.get("publish_target", ""),
            manual_review_required=data.get("manual_review_required", False),
            status=data.get("status", "draft"),
            profile_ref=data.get("profile_ref", ""),
            template_ref=data.get("template_ref", ""),
            brand_name=data.get("brand_name", ""),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            extra=extra,
            publish_attempts=data.get("publish_attempts", []),
        )

    def save(self, path: str | Path) -> None:
        """Save manifest to a JSON file at *path*."""
        self.updated_at = datetime.now(_tz.utc).isoformat()
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "PublishManifest":
        """Load a manifest from a JSON file.

        Raises FileNotFoundError if the file does not exist.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """Return a list of human-readable error strings (empty = valid)."""
        errors: list[str] = []

        if not self.video_path:
            errors.append("video_path is required")

        if self.platform not in VALID_PLATFORMS:
            errors.append(
                f"platform '{self.platform}' is not valid "
                f"(expected one of: {', '.join(sorted(VALID_PLATFORMS))})"
            )

        if self.status not in VALID_STATUSES:
            errors.append(
                f"status '{self.status}' is not valid "
                f"(expected one of: {', '.join(sorted(VALID_STATUSES))})"
            )

        if self.priority not in VALID_PRIORITIES:
            errors.append(
                f"priority '{self.priority}' is not valid "
                f"(expected one of: {', '.join(sorted(VALID_PRIORITIES))})"
            )

        if self.publish_at:
            try:
                datetime.fromisoformat(self.publish_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append(
                    f"publish_at '{self.publish_at}' is not a valid ISO-8601 datetime"
                )

        return errors

    # ── Helpers ───────────────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        """Return True if this manifest is ready to be queued (no validation errors)."""
        return len(self.validate()) == 0

    def touch(self) -> None:
        """Update updated_at to now."""
        self.updated_at = datetime.now(_tz.utc).isoformat()

    def record_attempt(self, result: Any, attempted_at: str = "") -> None:
        """Append a publish attempt record (from a PublishResult or dict).

        Call this after every publish/dry-run attempt to keep history.
        Does NOT save the manifest — call ``manifest.save(path)`` separately.
        """
        if hasattr(result, "to_dict"):
            entry: dict[str, Any] = result.to_dict()
        else:
            entry = dict(result)
        entry["attempted_at"] = attempted_at or datetime.now(_tz.utc).isoformat()
        self.publish_attempts.append(entry)
        self.touch()

    def last_attempt(self) -> dict[str, Any] | None:
        """Return the most recent publish attempt record, or None."""
        return self.publish_attempts[-1] if self.publish_attempts else None

    def as_publish_target(self, extra: dict[str, Any] | None = None) -> Any:
        """Build a :class:`~clipforge.providers.publish.base.PublishTarget` from this manifest.

        Converts hashtags string to a tags list for providers that need it.
        """
        from clipforge.providers.publish.base import PublishTarget
        tags = [t.lstrip("#") for t in self.hashtags.split() if t.startswith("#")]
        kw: dict[str, Any] = {
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "caption": self.caption,
            "hashtags": self.hashtags,
            "title": self.title,
            "platform": self.platform,
            "tags": tags,
            "privacy": "public",
            "schedule_at": self.publish_at,
            "extra": {
                "job_name": self.job_name,
                "manifest_id": self.manifest_id,
                "cta": self.cta,
                "hook": self.hook,
                **(extra or {}),
            },
        }
        return PublishTarget(**kw)

    def __repr__(self) -> str:
        return (
            f"PublishManifest(job={self.job_name!r}, platform={self.platform!r}, "
            f"status={self.status!r})"
        )
