"""thumbnail command — generate a thumbnail image using Pillow."""

from __future__ import annotations

import sys

import click


@click.command("thumbnail")
@click.option("--text", "-t", required=True, help="Main text for the thumbnail.")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Platform (determines size).")
@click.option("--brand-name", "-b", default="", help="Brand name to show.")
@click.option("--output", "-o", default="output/thumbnail.jpg", show_default=True, help="Output image path.")
@click.option("--bg-color", default="#1a1a2e", show_default=True, help="Background hex colour.")
@click.option("--text-color", default="#ffffff", show_default=True, help="Text hex colour.")
@click.option("--accent-color", default="#e94560", show_default=True, help="Accent bar colour.")
def thumbnail(
    text: str,
    platform: str,
    brand_name: str,
    output: str,
    bg_color: str,
    text_color: str,
    accent_color: str,
) -> None:
    """Generate a thumbnail image using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        click.echo("Error: Pillow is not installed. Run: pip install Pillow", err=True)
        sys.exit(1)

    from clipforge.utils import ensure_dir, get_platform_spec
    from pathlib import Path

    spec = get_platform_spec(platform)
    width, height = spec["width"], spec["height"]
    # For thumbnails, use a smaller version for landscape
    if platform in ("youtube", "landscape"):
        width, height = 1280, 720

    # Create image
    img = Image.new("RGB", (width, height), color=_parse_color(bg_color))
    draw = ImageDraw.Draw(img)

    # Draw gradient-like background strips
    for i in range(0, height, 4):
        alpha = int(255 * (1 - i / height) * 0.3)
        strip_color = _blend_colors(_parse_color(bg_color), (0, 0, 0), alpha / 255)
        draw.line([(0, i), (width, i)], fill=strip_color)

    # Draw accent bar
    accent_rgb = _parse_color(accent_color)
    bar_height = max(8, height // 40)
    draw.rectangle([0, height - bar_height, width, height], fill=accent_rgb)

    # Draw brand name
    if brand_name:
        brand_size = max(24, width // 20)
        try:
            font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", brand_size)
        except (IOError, OSError):
            font_brand = ImageFont.load_default()
        brand_text_color = _parse_color(accent_color)
        brand_bbox = draw.textbbox((0, 0), brand_name.upper(), font=font_brand)
        brand_w = brand_bbox[2] - brand_bbox[0]
        draw.text((width // 2 - brand_w // 2, height // 10), brand_name.upper(), font=font_brand, fill=brand_text_color)

    # Draw main text (word-wrapped)
    main_size = max(48, width // 10)
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", main_size)
    except (IOError, OSError):
        font_main = ImageFont.load_default()

    # Word wrap
    words = text.split()
    lines = []
    current_line = ""
    max_w = int(width * 0.85)
    for word in words:
        test = (current_line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font_main)
        if bbox[2] - bbox[0] <= max_w:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Draw each line centred
    total_text_height = len(lines) * (main_size + 10)
    y_start = (height - total_text_height) // 2
    text_rgb = _parse_color(text_color)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        y = y_start + i * (main_size + 10)
        # Shadow
        draw.text((x + 2, y + 2), line, font=font_main, fill=(0, 0, 0))
        # Main text
        draw.text((x, y), line, font=font_main, fill=text_rgb)

    # Save
    output_path = Path(output)
    ensure_dir(output_path.parent)
    img.save(str(output_path), quality=95)
    click.echo(f"Thumbnail saved to: {output}")


def _parse_color(hex_color: str) -> tuple[int, int, int]:
    """Parse a hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return (30, 30, 30)
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        return (30, 30, 30)


def _blend_colors(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    """Blend two RGB colours by ratio (0=color1, 1=color2)."""
    r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
    g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
    b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
    return (r, g, b)
