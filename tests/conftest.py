"""
Pytest configuration file for autovideo tests.

This file adds the project's `src` directory to `sys.path` so that modules
under `autovideo` can be imported without installing the package. Without
this, tests will fail with `ModuleNotFoundError: No module named 'autovideo'`.
"""

import sys
from pathlib import Path

# Compute the absolute path to the project root and append `src` to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
