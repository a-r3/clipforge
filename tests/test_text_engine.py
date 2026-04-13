"""
Tests for the text engine module.
"""

import importlib

def test_text_engine_module_exists():
    module = importlib.import_module("autovideo.text_engine")
    assert hasattr(module, "SubtitleRenderer")
