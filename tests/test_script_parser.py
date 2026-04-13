"""
Tests for the script parser module.
"""

import importlib

def test_script_parser_module_exists():
    module = importlib.import_module("autovideo.script_parser")
    assert hasattr(module, "split_script_into_scenes")
