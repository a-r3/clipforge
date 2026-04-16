"""Abstract base class for social platform publish providers.

V5 extends this with explicit validate_target(), dry_run_publish(), and
a richer PublishResult (provider name, dry_run flag, published_at, etc.).

Existing subclasses that only implement ``publish()`` continue to work —
``validate_target()`` and ``dry_run_publish()`` have safe concrete defaults.

Future usage::

    class InstagramPublisher(PublishProvider):
        def publish(self, target): ...

    publisher = InstagramPublisher(api_key="...")
    errors = publisher.validate_target(target)
    result = publisher.dry_run_publish(target)   # no side-effects
    result = publisher.publish(target)           # real upload
    print(result.post_url)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PublishTarget:
    """Everything needed to publish a video to a platform."""

    video_path: str = ""
    thumbnail_path: str = ""
    caption: str = ""
    hashtags: str = ""
    title: str = ""
    platform: str = ""
    tags: list[str] = field(default_factory=list)   # structured tags (YouTube)
    privacy: str = "public"                          # public / unlisted / private
    schedule_at: str = ""     # ISO-8601 datetime, empty = publish immediately
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    """Result of a publish attempt (real or dry-run).

    All fields have defaults so existing code that constructs
    ``PublishResult(success=True, post_url="…")`` remains valid.
    """

    # Core outcome
    success: bool = False
    post_url: str = ""
    post_id: str = ""
    platform: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    # V5 extensions
    provider: str = ""                  # name of the provider that ran
    dry_run: bool = False               # True if this was a dry-run, not a real publish
    published_at: str = ""              # ISO-8601, set when success=True and not dry_run
    retry_count: int = 0
    response_summary: str = ""          # short human-readable summary of provider response
    manual_action_required: bool = False  # True when manual provider was used

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "success": self.success,
            "dry_run": self.dry_run,
            "post_url": self.post_url,
            "post_id": self.post_id,
            "platform": self.platform,
            "published_at": self.published_at,
            "error": self.error,
            "retry_count": self.retry_count,
            "response_summary": self.response_summary,
            "manual_action_required": self.manual_action_required,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PublishResult":
        return cls(
            provider=d.get("provider", ""),
            success=d.get("success", False),
            dry_run=d.get("dry_run", False),
            post_url=d.get("post_url", ""),
            post_id=d.get("post_id", ""),
            platform=d.get("platform", ""),
            published_at=d.get("published_at", ""),
            error=d.get("error", ""),
            retry_count=d.get("retry_count", 0),
            response_summary=d.get("response_summary", ""),
            manual_action_required=d.get("manual_action_required", False),
            metadata=d.get("metadata", {}),
        )


class PublishNotAvailableError(RuntimeError):
    """Raised when a provider is requested but not configured."""


class PublishProvider(ABC):
    """Abstract base class for social platform publish providers.

    Subclass this to add publishing to Instagram Reels, TikTok,
    YouTube Shorts, etc.

    Lifecycle methods (all concrete except publish):

    1. ``validate_target(target)`` — check metadata/files before attempting.
    2. ``dry_run_publish(target)`` — simulate publish without side-effects.
    3. ``publish(target)`` — perform the real upload (abstract).
    """

    def __init__(self, api_key: str = "", access_token: str = "") -> None:
        self.api_key = api_key
        self.access_token = access_token

    # ── Abstract ──────────────────────────────────────────────────────────────

    @abstractmethod
    def publish(self, target: PublishTarget) -> PublishResult:
        """Publish *target* to the platform.

        Returns a :class:`PublishResult` — always check ``.success``.
        Never return ``success=True`` unless the platform confirmed the upload.
        """

    # ── Concrete (safe defaults — override for richer behaviour) ──────────────

    def validate_target(self, target: PublishTarget) -> list[str]:
        """Return a list of human-readable validation errors (empty = OK).

        Called before ``dry_run_publish()`` and ``publish()``.
        Default implementation checks that ``video_path`` is set.
        Override to add platform-specific field constraints.
        """
        errors: list[str] = []
        if not target.video_path:
            errors.append("video_path is required")
        return errors

    def dry_run_publish(self, target: PublishTarget) -> PublishResult:
        """Simulate a publish without uploading anything.

        Returns a :class:`PublishResult` with ``dry_run=True``.
        Default: runs ``validate_target()`` and reports the outcome.
        Override to add richer provider-specific dry-run checks.
        """
        errors = self.validate_target(target)
        if errors:
            return PublishResult(
                success=False,
                dry_run=True,
                provider=type(self).__name__,
                platform=target.platform,
                error="; ".join(errors),
                response_summary=f"Dry-run failed: {len(errors)} validation error(s)",
            )
        return PublishResult(
            success=True,
            dry_run=True,
            provider=type(self).__name__,
            platform=target.platform,
            response_summary=(
                f"Dry-run OK — would publish '{target.title or target.video_path}' "
                f"to {target.platform} via {type(self).__name__}"
            ),
        )

    def is_available(self) -> bool:
        """Return True if this provider is configured and ready to publish."""
        return bool(self.api_key or self.access_token)

    def provider_name(self) -> str:
        """Short lowercase provider name used in result records."""
        return type(self).__name__.lower().replace("publishprovider", "").replace("provider", "")

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"{cls}(available={self.is_available()})"
