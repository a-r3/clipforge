# Developer Guide

This document describes the architecture of ClipForge and how to extend it.

---

## Project layout

```
src/clipforge/
├── cli.py              — Click group entry point; registers all commands
├── constants.py        — Platform names, audio/text modes, defaults
├── utils.py            — Shared helpers (slugify, ensure_dir, load_json, …)
├── config_loader.py    — JSON config loading with defaults + validation
├── script_parser.py    — Text → list of Scene objects
├── scene_planner.py    — Scene list → planned scenes with visual_type/query
├── builder.py          — MoviePy-based video assembler
├── audio_engine.py     — Audio modes: silent/music/voiceover/voiceover+music
├── text_engine.py      — Text overlays: subtitles, title cards
├── social_pack.py      — Social media pack generator
├── batch_runner.py     — Multi-job batch processor
├── presets.py          — Preset loading and application
├── ai/                 — Optional AI layer (off by default)
│   ├── base.py         — AIProvider abstract class
│   ├── factory.py      — Provider selection (returns None gracefully)
│   ├── prompts.py      — Prompt templates
│   ├── cache.py        — File-based response cache
│   └── providers/      — openai / anthropic / gemini skeletons
└── commands/           — One file per CLI subcommand
```

---

## Entry point

`clipforge.cli:main` is the Click group. All subcommands are imported from
`clipforge.commands.*` and added with `main.add_command(...)`.

The `clipforge` binary is declared in `pyproject.toml`:

```toml
[project.scripts]
clipforge = "clipforge.cli:main"
```

---

## Rendering pipeline (`make` command)

```
script text
  → ScriptParser.parse()        — list[Scene]
  → ScenePlanner.plan()         — list[planned_scene dicts]
  → VideoBuilder.build()        — writes output.mp4
      ├── _build_scene_clip()   — per-scene image/video clip
      ├── TextEngine.add_text_overlay()   — subtitle/title_card overlay
      └── AudioEngine.build_audio()       — audio track
```

**moviepy version:** ClipForge is tested against **moviepy 1.0.3**. The
dependency is pinned in `pyproject.toml` and `requirements.txt`. moviepy 2.x
is a breaking API change and is not supported.

---

## Adding a CLI command

1. Create `src/clipforge/commands/mycommand.py`.
2. Define a Click command function decorated with `@click.command("mycommand")`.
3. Import it in `src/clipforge/cli.py` and register:
   ```python
   from clipforge.commands.mycommand import mycommand
   main.add_command(mycommand)
   ```
4. Add a test in `tests/test_cli.py` using `CliRunner`.

---

## Extending the AI layer

AI providers live under `src/clipforge/ai/providers/`. To add a new provider:

1. Create `src/clipforge/ai/providers/myprovider.py` subclassing `AIProvider`
   from `clipforge.ai.base`.
2. Implement `generate(prompt, schema) -> dict`.
3. Register it in `clipforge/ai/factory.py`.

The project must continue to work when no provider is configured (`ai_mode=off`).
`AIFactory.get_provider()` returns `None` when the provider is unknown or the
key is missing — all callers must handle `None`.

---

## Running tests

```bash
pip install -e ".[dev,tts]"
pytest tests/ -v
```

Tests are self-contained and do not require FFmpeg, moviepy, pyttsx3, or API
keys. VideoBuilder and AudioEngine calls that touch moviepy/pyttsx3 are mocked.

---

## Code style

- Black, line length 100 (`pyproject.toml`)
- Type hints on all public functions
- Docstrings on all public classes and methods
- `from __future__ import annotations` at the top of every module

```bash
black src/ tests/
```
