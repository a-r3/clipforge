"""Scene planner for ClipForge.

Takes parsed scenes and generates visual search queries, visual types,
durations, and fallback information for each scene.
"""

from __future__ import annotations

from typing import Any

from clipforge.constants import VISUAL_TYPES, VISUAL_ABSTRACT, AI_OFF
from clipforge.script_parser import Scene


# Fallback types for each visual type
_FALLBACKS: dict[str, str] = {
    "technology": "abstract",
    "business": "people",
    "people": "city",
    "city": "abstract",
    "nature": "abstract",
    "abstract": "abstract",
}

# Stock query templates per visual type
_QUERY_TEMPLATES: dict[str, list[str]] = {
    "technology": [
        "{keyword} technology",
        "digital {keyword}",
        "tech innovation",
        "artificial intelligence",
    ],
    "business": [
        "{keyword} business",
        "corporate {keyword}",
        "business meeting",
        "professional workplace",
    ],
    "people": [
        "{keyword} people",
        "diverse team collaboration",
        "community gathering",
        "professional people",
    ],
    "city": [
        "{keyword} city",
        "urban landscape",
        "city skyline",
        "modern architecture",
    ],
    "nature": [
        "{keyword} nature",
        "outdoor scenery",
        "natural landscape",
        "green environment",
    ],
    "abstract": [
        "{keyword} background",
        "abstract motion",
        "colorful background",
        "minimal background",
    ],
}


def _build_query(scene: Scene | dict, visual_type: str) -> str:
    """Build a search query for a scene given its visual type."""
    if isinstance(scene, dict):
        keywords = scene.get("keywords", [])
        text = scene.get("text", "")
    else:
        keywords = scene.keywords
        text = scene.text

    primary_keyword = keywords[0] if keywords else (text.split()[0] if text else "video")

    templates = _QUERY_TEMPLATES.get(visual_type, _QUERY_TEMPLATES["abstract"])
    query = templates[0].format(keyword=primary_keyword)
    return query


class ScenePlanner:
    """Plan visual queries and metadata for each scene."""

    def __init__(self, ai_mode: str = AI_OFF, ai_provider: Any = None) -> None:
        self.ai_mode = ai_mode
        self.ai_provider = ai_provider

    def plan(self, scenes: list[Scene | dict]) -> list[dict[str, Any]]:
        """Generate a plan for each scene.

        Returns a list of dicts, each containing:
        - query: search query string
        - visual_type: category of visual
        - duration: scene duration in seconds
        - fallback_type: fallback visual type
        - scene_text: original text
        """
        planned: list[dict[str, Any]] = []

        for scene in scenes:
            if isinstance(scene, dict):
                visual_intent = scene.get("visual_intent", VISUAL_ABSTRACT)
                duration = scene.get("estimated_duration", 3.0)
                text = scene.get("text", "")
                keywords = scene.get("keywords", [])
            else:
                visual_intent = scene.visual_intent
                duration = scene.estimated_duration
                text = scene.text
                keywords = scene.keywords

            # Normalize visual type
            visual_type = visual_intent if visual_intent in VISUAL_TYPES else VISUAL_ABSTRACT

            # In AI mode, we could call the AI provider here; for now use heuristics
            if self.ai_mode != AI_OFF and self.ai_provider is not None:
                # AI path — fallback to heuristics if AI fails
                try:
                    ai_plan = self._ai_plan_scene(text, keywords)
                    visual_type = ai_plan.get("visual_type", visual_type)
                    query = ai_plan.get("query", _build_query(scene, visual_type))
                except Exception:
                    query = _build_query(scene, visual_type)
            else:
                query = _build_query(scene, visual_type)

            planned.append(
                {
                    "query": query,
                    "visual_type": visual_type,
                    "duration": duration,
                    "fallback_type": _FALLBACKS.get(visual_type, VISUAL_ABSTRACT),
                    "scene_text": text,
                    "keywords": keywords,
                }
            )

        return planned

    def _ai_plan_scene(self, text: str, keywords: list[str]) -> dict[str, Any]:
        """Use AI provider to plan a scene. Falls back to empty dict on error."""
        if self.ai_provider is None:
            return {}
        from clipforge.ai.prompts import SCENE_PLAN_PROMPT
        prompt = SCENE_PLAN_PROMPT.format(text=text, keywords=", ".join(keywords))
        schema = {"visual_type": "string", "query": "string"}
        return self.ai_provider.generate(prompt, schema)
