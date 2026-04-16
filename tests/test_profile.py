"""Tests for clipforge.profile — BrandProfile system."""

from __future__ import annotations

import pytest

from clipforge.profile import BrandProfile


def test_brand_profile_importable():
    assert BrandProfile is not None


def test_brand_profile_instantiates_with_defaults():
    p = BrandProfile()
    assert p.brand_name == ""
    assert p.platform == "reels"
    assert p.style == "clean"


def test_brand_profile_instantiates_with_values():
    p = BrandProfile(
        brand_name="TestCo",
        platform="tiktok",
        style="bold",
        audio_mode="voiceover",
    )
    assert p.brand_name == "TestCo"
    assert p.platform == "tiktok"
    assert p.style == "bold"
    assert p.audio_mode == "voiceover"


def test_to_dict_has_required_keys():
    p = BrandProfile(brand_name="X")
    d = p.to_dict()
    for key in ("brand_name", "platform", "style", "audio_mode", "text_mode",
                "watermark_opacity", "watermark_size", "ai_mode"):
        assert key in d, f"Missing key: {key}"


def test_from_dict_roundtrip():
    original = BrandProfile(
        brand_name="Roundtrip",
        platform="youtube",
        style="minimal",
        watermark_opacity=0.5,
        watermark_size=32,
    )
    d = original.to_dict()
    restored = BrandProfile.from_dict(d)
    assert restored.brand_name == "Roundtrip"
    assert restored.platform == "youtube"
    assert restored.style == "minimal"
    assert restored.watermark_opacity == 0.5
    assert restored.watermark_size == 32


def test_save_and_load(tmp_path):
    p = BrandProfile(brand_name="SaveLoad", platform="tiktok", style="bold")
    path = tmp_path / "profile.json"
    p.save(path)
    assert path.exists()
    loaded = BrandProfile.load(path)
    assert loaded.brand_name == "SaveLoad"
    assert loaded.platform == "tiktok"


def test_load_nonexistent_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        BrandProfile.load(tmp_path / "missing.json")


def test_apply_to_config_fills_missing():
    p = BrandProfile(
        brand_name="Brand",
        platform="reels",
        style="bold",
        audio_mode="voiceover",
    )
    config = {"platform": "reels"}
    result = p.apply_to_config(config)
    assert result["brand_name"] == "Brand"
    assert result["style"] == "bold"
    assert result["audio_mode"] == "voiceover"


def test_apply_to_config_does_not_override_existing():
    p = BrandProfile(brand_name="Brand", style="bold")
    config = {"brand_name": "UserBrand", "style": "minimal", "platform": "tiktok"}
    result = p.apply_to_config(config)
    # Explicitly set values must not be overridden
    assert result["brand_name"] == "UserBrand"
    assert result["style"] == "minimal"


def test_apply_to_config_platform_aware_defaults():
    p = BrandProfile(platform="youtube-shorts")
    config = {"platform": "youtube-shorts"}
    result = p.apply_to_config(config)
    assert result.get("fps") == 60


def test_profile_extra_fields_preserved():
    d = {"brand_name": "X", "custom_field": "hello"}
    p = BrandProfile.from_dict(d)
    assert p.extra.get("custom_field") == "hello"
    assert p.to_dict().get("custom_field") == "hello"


def test_repr_contains_brand_name():
    p = BrandProfile(brand_name="MyBrand")
    assert "MyBrand" in repr(p)
