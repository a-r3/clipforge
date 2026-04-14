"""Social media pack generator for ClipForge.

Generates platform-aware social media content packs including title,
caption, hook, CTA, and hashtags.
"""

from __future__ import annotations

import re
from typing import Any

from clipforge.constants import (
    PLATFORM_REELS,
    PLATFORM_TIKTOK,
    PLATFORM_YOUTUBE_SHORTS,
    PLATFORM_YOUTUBE,
)

# Platform-specific hashtag pools
_PLATFORM_HASHTAGS: dict[str, list[str]] = {
    PLATFORM_REELS: [
        "#reels", "#instareels", "#reelsvideo", "#explore", "#viral",
        "#trending", "#shortsvideo", "#instagramreels",
    ],
    PLATFORM_TIKTOK: [
        "#tiktok", "#fyp", "#foryoupage", "#viral", "#trending",
        "#tiktokvideos", "#foryou", "#viralvideo",
    ],
    PLATFORM_YOUTUBE_SHORTS: [
        "#shorts", "#youtubeshorts", "#shortsvideo", "#viral",
        "#trending", "#youtube", "#youtubevideos",
    ],
    PLATFORM_YOUTUBE: [
        "#youtube", "#youtubevideos", "#video", "#viral",
        "#trending", "#subscribe", "#youtuber",
    ],
}

# Platform-specific CTA templates
_CTA_TEMPLATES: dict[str, list[str]] = {
    PLATFORM_REELS: [
        "Follow for more content like this! 🚀",
        "Save this for later and share with your friends!",
        "Double tap if you found this helpful! 💡",
    ],
    PLATFORM_TIKTOK: [
        "Follow for daily insights! 🔥",
        "Like and share if this helped you!",
        "Comment below what you think! 💬",
    ],
    PLATFORM_YOUTUBE_SHORTS: [
        "Subscribe for more Shorts!",
        "Hit the like button if you enjoyed this!",
        "Check out our full videos on the channel!",
    ],
    PLATFORM_YOUTUBE: [
        "Subscribe and hit the notification bell! 🔔",
        "Leave a comment with your thoughts!",
        "Like and share if this was valuable!",
    ],
}

# Hook templates
_HOOK_TEMPLATES = [
    "Did you know that {topic}?",
    "Here's the truth about {topic}:",
    "Most people don't know this about {topic}.",
    "This will change how you think about {topic}.",
    "{topic} — explained in under 60 seconds.",
    "The #1 thing you need to know about {topic}:",
    "Stop ignoring {topic}. Here's why it matters.",
]

# Caption templates
_CAPTION_TEMPLATES: dict[str, str] = {
    PLATFORM_REELS: "{hook}\n\n{summary}\n\n{cta}\n\n{hashtags}",
    PLATFORM_TIKTOK: "{hook}\n\n{summary}\n\n{cta}\n\n{hashtags}",
    PLATFORM_YOUTUBE_SHORTS: "{hook}\n\n{summary}\n\n{cta}\n\n{hashtags}",
    PLATFORM_YOUTUBE: "{hook}\n\n{summary}\n\n---\n{cta}\n\n{hashtags}",
}


def _extract_topic(script: str) -> str:
    """Extract the main topic from the first sentence of a script."""
    first_sentence = re.split(r"[.!?\n]", script.strip())[0]
    words = first_sentence.split()
    # Take up to 5 meaningful words as topic
    stop = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of"}
    topic_words = [w for w in words if w.lower() not in stop][:5]
    return " ".join(topic_words).strip() or "this topic"


def _build_title(script: str, brand_name: str, platform: str) -> str:
    """Build a platform-appropriate title."""
    topic = _extract_topic(script)
    # Capitalise each word of the topic
    topic_cap = " ".join(w.capitalize() for w in topic.split())

    if platform in (PLATFORM_REELS, PLATFORM_TIKTOK):
        title = topic_cap[:70]
    elif platform == PLATFORM_YOUTUBE_SHORTS:
        title = f"{topic_cap} #Shorts"[:70]
    else:
        title = topic_cap[:100]

    if brand_name:
        title = f"{brand_name}: {title}"

    return title


def _build_hook(script: str) -> str:
    """Build an engaging hook from the script topic."""
    topic = _extract_topic(script)
    import random
    template = random.choice(_HOOK_TEMPLATES)
    return template.format(topic=topic)


def _build_summary(script: str, max_chars: int = 200) -> str:
    """Extract a short summary from the script."""
    # Take the first paragraph or first few sentences
    paragraphs = [p.strip() for p in script.strip().split("\n\n") if p.strip()]
    first_para = paragraphs[0] if paragraphs else script.strip()
    sentences = re.split(r"(?<=[.!?])\s+", first_para)
    summary = ""
    for s in sentences:
        candidate = (summary + " " + s).strip()
        if len(candidate) <= max_chars:
            summary = candidate
        else:
            break
    return summary or first_para[:max_chars]


def _build_hashtags(script: str, platform: str, extra_tags: list[str] | None = None) -> str:
    """Build a short, clean hashtag string for the platform.

    Topic-based tags are limited to single meaningful words (max 20 chars)
    to avoid long unreadable slug-hashtags.
    """
    base_tags = list(_PLATFORM_HASHTAGS.get(platform, _PLATFORM_HASHTAGS[PLATFORM_REELS]))

    # Extract 1-2 short topic-specific hashtags from individual keywords
    topic = _extract_topic(script)
    words = [w for w in re.findall(r"[a-zA-Z]{4,}", topic.lower()) if w]
    topic_tags = []
    for w in words[:2]:
        tag = f"#{w}"
        # Skip if too long or already in platform tags
        if len(tag) <= 20 and tag not in base_tags:
            topic_tags.append(tag)

    combined = topic_tags + base_tags
    if extra_tags:
        combined.extend(extra_tags)

    # Deduplicate while preserving order, cap at 8 tags
    seen: set[str] = set()
    result: list[str] = []
    for tag in combined:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
        if len(result) >= 8:
            break

    return " ".join(result)


class SocialPackGenerator:
    """Generate social media content packs."""

    def generate(
        self,
        scenes: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a social media pack for the given scenes and config.

        Returns a dict with keys: title, caption, hook, cta, hashtags.
        """
        platform = config.get("platform", PLATFORM_REELS)
        brand_name = config.get("brand_name", "")

        # Reconstruct script from scenes
        script = " ".join(s.get("text", "") for s in scenes if s.get("text"))
        if not script:
            script = config.get("script_text", "No script provided.")

        title = _build_title(script, brand_name, platform)
        hook = _build_hook(script)
        summary = _build_summary(script)
        hashtags = _build_hashtags(script, platform)

        cta_list = _CTA_TEMPLATES.get(platform, _CTA_TEMPLATES[PLATFORM_REELS])
        import random
        cta = random.choice(cta_list)

        caption_template = _CAPTION_TEMPLATES.get(platform, _CAPTION_TEMPLATES[PLATFORM_REELS])
        caption = caption_template.format(
            hook=hook,
            summary=summary,
            cta=cta,
            hashtags=hashtags,
        )

        # V2: produce variants (multiple options for A/B testing / scheduling)
        hook_variants = [_build_hook(script) for _ in range(3)]
        # Deduplicate while preserving first
        seen_hooks: set[str] = set()
        unique_hooks: list[str] = []
        for h in [hook] + hook_variants:
            if h not in seen_hooks:
                seen_hooks.add(h)
                unique_hooks.append(h)
        hook_variants = unique_hooks[:3]

        cta_variants = cta_list[:3]

        # Title variants: with/without brand prefix and with different truncation
        topic = _extract_topic(script)
        topic_cap = " ".join(w.capitalize() for w in topic.split())
        title_base = topic_cap[:70]
        title_variants = [
            f"{brand_name}: {title_base}" if brand_name else title_base,
            title_base,
            f"{title_base} — {brand_name}" if brand_name else title_base,
        ]
        # Deduplicate
        seen_titles: set[str] = set()
        unique_titles: list[str] = []
        for t in title_variants:
            if t not in seen_titles:
                seen_titles.add(t)
                unique_titles.append(t)
        title_variants = unique_titles[:3]

        return {
            "title": title,
            "caption": caption,
            "hook": hook,
            "cta": cta,
            "hashtags": hashtags,
            "platform": platform,
            "brand_name": brand_name,
            # V2 variant fields
            "title_variants": title_variants,
            "hook_variants": hook_variants,
            "cta_variants": cta_variants,
        }


# Module-level convenience function
def generate_social_pack(
    script: str,
    platform: str = PLATFORM_REELS,
    brand_name: str = "",
) -> dict[str, str]:
    """Generate a social pack from a raw script string.

    Convenience wrapper around SocialPackGenerator.
    """
    from clipforge.script_parser import ScriptParser
    parser = ScriptParser()
    scenes = [s.to_dict() for s in parser.parse(script)]

    config = {"platform": platform, "brand_name": brand_name}
    generator = SocialPackGenerator()
    return generator.generate(scenes, config)
