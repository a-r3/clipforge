"""
Configuration loading utilities.

The functions in this module handle reading JSON configuration files from disk
and returning Python dictionaries. In the future this module may support
additional formats such as YAML.
"""

import json
from typing import Dict, Any


def load_config(path: str) -> Dict[str, Any]:
    """
    Load a JSON configuration file.

    :param path: Path to the configuration file.
    :return: Dictionary representation of the config file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
