"""Tests for clipforge.utils module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clipforge.utils import (
    slugify,
    ensure_dir,
    merge_dicts,
    clamp,
    format_duration,
    estimate_read_time,
    load_json,
    save_json,
    get_platform_spec,
    extract_keywords,
)


class TestSlugify:
    def test_basic_lowercase(self):
        assert slugify("Hello World") == "hello-world"

    def test_removes_special_chars(self):
        assert slugify("How AI Changes Business!") == "how-ai-changes-business"

    def test_handles_multiple_spaces(self):
        assert slugify("foo  bar") == "foo-bar"

    def test_strips_leading_trailing_hyphens(self):
        assert slugify("  hello  ") == "hello"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_numbers(self):
        result = slugify("Top 10 Tips")
        assert result == "top-10-tips"


class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        new_dir = tmp_path / "subdir" / "nested"
        result = ensure_dir(new_dir)
        assert result.is_dir()
        assert result == new_dir

    def test_existing_directory_ok(self, tmp_path):
        result = ensure_dir(tmp_path)
        assert result == tmp_path

    def test_accepts_string(self, tmp_path):
        new_dir = str(tmp_path / "stringtest")
        result = ensure_dir(new_dir)
        assert result.is_dir()


class TestMergeDicts:
    def test_override_values(self):
        result = merge_dicts({"a": 1, "b": 2}, {"b": 99})
        assert result == {"a": 1, "b": 99}

    def test_deep_merge(self):
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": {"y": 99, "z": 3}}
        result = merge_dicts(base, override)
        assert result == {"a": {"x": 1, "y": 99, "z": 3}}

    def test_empty_override(self):
        base = {"a": 1}
        result = merge_dicts(base, {})
        assert result == {"a": 1}

    def test_empty_base(self):
        result = merge_dicts({}, {"a": 1})
        assert result == {"a": 1}

    def test_does_not_mutate_base(self):
        base = {"a": 1}
        merge_dicts(base, {"a": 2})
        assert base["a"] == 1


class TestClamp:
    def test_within_range(self):
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_below_min(self):
        assert clamp(-1.0, 0.0, 10.0) == 0.0

    def test_above_max(self):
        assert clamp(15.0, 0.0, 10.0) == 10.0

    def test_at_boundaries(self):
        assert clamp(0.0, 0.0, 10.0) == 0.0
        assert clamp(10.0, 0.0, 10.0) == 10.0


class TestFormatDuration:
    def test_seconds_only(self):
        assert format_duration(45) == "0:45"

    def test_minutes_and_seconds(self):
        assert format_duration(75) == "1:15"

    def test_zero(self):
        assert format_duration(0) == "0:00"

    def test_one_hour(self):
        assert format_duration(3600) == "60:00"

    def test_float_truncates(self):
        assert format_duration(45.9) == "0:45"


class TestEstimateReadTime:
    def test_short_text(self):
        result = estimate_read_time("Hello world")
        assert result >= 1.0

    def test_empty_text(self):
        result = estimate_read_time("")
        assert result == 1.0

    def test_longer_text_takes_longer(self):
        short = estimate_read_time("Hello world")
        long = estimate_read_time(" ".join(["word"] * 130))
        assert long > short

    def test_wpm_parameter(self):
        text = " ".join(["word"] * 130)
        slow = estimate_read_time(text, wpm=65)
        fast = estimate_read_time(text, wpm=260)
        assert slow > fast

    def test_minimum_one_second(self):
        assert estimate_read_time("Hi") == 1.0


class TestLoadJson:
    def test_loads_valid_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = load_json(f)
        assert result == {"key": "value"}

    def test_returns_empty_dict_for_missing_file(self, tmp_path):
        result = load_json(tmp_path / "nonexistent.json")
        assert result == {}

    def test_returns_empty_dict_for_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json", encoding="utf-8")
        result = load_json(f)
        assert result == {}

    def test_accepts_string_path(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"x": 1}', encoding="utf-8")
        result = load_json(str(f))
        assert result == {"x": 1}


class TestSaveJson:
    def test_saves_json_file(self, tmp_path):
        data = {"hello": "world", "count": 42}
        out = tmp_path / "output.json"
        save_json(data, out)
        loaded = json.loads(out.read_text())
        assert loaded == data

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "dir" / "file.json"
        save_json({"a": 1}, out)
        assert out.exists()


class TestGetPlatformSpec:
    def test_reels(self):
        spec = get_platform_spec("reels")
        assert spec["width"] == 1080
        assert spec["height"] == 1920

    def test_youtube(self):
        spec = get_platform_spec("youtube")
        assert spec["width"] == 1920
        assert spec["height"] == 1080

    def test_unknown_platform_falls_back_to_reels(self):
        spec = get_platform_spec("unknown")
        assert spec["width"] == 1080

    def test_all_specs_have_required_keys(self):
        for platform in ["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]:
            spec = get_platform_spec(platform)
            assert "width" in spec
            assert "height" in spec
            assert "fps" in spec


class TestExtractKeywords:
    def test_removes_stop_words(self):
        kws = extract_keywords("The quick brown fox jumps over the lazy dog")
        assert "the" not in kws
        assert "over" not in kws

    def test_returns_list(self):
        kws = extract_keywords("artificial intelligence")
        assert isinstance(kws, list)

    def test_max_keywords(self):
        text = "one two three four five six seven eight nine ten eleven"
        kws = extract_keywords(text, max_keywords=5)
        assert len(kws) <= 5

    def test_deduplicates(self):
        kws = extract_keywords("business business business")
        assert kws.count("business") == 1

    def test_empty_text(self):
        kws = extract_keywords("")
        assert kws == []
