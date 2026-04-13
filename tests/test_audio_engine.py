"""
Tests for the audio engine module.
"""

import importlib

def test_audio_engine_module_exists():
    module = importlib.import_module("autovideo.audio_engine")
    # Expect at least a placeholder class or function
    assert hasattr(module, "AudioEngine")
