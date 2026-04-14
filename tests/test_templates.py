"""Tests for clipforge.templates — TemplateManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clipforge.templates import TemplateManager


@pytest.fixture
def tmp_templates(tmp_path) -> Path:
    """Create a small set of test templates in a temp directory."""
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    for name, platform, style in [
        ("biz", "reels", "bold"),
        ("edu", "youtube-shorts", "clean"),
    ]:
        data = {
            "name": name,
            "label": f"Label {name}",
            "description": f"Description for {name}",
            "platform": platform,
            "style": style,
            "audio_mode": "silent",
            "text_mode": "subtitle",
            "subtitle_mode": "static",
            "music_volume": 0.10,
            "max_scenes": 8,
            "outro_text": "Follow us",
            "sample_script": f"Sample script for {name}.",
        }
        (tpl_dir / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")
    return tpl_dir


def test_template_manager_importable():
    assert TemplateManager is not None


def test_list_templates_real():
    """TemplateManager should find the real data/templates/ directory."""
    mgr = TemplateManager()
    templates = mgr.list_templates()
    assert isinstance(templates, list)
    # We have 4 real templates
    assert len(templates) >= 4


def test_real_template_names():
    """All expected template names should be present."""
    mgr = TemplateManager()
    names = {t["name"] for t in mgr.list_templates()}
    for expected in ("business", "ai_content", "motivation", "educational"):
        assert expected in names, f"Missing template: {expected}"


def test_get_template_returns_dict():
    mgr = TemplateManager()
    t = mgr.get("business")
    assert isinstance(t, dict)
    assert t["name"] == "business"


def test_get_template_has_required_keys():
    mgr = TemplateManager()
    for name in ("business", "ai_content", "motivation", "educational"):
        t = mgr.get(name)
        for key in ("name", "label", "description", "platform", "style",
                    "audio_mode", "text_mode", "subtitle_mode"):
            assert key in t, f"Template '{name}' missing key '{key}'"


def test_get_nonexistent_raises_key_error():
    mgr = TemplateManager()
    with pytest.raises(KeyError):
        mgr.get("nonexistent_template_xyz")


def test_get_sample_script_nonempty():
    mgr = TemplateManager()
    for name in ("business", "ai_content", "motivation", "educational"):
        script = mgr.get_sample_script(name)
        assert isinstance(script, str)
        assert len(script.strip()) > 0, f"Template '{name}' has empty sample script"


def test_apply_to_config_fills_missing():
    mgr = TemplateManager()
    config = {}
    result = mgr.apply_to_config(config, "business")
    assert result["platform"] == "reels"
    assert result["style"] == "bold"
    assert result["audio_mode"] == "music"


def test_apply_to_config_does_not_override_existing():
    mgr = TemplateManager()
    config = {"platform": "youtube", "style": "minimal"}
    result = mgr.apply_to_config(config, "business")
    assert result["platform"] == "youtube"
    assert result["style"] == "minimal"


def test_list_templates_tmp(tmp_templates):
    mgr = TemplateManager(templates_dir=tmp_templates)
    templates = mgr.list_templates()
    assert len(templates) == 2
    names = {t["name"] for t in templates}
    assert "biz" in names
    assert "edu" in names


def test_get_template_tmp(tmp_templates):
    mgr = TemplateManager(templates_dir=tmp_templates)
    t = mgr.get("edu")
    assert t["platform"] == "youtube-shorts"
    assert t["style"] == "clean"


def test_sample_script_tmp(tmp_templates):
    mgr = TemplateManager(templates_dir=tmp_templates)
    script = mgr.get_sample_script("biz")
    assert "biz" in script


def test_empty_dir_returns_empty_list(tmp_path):
    empty = tmp_path / "empty_templates"
    empty.mkdir()
    mgr = TemplateManager(templates_dir=empty)
    assert mgr.list_templates() == []


def test_missing_dir_returns_empty_list(tmp_path):
    mgr = TemplateManager(templates_dir=tmp_path / "no_such_dir")
    assert mgr.list_templates() == []
