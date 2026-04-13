## Developer Guide

This document outlines the high‑level architecture of the `autovideo` project and provides guidance for contributors who want to extend or maintain the codebase.

### Project Structure

The project is organised into several key packages:

* `src/autovideo` – core functionality and CLI entry points.
* `src/autovideo/commands` – individual CLI subcommands are implemented here, separated by concern.
* `src/autovideo/ai` – optional artificial intelligence providers and abstractions that can be enabled via configuration.
* `data` – JSON files containing static definitions for presets, styles, platforms and voices.
* `assets` – placeholders for stock music, logos and images.
* `tests` – unit tests covering the public API and individual components.

### Entry Points

The CLI entry point is defined in `src/autovideo/cli.py` and uses the `click` library to register subcommands. Each subcommand delegates work to a module within `autovideo/commands`.

### Adding a Command

1. Create a new file under `src/autovideo/commands` with a descriptive name (for example, `export_cmd.py`).
2. Define a `cli` function decorated with `@click.command()` and accept any required options or arguments.
3. Implement the command’s logic, delegating to core utilities in `autovideo` where possible.
4. Register the command in `src/autovideo/cli.py` by importing it and adding it to the main group.

### Extending the AI Layer

Providers live under `src/autovideo/ai/providers`. To add support for a new provider:

1. Create a new file in that directory (e.g. `myprovider.py`) that subclasses `AIProvider`.
2. Implement the required methods such as `generate_scene_plan` and `generate_social_pack`. These should return structured Python objects or dictionaries.
3. Update `factory.py` to include your provider in the selection logic.

### Unit Tests

Tests live under the `tests` directory and can be run with `pytest`. Each new module should have a corresponding test file with simple sanity checks. Use fixtures and mocks to isolate dependencies.
