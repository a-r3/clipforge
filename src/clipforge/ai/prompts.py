"""Prompt templates for ClipForge AI integration."""

SCENE_PLAN_PROMPT = """\
You are a video scene planner. Given the following scene text and keywords,
determine the best visual type and search query for finding stock footage.

Scene text:
{text}

Keywords: {keywords}

Visual types available: technology, business, people, city, nature, abstract

Respond with a JSON object with exactly these keys:
- visual_type: one of the types above
- query: a 2-5 word stock footage search query

Example response:
{{"visual_type": "technology", "query": "AI technology abstract"}}
"""

SOCIAL_PACK_PROMPT = """\
You are a social media content creator. Given the following script and platform,
generate engaging social media content.

Script:
{script}

Platform: {platform}
Brand name: {brand_name}

Generate a JSON object with these keys:
- title: engaging title (max 100 chars)
- hook: attention-grabbing opening line
- caption: full caption with emojis (max 500 chars)
- cta: call-to-action
- hashtags: space-separated hashtags (max 12)
"""

QUERY_GEN_PROMPT = """\
Given the following scene text, generate the best 2-4 word search query
to find relevant stock footage or images.

Scene: {text}

Respond with only the search query string, nothing else.
"""

SCENE_PLAN_PROMPT_V2 = """\
You are a video scene planner. Given a scene's text, keywords, and an initial
local analysis, refine the visual type and stock footage search queries.

Scene text:
{text}

Keywords: {keywords}

Local analysis — visual type: {local_visual_type}
Local queries: {local_queries}

Visual types available: technology, business, people, city, nature, abstract

Respond with a JSON object with exactly these keys:
- visual_type: one of the types above (keep the local type if it looks correct)
- primary_query: the single best 2-5 word stock footage search query
- alternate_queries: list of 2-3 alternative queries in case the primary fails

Example response:
{{"visual_type": "technology", "primary_query": "AI data visualization", "alternate_queries": ["machine learning abstract", "digital technology background"]}}
"""
