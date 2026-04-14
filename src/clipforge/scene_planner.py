"""Scene planner for ClipForge.

Takes parsed scenes and generates visual search queries, visual types,
durations, and fallback information for each scene.
"""

from __future__ import annotations

import re
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

# Weighted keyword → (visual_type, weight) mapping
# Weight 2.0 = strong signal, 1.0 = moderate, 0.5 = weak
_KEYWORD_SCORES: dict[str, tuple[str, float]] = {
    # Technology
    "artificial intelligence": ("technology", 2.0),
    "machine learning": ("technology", 2.0),
    "deep learning": ("technology", 2.0),
    "neural network": ("technology", 2.0),
    "algorithm": ("technology", 1.5),
    "software": ("technology", 1.5),
    "programming": ("technology", 1.5),
    "computer": ("technology", 1.0),
    "digital": ("technology", 1.0),
    "technology": ("technology", 1.5),
    "tech": ("technology", 1.0),
    "data": ("technology", 1.0),
    "internet": ("technology", 1.0),
    "cloud": ("technology", 1.0),
    "robot": ("technology", 1.5),
    "automation": ("technology", 1.5),
    "coding": ("technology", 1.5),
    "developer": ("technology", 1.0),
    "cybersecurity": ("technology", 2.0),
    "blockchain": ("technology", 2.0),
    "virtual reality": ("technology", 2.0),
    "augmented reality": ("technology", 2.0),
    # Business
    "business": ("business", 1.5),
    "company": ("business", 1.5),
    "corporate": ("business", 1.5),
    "entrepreneur": ("business", 1.5),
    "startup": ("business", 1.5),
    "investment": ("business", 1.5),
    "revenue": ("business", 1.5),
    "profit": ("business", 1.0),
    "market": ("business", 1.0),
    "customer": ("business", 1.0),
    "strategy": ("business", 1.0),
    "leadership": ("business", 1.0),
    "management": ("business", 1.0),
    "finance": ("business", 1.5),
    "economy": ("business", 1.0),
    "brand": ("business", 1.0),
    "product": ("business", 1.0),
    "sales": ("business", 1.5),
    "marketing": ("business", 1.5),
    # People
    "people": ("people", 1.5),
    "team": ("people", 1.5),
    "community": ("people", 1.5),
    "collaboration": ("people", 1.5),
    "diversity": ("people", 1.5),
    "family": ("people", 1.5),
    "student": ("people", 1.0),
    "employee": ("people", 1.0),
    "volunteer": ("people", 1.5),
    "social": ("people", 1.0),
    "relationship": ("people", 1.0),
    # City / Urban
    "city": ("city", 1.5),
    "urban": ("city", 1.5),
    "building": ("city", 1.0),
    "architecture": ("city", 1.5),
    "street": ("city", 1.0),
    "skyline": ("city", 2.0),
    "downtown": ("city", 1.5),
    "infrastructure": ("city", 1.5),
    "traffic": ("city", 1.0),
    # Nature
    "nature": ("nature", 1.5),
    "environment": ("nature", 1.5),
    "sustainability": ("nature", 1.5),
    "climate": ("nature", 1.5),
    "forest": ("nature", 2.0),
    "ocean": ("nature", 2.0),
    "water": ("nature", 1.0),
    "green": ("nature", 0.5),
    "energy": ("nature", 1.0),
    "renewable": ("nature", 1.5),
    "wildlife": ("nature", 2.0),
    "plant": ("nature", 1.0),
}

# Stop words to skip during keyword selection
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "that", "this",
    "these", "those", "it", "its", "not", "no", "so", "as", "if", "then",
    "than", "into", "out", "up", "down", "about", "after", "before",
    "through", "during", "just", "each", "every", "all", "both", "over",
    "under", "within", "without", "how", "when", "where", "what", "which",
}

# Stock query templates per visual type (ordered best → fallback)
_QUERY_TEMPLATES: dict[str, list[str]] = {
    "technology": [
        "{keyword} technology",
        "digital {keyword}",
        "tech innovation",
        "artificial intelligence abstract",
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


def _score_visual_type(text: str, keywords: list[str]) -> tuple[str, float]:
    """Score text and keywords to determine the most likely visual type.

    Returns (visual_type, confidence) where confidence is 0.0–1.0.
    """
    scores: dict[str, float] = {}
    combined = (text + " " + " ".join(keywords)).lower()

    # Check bigrams first (higher specificity)
    for phrase, (vtype, weight) in _KEYWORD_SCORES.items():
        if " " in phrase and phrase in combined:
            scores[vtype] = scores.get(vtype, 0.0) + weight
        elif " " not in phrase and re.search(r"\b" + re.escape(phrase) + r"\b", combined):
            scores[vtype] = scores.get(vtype, 0.0) + weight

    if not scores:
        return VISUAL_ABSTRACT, 0.0

    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]
    confidence = min(1.0, best_score / 3.0)
    return best_type, confidence


def _select_best_keyword(keywords: list[str], text: str) -> str:
    """Pick the most useful keyword for query building.

    Prefers longer, meaningful words over short stop words.
    Falls back to first content word in text if keywords are all stop words.
    """
    candidates = [
        kw for kw in keywords
        if kw.lower() not in _STOP_WORDS
        and kw.isascii()
        and len(kw) >= 4
    ]
    if candidates:
        # Prefer longer keywords as they tend to be more specific
        return max(candidates, key=len)

    # Fall back to text words
    for word in text.split():
        word_clean = re.sub(r"[^a-zA-Z]", "", word).lower()
        if word_clean and word_clean not in _STOP_WORDS and len(word_clean) >= 4:
            return word_clean

    return keywords[0] if keywords else "video"


def build_queries(scene: "Scene | dict", visual_type: str, count: int = 4) -> list[str]:
    """Build a ranked list of search queries for a scene.

    Returns up to `count` queries from most specific to most generic.
    """
    if isinstance(scene, dict):
        keywords = scene.get("keywords", [])
        text = scene.get("text", "")
    else:
        keywords = scene.keywords
        text = scene.text

    keyword = _select_best_keyword(keywords, text)
    templates = _QUERY_TEMPLATES.get(visual_type, _QUERY_TEMPLATES["abstract"])

    queries: list[str] = []
    seen: set[str] = set()
    for tmpl in templates[:count]:
        q = tmpl.format(keyword=keyword)
        if q not in seen:
            queries.append(q)
            seen.add(q)

    # Pad with abstract fallbacks if needed
    if len(queries) < count:
        for tmpl in _QUERY_TEMPLATES["abstract"][:count]:
            q = tmpl.format(keyword=keyword)
            if q not in seen:
                queries.append(q)
                seen.add(q)
            if len(queries) >= count:
                break

    return queries[:count]


def _build_query(scene: "Scene | dict", visual_type: str) -> str:
    """Backward-compatible single query builder."""
    return build_queries(scene, visual_type, count=1)[0]


class ScenePlanner:
    """Plan visual queries and metadata for each scene."""

    def __init__(self, ai_mode: str = AI_OFF, ai_provider: Any = None) -> None:
        self.ai_mode = ai_mode
        self.ai_provider = ai_provider

    def plan(self, scenes: list["Scene | dict"]) -> list[dict[str, Any]]:
        """Generate a plan for each scene.

        Returns a list of dicts, each containing:
        - query: primary search query (backward compat alias)
        - primary_query: best search query string
        - alternate_queries: list of fallback queries
        - visual_type: category of visual
        - confidence: float 0.0–1.0 indicating planning confidence
        - duration: scene duration in seconds
        - fallback_type: fallback visual type
        - scene_text: original text
        - keywords: extracted keywords
        """
        planned: list[dict[str, Any]] = []

        for scene in scenes:
            planned.append(self._plan_scene(scene))

        return planned

    def _plan_scene(self, scene: "Scene | dict") -> dict[str, Any]:
        """Plan a single scene using heuristics and optional AI."""
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

        # V2: Score visual type from text content (ignore hint if confidence is low)
        scored_type, confidence = _score_visual_type(text, keywords)

        # Use hint from parser if scoring has no signal
        if confidence < 0.1 and visual_intent in VISUAL_TYPES:
            visual_type = visual_intent
        else:
            visual_type = scored_type if scored_type in VISUAL_TYPES else VISUAL_ABSTRACT

        # Build local queries
        local_queries = build_queries(scene, visual_type, count=4)

        # AI enhancement path
        if self.ai_mode != AI_OFF and self.ai_provider is not None:
            try:
                ai_result = self._ai_plan_scene(text, keywords, visual_type, local_queries)
                if ai_result:
                    ai_vtype = ai_result.get("visual_type", visual_type)
                    if ai_vtype in VISUAL_TYPES:
                        visual_type = ai_vtype
                    ai_primary = ai_result.get("primary_query") or ai_result.get("query", "")
                    ai_alternates = ai_result.get("alternate_queries", [])
                    if ai_primary:
                        all_queries = [ai_primary] + ai_alternates + local_queries
                        # Deduplicate while preserving order
                        seen: set[str] = set()
                        merged: list[str] = []
                        for q in all_queries:
                            if q and q not in seen:
                                merged.append(q)
                                seen.add(q)
                        local_queries = merged[:4]
                    confidence = min(1.0, confidence + 0.2)
            except Exception:
                pass  # Fall back to local heuristics silently

        primary_query = local_queries[0] if local_queries else "abstract background"
        alternate_queries = local_queries[1:] if len(local_queries) > 1 else []

        return {
            # Backward compat
            "query": primary_query,
            # V2 fields
            "primary_query": primary_query,
            "alternate_queries": alternate_queries,
            "confidence": round(confidence, 2),
            "visual_type": visual_type,
            "duration": duration,
            "fallback_type": _FALLBACKS.get(visual_type, VISUAL_ABSTRACT),
            "scene_text": text,
            "keywords": keywords,
        }

    def _ai_plan_scene(
        self,
        text: str,
        keywords: list[str],
        local_visual_type: str,
        local_queries: list[str],
    ) -> dict[str, Any]:
        """Use AI provider to improve scene planning.

        Returns a dict with optional keys: visual_type, primary_query,
        alternate_queries. Returns {} on any failure.
        """
        if self.ai_provider is None:
            return {}
        try:
            from clipforge.ai.prompts import SCENE_PLAN_PROMPT_V2
        except ImportError:
            from clipforge.ai.prompts import SCENE_PLAN_PROMPT as SCENE_PLAN_PROMPT_V2  # type: ignore
        prompt = SCENE_PLAN_PROMPT_V2.format(
            text=text,
            keywords=", ".join(keywords),
            local_visual_type=local_visual_type,
            local_queries=", ".join(local_queries),
        )
        schema = {
            "visual_type": "string",
            "primary_query": "string",
            "alternate_queries": "list",
        }
        try:
            return self.ai_provider.generate(prompt, schema) or {}
        except Exception:
            return {}
