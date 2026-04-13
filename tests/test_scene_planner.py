"""
Tests for the scene planner module.
"""

import importlib

def test_scene_planner_module_exists():
    module = importlib.import_module("autovideo.scene_planner")
    assert hasattr(module, "ScenePlanner")
