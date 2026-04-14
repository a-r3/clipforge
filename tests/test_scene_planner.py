"""Tests for clipforge.scene_planner module."""

from __future__ import annotations

import pytest

from clipforge.scene_planner import (
    ScenePlanner,
    _build_query,
    _score_visual_type,
    _select_best_keyword,
    build_queries,
)
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


class TestV2ScoreFunctions:
    """V2 helper function tests."""

    def test_score_visual_type_technology(self):
        vtype, conf = _score_visual_type(
            "Machine learning and AI are transforming software development.",
            ["machine", "learning", "software"],
        )
        assert vtype == "technology"
        assert conf > 0.0

    def test_score_visual_type_business(self):
        vtype, conf = _score_visual_type(
            "Our startup revenue grew as customers adopted our product.",
            ["startup", "revenue", "customers"],
        )
        assert vtype == "business"

    def test_score_visual_type_nature(self):
        vtype, conf = _score_visual_type(
            "Forest conservation and ocean preservation are critical for wildlife.",
            ["forest", "ocean", "wildlife"],
        )
        assert vtype == "nature"

    def test_score_empty_returns_abstract(self):
        vtype, conf = _score_visual_type("", [])
        assert vtype == "abstract"
        assert conf == 0.0

    def test_confidence_between_0_and_1(self):
        _, conf = _score_visual_type("AI machine learning blockchain cybersecurity", [])
        assert 0.0 <= conf <= 1.0

    def test_select_best_keyword_prefers_long(self):
        kw = _select_best_keyword(["AI", "technology", "transforming"], "")
        assert kw == "transforming"

    def test_select_best_keyword_skips_stop_words(self):
        kw = _select_best_keyword(["the", "this", "business"], "")
        assert kw == "business"

    def test_select_best_keyword_fallback_to_text(self):
        kw = _select_best_keyword([], "climate change matters today")
        assert kw in ("climate", "change", "matters", "today")

    def test_build_queries_returns_list(self):
        scene = {"text": "Technology is changing everything.", "keywords": ["technology"]}
        queries = build_queries(scene, "technology", count=3)
        assert isinstance(queries, list)
        assert len(queries) == 3

    def test_build_queries_are_strings(self):
        scene = {"text": "Business grows.", "keywords": ["business"]}
        for q in build_queries(scene, "business", count=4):
            assert isinstance(q, str)
            assert len(q.strip()) > 0

    def test_build_queries_no_duplicates(self):
        scene = {"text": "City skyline urban.", "keywords": ["city"]}
        queries = build_queries(scene, "city", count=4)
        assert len(queries) == len(set(queries))


class TestV2PlanOutput:
    """Tests for V2 fields in plan() output."""

    def test_plan_has_primary_query(self):
        planner = ScenePlanner()
        scene = {"text": "AI technology.", "estimated_duration": 3.0, "keywords": ["technology"], "visual_intent": "technology"}
        result = planner.plan([scene])
        assert "primary_query" in result[0]

    def test_plan_has_alternate_queries(self):
        planner = ScenePlanner()
        scene = {"text": "AI technology.", "estimated_duration": 3.0, "keywords": ["technology"], "visual_intent": "technology"}
        result = planner.plan([scene])
        assert "alternate_queries" in result[0]
        assert isinstance(result[0]["alternate_queries"], list)

    def test_plan_has_confidence(self):
        planner = ScenePlanner()
        scene = {"text": "AI technology.", "estimated_duration": 3.0, "keywords": ["technology"], "visual_intent": "technology"}
        result = planner.plan([scene])
        assert "confidence" in result[0]
        assert 0.0 <= result[0]["confidence"] <= 1.0

    def test_query_equals_primary_query(self):
        """backward compat: query == primary_query."""
        planner = ScenePlanner()
        scene = {"text": "Machine learning.", "estimated_duration": 3.0, "keywords": ["machine"], "visual_intent": "technology"}
        result = planner.plan([scene])
        assert result[0]["query"] == result[0]["primary_query"]

    def test_ai_mode_off_no_provider_needed(self):
        planner = ScenePlanner(ai_mode="off", ai_provider=None)
        scene = {"text": "Test.", "estimated_duration": 2.0, "keywords": [], "visual_intent": "abstract"}
        result = planner.plan([scene])
        assert len(result) == 1
