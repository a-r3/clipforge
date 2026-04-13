# Troubleshooting

Run `clipforge doctor` first — it checks the most common problems and prints
`[OK]`, `[WARN]`, or `[ERROR]` for each item.

---

## FFmpeg not found

**Symptom:** `[ERROR] FFmpeg not found on PATH` or `FileNotFoundError` during render.

**Fix:**
- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to `PATH`.

After installing, open a new terminal and run `ffmpeg -version` to confirm.

---

## moviepy version mismatch

**Symptom:** `AttributeError` or `ImportError` referencing `moviepy.editor` or
`VideoFileClip`.

**Fix:** ClipForge requires **exactly `moviepy==1.0.3`**. moviepy 2.x changed its
API in breaking ways and is not supported.

```bash
pip install "moviepy==1.0.3"
```

If you have a newer version installed, downgrade:

```bash
pip install "moviepy==1.0.3" --force-reinstall
```

---

## Missing API keys

Some features require API keys in a `.env` file:

- **Stock media** (Pexels, Pixabay): needed for automatic visual search. Without
  them, ClipForge uses a solid-colour fallback background.
- **AI providers** (OpenAI, Anthropic, Gemini): only needed when `ai_mode` is
  `assist` or `full`.

```bash
cp .env.example .env
# Edit .env and fill in the keys you need
```

---

## pyttsx3 / TTS not working

**Symptom:** Voiceover mode produces no audio, or an error about pyttsx3.

**Fix:** Install pyttsx3 and a system speech engine:

```bash
pip install pyttsx3
# Linux also needs: sudo apt install espeak
```

Use `audio_mode: silent` or `audio_mode: music` if you don't need voiceover.

---

## Unsupported platform name

**Symptom:** `Invalid value for '--platform'` or similar Click error.

**Fix:** Supported platforms are `reels`, `tiktok`, `youtube-shorts`, `youtube`,
`landscape`. Use `clipforge presets` to see available presets.

---

## Tests failing

```bash
# Make sure dev dependencies are installed
pip install -e ".[dev,tts]"

# Run the test suite
pytest tests/ -v
```

Tests are self-contained and do not require FFmpeg, moviepy, or API keys.

---

## `clipforge` command not found after install

Make sure you have activated the virtual environment:

```bash
source .venv/bin/activate      # Unix/macOS
.venv\Scripts\activate.bat     # Windows
```

Or reinstall in editable mode:

```bash
pip install -e ".[tts]"
```
