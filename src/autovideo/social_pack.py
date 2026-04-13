"""
Social pack generator.

This module provides a simple function to produce social media metadata such as
a title, caption and hashtags. A full implementation would adapt output to
platform‑specific requirements and brand guidelines.
"""

from typing import Dict


def generate_social_pack(script: str, platform: str, brand_name: str = "") -> Dict[str, str]:
    """
    Generate a minimal social pack dictionary for a given script and platform.

    :param script: The script text used to derive the title and caption.
    :param platform: Target platform identifier (e.g. "reels", "tiktok").
    :param brand_name: Optional brand name to prefix the title.
    :return: Dictionary containing keys `title`, `caption` and `hashtags`.
    """
    lines = script.strip().split("\n")
    first_line = lines[0] if lines else ""
    # Construct a simple title using the first line of the script
    title = f"{brand_name} - {first_line[:60].strip()}" if brand_name else first_line[:60].strip()
    caption = script.strip()
    hashtags = "#shortvideo #autovideo"
    return {"title": title, "caption": caption, "hashtags": hashtags}
