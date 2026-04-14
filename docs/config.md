# Configuration

ClipForge accepts all options via CLI flags or a JSON config file.
Use `clipforge init-config --output myconfig.json` to generate a starter file.

---

## Full reference

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
  "logo_file": "assets/logo.png",
  "max_scenes": 15,
  "ai_mode": "off",
  "ai_provider": "openai",
  "ai_model": "gpt-4o-mini"
}
```

---

## Platforms

| Value | Resolution | Aspect | Max duration |
|-------|-----------|--------|-------------|
| `reels` | 1080×1920 | 9:16 | 90 s |
| `tiktok` | 1080×1920 | 9:16 | 180 s |
| `youtube-shorts` | 1080×1920 | 9:16 | 60 s |
| `youtube` | 1920×1080 | 16:9 | 900 s |
| `landscape` | 1920×1080 | 16:9 | 900 s |

---

## Audio modes

| `audio_mode` | Description |
|-------------|-------------|
| `silent` | No audio |
| `music` | Background music (requires `music_file`) |
| `voiceover` | Local TTS via pyttsx3 |
| `voiceover+music` | Voiceover with music ducking |

---

## Text modes

| `text_mode` | `subtitle_mode` | Effect |
|------------|----------------|--------|
| `none` | — | No text overlay |
| `subtitle` | `static` | Full text, fixed position |
| `subtitle` | `typewriter` | Characters appear one by one |
| `subtitle` | `word-by-word` | Highlighted word-by-word karaoke |
| `title_cards` | — | Large centred title per scene |

---

## AI keys (v0.3+)

| Key | Values | Default |
|-----|--------|---------|
| `ai_mode` | `off`, `assist`, `full` | `off` |
| `ai_provider` | `openai`, `anthropic`, `gemini` | `""` |
| `ai_model` | provider-specific model name | provider default |

See [docs/ai.md](ai.md) for full AI documentation.

---

## Brand profile

You can store brand defaults in a profile JSON and apply them automatically:

```bash
clipforge init-profile --output myprofile.json
```

```json
{
  "brand_name": "TechBrief",
  "platform": "reels",
  "style": "bold",
  "audio_mode": "voiceover+music",
  "watermark_text": "TechBrief",
  "watermark_position": "bottom-right",
  "watermark_opacity": 0.7
}
```

Load in code:

```python
from clipforge.profile import BrandProfile
profile = BrandProfile.load("myprofile.json")
config = profile.apply_to_config(config)
```

Profile values fill in missing config keys but never override values you
explicitly set on the CLI or in your config file.
