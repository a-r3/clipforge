"""
Tests for the top‑level CLI module.
"""

import importlib
import types


def test_cli_package_importable():
    # The `autovideo.cli` package should be importable. It contains
    # submodules for each subcommand but does not define a top‑level `main`.
    cli_pkg = importlib.import_module("autovideo.cli")
    assert isinstance(cli_pkg, types.ModuleType)


def test_cli_subcommand_modules_importable():
    # Ensure that each declared subcommand maps to a valid module with a main function
    commands = [
        "make",
        "scenes",
        "doctor",
        "presets",
        "wizard",
        "init-config",
        "init-batch",
        "batch",
        "social-pack",
        "export-bundle",
        "init-profile",
        "thumbnail",
        "studio",
    ]
    for cmd in commands:
        module_name = cmd.replace("-", "_")
        module = importlib.import_module(f"autovideo.cli.{module_name}")
        assert hasattr(module, "main")
