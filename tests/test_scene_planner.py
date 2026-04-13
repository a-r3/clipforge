"""Tests for clipforge.scene_planner module."""

from __future__ import annotations

import pytest

from clipforge.scene_planner import ScenePlanner, _build_query
from clipforge.script_parser import ScriptParser


@pytest.fixture
def parsed_scenes(sample_script):
    parser = ScriptParser()
    return [s.to_dict() for s in parser.parse(sample_script)]


class TestScenePlanner:
    def test_module_has_class(self):
        import importlib
        module = importlib.import_module("clipforge.scene_planner")
        assert hasattr(module, "ScenePlanner")

    def test_plan_returns_list(self, parsed_scenes):
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        assert isinstance(result, list)

    def test_plan_length_matches_input(self, parsed_scenes):
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        assert len(result) == len(parsed_scenes)

    def test_plan_has_required_keys(self, parsed_scenes):
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        for item in result:
            assert "query" in item
            assert "visual_type" in item
            assert "duration" in item
            assert "fallback_type" in item

    def test_plan_visual_types_valid(self, parsed_scenes):
        from clipforge.constants import VISUAL_TYPES
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        for item in result:
            assert item["visual_type"] in VISUAL_TYPES

    def test_plan_queries_are_non_empty(self, parsed_scenes):
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        for item in result:
            assert item["query"].strip()

    def test_plan_durations_positive(self, parsed_scenes):
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        for item in result:
            assert item["duration"] > 0

    def test_empty_scenes(self):
        planner = ScenePlanner()
        result = planner.plan([])
        assert result == []

    def test_default_ai_mode_is_off(self):
        planner = ScenePlanner()
        assert planner.ai_mode == "off"

    def test_accepts_scene_dicts(self):
        planner = ScenePlanner()
        scene = {
            "text": "AI technology is amazing",
            "estimated_duration": 3.0,
            "keywords": ["technology", "amazing"],
            "visual_intent": "technology",
        }
        result = planner.plan([scene])
        assert len(result) == 1
        assert result[0]["visual_type"] == "technology"

    def test_unknown_visual_type_defaults_to_abstract(self):
        planner = ScenePlanner()
        scene = {
            "text": "Some text here",
            "estimated_duration": 2.0,
            "keywords": [],
            "visual_intent": "unknown_type",
        }
        result = planner.plan([scene])
        assert result[0]["visual_type"] == "abstract"

    def test_fallback_type_is_set(self, parsed_scenes):
        planner = ScenePlanner()
        result = planner.plan(parsed_scenes)
        from clipforge.constants import VISUAL_TYPES
        for item in result:
            assert item["fallback_type"] in VISUAL_TYPES


class TestBuildQuery:
    def test_uses_first_keyword(self):
        scene = {
            "text": "AI technology changes everything",
            "keywords": ["technology", "changes"],
            "visual_intent": "technology",
        }
        query = _build_query(scene, "technology")
        assert "technology" in query.lower()

    def test_fallback_when_no_keywords(self):
        scene = {"text": "Hello world", "keywords": [], "visual_intent": "abstract"}
        query = _build_query(scene, "abstract")
        assert isinstance(query, str)
        assert len(query) > 0
