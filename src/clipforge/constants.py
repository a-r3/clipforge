"""Constants used throughout ClipForge."""

from __future__ import annotations

# Platform identifiers
PLATFORM_REELS = "reels"
PLATFORM_TIKTOK = "tiktok"
PLATFORM_YOUTUBE_SHORTS = "youtube-shorts"
PLATFORM_YOUTUBE = "youtube"
PLATFORM_LANDSCAPE = "landscape"

VERTICAL_PLATFORMS = {PLATFORM_REELS, PLATFORM_TIKTOK, PLATFORM_YOUTUBE_SHORTS}
ALL_PLATFORMS = {PLATFORM_REELS, PLATFORM_TIKTOK, PLATFORM_YOUTUBE_SHORTS, PLATFORM_YOUTUBE, PLATFORM_LANDSCAPE}

# Platform specs: (width, height, fps, max_duration_seconds)
PLATFORM_SPECS: dict[str, dict] = {
    PLATFORM_REELS: {"width": 1080, "height": 1920, "fps": 30, "max_duration": 90, "aspect": "9:16"},
    PLATFORM_TIKTOK: {"width": 1080, "height": 1920, "fps": 30, "max_duration": 180, "aspect": "9:16"},
    PLATFORM_YOUTUBE_SHORTS: {"width": 1080, "height": 1920, "fps": 60, "max_duration": 60, "aspect": "9:16"},
    PLATFORM_YOUTUBE: {"width": 1920, "height": 1080, "fps": 30, "max_duration": 900, "aspect": "16:9"},
    PLATFORM_LANDSCAPE: {"width": 1920, "height": 1080, "fps": 30, "max_duration": 900, "aspect": "16:9"},
}

# Audio modes
AUDIO_SILENT = "silent"
AUDIO_MUSIC = "music"
AUDIO_VOICEOVER = "voiceover"
AUDIO_VOICEOVER_MUSIC = "voiceover+music"
AUDIO_MODES = {AUDIO_SILENT, AUDIO_MUSIC, AUDIO_VOICEOVER, AUDIO_VOICEOVER_MUSIC}

# Text modes
TEXT_NONE = "none"
TEXT_SUBTITLE = "subtitle"
TEXT_TITLE_CARDS = "title_cards"
TEXT_MODES = {TEXT_NONE, TEXT_SUBTITLE, TEXT_TITLE_CARDS}

# Subtitle animation modes
SUBTITLE_STATIC = "static"
SUBTITLE_TYPEWRITER = "typewriter"
SUBTITLE_WORD_BY_WORD = "word-by-word"
SUBTITLE_MODES = {SUBTITLE_STATIC, SUBTITLE_TYPEWRITER, SUBTITLE_WORD_BY_WORD}

# Visual types for scene planning
VISUAL_TECHNOLOGY = "technology"
VISUAL_BUSINESS = "business"
VISUAL_PEOPLE = "people"
VISUAL_CITY = "city"
VISUAL_NATURE = "nature"
VISUAL_ABSTRACT = "abstract"
VISUAL_TYPES = {VISUAL_TECHNOLOGY, VISUAL_BUSINESS, VISUAL_PEOPLE, VISUAL_CITY, VISUAL_NATURE, VISUAL_ABSTRACT}

# AI modes
AI_OFF = "off"
AI_ASSIST = "assist"
AI_FULL = "full"
AI_MODES = {AI_OFF, AI_ASSIST, AI_FULL}

# AI providers
AI_PROVIDER_OPENAI = "openai"
AI_PROVIDER_ANTHROPIC = "anthropic"
AI_PROVIDER_GEMINI = "gemini"

# Default config values
DEFAULT_PLATFORM = PLATFORM_REELS
DEFAULT_STYLE = "clean"
DEFAULT_AUDIO_MODE = AUDIO_SILENT
DEFAULT_TEXT_MODE = TEXT_SUBTITLE
DEFAULT_SUBTITLE_MODE = SUBTITLE_STATIC
DEFAULT_AI_MODE = AI_OFF
DEFAULT_MAX_SCENES = 15
DEFAULT_MUSIC_VOLUME = 0.12
DEFAULT_WPM = 130

# Style names
STYLE_CLEAN = "clean"
STYLE_BOLD = "bold"
STYLE_MINIMAL = "minimal"
STYLE_CINEMATIC = "cinematic"
STYLES = {STYLE_CLEAN, STYLE_BOLD, STYLE_MINIMAL, STYLE_CINEMATIC}

# Data directory (relative to package)
DATA_DIR = "data"

# Watermark positions
WATERMARK_TOP_LEFT = "top-left"
WATERMARK_TOP_RIGHT = "top-right"
WATERMARK_BOTTOM_LEFT = "bottom-left"
WATERMARK_BOTTOM_RIGHT = "bottom-right"
WATERMARK_CENTER = "center"
