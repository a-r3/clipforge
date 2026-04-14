"""Platform-aware publish formatting rules.

Each supported platform has different constraints: title length, caption
length, hashtag limits, thumbnail requirements, and aspect ratios.

This module provides:

* ``PlatformRules`` — a dataclass of per-platform constraints
* ``PLATFORM_RULES`` — a dict mapping platform name → ``PlatformRules``
* ``validate_for_platform()`` — check a manifest against platform rules
* ``format_for_platform()`` — truncate/clean metadata to fit platform rules
* ``get_rules()`` — get rules with a clear error for unknown platforms

Usage::

    from clipforge.publish_format import get_rules, validate_for_platform

    rules = get_rules("reels")
    errors = validate_for_platform(manifest, "reels")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from clipforge.publish_manifest import PublishManifest


@dataclass
class PlatformRules:
    """Constraints and metadata for a publish platform."""

    name: str
    display_name: str

    # Text limits (characters)
    title_max: int = 0          # 0 = not applicable
    caption_max: int = 2200
    hashtag_max: int = 30
    hashtag_chars_max: int = 0  # 0 = unlimited

    # File requirements
    thumbnail_required: bool = False
    supports_thumbnail: bool = True
    video_max_duration_s: int = 0   # 0 = no limit checked here

    # Aspect ratio (width:height as floats)
    aspect_ratio: str = "9:16"
    aspect_ratio_float: float = 9 / 16

    # Publishing features
    supports_scheduling: bool = True
    supports_tags: bool = True          # @mentions
    supports_chapters: bool = False

    # Notes for users
    notes: str = ""

    # Extra platform-specific fields
    extra: dict[str, Any] = field(default_factory=dict)


# ── Platform rule definitions ─────────────────────────────────────────────────

PLATFORM_RULES: dict[str, PlatformRules] = {
    "reels": PlatformRules(
        name="reels",
        display_name="Instagram Reels",
        title_max=0,            # Reels don't have a title field
        caption_max=2200,
        hashtag_max=30,
        thumbnail_required=False,
        supports_thumbnail=True,
        video_max_duration_s=90,
        aspect_ratio="9:16",
        aspect_ratio_float=9 / 16,
        supports_scheduling=True,
        supports_tags=True,
        notes="Hashtags count against the 2200-char caption limit on Instagram.",
    ),
    "tiktok": PlatformRules(
        name="tiktok",
        display_name="TikTok",
        title_max=150,
        caption_max=2200,
        hashtag_max=0,          # No strict hashtag count limit, but keep ≤5 for reach
        hashtag_chars_max=300,  # Hashtags + caption combined ~300 chars recommended
        thumbnail_required=False,
        supports_thumbnail=True,
        video_max_duration_s=600,
        aspect_ratio="9:16",
        aspect_ratio_float=9 / 16,
        supports_scheduling=True,
        supports_tags=True,
        notes="Keep captions short; TikTok truncates after ~150 chars in feed.",
    ),
    "youtube-shorts": PlatformRules(
        name="youtube-shorts",
        display_name="YouTube Shorts",
        title_max=100,
        caption_max=5000,
        hashtag_max=15,
        thumbnail_required=False,  # Shorts can auto-select frame
        supports_thumbnail=True,
        video_max_duration_s=60,
        aspect_ratio="9:16",
        aspect_ratio_float=9 / 16,
        supports_scheduling=True,
        supports_tags=True,
        supports_chapters=False,
        notes="Add #Shorts in the title or description to surface as a Short.",
    ),
    "youtube": PlatformRules(
        name="youtube",
        display_name="YouTube",
        title_max=100,
        caption_max=5000,
        hashtag_max=15,
        thumbnail_required=True,
        supports_thumbnail=True,
        video_max_duration_s=0,     # No duration limit
        aspect_ratio="16:9",
        aspect_ratio_float=16 / 9,
        supports_scheduling=True,
        supports_tags=True,
        supports_chapters=True,
        notes="Custom thumbnail is strongly recommended for YouTube long-form.",
    ),
    "landscape": PlatformRules(
        name="landscape",
        display_name="Landscape / Custom",
        title_max=0,
        caption_max=0,
        hashtag_max=0,
        thumbnail_required=False,
        supports_thumbnail=True,
        video_max_duration_s=0,
        aspect_ratio="16:9",
        aspect_ratio_float=16 / 9,
        supports_scheduling=False,
        supports_tags=False,
        notes="Generic landscape format — no platform-specific constraints applied.",
    ),
}


# ── Public helpers ────────────────────────────────────────────────────────────


def get_rules(platform: str) -> PlatformRules:
    """Return ``PlatformRules`` for *platform*.

    Raises ValueError for unknown platform names.
    """
    rules = PLATFORM_RULES.get(platform)
    if rules is None:
        valid = ", ".join(sorted(PLATFORM_RULES))
        raise ValueError(
            f"Unknown platform '{platform}'. Valid platforms: {valid}"
        )
    return rules


def validate_for_platform(
    manifest: "PublishManifest",
    platform: str | None = None,
) -> list[str]:
    """Return a list of platform-constraint violations (empty = OK).

    Checks title length, caption length, hashtag count, and thumbnail
    requirement against the rules for *platform* (defaults to
    ``manifest.platform``).
    """
    plat = platform or manifest.platform
    try:
        rules = get_rules(plat)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []

    # Title length
    if rules.title_max and manifest.title:
        if len(manifest.title) > rules.title_max:
            errors.append(
                f"title is {len(manifest.title)} chars "
                f"(max {rules.title_max} for {rules.display_name})"
            )

    # Caption length
    if rules.caption_max and manifest.caption:
        if len(manifest.caption) > rules.caption_max:
            errors.append(
                f"caption is {len(manifest.caption)} chars "
                f"(max {rules.caption_max} for {rules.display_name})"
            )

    # Hashtag count
    if rules.hashtag_max and manifest.hashtags:
        tags = [t for t in manifest.hashtags.split() if t.startswith("#")]
        if len(tags) > rules.hashtag_max:
            errors.append(
                f"hashtag count is {len(tags)} "
                f"(max {rules.hashtag_max} for {rules.display_name})"
            )

    # Thumbnail requirement
    if rules.thumbnail_required and not manifest.thumbnail_path:
        errors.append(
            f"thumbnail_path is required for {rules.display_name}"
        )

    return errors


def format_for_platform(
    manifest: "PublishManifest",
    platform: str | None = None,
    truncate: bool = True,
) -> dict[str, str]:
    """Return a dict of formatted fields ready for the platform.

    If *truncate* is True, title and caption are hard-truncated to the
    platform maximums (with an ellipsis appended).  Hashtags are trimmed
    to the allowed count.

    Returns a plain dict — does NOT modify the manifest in place.
    """
    plat = platform or manifest.platform
    rules = PLATFORM_RULES.get(plat, PLATFORM_RULES["landscape"])

    title = manifest.title
    caption = manifest.caption
    hashtags = manifest.hashtags

    if truncate:
        if rules.title_max and len(title) > rules.title_max:
            title = title[: rules.title_max - 1] + "…"
        if rules.caption_max and len(caption) > rules.caption_max:
            caption = caption[: rules.caption_max - 1] + "…"
        if rules.hashtag_max and hashtags:
            tags = [t for t in hashtags.split() if t.startswith("#")]
            if len(tags) > rules.hashtag_max:
                tags = tags[: rules.hashtag_max]
                hashtags = " ".join(tags)

    return {
        "platform": rules.display_name,
        "title": title,
        "caption": caption,
        "hashtags": hashtags,
        "cta": manifest.cta,
        "hook": manifest.hook,
        "aspect_ratio": rules.aspect_ratio,
        "thumbnail_required": str(rules.thumbnail_required).lower(),
    }
