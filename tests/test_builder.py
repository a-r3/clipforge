"""
Tests for the builder module.
"""

import importlib

def test_builder_module_exists():
    module = importlib.import_module("autovideo.builder")
    assert hasattr(module, "make_video")
