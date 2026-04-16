"""Pytest configuration and shared fixtures for ClipForge tests.

Adds the project's ``src`` directory to ``sys.path`` so that the
``clipforge`` package can be imported without installing the package.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def sample_script() -> str:
    """A multi-paragraph script about AI and business."""
    return """Artificial intelligence is transforming the way businesses operate in the digital age.
Companies that embrace AI technology are gaining significant competitive advantages.

The business landscape is changing rapidly. Market leaders are investing in machine learning
and data analytics to improve their decision-making processes.

Technology companies are developing powerful tools that automate repetitive tasks.
This automation allows human workers to focus on creative and strategic work.

People and communities benefit when businesses use AI responsibly. Customer service
has improved dramatically thanks to intelligent chatbot systems and personalized recommendations.

The city of tomorrow will be driven by smart infrastructure and digital innovation.
Urban planning teams are using AI to optimize traffic flow and reduce energy consumption.

Nature and sustainability are also being transformed by technology. Scientists use
machine learning to monitor ecosystems and predict environmental changes.

Looking ahead, the integration of AI into everyday business operations will continue
to accelerate. Organizations that adapt early will be best positioned for success."""


@pytest.fixture
def sample_config() -> dict:
    """A minimal valid config dict."""
    return {
        "script_file": "",
        "output": "output/test_video.mp4",
        "platform": "reels",
        "style": "clean",
        "audio_mode": "silent",
        "text_mode": "subtitle",
        "subtitle_mode": "static",
        "music_file": "",
        "music_volume": 0.12,
        "auto_voice": False,
        "voice_language": "en",
        "intro_text": "",
        "outro_text": "",
        "logo_file": "",
        "watermark_position": "top-right",
        "ai_mode": "off",
        "ai_provider": "",
        "ai_model": "",
        "max_scenes": 15,
        "brand_name": "TestBrand",
    }


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """A temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def sample_config_file(tmp_path: Path, sample_config: dict) -> Path:
    """Write sample_config to a temp JSON file and return its path."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(sample_config, indent=2), encoding="utf-8")
    return config_file


@pytest.fixture
def sample_script_file(tmp_path: Path, sample_script: str) -> Path:
    """Write sample_script to a temp text file and return its path."""
    script_file = tmp_path / "script.txt"
    script_file.write_text(sample_script, encoding="utf-8")
    return script_file
