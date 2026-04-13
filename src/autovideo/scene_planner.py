"""
Scene planning utilities.

The scene planner is responsible for analysing the script, determining what
visuals should accompany each scene and constructing search queries for stock
media. This stub returns a trivial plan where each query is based on the
first word of the scene.
"""

from typing import List, Dict


class ScenePlanner:
    """
    Plan scenes by generating search queries. The `ai_mode` parameter controls
    whether an AI provider is used; in this stub it is ignored.
    """

    def __init__(self, ai_mode: str = "off") -> None:
        self.ai_mode = ai_mode

    def plan(self, scenes: List[str]) -> List[Dict[str, str]]:
        """
        Plan each scene and return a list of dictionaries containing at least a
        `query` key. The query uses the first word of the scene as a naive
        keyword.

        :param scenes: List of scene strings.
        :return: List of dictionaries with search queries.
        """
        return [
            {"query": scene.split()[0] if scene else ""}
            for scene in scenes
        ]
