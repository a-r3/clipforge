"""
Tests for the social pack module.
"""

import importlib

def test_social_pack_module_exists():
    module = importlib.import_module("autovideo.social_pack")
    assert hasattr(module, "generate_social_pack")
