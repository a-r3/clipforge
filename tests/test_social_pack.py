"""Tests for the social pack generator module."""

from __future__ import annotations

from clipforge.social_pack import SocialPackGenerator, generate_social_pack


SAMPLE_SCRIPT = (
    "Artificial intelligence is transforming how businesses operate today.\n\n"
    "Companies that adopt AI technology gain significant competitive advantages."
)

SAMPLE_SCENES = [
    {
        "index": 0,
        "text": "Artificial intelligence is transforming how businesses operate today.",
        "estimated_duration": 5.0,
        "keywords": ["artificial", "intelligence", "businesses"],
        "visual_intent": "technology",
    },
    {
        "index": 1,
        "text": "Companies that adopt AI technology gain significant competitive advantages.",
        "estimated_duration": 5.0,
        "keywords": ["companies", "technology", "competitive"],
        "visual_intent": "business",
    },
]


def _make_config(platform: str = "reels", brand: str = "TestBrand") -> dict:
    return {"platform": platform, "brand_name": brand}


def test_social_pack_importable():
    """SocialPackGenerator and generate_social_pack must be importable."""
    assert SocialPackGenerator is not None
    assert callable(generate_social_pack)


def test_generator_instantiates():
    """SocialPackGenerator instantiates without arguments."""
    gen = SocialPackGenerator()
    assert gen is not None


def test_generate_returns_dict():
    """generate() must return a dict."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    assert isinstance(result, dict)


def test_generate_has_required_keys():
    """Social pack must contain all required keys."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    for key in ("title", "caption", "hook", "cta", "hashtags"):
        assert key in result, f"Missing key: {key}"


def test_generate_non_empty_values():
    """All social pack fields must be non-empty strings."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    for key in ("title", "caption", "hook", "cta", "hashtags"):
        assert isinstance(result[key], str), f"{key} is not a string"
        assert len(result[key].strip()) > 0, f"{key} is empty"


def test_brand_name_appears_in_title():
    """Brand name should appear somewhere in the title."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config(brand="Azerbite"))
    assert "Azerbite" in result["title"]


def test_different_platforms_produce_different_hashtags():
    """Hashtags should differ between reels and tiktok."""
    gen = SocialPackGenerator()
    reels = gen.generate(SAMPLE_SCENES, _make_config(platform="reels"))
    tiktok = gen.generate(SAMPLE_SCENES, _make_config(platform="tiktok"))
    assert reels["hashtags"] != tiktok["hashtags"]


def test_generate_social_pack_convenience_function():
    """Module-level convenience function must return same shape."""
    result = generate_social_pack(SAMPLE_SCRIPT, platform="youtube-shorts", brand_name="Brand")
    assert isinstance(result, dict)
    assert "title" in result
    assert "hashtags" in result


def test_generate_empty_scenes():
    """Empty scenes list should still produce a pack (with defaults)."""
    gen = SocialPackGenerator()
    result = gen.generate([], _make_config())
    assert isinstance(result, dict)
    assert "title" in result


def test_tiktok_platform_hashtags():
    """TikTok platform should include tiktok-specific hashtags."""
    result = generate_social_pack(SAMPLE_SCRIPT, platform="tiktok", brand_name="Brand")
    assert "tiktok" in result["hashtags"].lower()


def test_hashtags_are_short_and_clean():
    """No single hashtag should exceed 25 characters (no slug-monsters)."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    tags = result["hashtags"].split()
    for tag in tags:
        assert len(tag) <= 25, f"Hashtag too long: {tag!r}"


def test_hashtags_max_eight():
    """Result should contain at most 8 hashtags."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    tags = result["hashtags"].split()
    assert len(tags) <= 8, f"Too many hashtags: {len(tags)}"


def test_hashtags_all_start_with_hash():
    """Every hashtag must start with #."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    for tag in result["hashtags"].split():
        assert tag.startswith("#"), f"Not a hashtag: {tag!r}"


def test_save_json(tmp_path):
    """generate_social_pack result can be saved as JSON via save_json."""
    from clipforge.utils import save_json, load_json
    result = generate_social_pack(SAMPLE_SCRIPT, platform="reels", brand_name="Brand")
    out = tmp_path / "pack.json"
    save_json(result, out)
    loaded = load_json(out)
    assert loaded["title"] == result["title"]
    assert loaded["hashtags"] == result["hashtags"]


def test_save_txt(tmp_path):
    """The TXT writer used by social-pack command produces a non-empty text file."""
    from clipforge.commands.social_pack import _write_txt
    pack = generate_social_pack(SAMPLE_SCRIPT, platform="reels", brand_name="Brand")
    out = tmp_path / "pack.txt"
    _write_txt(pack, str(out))
    text = out.read_text(encoding="utf-8")
    assert "TITLE" in text
    assert "HASHTAGS" in text
    assert pack["hashtags"] in text


# ---------------------------------------------------------------------------
# V2 variant tests
# ---------------------------------------------------------------------------


def test_generate_has_title_variants():
    """V2: generate() should include title_variants list."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config(brand="Brand"))
    assert "title_variants" in result
    assert isinstance(result["title_variants"], list)
    assert len(result["title_variants"]) >= 1


def test_generate_has_hook_variants():
    """V2: generate() should include hook_variants list."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    assert "hook_variants" in result
    assert isinstance(result["hook_variants"], list)
    assert len(result["hook_variants"]) >= 1


def test_generate_has_cta_variants():
    """V2: generate() should include cta_variants list."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    assert "cta_variants" in result
    assert isinstance(result["cta_variants"], list)
    assert len(result["cta_variants"]) >= 1


def test_title_is_first_title_variant():
    """V2: title field should be the first item in title_variants (backward compat)."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config(brand="Compat"))
    assert result["title"] == result["title_variants"][0]


def test_title_variants_contain_brand():
    """V2: at least one title variant should contain the brand name."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config(brand="UniqueBrand"))
    any_has_brand = any("UniqueBrand" in t for t in result["title_variants"])
    assert any_has_brand


def test_hook_variants_are_strings():
    """V2: all hook variants should be non-empty strings."""
    gen = SocialPackGenerator()
    result = gen.generate(SAMPLE_SCENES, _make_config())
    for h in result["hook_variants"]:
        assert isinstance(h, str) and len(h.strip()) > 0
