"""Tests for the top-level CLI module."""

import importlib
import types

from click.testing import CliRunner

from clipforge.cli import main


def test_cli_package_importable():
    """The clipforge.cli module must be importable and expose `main`."""
    cli_pkg = importlib.import_module("clipforge.cli")
    assert isinstance(cli_pkg, types.ModuleType)
    assert hasattr(cli_pkg, "main")


def test_cli_subcommand_modules_importable():
    """Each declared subcommand module must be importable and expose a Click command."""
    commands = [
        "make",
        "scenes",
        "doctor",
        "presets",
        "wizard",
        "init_config",
        "init_batch",
        "batch",
        "social_pack",
        "export_bundle",
        "init_profile",
        "thumbnail",
        "studio",
    ]
    import click
    for module_name in commands:
        module = importlib.import_module(f"clipforge.commands.{module_name}")
        # Each module must expose at least one Click command object
        has_click_command = any(
            isinstance(getattr(module, attr), click.Command)
            for attr in dir(module)
            if not attr.startswith("_")
        )
        assert has_click_command, f"clipforge.commands.{module_name} exposes no Click command"


def test_cli_help():
    """--help should exit 0 and list commands."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "make" in result.output
    assert "doctor" in result.output


def test_cli_presets():
    """presets command should list at least one preset."""
    runner = CliRunner()
    result = runner.invoke(main, ["presets"])
    assert result.exit_code == 0
    assert "clean" in result.output.lower() or "bold" in result.output.lower()


def test_cli_scenes(tmp_path):
    """scenes command should parse the example script."""
    script = tmp_path / "script.txt"
    script.write_text(
        "Artificial intelligence is transforming businesses worldwide.\n\n"
        "Companies that adopt AI technology gain competitive advantages today.",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["scenes", "--script-file", str(script)])
    assert result.exit_code == 0
    assert "Scene" in result.output


def test_cli_init_config(tmp_path):
    """init-config should write a JSON file."""
    out = tmp_path / "config.json"
    runner = CliRunner()
    result = runner.invoke(main, ["init-config", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_init_batch(tmp_path):
    """init-batch should write a JSON file."""
    out = tmp_path / "batch.json"
    runner = CliRunner()
    result = runner.invoke(main, ["init-batch", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_doctor():
    """doctor command should run and produce output with OK/WARN/ERROR markers."""
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code in (0, 1)  # may warn/error about missing deps
    assert any(marker in result.output for marker in ("[OK]", "[WARN]", "[ERROR]"))


def test_cli_social_pack(tmp_path):
    """social-pack should generate a pack from a script file."""
    script = tmp_path / "script.txt"
    script.write_text(
        "AI is changing how businesses operate every day.\n\n"
        "Teams using machine learning tools outperform their competitors.",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["social-pack", "--script-file", str(script), "--platform", "reels", "--brand-name", "TestBrand"],
    )
    assert result.exit_code == 0
    assert "TestBrand" in result.output or "Social Pack" in result.output


def test_cli_thumbnail(tmp_path):
    """thumbnail command should create an image file."""
    out = tmp_path / "thumb.jpg"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["thumbnail", "--text", "Test Title", "--platform", "reels", "--output", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    assert out.stat().st_size > 0


def test_cli_thumbnail_style_presets(tmp_path):
    """thumbnail --style should accept clean, bold, minimal."""
    runner = CliRunner()
    for style in ("clean", "bold", "minimal"):
        out = tmp_path / f"thumb_{style}.jpg"
        result = runner.invoke(
            main,
            ["thumbnail", "--text", "Test", "--style", style, "--output", str(out)],
        )
        assert result.exit_code == 0, f"style={style} failed: {result.output}"
        assert out.exists()


def test_cli_thumbnail_rejects_bad_extension(tmp_path):
    """thumbnail should reject non-jpg/png output extension."""
    runner = CliRunner()
    out = tmp_path / "thumb.gif"
    result = runner.invoke(main, ["thumbnail", "--text", "T", "--output", str(out)])
    assert result.exit_code != 0
    assert "extension" in result.output.lower() or result.exit_code != 0


def test_cli_thumbnail_png_output(tmp_path):
    """thumbnail should accept .png output."""
    out = tmp_path / "thumb.png"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["thumbnail", "--text", "PNG Test", "--platform", "youtube", "--output", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_cli_social_pack_save_json(tmp_path):
    """social-pack --save-json should write a JSON file."""
    script = tmp_path / "script.txt"
    script.write_text("AI is transforming business today.", encoding="utf-8")
    out_json = tmp_path / "pack.json"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "social-pack", "--script-file", str(script),
            "--platform", "reels",
            "--save-json", str(out_json),
        ],
    )
    assert result.exit_code == 0
    assert out_json.exists()
    import json
    data = json.loads(out_json.read_text())
    assert "title" in data
    assert "hashtags" in data


def test_cli_social_pack_save_txt(tmp_path):
    """social-pack --save-txt should write a plain-text file."""
    script = tmp_path / "script.txt"
    script.write_text("Technology is changing the world.", encoding="utf-8")
    out_txt = tmp_path / "pack.txt"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "social-pack", "--script-file", str(script),
            "--platform", "tiktok",
            "--save-txt", str(out_txt),
        ],
    )
    assert result.exit_code == 0
    assert out_txt.exists()
    content = out_txt.read_text()
    assert "TITLE" in content
    assert "HASHTAGS" in content


def test_cli_make_dry_run(tmp_path):
    """make --dry-run should print planned scenes without rendering."""
    script = tmp_path / "script.txt"
    script.write_text(
        "AI is transforming business today.\n\nTeams using AI gain advantages.",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["make", "--script-file", str(script), "--dry-run"],
    )
    assert result.exit_code == 0
    assert "Scene" in result.output or "scene" in result.output


def test_cli_make_invalid_platform_rejected(tmp_path):
    """make with an invalid platform value should fail at Click level."""
    script = tmp_path / "script.txt"
    script.write_text("Test script.", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["make", "--script-file", str(script), "--platform", "snapchat"],
    )
    assert result.exit_code != 0
