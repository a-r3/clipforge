"""Tests for clipforge.script_parser module."""

from __future__ import annotations

import pytest

from clipforge.script_parser import (
    ScriptParser,
    Scene,
    split_script_into_scenes,
    _detect_visual_intent,
)


class TestScene:
    def test_to_dict_has_required_keys(self):
        scene = Scene(text="Hello world", index=0, estimated_duration=1.0, keywords=["hello"], visual_intent="abstract")
        d = scene.to_dict()
        assert "text" in d
        assert "index" in d
        assert "estimated_duration" in d
        assert "keywords" in d
        assert "visual_intent" in d

    def test_to_dict_values(self):
        scene = Scene(text="Test text", index=2, estimated_duration=3.5, keywords=["test"], visual_intent="technology")
        d = scene.to_dict()
        assert d["text"] == "Test text"
        assert d["index"] == 2
        assert abs(d["estimated_duration"] - 3.5) < 0.01
        assert d["visual_intent"] == "technology"


class TestDetectVisualIntent:
    def test_technology(self):
        assert _detect_visual_intent("AI and machine learning technology") == "technology"

    def test_business(self):
        assert _detect_visual_intent("business company market strategy") == "business"

    def test_people(self):
        assert _detect_visual_intent("people team community collaboration") == "people"

    def test_city(self):
        assert _detect_visual_intent("city urban street building") == "city"

    def test_nature(self):
        assert _detect_visual_intent("nature outdoor green forest") == "nature"

    def test_fallback_to_abstract(self):
        result = _detect_visual_intent("xyz zzz something random words")
        assert result == "abstract"


class TestScriptParser:
    def test_parse_empty_returns_empty(self):
        parser = ScriptParser()
        assert parser.parse("") == []
        assert parser.parse("   ") == []

    def test_parse_single_paragraph(self):
        parser = ScriptParser()
        text = "This is a simple test paragraph with enough words to make one scene."
        scenes = parser.parse(text)
        assert len(scenes) >= 1
        assert all(isinstance(s, Scene) for s in scenes)

    def test_parse_multiple_paragraphs(self, sample_script):
        parser = ScriptParser()
        scenes = parser.parse(sample_script)
        assert len(scenes) >= 2

    def test_max_scenes_enforced(self):
        parser = ScriptParser(max_scenes=3)
        # Create a script with many paragraphs
        paragraphs = [f"This is paragraph {i} with enough words to form its own scene completely." for i in range(10)]
        text = "\n\n".join(paragraphs)
        scenes = parser.parse(text)
        assert len(scenes) <= 3

    def test_scenes_have_text(self, sample_script):
        parser = ScriptParser()
        scenes = parser.parse(sample_script)
        for scene in scenes:
            assert scene.text.strip()

    def test_scenes_have_positive_duration(self, sample_script):
        parser = ScriptParser()
        scenes = parser.parse(sample_script)
        for scene in scenes:
            assert scene.estimated_duration > 0

    def test_scenes_have_visual_intent(self, sample_script):
        parser = ScriptParser()
        scenes = parser.parse(sample_script)
        valid_intents = {"technology", "business", "people", "city", "nature", "abstract"}
        for scene in scenes:
            assert scene.visual_intent in valid_intents

    def test_scenes_have_keywords(self, sample_script):
        parser = ScriptParser()
        scenes = parser.parse(sample_script)
        for scene in scenes:
            assert isinstance(scene.keywords, list)

    def test_indices_are_sequential(self, sample_script):
        parser = ScriptParser()
        scenes = parser.parse(sample_script)
        for i, scene in enumerate(scenes):
            assert scene.index == i

    def test_tiny_fragments_merged(self):
        parser = ScriptParser(min_words=10)
        # Short paragraph should be merged
        text = "Short.\n\nThis is a longer paragraph with enough words to form a proper scene here."
        scenes = parser.parse(text)
        # Short fragment should have been merged into the longer one
        for scene in scenes:
            assert len(scene.text.split()) >= 5  # at least a reasonable size


class TestSplitScriptIntoScenes:
    """Test the legacy convenience function."""

    def test_returns_list_of_dicts(self, sample_script):
        result = split_script_into_scenes(sample_script)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert "text" in item

    def test_empty_input(self):
        result = split_script_into_scenes("")
        assert result == []

    def test_max_scenes_respected(self, sample_script):
        result = split_script_into_scenes(sample_script, max_scenes=3)
        assert len(result) <= 3

    def test_module_has_function(self):
        import importlib
        module = importlib.import_module("clipforge.script_parser")
        assert hasattr(module, "split_script_into_scenes")
