"""
Utility functions to split scripts into scenes.
"""

import re
from typing import List


def split_script_into_scenes(script: str, max_scenes: int = 20) -> List[str]:
    """
    Split a script into a list of scenes by blank lines and sentence length.

    :param script: The raw script text.
    :param max_scenes: Maximum number of scenes to return.
    :return: A list of scene strings.
    """
    if not script:
        return []

    script = script.strip()
    # Split on double newlines to separate paragraphs
    parts = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    scenes: List[str] = []
    for part in parts:
        # Further split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", part)
        chunk = ""
        for s in sentences:
            if len((chunk + " " + s).strip()) < 180:
                chunk = (chunk + " " + s).strip()
            else:
                if chunk:
                    scenes.append(chunk)
                chunk = s.strip()
        if chunk:
            scenes.append(chunk)
    return scenes[:max_scenes]
