# CLAUDE CODE PROMPT — CLIPFORGE

Build a **fully working, tested, GitHub-ready** Python CLI project called:

`clipforge`

## Goal

Create a professional CLI tool that turns a text script into short videos for:
- YouTube Shorts
- Instagram Reels
- TikTok
- optional 16:9 landscape videos

The tool must:
- split a script into scenes
- find suitable royalty-free stock visuals for each scene
- assemble a video
- add subtitles or title cards
- optionally add:
  - silent mode
  - music only
  - voiceover only
  - voiceover + music
- support presets
- support batch jobs
- generate social media text packs
- include an **optional AI integration skeleton**
- work completely **without AI** as a stable default

---

## Core requirement

Do **not** build a fake scaffold.

I want you to:
1. create the full structure
2. write real code
3. write tests
4. run the tests
5. fix failures
6. make the project ready to use

Final result must:
- work locally
- pass `pytest`
- provide working CLI commands
- be clean enough to upload to GitHub

---

## Tech stack

Use:
- Python 3.10+
- MoviePy
- FFmpeg
- requests
- python-dotenv
- pytest
- click **or** argparse
- pyttsx3 for local TTS

Optional:
- Pillow
- pydantic
- rich
- typer
- jsonschema

Keep it stable and practical.

---

## Project structure

Create this structure:

```text
clipforge/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ .env.example
├─ requirements.txt
├─ pyproject.toml
├─ setup.cfg
├─ install.sh
├─ install.bat
├─ .pre-commit-config.yaml
├─ .github/
│  ├─ workflows/
│  │  └─ ci.yml
│  ├─ ISSUE_TEMPLATE/
│  │  ├─ bug_report.md
│  │  └─ feature_request.md
│  └─ PULL_REQUEST_TEMPLATE.md
├─ docs/
│  ├─ usage.md
│  ├─ config.md
│  ├─ presets.md
│  ├─ ai.md
│  ├─ developer.md
│  ├─ troubleshooting.md
│  ├─ roadmap.md
│  ├─ workflows.md
│  ├─ changelog.md
│  ├─ features.md
│  ├─ faq.md
│  ├─ contributing.md
│  └─ extensions.md
├─ examples/
│  ├─ README.md
│  ├─ script_example.txt
│  ├─ script_ai_example.txt
│  ├─ config_example.json
│  ├─ batch_example.json
│  └─ profile_example.json
├─ assets/
│  ├─ music/
│  │  └─ placeholder.txt
│  ├─ logo/
│  │  └─ placeholder.txt
│  └─ images/
│     └─ placeholder.txt
├─ data/
│  ├─ presets.json
│  ├─ styles.json
│  ├─ platforms.json
│  └─ voices.json
├─ src/
│  └─ clipforge/
│     ├─ __init__.py
│     ├─ cli.py
│     ├─ utils.py
│     ├─ constants.py
│     ├─ config_loader.py
│     ├─ presets.py
│     ├─ script_parser.py
│     ├─ scene_planner.py
│     ├─ builder.py
│     ├─ audio_engine.py
│     ├─ text_engine.py
│     ├─ social_pack.py
│     ├─ batch_runner.py
│     ├─ ai/
│     │  ├─ __init__.py
│     │  ├─ base.py
│     │  ├─ factory.py
│     │  ├─ prompts.py
│     │  ├─ cache.py
│     │  └─ providers/
│     │     ├─ __init__.py
│     │     ├─ openai_provider.py
│     │     ├─ anthropic_provider.py
│     │     └─ gemini_provider.py
│     └─ commands/
│        ├─ __init__.py
│        ├─ make.py
│        ├─ scenes.py
│        ├─ doctor.py
│        ├─ presets.py
│        ├─ wizard.py
│        ├─ init_config.py
│        ├─ init_batch.py
│        ├─ batch.py
│        ├─ social_pack.py
│        ├─ export_bundle.py
│        ├─ init_profile.py
│        ├─ thumbnail.py
│        └─ studio.py
└─ tests/
   ├─ __init__.py
   ├─ conftest.py
   ├─ test_cli.py
   ├─ test_utils.py
   ├─ test_script_parser.py
   ├─ test_scene_planner.py
   ├─ test_builder.py
   ├─ test_audio_engine.py
   ├─ test_text_engine.py
   ├─ test_social_pack.py
   └─ test_config_loader.py
````

---

## Functional requirements

### 1. Script parsing

Implement real script splitting:

* split by blank lines and sentence boundaries
* merge tiny fragments
* enforce a max scene count
* return scene metadata:

  * text
  * estimated duration
  * keywords
  * visual_intent

### 2. Scene planning

For each scene generate:

* query
* visual_type
* duration
* fallback_type

Use local heuristics when AI is off.

Example visual types:

* technology
* business
* people
* city
* nature
* abstract

### 3. Stock media search

Use `.env` keys if present:

* Pexels video
* Pexels image
* Pixabay video
* Pixabay image
* fallback background if nothing is found

Must include:

* timeout
* retries
* clear error handling
* duplicate media avoidance

### 4. Video assembly

Use MoviePy + FFmpeg.

Support:

* 9:16
* 16:9

Per scene:

* use video or image clip
* crop/resize to fill
* overlay subtitles or title cards
* optional intro/outro text

Final output:

* mp4
* h264
* aac

### 5. Audio engine

Implement real audio modes:

* `silent`
* `music`
* `voiceover`
* `voiceover+music`

Rules:

* music volume control
* local TTS voiceover
* simple ducking when voiceover + music
* if music file missing, warn instead of crashing
* if TTS fails, fallback cleanly

### 6. Text engine

Implement real text modes:

* `none`
* `subtitle`
* `title_cards`

Subtitle animation modes:

* `static`
* `typewriter`
* `word-by-word`

At minimum:

* static fully working
* typewriter and word-by-word visibly different and usable

### 7. Social pack

Generate:

* title
* caption
* hook
* CTA
* hashtags

Make it platform-aware for:

* reels
* tiktok
* youtube-shorts
* youtube

If AI is off, use local templates.

### 8. Batch mode

Support batch JSON jobs:

* process multiple jobs
* continue even if one job fails
* print summary

### 9. Wizard and init commands

These must create real files:

* `init-config`
* `init-batch`
* `init-profile`

`wizard` should ask for:

* script file
* output
* platform
* style
* audio mode
* text mode
* subtitle mode
* music file
* AI mode
* brand name
* logo file

Then save a config JSON.

### 10. Thumbnail

Create a real thumbnail generator using Pillow.
Support:

* text
* brand name
* platform size
* jpg/png output

### 11. Export bundle

Bundle together:

* video
* thumbnail
* social json
* social txt

### 12. Doctor command

Very important.

Check:

* ffmpeg availability
* Python version
* `.env` presence
* stock media API keys
* AI provider key if AI enabled
* referenced music/logo files
* required directories

Human-readable output:

* `[OK]`
* `[WARN]`
* `[ERROR]`

---

## AI integration skeleton

AI must be **optional**.

Modes:

* `off`
* `assist`
* `full`

Tasks:

* scene planning
* query generation
* social pack

Create provider skeletons for:

* OpenAI
* Anthropic
* Gemini

Rules:

* no provider = no crash
* missing key = warning
* AI error = fallback
* structured JSON response interface

Implement:

* `src/clipforge/ai/base.py`
* `src/clipforge/ai/factory.py`
* `src/clipforge/ai/prompts.py`
* `src/clipforge/ai/cache.py`

The project must still work fully with AI disabled.

---

## CLI commands

These commands must exist and work:

```bash
clipforge --help
clipforge presets
clipforge doctor
clipforge scenes --script-file examples/script_example.txt
clipforge init-config --output myvideo.json
clipforge init-batch --output jobs.json
clipforge init-profile --output channel.profile.json
clipforge wizard --output myvideo.json
clipforge make --script-file examples/script_example.txt --output output/demo.mp4
clipforge make --config examples/config_example.json
clipforge batch --batch-file examples/batch_example.json
clipforge social-pack --script-file examples/script_example.txt --platform reels --brand-name Azerbite
clipforge thumbnail --text "How AI changes business" --platform reels --brand-name Azerbite --output output/thumb.jpg
clipforge export-bundle --video-file output/demo.mp4 --social-json output/social.json --output-dir bundle
clipforge studio
```

---

## Config support

Support this config shape:

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
  "voice_language": "az",

  "intro_text": "Azerbite",
  "outro_text": "Follow for more",

  "logo_file": "assets/logo/logo.png",
  "watermark_position": "top-right",

  "ai_mode": "off",
  "ai_provider": "",
  "ai_model": ""
}
```

---

## README requirements

README must clearly explain:

* what the project does
* installation
* `.env` setup
* ffmpeg requirement
* key CLI commands
* audio/text/subtitle modes
* AI support as optional future-ready layer
* local testing
* GitHub push basics

---

## Tests

Write real pytest tests for:

* script parser
* config loader
* utils
* social pack
* scene planner
* CLI import
* doctor logic
* batch runner

Use temp files and mocks where useful.

Final requirement:

* `pytest` must pass
* do not leave broken tests

---

## Code quality

Requirements:

* type hints
* docstrings
* clean structure
* reusable functions
* good error handling
* practical logging
* future extensibility

---

## Installer requirements

`install.sh` and `install.bat` must:

* create virtual environment
* install dependencies
* run editable install (`pip install -e .`)
* tell the user to:

  * create `.env`
  * add API keys
  * run `clipforge doctor`

---

## GitHub ready

Make the repo ready for GitHub:

* correct `.gitignore`
* `.env` excluded
* CI workflow
* LICENSE
* issue templates
* PR template

---

## Final task

Do all of this for real.

At the end:

1. create all files
2. finish the implementation
3. write tests
4. run tests
5. fix issues
6. make `pytest` pass
7. clean temp/cache files
8. ensure repo is clean
9. make it GitHub-ready
10. provide a final report with:

* files created
* commands working
* what is fully implemented
* what is intentionally left as future extension
* final test result

If something is incomplete, say it clearly.
Do not hide it.

Now build the project completely and make it ready.

```
```

