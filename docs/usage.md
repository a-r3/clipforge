# Usage Guide

## Installation

Run the provided `install.sh` (Unix) or `install.bat` (Windows) script to set up a Python virtual environment and install dependencies.

```bash
cd auto_scenario_video_builder_v9
cp .env.example .env
./install.sh
```

Edit the `.env` file to add API keys for Pexels or Pixabay if you wish to download stock media.

## Creating a video

The basic command to create a video from a script:

```bash
clipforge make --script-file examples/script_example.txt --output output/demo.mp4
```

### Options

- `--audio-mode`: `silent`, `music`, `voiceover`, `voiceover+music`
- `--text-mode`: `none`, `subtitle`, `title_cards`
- `--subtitle-mode`: `static`, `typewriter`, `word-by-word`

You can also provide a JSON configuration file:

```bash
clipforge make --config examples/config_example.json
```

## Previewing scenes

Use the `scenes` subcommand to preview how your script will be segmented:

```bash
clipforge scenes --script-file examples/script_example.txt
```

## Diagnostics

Check your installation and environment with the `doctor` command:

```bash
clipforge doctor
```