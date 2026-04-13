## Troubleshooting

This document lists common issues you might encounter when running or developing `autovideo`, along with suggested resolutions.

### Missing FFmpeg

If you see an error indicating that FFmpeg is not installed, install FFmpeg on your system and ensure it is available on the PATH. On many Linux distributions this can be done via your package manager (`sudo apt install ffmpeg`). The `autovideo doctor` command will alert you if FFmpeg cannot be found.

### Missing API Keys

Some functionality depends on external APIs (for example, Pexels or Pixabay for stock media and optional AI providers). Create a `.env` file based on `.env.example` and fill in the appropriate keys. Without these keys the application will fall back to placeholder assets or skip AI features.

### Unsupported Platform Preset

When invoking `autovideo make`, ensure the `--platform` option corresponds to a supported preset defined in `data/platforms.json`. Use `autovideo presets` to list available options.

### Testing Failures

If running `pytest` yields failures, make sure you have installed development dependencies and activated a virtual environment created by `install.sh` or `install.bat`. Tests are intended to be lightweight and should not depend on external services.
