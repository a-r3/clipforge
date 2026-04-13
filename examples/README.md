# ClipForge Examples

This directory contains example input files for ClipForge.

## Files

| File | Description |
|------|-------------|
| `script_example.txt` | A plain-text script about AI and business (used in most demos) |
| `script_ai_example.txt` | A script with optional AI scene/visual directives in `[brackets]` |
| `config_example.json` | A full ClipForge config file demonstrating all options |
| `batch_example.json` | A batch file with multiple video jobs |
| `profile_example.json` | A reusable channel profile with brand defaults |

## Quick Start

```bash
# Parse a script and see scenes
clipforge scenes --script-file examples/script_example.txt

# Build a video using the example config
clipforge make --config examples/config_example.json

# Run a batch of jobs
clipforge batch --batch-file examples/batch_example.json

# Generate a social pack
clipforge social-pack --script-file examples/script_example.txt --platform reels --brand-name Azerbite
```
