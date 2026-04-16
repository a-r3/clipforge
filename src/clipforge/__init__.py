"""ClipForge — CLI tool to turn text scripts into short videos, with publish, analytics, and optimization."""

from PIL import Image

# Pillow 10 removed Image.ANTIALIAS, but MoviePy 1.x still references it.
if not hasattr(Image, "ANTIALIAS") and hasattr(Image, "Resampling"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

__version__ = "1.0.0"
__author__ = "ClipForge"
