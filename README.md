# ClipForge

Turn text scripts into short videos for YouTube Shorts, Instagram Reels, and TikTok — from the command line.

```
clipforge make --script-file examples/script_example.txt --platform reels --output output/demo.mp4
```

---

## What it does

ClipForge takes a plain-text script, splits it into scenes, assembles a video with the correct aspect ratio for your target platform, overlays subtitles or title cards, and optionally adds a voiceover and background music.

It works **completely without AI** as a stable default. An optional AI layer (OpenAI, Anthropic, Gemini) can improve scene planning and social pack generation when enabled.

---

## Requirements

| Dependency | Notes |
|-----------|-------|
| Python 3.10+ | |
| FFmpeg | Must be on `PATH`. Install from [ffmpeg.org](https://ffmpeg.org/download.html) or via your package manager (`sudo apt install ffmpeg`) |
| moviepy 1.0.3 | Pinned — do not upgrade; moviepy 2.x changed its API in breaking ways |

---

## Installation

### Unix / macOS

```bash
git clone <repo-url> clipforge
cd clipforge
bash install.sh
source .venv/bin/activate
```

### Windows

```bat
git clone <repo-url> clipforge
cd clipforge
install.bat
.venv\Scripts\activate.bat
```

### Manual

```bash
python3 -m venv .venv
source .venv/bin/activate          # or .venv\Scripts\activate.bat on Windows
pip install -e ".[tts]"            # includes pyttsx3 for local voiceover
```

---

## .env setup

Copy the example and fill in your API keys:

```bash
cp .env.example .env
```

```ini
# Stock media (optional — ClipForge works without these, using solid-colour fallbacks)
PEXELS_API_KEY=your_pexels_key_here
PIXABAY_API_KEY=your_pixabay_key_here

# AI providers (optional — only needed when ai_mode != "off")
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

Then verify your setup:

```bash
clipforge doctor
```

---

## Quick start

```bash
# Parse a script and preview scene breakdown
clipforge scenes --script-file examples/script_example.txt

# Build a video (silent audio, static subtitles)
clipforge make --script-file examples/script_example.txt \
               --platform reels \
               --audio-mode silent \
               --output output/demo.mp4

# Build from a config file
clipforge make --config examples/config_example.json

# Generate a social media content pack
clipforge social-pack --script-file examples/script_example.txt \
                      --platform reels --brand-name YourBrand

# Create a thumbnail
clipforge thumbnail --text "How AI changes business" \
                    --platform reels --brand-name YourBrand \
                    --output output/thumb.jpg
```

---

## All commands

| Command | Description |
|---------|-------------|
| `clipforge make` | Build a video from a script or config file |
| `clipforge scenes` | Parse a script and print scene breakdown |
| `clipforge doctor` | Check FFmpeg, Python, .env, API keys |
| `clipforge presets` | List available presets |
| `clipforge wizard` | Interactive config builder |
| `clipforge init-config` | Write a starter config JSON |
| `clipforge init-batch` | Write a starter batch JSON |
| `clipforge init-profile` | Write a starter channel profile JSON |
| `clipforge batch` | Run multiple jobs from a batch file |
| `clipforge social-pack` | Generate title, caption, hashtags |
| `clipforge thumbnail` | Generate a thumbnail image (Pillow) |
| `clipforge export-bundle` | Bundle video + thumbnail + social pack |
| `clipforge studio` | Interactive TUI (rich) |

---

## Audio modes

| Mode | Description |
|------|-------------|
| `silent` | No audio track |
| `music` | Background music only (provide `music_file`) |
| `voiceover` | Local TTS via pyttsx3 (`pip install ".[tts]"`) |
| `voiceover+music` | Voiceover with music ducking |

---

## Text / subtitle modes

| `text_mode` | `subtitle_mode` | Effect |
|------------|----------------|--------|
| `none` | — | No text overlay |
| `subtitle` | `static` | Full scene text, fixed position |
| `subtitle` | `typewriter` | Characters appear one by one |
| `subtitle` | `word-by-word` | Words appear one at a time |
| `title_cards` | — | Large centred title card per scene |

---

## AI support (optional)

Set `ai_mode` in your config:

| Mode | Behaviour |
|------|-----------|
| `off` *(default)* | Local heuristics only — no API calls |
| `assist` | AI improves scene queries and social pack |
| `full` | AI drives scene planning end-to-end |

Set `ai_provider` to `openai`, `anthropic`, or `gemini` and add the matching key to `.env`. If the key is missing or the provider is unavailable, ClipForge falls back silently to local mode.

---

## Config file

All CLI options can be stored in a JSON config file:

```json
{
  "script_file": "examples/script_example.txt",
  "output": "output/demo.mp4",
  "platform": "reels",
  "style": "clean",
  "audio_mode": "voiceover+music",
  "text_mode": "subtitle",
  "subtitle_mode": "word-by-word",
  "music_file": "assets/music/background.mp3",
  "music_volume": 0.12,
  "auto_voice": true,
  "voice_language": "en",
  "intro_text": "YourBrand",
  "outro_text": "Follow for more",
  "brand_name": "YourBrand",
  "ai_mode": "off"
}
```

Generate a starter file:

```bash
clipforge init-config --output myconfig.json
```

---

## Local testing

```bash
# Install dev dependencies
pip install -e ".[dev,tts]"

# Run tests
pytest tests/ -v

# Smoke test the CLI
clipforge --help
clipforge doctor
clipforge scenes --script-file examples/script_example.txt
```

---

## GitHub push

```bash
git add .
git commit -m "feat: initial clipforge setup"
git remote add origin https://github.com/youruser/clipforge.git
git push -u origin main
```

The `.gitignore` already excludes `.env`, `.venv/`, `output/`, and media files.

---

## License

MIT — see [LICENSE](LICENSE).
