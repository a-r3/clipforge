"""thumbnail command — generate a thumbnail image using Pillow."""

from __future__ import annotations

import sys
from pathlib import Path

import click

# Style presets: bg_color, text_color, accent_color, font_weight
_STYLE_PRESETS: dict[str, dict] = {
    "clean": {
        "bg_color": "#1a1a2e",
        "text_color": "#ffffff",
        "accent_color": "#e94560",
    },
    "bold": {
        "bg_color": "#0a0a0a",
        "text_color": "#ffdd00",
        "accent_color": "#ff4400",
    },
    "minimal": {
        "bg_color": "#f5f5f0",
        "text_color": "#1a1a1a",
        "accent_color": "#888888",
    },
}

# Font search paths for common Linux/macOS/Windows locations
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Arial Bold.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\calibrib.ttf",
]


def _find_font(size: int):
    """Return the first available TrueType font at *size*, or the default."""
    try:
        from PIL import ImageFont
        for path in _FONT_CANDIDATES:
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


@click.command("thumbnail")
@click.option("--text", "-t", required=True, help="Main text for the thumbnail.")
@click.option("--platform", "-p", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Platform (determines size).")
@click.option("--brand-name", "-b", default="", help="Brand name to show.")
@click.option("--style", default="clean",
              type=click.Choice(["clean", "bold", "minimal"]),
              show_default=True,
              help="Visual style preset.")
@click.option("--output", "-o", default="output/thumbnail.jpg", show_default=True,
              help="Output image path (.jpg or .png).")
@click.option("--bg-color", default=None, help="Override background hex colour.")
@click.option("--text-color", default=None, help="Override text hex colour.")
@click.option("--accent-color", default=None, help="Override accent bar colour.")
def thumbnail(
    text: str,
    platform: str,
    brand_name: str,
    style: str,
    output: str,
    bg_color: str | None,
    text_color: str | None,
    accent_color: str | None,
) -> None:
    """Generate a thumbnail image using Pillow."""
    # Validate output extension
    out_path = Path(output)
    if out_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        click.echo(
            f"Error: Output file must have a .jpg or .png extension, got: {out_path.suffix!r}",
            err=True,
        )
        sys.exit(1)

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        click.echo("Error: Pillow is not installed. Run: pip install Pillow", err=True)
        sys.exit(1)

    from clipforge.utils import ensure_dir, get_platform_spec

    # Resolve style preset, allow per-option overrides
    preset = _STYLE_PRESETS.get(style, _STYLE_PRESETS["clean"])
    bg_hex = bg_color or preset["bg_color"]
    txt_hex = text_color or preset["text_color"]
    acc_hex = accent_color or preset["accent_color"]

    spec = get_platform_spec(platform)
    width, height = spec["width"], spec["height"]
    # Thumbnails: cap landscape at standard YouTube thumbnail size
    if platform in ("youtube", "landscape"):
        width, height = 1280, 720

    bg_rgb = _parse_color(bg_hex)
    txt_rgb = _parse_color(txt_hex)
    acc_rgb = _parse_color(acc_hex)

    img = Image.new("RGB", (width, height), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # Subtle gradient overlay (darken bottom)
    for i in range(height):
        ratio = (i / height) ** 2 * 0.5
        strip = _blend(bg_rgb, (0, 0, 0), ratio)
        draw.line([(0, i), (width, i)], fill=strip)

    # Accent bar at bottom
    bar_h = max(8, height // 35)
    draw.rectangle([0, height - bar_h, width, height], fill=acc_rgb)

    # Brand name
    if brand_name:
        brand_size = max(22, width // 22)
        font_brand = _find_font(brand_size)
        draw.text(
            (width // 2, height // 9),
            brand_name.upper(),
            font=font_brand,
            fill=acc_rgb,
            anchor="mm",
        )

    # Main text — word-wrapped
    main_size = max(44, width // 11)
    font_main = _find_font(main_size)
    lines = _wrap_text(draw, text, font_main, int(width * 0.85))

    line_h = main_size + max(8, main_size // 5)
    total_h = len(lines) * line_h
    y = (height - total_h) // 2

    for line in lines:
        # Shadow
        draw.text((width // 2 + 2, y + 2), line, font=font_main, fill=(0, 0, 0), anchor="mt")
        # Text
        draw.text((width // 2, y), line, font=font_main, fill=txt_rgb, anchor="mt")
        y += line_h

    ensure_dir(out_path.parent)
    fmt = "PNG" if out_path.suffix.lower() == ".png" else "JPEG"
    save_kwargs: dict = {"format": fmt}
    if fmt == "JPEG":
        save_kwargs["quality"] = 95
    img.save(str(out_path), **save_kwargs)
    click.echo(f"Thumbnail saved to: {output}")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    """Word-wrap *text* to fit within *max_width* pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def _parse_color(hex_color: str) -> tuple[int, int, int]:
    """Parse a hex colour string to an RGB tuple. Returns dark grey on error."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return (30, 30, 30)
    try:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    except ValueError:
        return (30, 30, 30)


def _blend(
    c1: tuple[int, int, int],
    c2: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    """Blend two RGB colours; ratio=0 → c1, ratio=1 → c2."""
    return (
        int(c1[0] * (1 - ratio) + c2[0] * ratio),
        int(c1[1] * (1 - ratio) + c2[1] * ratio),
        int(c1[2] * (1 - ratio) + c2[2] * ratio),
    )
