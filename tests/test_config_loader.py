"""
Tests for the config loader module.
"""

import importlib

def test_config_loader_module_exists():
    module = importlib.import_module("autovideo.config_loader")
    assert hasattr(module, "load_config")
