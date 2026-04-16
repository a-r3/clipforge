# ClipForge v1.0

Turn text scripts into short videos for YouTube Shorts, Instagram Reels, and TikTok — with publish, analytics, and optimization built in.

```bash
clipforge make --script-file my_script.txt --platform reels
```

---

## What it does

You write a script. ClipForge renders the video, generates social content, manages your publish queue, collects performance analytics, and recommends improvements for your next video — all from the command line.

Works **completely without AI** by default. Every feature is local-first. No hidden uploads.

---

## Quick start

**Step 1** — Install

```bash
git clone <repo-url> clipforge
cd clipforge
bash install.sh
source .venv/bin/activate
```

**Step 2** — Check your setup

```bash
clipforge doctor
```

**Step 3** — Build your first video

```bash
# Guided interactive studio (recommended for first use)
clipforge studio

# Or directly
clipforge make --script-file examples/script_example.txt
```

---

## Requirements

| Dependency | Notes |
|---|---|
| Python 3.10+ | 3.11 or 3.12 recommended |
| FFmpeg | Must be on `PATH` — `brew install ffmpeg` or `sudo apt install ffmpeg` |
| moviepy 1.0.3 | Pinned — 2.x breaks the render pipeline |

---

## Installation

```bash
# Core (video rendering + TTS voiceover)
bash install.sh

# With YouTube publishing + analytics
bash install.sh --youtube

# Everything (TTS + YouTube + AI providers)
bash install.sh --full
```

Windows: use `install.bat` with the same flags.

See `docs/install.md` for manual install, upgrade, and uninstall instructions.

---

## .env setup

```bash
cp .env.example .env
```

Add the keys you need — all optional:

```ini
PEXELS_API_KEY=          # Stock visuals (free tier at pexels.com)
PIXABAY_API_KEY=         # Alternative stock visuals

YOUTUBE_CREDENTIALS_PATH=  # For YouTube uploads + analytics
CLIPFORGE_PUBLISH_DRY_RUN= # Set to 1 to default all publishes to dry-run
```

Without API keys, ClipForge uses solid-colour backgrounds and still renders correctly.

---

## All commands

### Render
| Command | What it does |
|---|---|
| `make` | Render a video from a script |
| `scenes` | Preview scene breakdown before rendering |
| `batch` | Run multiple render jobs |
| `export-bundle` | Bundle video + thumbnail + social pack |

### Social content
| Command | What it does |
|---|---|
| `social-pack` | Generate title, caption, hashtags |
| `thumbnail` | Create a thumbnail image |

### Publish
| Command | What it does |
|---|---|
| `publish-manifest` | Create, show, validate publish manifests |
| `queue` | Manage publish queue (add/list/execute/retry) |
| `publish` | Execute publish jobs (validate/dry-run/execute/retry) |

### Analytics
| Command | What it does |
|---|---|
| `analytics` | Fetch, show, summarise, and compare performance metrics |

### Optimization
| Command | What it does |
|---|---|
| `optimize` | Data-driven recommendations for your next video |

### Setup & config
| Command | What it does |
|---|---|
| `doctor` | Check system requirements and configuration |
| `wizard` | Guided interactive setup |
| `studio` | Interactive TUI (recommended for new users) |
| `project` | Manage reusable project folders |
| `templates` | Content template packs |
| `presets` | List available style presets |
| `init-config` | Write a starter config JSON |
| `init-profile` | Write a starter brand profile JSON |
| `init-batch` | Write a starter batch jobs JSON |

Run any command with `--help` for full options.

---

## Common workflows

### Render and publish (YouTube)

```bash
# 1. Render
clipforge make --script-file script.txt --platform youtube --output output/ep01.mp4

# 2. Create manifest
clipforge publish-manifest create --video-file output/ep01.mp4 --platform youtube \
    --title "My Title" --caption "Description here" --job-name ep01

# 3. Dry-run (always first)
clipforge publish dry-run ep01.manifest.json

# 4. Upload
clipforge publish execute ep01.manifest.json
```

### Collect and act on analytics

```bash
# Fetch after publishing
clipforge analytics fetch ep01.manifest.json

# After several videos, run the optimizer
clipforge optimize report

# Save recommendations for reference
clipforge optimize apply --output optimization_notes.json
```

### Interactive all-in-one

```bash
clipforge studio
```

Covers every workflow through guided menus: render → publish prep → analytics → optimize.

---

## Platform support

| Platform | Render | Publish | Analytics |
|---|---|---|---|
| YouTube | ✓ | ✓ Real API | ✓ Real API |
| YouTube Shorts | ✓ | ✓ Real API | ✓ Real API |
| Instagram Reels | ✓ | Manual checklist | Manual entry |
| TikTok | ✓ | Manual checklist | Manual entry |
| Landscape | ✓ | Manual checklist | — |

Real YouTube publishing requires `pip install -e ".[publish-youtube]"` and Google credentials. See `docs/publish.md`.

---

## Audio modes

| Mode | Description |
|---|---|
| `silent` | No audio |
| `music` | Background music (you provide the file) |
| `voiceover` | Auto-generated voiceover (pyttsx3) |
| `voiceover+music` | Voiceover + music with ducking |

---

## Smart defaults by platform

| Platform | Style | Subtitles |
|---|---|---|
| reels, tiktok | bold | word-by-word |
| youtube-shorts | clean | static |
| youtube, landscape | cinematic | static |

---

## Documentation

| Guide | Contents |
|---|---|
| `docs/install.md` | Install, upgrade, uninstall |
| `docs/usage.md` | Full CLI reference |
| `docs/workflows.md` | End-to-end workflow guides |
| `docs/publish.md` | Publish manifests, queue, providers, credentials |
| `docs/analytics.md` | Analytics collection and interpretation |
| `docs/optimization.md` | Optimization recommendations methodology |
| `docs/config.md` | Config file reference |
| `docs/ai.md` | AI provider setup |

---

## AI support (optional)

```json
{ "ai_mode": "assist", "ai_provider": "openai" }
```

Modes: `off` (default, local only) | `assist` | `full`. Providers: `openai`, `anthropic`, `gemini`. See `docs/ai.md`.

---

## License

MIT — see [LICENSE](LICENSE).
