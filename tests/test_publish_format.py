"""Tests for clipforge.publish_format — platform rules and validation."""

from __future__ import annotations

import pytest

from clipforge.publish_format import (
    PlatformRules,
    format_for_platform,
    get_rules,
    validate_for_platform,
)
from clipforge.publish_manifest import PublishManifest

# ── get_rules ─────────────────────────────────────────────────────────────────


def test_get_rules_reels():
    r = get_rules("reels")
    assert isinstance(r, PlatformRules)
    assert r.name == "reels"
    assert r.aspect_ratio == "9:16"


def test_get_rules_youtube():
    r = get_rules("youtube")
    assert r.thumbnail_required is True
    assert r.aspect_ratio == "16:9"


def test_get_rules_unknown_raises():
    with pytest.raises(ValueError, match="Unknown platform"):
        get_rules("snapchat")


def test_all_platforms_have_rules():
    for plat in ("reels", "tiktok", "youtube-shorts", "youtube", "landscape"):
        r = get_rules(plat)
        assert r.name == plat


# ── validate_for_platform ─────────────────────────────────────────────────────


def test_validate_clean_manifest():
    m = PublishManifest(video_path="v.mp4", platform="reels", title="Short")
    errors = validate_for_platform(m)
    assert errors == []


def test_validate_title_too_long_tiktok():
    long_title = "A" * 160  # TikTok max is 150
    m = PublishManifest(video_path="v.mp4", platform="tiktok", title=long_title)
    errors = validate_for_platform(m)
    assert any("title" in e for e in errors)


def test_validate_title_ok_youtube_shorts():
    m = PublishManifest(video_path="v.mp4", platform="youtube-shorts", title="A" * 100)
    errors = validate_for_platform(m)
    assert errors == []


def test_validate_title_too_long_youtube_shorts():
    m = PublishManifest(video_path="v.mp4", platform="youtube-shorts", title="A" * 101)
    errors = validate_for_platform(m)
    assert any("title" in e for e in errors)


def test_validate_caption_too_long_reels():
    m = PublishManifest(
        video_path="v.mp4",
        platform="reels",
        caption="X" * 2201,
    )
    errors = validate_for_platform(m)
    assert any("caption" in e for e in errors)


def test_validate_caption_ok_reels():
    m = PublishManifest(video_path="v.mp4", platform="reels", caption="X" * 100)
    errors = validate_for_platform(m)
    assert errors == []


def test_validate_too_many_hashtags_reels():
    # reels max is 30
    tags = " ".join(f"#tag{i}" for i in range(35))
    m = PublishManifest(video_path="v.mp4", platform="reels", hashtags=tags)
    errors = validate_for_platform(m)
    assert any("hashtag" in e for e in errors)


def test_validate_hashtag_count_ok():
    tags = " ".join(f"#tag{i}" for i in range(10))
    m = PublishManifest(video_path="v.mp4", platform="reels", hashtags=tags)
    errors = validate_for_platform(m)
    assert errors == []


def test_validate_youtube_thumbnail_required():
    m = PublishManifest(video_path="v.mp4", platform="youtube", thumbnail_path="")
    errors = validate_for_platform(m)
    assert any("thumbnail" in e for e in errors)


def test_validate_youtube_thumbnail_present():
    m = PublishManifest(video_path="v.mp4", platform="youtube", thumbnail_path="thumb.jpg")
    errors = validate_for_platform(m)
    assert errors == []


def test_validate_platform_override():
    # Manifest says reels, but validate as youtube (which requires thumbnail)
    m = PublishManifest(video_path="v.mp4", platform="reels", thumbnail_path="")
    errors = validate_for_platform(m, platform="youtube")
    assert any("thumbnail" in e for e in errors)


def test_validate_unknown_platform():
    m = PublishManifest(video_path="v.mp4")
    errors = validate_for_platform(m, platform="snapchat")
    assert any("Unknown platform" in e for e in errors)


# ── format_for_platform ───────────────────────────────────────────────────────


def test_format_returns_dict():
    m = PublishManifest(video_path="v.mp4", platform="reels", title="Hello")
    result = format_for_platform(m)
    assert isinstance(result, dict)
    assert "title" in result
    assert "caption" in result
    assert "hashtags" in result


def test_format_truncates_title():
    long_title = "A" * 200
    m = PublishManifest(video_path="v.mp4", platform="tiktok", title=long_title)
    result = format_for_platform(m, truncate=True)
    assert len(result["title"]) <= 150
    assert result["title"].endswith("…")


def test_format_no_truncate():
    long_title = "A" * 200
    m = PublishManifest(video_path="v.mp4", platform="tiktok", title=long_title)
    result = format_for_platform(m, truncate=False)
    assert len(result["title"]) == 200


def test_format_truncates_hashtags():
    tags = " ".join(f"#tag{i}" for i in range(50))
    m = PublishManifest(video_path="v.mp4", platform="reels", hashtags=tags)
    result = format_for_platform(m, truncate=True)
    result_tags = [t for t in result["hashtags"].split() if t.startswith("#")]
    assert len(result_tags) <= 30


def test_format_includes_aspect_ratio():
    m = PublishManifest(video_path="v.mp4", platform="youtube")
    result = format_for_platform(m)
    assert result["aspect_ratio"] == "16:9"


def test_format_landscape_no_truncation():
    # landscape has no limits (max=0)
    m = PublishManifest(video_path="v.mp4", platform="landscape", title="A" * 500)
    result = format_for_platform(m, truncate=True)
    assert len(result["title"]) == 500  # no truncation for landscape


def test_format_platform_override():
    m = PublishManifest(video_path="v.mp4", platform="reels")
    result = format_for_platform(m, platform="youtube")
    assert result["aspect_ratio"] == "16:9"
