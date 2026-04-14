# ClipForge v1.0 — Install, Upgrade, Uninstall

---

## Requirements

| Dependency | Minimum | Notes |
|---|---|---|
| Python | 3.10 | 3.11 or 3.12 recommended |
| FFmpeg | Any recent | Must be on `PATH` |
| moviepy | **1.0.3** | Pinned — 2.x changed API in breaking ways |

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows — download from https://ffmpeg.org/download.html
# Add the bin/ folder to your PATH
```

Verify: `ffmpeg -version`

---

## Install

### Unix / macOS

```bash
git clone <repo-url> clipforge
cd clipforge

# Core install (video rendering + TTS)
bash install.sh

# With YouTube publishing support
bash install.sh --youtube

# With everything (TTS + YouTube + AI providers)
bash install.sh --full

# Activate the environment
source .venv/bin/activate
```

### Windows

```bat
git clone <repo-url> clipforge
cd clipforge

install.bat
:: or: install.bat --youtube

.venv\Scripts\activate.bat
```

### Manual install (any platform)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate.bat

# Core only
pip install -e ".[tts]"

# With YouTube publishing
pip install -e ".[tts,publish-youtube]"

# With AI providers
pip install -e ".[tts,ai]"

# Everything
pip install -e ".[full]"
```

---

## Post-install setup

### 1. Copy and fill in the .env file

```bash
cp .env.example .env
```

Open `.env` and add any keys you need:

```env
# Stock visuals (free tier available)
PEXELS_API_KEY=your_key_here

# YouTube credentials path (for publishing + analytics)
YOUTUBE_CREDENTIALS_PATH=/path/to/credentials.json
```

See the comments in `.env.example` for all available variables.

### 2. Run the doctor

```bash
clipforge doctor
```

This checks: Python version, FFmpeg, moviepy, optional packages, .env values.

### 3. Try a render

```bash
clipforge make --script-file examples/script_example.txt \
               --platform reels --audio-mode silent \
               --output output/demo.mp4
```

---

## Optional extras

| Extra | What it adds | Install |
|---|---|---|
| `tts` | Voiceover via pyttsx3 | `pip install -e ".[tts]"` |
| `publish-youtube` | Real YouTube uploads + analytics | `pip install -e ".[publish-youtube]"` |
| `ai` | AI-powered social pack + scene planning | `pip install -e ".[ai]"` |
| `full` | All of the above | `pip install -e ".[full]"` |
| `dev` | pytest, ruff (for contributors) | `pip install -e ".[dev]"` |

---

## Upgrade

```bash
# Pull the latest code
git pull origin main

# Re-install in place (keeps your .env and data files)
source .venv/bin/activate
pip install -e ".[tts,publish-youtube]" --upgrade
```

Check what changed:

```bash
clipforge --version
```

---

## Uninstall

### Unix / macOS

```bash
bash uninstall.sh
```

This removes `.venv` and uninstalls the `clipforge` package. Your `.env` file, script files, video outputs, analytics store, and publish queue are **not** deleted.

### Manual / Windows

```bash
pip uninstall clipforge -y
rm -rf .venv          # Unix
rmdir /s /q .venv     # Windows
```

---

## Troubleshooting

### `clipforge: command not found`

The virtual environment is not activated. Run:

```bash
source .venv/bin/activate        # Unix
.venv\Scripts\activate.bat       # Windows
```

### `FFmpeg not found`

FFmpeg must be on your `PATH`. Install it and verify with `ffmpeg -version`.

### `moviepy` errors

ClipForge pins `moviepy==1.0.3`. If you see import errors after an upgrade, run:

```bash
pip install moviepy==1.0.3 --force-reinstall
```

### YouTube publish fails

- Verify `YOUTUBE_CREDENTIALS_PATH` points to a valid JSON file.
- For uploads, the credentials need the `youtube.upload` scope.
- For analytics, also needs `yt-analytics.readonly`.
- Run `clipforge publish dry-run manifest.json` to check credentials before executing.

See `docs/publish.md` for full credential setup.

### `clipforge doctor` shows issues

Run `clipforge doctor` — it prints a checklist with pass/fail for every dependency and configuration item, and suggests fixes.
