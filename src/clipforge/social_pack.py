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
    """Build a hashtag string for the platform."""
    base_tags = list(_PLATFORM_HASHTAGS.get(platform, _PLATFORM_HASHTAGS[PLATFORM_REELS]))

    # Add topic-based hashtags
    topic = _extract_topic(script)
    topic_tag = "#" + re.sub(r"\s+", "", topic.lower())
    if len(topic_tag) > 2:
        base_tags.insert(0, topic_tag)

    if extra_tags:
        base_tags.extend(extra_tags)

    return " ".join(base_tags[:12])


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

        return {
            "title": title,
            "caption": caption,
            "hook": hook,
            "cta": cta,
            "hashtags": hashtags,
            "platform": platform,
            "brand_name": brand_name,
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
