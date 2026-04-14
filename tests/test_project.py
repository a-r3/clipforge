"""Tests for clipforge.project — ClipForgeProject."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clipforge.project import ClipForgeProject


def test_project_importable():
    assert ClipForgeProject is not None


def test_project_init_creates_folder(tmp_path):
    project = ClipForgeProject.init(tmp_path / "myproject", name="MyProject")
    assert (tmp_path / "myproject").is_dir()


def test_project_init_creates_subdirs(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p")
    for subdir in ("scripts", "output", "assets/music", "assets/logo", "assets/downloads"):
        assert (project.path / subdir).is_dir(), f"Missing subdir: {subdir}"


def test_project_save_writes_json(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", name="SaveTest")
    project.save()
    meta = tmp_path / "p" / "project.json"
    assert meta.exists()
    data = json.loads(meta.read_text())
    assert data["name"] == "SaveTest"


def test_project_load_roundtrip(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", name="RoundTrip", platform="tiktok")
    project.save()
    loaded = ClipForgeProject.load(tmp_path / "p")
    assert loaded.name == "RoundTrip"
    assert loaded.platform == "tiktok"


def test_project_load_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ClipForgeProject.load(tmp_path / "nonexistent")


def test_project_load_missing_json_raises(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()
    with pytest.raises(FileNotFoundError):
        ClipForgeProject.load(folder)


def test_project_auto_style_reels(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", platform="reels")
    assert project.style == "bold"


def test_project_auto_style_youtube(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", platform="youtube")
    assert project.style == "clean"


def test_project_list_scripts_empty(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p")
    assert project.list_scripts() == []


def test_project_list_scripts_finds_txt(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p")
    project.save()
    (project.scripts_dir() / "ep1.txt").write_text("Hello world.", encoding="utf-8")
    (project.scripts_dir() / "ep2.txt").write_text("Hello again.", encoding="utf-8")
    scripts = project.list_scripts()
    assert len(scripts) == 2
    names = {s.name for s in scripts}
    assert "ep1.txt" in names
    assert "ep2.txt" in names


def test_project_build_config_uses_project_defaults(tmp_path):
    project = ClipForgeProject.init(
        tmp_path / "p", platform="tiktok", style="bold", brand_name="TestBrand"
    )
    project.save()
    config = project.build_config()
    assert config["platform"] == "tiktok"
    assert config["brand_name"] == "TestBrand"


def test_project_build_config_overrides_win(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", platform="reels")
    project.save()
    config = project.build_config(overrides={"platform": "youtube"})
    assert config["platform"] == "youtube"


def test_project_to_dict(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", name="DictTest")
    d = project.to_dict()
    assert d["name"] == "DictTest"
    assert "path" in d
    assert "platform" in d


def test_project_repr(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", name="ReprTest")
    r = repr(project)
    assert "ReprTest" in r


def test_project_brand_name_stored(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", brand_name="Acme")
    project.save()
    loaded = ClipForgeProject.load(tmp_path / "p")
    assert loaded.brand_name == "Acme"


# ── V4 — Publish / queue integration ─────────────────────────────────────────


def test_project_default_queue_field(tmp_path):
    project = ClipForgeProject(
        tmp_path / "p",
        default_queue="my_queue",
        default_campaign="spring2026",
    )
    assert project.default_queue == "my_queue"
    assert project.default_campaign == "spring2026"


def test_project_publish_fields_roundtrip(tmp_path):
    project = ClipForgeProject.init(
        tmp_path / "p",
        name="PubTest",
    )
    project.default_queue = "content_queue"
    project.default_campaign = "q2"
    project.default_publish_target = "instagram_main"
    project.manual_review_required = True
    project.save()

    loaded = ClipForgeProject.load(tmp_path / "p")
    assert loaded.default_queue == "content_queue"
    assert loaded.default_campaign == "q2"
    assert loaded.default_publish_target == "instagram_main"
    assert loaded.manual_review_required is True


def test_project_make_manifest_defaults(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", name="MkMfst", platform="tiktok")
    project.brand_name = "BrandX"
    project.default_campaign = "summer"
    project.default_queue = "main_queue"

    m = project.make_manifest(job_name="ep1", video_path="output/v.mp4")
    assert m.job_name == "ep1"
    assert m.project_name == "MkMfst"
    assert m.platform == "tiktok"
    assert m.brand_name == "BrandX"
    assert m.campaign_name == "summer"
    assert m.queue_name == "main_queue"
    assert m.status == "draft"


def test_project_make_manifest_overrides(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p", platform="reels")
    m = project.make_manifest(
        job_name="ep2",
        overrides={"platform": "youtube", "status": "ready"},
    )
    assert m.platform == "youtube"
    assert m.status == "ready"


def test_project_queue_dir(tmp_path):
    project = ClipForgeProject.init(tmp_path / "p")
    assert project.queue_dir() == project.path / "publish_queue"
