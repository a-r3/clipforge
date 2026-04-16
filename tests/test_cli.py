"""Tests for the top-level CLI module."""

import importlib
import json
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


def test_cli_social_pack_with_optimization_report(tmp_path):
    """social-pack should display optimization notes when a report is provided."""
    from clipforge.optimize.models import OptimizationReport

    script = tmp_path / "script.txt"
    script.write_text("AI is transforming business today.", encoding="utf-8")
    report = OptimizationReport(
        source_records=6,
        next_video_brief={
            "title_direction": "Lead with the payoff.",
            "hook_direction": "Open with the strongest claim.",
            "action_checklist": ["Do X.", "Do Y."],
        },
    )
    report_path = tmp_path / "opt.json"
    report.save(report_path)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "social-pack", "--script-file", str(script),
            "--platform", "reels",
            "--optimization-report", str(report_path),
        ],
    )
    assert result.exit_code == 0
    assert "Optimization notes:" in result.output
    assert "Lead with the payoff." in result.output
    assert "Checklist" in result.output


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


def test_cli_social_pack_save_txt_with_optimization_report(tmp_path):
    """social-pack TXT output should include optimization notes when present."""
    from clipforge.optimize.models import OptimizationReport

    script = tmp_path / "script.txt"
    script.write_text("Technology is changing the world.", encoding="utf-8")
    out_txt = tmp_path / "pack.txt"
    report = OptimizationReport(
        source_records=6,
        next_video_brief={
            "thumbnail_direction": "Use a single dominant visual.",
            "action_checklist": ["Do X."],
        },
    )
    report_path = tmp_path / "opt.json"
    report.save(report_path)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "social-pack", "--script-file", str(script),
            "--platform", "tiktok",
            "--optimization-report", str(report_path),
            "--save-txt", str(out_txt),
        ],
    )
    assert result.exit_code == 0
    content = out_txt.read_text()
    assert "OPTIMIZATION NOTES" in content
    assert "Use a single dominant visual." in content


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


def test_cli_make_dry_run_with_optimization_report(tmp_path):
    """make --dry-run should show optimization guidance when provided."""
    from clipforge.optimize.models import OptimizationReport

    script = tmp_path / "script.txt"
    script.write_text(
        "AI is transforming business today.\n\nTeams using AI gain advantages.",
        encoding="utf-8",
    )
    report = OptimizationReport(
        source_records=6,
        next_video_brief={
            "title_direction": "Lead with the payoff.",
            "hook_direction": "Open with the strongest claim.",
        },
    )
    report_path = tmp_path / "opt.json"
    report.save(report_path)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "make",
            "--script-file", str(script),
            "--dry-run",
            "--optimization-report", str(report_path),
        ],
    )
    assert result.exit_code == 0
    assert "Optimization notes:" in result.output
    assert "Lead with the payoff." in result.output


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


# ---------------------------------------------------------------------------
# UX / smart defaults tests
# ---------------------------------------------------------------------------


def test_cli_make_dry_run_shows_settings(tmp_path):
    """make --dry-run should show platform/style/audio in output."""
    script = tmp_path / "script.txt"
    script.write_text("AI is changing business today.\n\nTeams using AI win.", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["make", "--script-file", str(script), "--dry-run", "--platform", "reels"],
    )
    assert result.exit_code == 0
    # Should show platform/style/audio settings line
    assert "reels" in result.output


def test_cli_make_dry_run_shows_confidence(tmp_path):
    """make --dry-run with a tech script should show confidence values."""
    script = tmp_path / "script.txt"
    script.write_text(
        "Machine learning and AI are transforming software development.\n\n"
        "Deep learning algorithms power modern recommendation systems.",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["make", "--script-file", str(script), "--dry-run"],
    )
    assert result.exit_code == 0
    # V2 scene planning should show confidence
    assert "conf=" in result.output or "Scene" in result.output


def test_cli_doctor_shows_next_steps():
    """doctor output should include helpful next steps."""
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code in (0, 1)
    # Should mention clipforge make or wizard
    assert "clipforge" in result.output.lower() or "make" in result.output.lower()


def test_cli_presets_shows_descriptions():
    """presets output should show preset descriptions."""
    runner = CliRunner()
    result = runner.invoke(main, ["presets"])
    assert result.exit_code == 0
    # Should have descriptions, not just names
    assert "bold" in result.output
    assert "clean" in result.output


def test_cli_presets_detail():
    """presets --preset bold should show details."""
    runner = CliRunner()
    result = runner.invoke(main, ["presets", "--preset", "bold"])
    assert result.exit_code == 0
    assert "bold" in result.output.lower()


def test_cli_wizard_quick_mode(tmp_path):
    """wizard --quick should produce a config with minimal prompts."""
    out = tmp_path / "quick.json"
    runner = CliRunner()
    # Simulate answering 3 questions: script_file, platform, output
    inputs = "\n".join([
        "examples/script_example.txt",  # script file
        "reels",                          # platform
        str(tmp_path / "video.mp4"),     # output
    ]) + "\n"
    result = runner.invoke(main, ["wizard", "--quick", "--output", str(out)], input=inputs)
    assert result.exit_code == 0, f"wizard failed: {result.output}"
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert data["platform"] == "reels"
    assert "script_file" in data


def test_cli_init_config_minimal(tmp_path):
    """init-config --minimal should produce a short config."""
    out = tmp_path / "mini.json"
    runner = CliRunner()
    result = runner.invoke(main, ["init-config", "--output", str(out), "--minimal"])
    assert result.exit_code == 0
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    # Minimal config has essential fields
    assert "platform" in data
    assert "script_file" in data
    # Advanced fields not present in minimal
    assert "max_scenes" not in data


def test_cli_init_config_reels_smart_defaults(tmp_path):
    """init-config --platform reels should set bold style and word-by-word."""
    out = tmp_path / "reels.json"
    runner = CliRunner()
    result = runner.invoke(main, ["init-config", "--output", str(out), "--platform", "reels", "--minimal"])
    assert result.exit_code == 0
    import json
    data = json.loads(out.read_text())
    assert data["style"] == "bold"
    assert data["subtitle_mode"] == "word-by-word"


def test_cli_social_pack_show_variants(tmp_path):
    """social-pack --show-variants should include variant sections."""
    script = tmp_path / "script.txt"
    script.write_text("AI is changing business today.\n\nTeams win with machine learning.", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["social-pack", "--script-file", str(script), "--platform", "reels", "--show-variants"],
    )
    assert result.exit_code == 0
    # Should show VARIANTS section or multiple options
    assert "VARIANTS" in result.output or "options" in result.output.lower()


def test_cli_init_profile_creates_profile(tmp_path):
    """init-profile should create a valid brand profile JSON."""
    out = tmp_path / "profile.json"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["init-profile", "--output", str(out), "--brand-name", "TestCo", "--platform", "reels"],
    )
    assert result.exit_code == 0
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert data["brand_name"] == "TestCo"
    assert data["platform"] == "reels"


def test_cli_make_with_profile(tmp_path):
    """make --profile should apply profile values to the build."""
    script = tmp_path / "script.txt"
    script.write_text("AI transforms business.\n\nTeams with AI outperform.", encoding="utf-8")
    profile_path = tmp_path / "profile.json"

    # Create profile first
    runner = CliRunner()
    runner.invoke(
        main,
        ["init-profile", "--output", str(profile_path), "--brand-name", "TestBrand"],
    )
    assert profile_path.exists()

    # Now use it in a dry run
    result = runner.invoke(
        main,
        ["make", "--script-file", str(script), "--profile", str(profile_path), "--dry-run"],
    )
    assert result.exit_code == 0
    assert "Profile applied" in result.output or "TestBrand" in result.output or "Scene" in result.output


# ---------------------------------------------------------------------------
# V3 — Templates, Project, Export bundle
# ---------------------------------------------------------------------------


def test_cli_templates_list():
    """templates list should show all template packs."""
    runner = CliRunner()
    result = runner.invoke(main, ["templates", "list"])
    assert result.exit_code == 0
    assert "business" in result.output
    assert "motivation" in result.output


def test_cli_templates_show():
    """templates show <name> should display template details."""
    runner = CliRunner()
    result = runner.invoke(main, ["templates", "show", "business"])
    assert result.exit_code == 0
    assert "business" in result.output.lower()
    assert "platform" in result.output


def test_cli_templates_show_unknown():
    """templates show with unknown name should fail."""
    runner = CliRunner()
    result = runner.invoke(main, ["templates", "show", "nonexistent_xyz"])
    assert result.exit_code != 0


def test_cli_templates_apply(tmp_path):
    """templates apply should write a config JSON."""
    out = tmp_path / "business_config.json"
    runner = CliRunner()
    result = runner.invoke(main, ["templates", "apply", "business", "--output", str(out)])
    assert result.exit_code == 0, f"templates apply failed: {result.output}"
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert data["platform"] == "reels"
    assert data["style"] == "bold"


def test_cli_templates_sample(tmp_path):
    """templates sample should print or save the sample script."""
    out = tmp_path / "sample.txt"
    runner = CliRunner()
    result = runner.invoke(main, ["templates", "sample", "motivation", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert len(out.read_text()) > 10


def test_cli_project_init(tmp_path):
    """project init should create a project folder with project.json."""
    project_dir = tmp_path / "myproject"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["project", "init", "--path", str(project_dir), "--name", "TestProject", "--platform", "reels"],
    )
    assert result.exit_code == 0, f"project init failed: {result.output}"
    assert (project_dir / "project.json").exists()
    assert (project_dir / "scripts").is_dir()
    assert (project_dir / "output").is_dir()


def test_cli_project_info(tmp_path):
    """project info should print project metadata."""
    project_dir = tmp_path / "proj"
    runner = CliRunner()
    runner.invoke(main, ["project", "init", "--path", str(project_dir), "--name", "InfoTest"])
    result = runner.invoke(main, ["project", "info", "--path", str(project_dir)])
    assert result.exit_code == 0
    assert "InfoTest" in result.output


def test_cli_project_build_dry_run(tmp_path):
    """project build --dry-run should work when project has a script."""
    project_dir = tmp_path / "proj"
    runner = CliRunner()
    runner.invoke(main, ["project", "init", "--path", str(project_dir), "--name", "BuildTest"])
    # Add a script
    scripts_dir = project_dir / "scripts"
    (scripts_dir / "ep1.txt").write_text(
        "AI is changing everything.\n\nTeams using AI outperform their rivals.",
        encoding="utf-8",
    )
    result = runner.invoke(
        main,
        ["project", "build", "--path", str(project_dir), "--dry-run"],
    )
    assert result.exit_code == 0, f"project build --dry-run failed: {result.output}"
    assert "Scene" in result.output or "scene" in result.output


def test_cli_export_bundle(tmp_path):
    """export-bundle should create a bundle directory with manifest.json."""
    # Create a fake video file
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake video content")
    out_dir = tmp_path / "bundle"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export-bundle", "--video-file", str(video), "--output-dir", str(out_dir)],
    )
    assert result.exit_code == 0, f"export-bundle failed: {result.output}"
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / video.name).exists()


def test_cli_export_bundle_includes_config(tmp_path):
    """export-bundle --config-file should snapshot the config."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    config_file = tmp_path / "config.json"
    config_file.write_text('{"platform":"reels"}', encoding="utf-8")
    out_dir = tmp_path / "bundle2"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["export-bundle", "--video-file", str(video), "--output-dir", str(out_dir),
         "--config-file", str(config_file)],
    )
    assert result.exit_code == 0
    assert (out_dir / "config_snapshot.json").exists()


def test_cli_version():
    """--version should print the package version."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_cli_subcommand_modules_include_new_commands():
    """New V3 commands must be importable and expose a Click command."""
    import click
    for module_name in ("templates", "project"):
        module = importlib.import_module(f"clipforge.commands.{module_name}")
        has_click_command = any(
            isinstance(getattr(module, attr), (click.Command, click.Group))
            for attr in dir(module)
            if not attr.startswith("_")
        )
        assert has_click_command, f"clipforge.commands.{module_name} exposes no Click command/group"


# ---------------------------------------------------------------------------
# V4 — Publish manifest, queue, export-bundle integration
# ---------------------------------------------------------------------------


def test_cli_publish_manifest_help():
    """publish-manifest --help should list subcommands."""
    runner = CliRunner()
    result = runner.invoke(main, ["publish-manifest", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output
    assert "show" in result.output
    assert "validate" in result.output


def test_cli_publish_manifest_create(tmp_path):
    """publish-manifest create should write a JSON file."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    out = tmp_path / "ep1.manifest.json"
    runner = CliRunner()
    result = runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--platform", "reels",
        "--job-name", "ep1",
        "--output", str(out),
    ])
    assert result.exit_code == 0, f"publish-manifest create failed: {result.output}"
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert data["job_name"] == "ep1"
    assert data["platform"] == "reels"
    assert data["status"] == "draft"


def test_cli_publish_manifest_create_from_social_json(tmp_path):
    """publish-manifest create --social-json imports social metadata."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    import json
    social = tmp_path / "social.json"
    social.write_text(json.dumps({
        "title": "My Title",
        "caption": "My caption",
        "hashtags": "#AI #reels",
        "cta": "Follow now",
        "hook": "Did you know...",
    }), encoding="utf-8")
    out = tmp_path / "m.json"
    runner = CliRunner()
    result = runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--social-json", str(social),
        "--output", str(out),
    ])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["title"] == "My Title"
    assert data["hashtags"] == "#AI #reels"


def test_cli_publish_manifest_create_with_optimization_report(tmp_path):
    """publish-manifest create should attach optimization notes into extra."""
    from clipforge.optimize.models import OptimizationReport

    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    report = OptimizationReport(
        source_records=6,
        next_video_brief={
            "platform": "youtube",
            "template_ref": "tmpl-good",
            "title_direction": "Lead with the payoff.",
        },
    )
    report_path = tmp_path / "opt.json"
    report.save(report_path)
    out = tmp_path / "m.json"
    runner = CliRunner()
    result = runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--optimization-report", str(report_path),
        "--output", str(out),
    ])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data["optimization_notes"]["platform"] == "youtube"
    assert data["optimization_notes"]["template_ref"] == "tmpl-good"


def test_cli_publish_manifest_show(tmp_path):
    """publish-manifest show should display manifest fields."""
    from clipforge.publish_manifest import PublishManifest
    m = PublishManifest(job_name="showtest", platform="tiktok", video_path="v.mp4")
    p = tmp_path / "m.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish-manifest", "show", str(p)])
    assert result.exit_code == 0
    assert "showtest" in result.output
    assert "tiktok" in result.output


def test_cli_publish_manifest_show_optimization_notes(tmp_path):
    """publish-manifest show should render optimization notes when present."""
    from clipforge.publish_manifest import PublishManifest

    m = PublishManifest(
        job_name="showtest",
        platform="tiktok",
        video_path="v.mp4",
        extra={"optimization_notes": {"platform": "youtube", "publish_day": "Thursday"}},
    )
    p = tmp_path / "m.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish-manifest", "show", str(p)])
    assert result.exit_code == 0
    assert "Optimization notes" in result.output
    assert "Thursday" in result.output


def test_cli_publish_manifest_show_json(tmp_path):
    """publish-manifest show --json should output raw JSON."""
    import json

    from clipforge.publish_manifest import PublishManifest
    m = PublishManifest(job_name="jsontest", video_path="v.mp4")
    p = tmp_path / "m.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish-manifest", "show", "--json", str(p)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["job_name"] == "jsontest"


def test_cli_publish_manifest_validate_valid(tmp_path):
    """publish-manifest validate should exit 0 for a valid manifest."""
    from clipforge.publish_manifest import PublishManifest
    m = PublishManifest(job_name="valid", platform="reels", video_path="v.mp4")
    p = tmp_path / "m.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish-manifest", "validate", str(p)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_publish_manifest_validate_invalid(tmp_path):
    """publish-manifest validate should exit nonzero for an invalid manifest."""
    from clipforge.publish_manifest import PublishManifest
    # no video_path, bad platform
    m = PublishManifest(platform="snapchat")
    p = tmp_path / "m.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish-manifest", "validate", str(p)])
    assert result.exit_code != 0
    assert "INVALID" in result.output


def test_cli_queue_help():
    """queue --help should list subcommands."""
    runner = CliRunner()
    result = runner.invoke(main, ["queue", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "add" in result.output
    assert "list" in result.output
    assert "summary" in result.output


def test_cli_queue_init(tmp_path):
    """queue init should create queue.json."""
    q_dir = tmp_path / "q"
    runner = CliRunner()
    result = runner.invoke(main, ["queue", "init", str(q_dir)])
    assert result.exit_code == 0
    assert (q_dir / "queue.json").exists()


def test_cli_queue_init_already_exists(tmp_path):
    """queue init on an existing queue should fail."""
    q_dir = tmp_path / "q"
    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    result = runner.invoke(main, ["queue", "init", str(q_dir)])
    assert result.exit_code != 0 or "already exists" in result.output


def test_cli_queue_add_and_list(tmp_path):
    """queue add then queue list should show the manifest."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    q_dir = tmp_path / "q"
    manifest_file = tmp_path / "ep1.manifest.json"

    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--job-name", "ep1",
        "--output", str(manifest_file),
    ])
    result_add = runner.invoke(main, ["queue", "add", str(q_dir), str(manifest_file)])
    assert result_add.exit_code == 0

    result_list = runner.invoke(main, ["queue", "list", str(q_dir)])
    assert result_list.exit_code == 0
    assert "ep1" in result_list.output


def test_cli_queue_summary(tmp_path):
    """queue summary should show status counts."""
    q_dir = tmp_path / "q"
    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    result = runner.invoke(main, ["queue", "summary", str(q_dir)])
    assert result.exit_code == 0
    assert "total" in result.output.lower() or "0" in result.output


def test_cli_queue_status_update(tmp_path):
    """queue status should update a manifest's status."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    q_dir = tmp_path / "q"
    manifest_file = tmp_path / "ep1.manifest.json"

    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--job-name", "ep1",
        "--output", str(manifest_file),
    ])
    runner.invoke(main, ["queue", "add", str(q_dir), str(manifest_file)])

    import json
    mid = json.loads(manifest_file.read_text())["manifest_id"]
    result = runner.invoke(main, ["queue", "status", str(q_dir), mid, "ready"])
    assert result.exit_code == 0
    assert "ready" in result.output


def test_cli_export_bundle_generates_publish_manifest(tmp_path):
    """export-bundle should auto-generate a publish_manifest.json."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    out_dir = tmp_path / "bundle"
    runner = CliRunner()
    result = runner.invoke(main, [
        "export-bundle",
        "--video-file", str(video),
        "--output-dir", str(out_dir),
    ])
    assert result.exit_code == 0
    assert (out_dir / "publish_manifest.json").exists()
    import json
    data = json.loads((out_dir / "publish_manifest.json").read_text())
    assert "manifest_id" in data
    assert data["status"] == "draft"


def test_cli_v4_subcommand_modules_importable():
    """V4 command modules must be importable and expose Click objects."""
    import click
    for module_name in ("publish_manifest", "queue"):
        module = importlib.import_module(f"clipforge.commands.{module_name}")
        has_click_command = any(
            isinstance(getattr(module, attr), (click.Command, click.Group))
            for attr in dir(module)
            if not attr.startswith("_")
        )
        assert has_click_command, f"clipforge.commands.{module_name} exposes no Click command/group"


# ---------------------------------------------------------------------------
# V5 — publish commands, queue execute, publish config
# ---------------------------------------------------------------------------


def test_cli_publish_help():
    """publish --help should list subcommands."""
    runner = CliRunner()
    result = runner.invoke(main, ["publish", "--help"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert "execute" in result.output
    assert "validate" in result.output
    assert "retry" in result.output


def test_cli_publish_validate_valid(tmp_path):
    """publish validate should exit 0 for a valid manifest."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    manifest_file = tmp_path / "m.json"
    runner = CliRunner()
    runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--platform", "reels",
        "--title", "Test Title",
        "--caption", "Test caption for reels video.",
        "--output", str(manifest_file),
    ])
    result = runner.invoke(main, ["publish", "validate", str(manifest_file)])
    assert result.exit_code == 0, f"publish validate failed: {result.output}"
    assert "OK" in result.output


def test_cli_publish_validate_invalid(tmp_path):
    """publish validate exits nonzero for a bad manifest."""
    from clipforge.publish_manifest import PublishManifest
    m = PublishManifest(platform="snapchat")  # no video, bad platform
    p = tmp_path / "bad.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish", "validate", str(p)])
    assert result.exit_code != 0


def test_cli_publish_dry_run_manual(tmp_path):
    """publish dry-run with manual provider should succeed and show summary."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    manifest_file = tmp_path / "m.json"
    runner = CliRunner()
    runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--platform", "reels",
        "--job-name", "drytest",
        "--title", "Dry Run Test",
        "--caption", "Caption for the dry run test.",
        "--output", str(manifest_file),
    ])
    result = runner.invoke(main, [
        "publish", "dry-run", str(manifest_file),
        "--provider", "manual",
    ])
    assert result.exit_code == 0, f"dry-run failed: {result.output}"
    assert "manual" in result.output.lower()


def test_cli_publish_dry_run_missing_manifest(tmp_path):
    """publish dry-run should fail gracefully for missing file."""
    runner = CliRunner()
    result = runner.invoke(main, ["publish", "dry-run", str(tmp_path / "none.json")])
    assert result.exit_code != 0


def test_cli_publish_execute_manual_sets_status(tmp_path):
    """publish execute via manual provider marks manifest as manual_action_required."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    manifest_file = tmp_path / "m.json"
    runner = CliRunner()
    runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--platform", "reels",
        "--title", "Execute Test",
        "--caption", "Caption for execute test.",
        "--status", "ready",
        "--output", str(manifest_file),
    ])
    result = runner.invoke(main, [
        "publish", "execute", str(manifest_file),
        "--provider", "manual",
        "--yes",
    ])
    assert result.exit_code == 0
    assert "manual_action_required" in result.output

    import json
    data = json.loads(manifest_file.read_text())
    assert len(data["publish_attempts"]) == 1
    assert data["publish_attempts"][0]["manual_action_required"] is True


def test_cli_publish_execute_wrong_status_fails(tmp_path):
    """publish execute should reject manifests not in ready/scheduled/pending."""
    from clipforge.publish_manifest import PublishManifest
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    m = PublishManifest(video_path=str(video), platform="reels", status="draft")
    p = tmp_path / "m.json"
    m.save(p)
    runner = CliRunner()
    result = runner.invoke(main, ["publish", "execute", str(p), "--yes"])
    assert result.exit_code != 0
    assert "draft" in result.output or "draft" in (result.output + result.exception.__str__() if result.exception else result.output)


def test_cli_publish_execute_updates_queue(tmp_path):
    """publish execute --queue-dir should update the queue item status."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    manifest_file = tmp_path / "m.json"
    q_dir = tmp_path / "q"

    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    runner.invoke(main, [
        "publish-manifest", "create",
        "--video-file", str(video),
        "--platform", "reels",
        "--title", "Queue Update Test",
        "--caption", "Test caption.",
        "--status", "ready",
        "--output", str(manifest_file),
    ])
    runner.invoke(main, ["queue", "add", str(q_dir), str(manifest_file)])

    result = runner.invoke(main, [
        "publish", "execute", str(manifest_file),
        "--provider", "manual",
        "--queue-dir", str(q_dir),
        "--yes",
    ])
    assert result.exit_code == 0

    # Queue item should now be manual_action_required
    from clipforge.publish_queue import PublishQueue
    q = PublishQueue.load(q_dir)
    items = q.filter_by_status("manual_action_required")
    assert len(items) == 1


def test_cli_queue_execute_dry_run(tmp_path):
    """queue execute --dry-run should validate all ready items without publishing."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake")
    q_dir = tmp_path / "q"
    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])

    for i in range(2):
        mf = tmp_path / f"ep{i}.manifest.json"
        runner.invoke(main, [
            "publish-manifest", "create",
            "--video-file", str(video),
            "--platform", "reels",
            "--job-name", f"ep{i}",
            "--title", f"Episode {i}",
            "--caption", "Test caption.",
            "--status", "ready",
            "--output", str(mf),
        ])
        runner.invoke(main, ["queue", "add", str(q_dir), str(mf)])

    result = runner.invoke(main, ["queue", "execute", str(q_dir), "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output.lower() or "OK" in result.output


def test_cli_queue_execute_nothing_to_do(tmp_path):
    """queue execute on an empty queue should exit cleanly."""
    q_dir = tmp_path / "q"
    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    result = runner.invoke(main, ["queue", "execute", str(q_dir)])
    assert result.exit_code == 0
    assert "Nothing to do" in result.output or "0" in result.output


def test_cli_queue_retry_failed_no_failures(tmp_path):
    """queue retry-failed with no failed items should exit cleanly."""
    q_dir = tmp_path / "q"
    runner = CliRunner()
    runner.invoke(main, ["queue", "init", str(q_dir)])
    result = runner.invoke(main, ["queue", "retry-failed", str(q_dir), "--yes"])
    assert result.exit_code == 0
    assert "No failed items" in result.output


def test_cli_v5_publish_module_importable():
    """V5 publish module must be importable and expose a Click group."""
    import click
    module = importlib.import_module("clipforge.commands.publish")
    has_click = any(
        isinstance(getattr(module, attr), (click.Command, click.Group))
        for attr in dir(module) if not attr.startswith("_")
    )
    assert has_click, "clipforge.commands.publish exposes no Click command/group"


# ── V6 Analytics CLI tests ─────────────────────────────────────────────────────────


def test_cli_v6_analytics_module_importable():
    """V6 analytics module must be importable and expose a Click group."""
    import click
    module = importlib.import_module("clipforge.commands.analytics")
    has_click = any(
        isinstance(getattr(module, attr), (click.Command, click.Group))
        for attr in dir(module) if not attr.startswith("_")
    )
    assert has_click, "clipforge.commands.analytics exposes no Click command/group"


def test_cli_analytics_help():
    runner = CliRunner()
    result = runner.invoke(main, ["analytics", "--help"])
    assert result.exit_code == 0
    assert "analytics" in result.output.lower()


def test_cli_analytics_fetch_requires_args():
    """analytics fetch without manifest or --queue should exit non-zero."""
    runner = CliRunner()
    result = runner.invoke(main, ["analytics", "fetch"])
    assert result.exit_code != 0


def test_cli_analytics_fetch_manifest_not_found(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "fetch", str(tmp_path / "missing.json"),
        "--store", str(tmp_path / "store"),
    ])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def _make_test_manifest(tmp_path, platform="youtube"):
    """Create a minimal manifest JSON for analytics tests."""
    import json
    import uuid
    m = {
        "manifest_id": str(uuid.uuid4()),
        "job_name": "test-job",
        "platform": platform,
        "video_path": "output/video.mp4",
        "status": "published",
        "publish_at": "2024-01-01T00:00:00+00:00",
        "campaign_name": "Q1",
        "template_ref": "tmpl-a",
        "profile_ref": "",
        "publish_attempts": [
            {
                "post_id": "vid-123",
                "post_url": "https://yt.com/watch?v=vid-123",
                "published_at": "2024-01-01T12:00:00+00:00",
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(m, indent=2), encoding="utf-8")
    return path, m["manifest_id"]


def test_cli_analytics_fetch_stub_tiktok(tmp_path):
    """Fetching analytics for tiktok saves a stub record."""
    mpath, _ = _make_test_manifest(tmp_path, platform="tiktok")
    store_dir = tmp_path / "store"
    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "fetch", str(mpath),
        "--store", str(store_dir),
    ])
    assert result.exit_code == 0
    assert store_dir.exists()
    assert any(store_dir.glob("*.json"))


def test_cli_analytics_fetch_force_refetches(tmp_path):
    """--force re-fetches even if a record already exists."""
    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    mpath, manifest_id = _make_test_manifest(tmp_path, platform="tiktok")
    store_dir = tmp_path / "store"

    # Pre-populate with a stub (data_source != "api" so would normally be skipped)
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(
        manifest_id=manifest_id,
        platform="tiktok",
        data_source="api",  # mark as real to trigger skip logic
    ))

    runner = CliRunner()
    result_no_force = runner.invoke(main, [
        "analytics", "fetch", str(mpath), "--store", str(store_dir),
    ])
    assert "Skipping" in result_no_force.output

    result_force = runner.invoke(main, [
        "analytics", "fetch", str(mpath), "--store", str(store_dir), "--force",
    ])
    assert "Skipping" not in result_force.output


def test_cli_analytics_show_no_records(tmp_path):
    """analytics show with no stored records prints helpful message."""
    mpath, _ = _make_test_manifest(tmp_path)
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "show", str(mpath),
        "--store", str(store_dir),
    ])
    assert result.exit_code == 0
    assert "No analytics" in result.output


def test_cli_analytics_show_with_record(tmp_path):
    """analytics show displays stored record metrics."""
    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    mpath, manifest_id = _make_test_manifest(tmp_path)
    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(
        manifest_id=manifest_id,
        platform="youtube",
        views=9876,
        likes=100,
        data_source="api",
    ))

    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "show", str(mpath),
        "--store", str(store_dir),
    ])
    assert result.exit_code == 0
    assert "9,876" in result.output or "9876" in result.output


def test_cli_analytics_show_json(tmp_path):
    import json

    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    mpath, manifest_id = _make_test_manifest(tmp_path)
    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(manifest_id=manifest_id, platform="youtube", views=42))

    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "show", str(mpath),
        "--store", str(store_dir), "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["views"] == 42


def test_cli_analytics_summary_empty_store(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["analytics", "summary", "--store", str(store_dir)])
    assert result.exit_code == 0
    assert "No analytics records" in result.output


def test_cli_analytics_summary_with_records(tmp_path):
    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(platform="youtube", views=500, likes=25))
    store.save(ContentAnalytics(platform="youtube", views=1000, likes=50))

    runner = CliRunner()
    result = runner.invoke(main, ["analytics", "summary", "--store", str(store_dir)])
    assert result.exit_code == 0
    assert "2" in result.output  # record count
    assert "1,500" in result.output or "1500" in result.output  # total views


def test_cli_analytics_summary_platform_filter(tmp_path):
    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(platform="youtube", views=1000))
    store.save(ContentAnalytics(platform="tiktok", views=500))

    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "summary", "--store", str(store_dir), "--platform", "youtube",
    ])
    assert result.exit_code == 0
    # Only youtube record should be in summary
    assert "1,000" in result.output or "1000" in result.output


def test_cli_analytics_compare_empty_store(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "compare", "--store", str(store_dir), "--by", "platform",
    ])
    assert result.exit_code == 0
    assert "No analytics records" in result.output


def test_cli_analytics_compare_by_platform(tmp_path):
    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(platform="youtube", views=1000))
    store.save(ContentAnalytics(platform="tiktok", views=200))

    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "compare", "--store", str(store_dir), "--by", "platform",
    ])
    assert result.exit_code == 0
    assert "youtube" in result.output
    assert "tiktok" in result.output


def test_cli_analytics_compare_json(tmp_path):
    import json

    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    store.save(ContentAnalytics(platform="youtube", campaign_name="Q1"))

    runner = CliRunner()
    result = runner.invoke(main, [
        "analytics", "compare", "--store", str(store_dir), "--by", "campaign", "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "Q1" in data


# ── V7 Optimize CLI tests ──────────────────────────────────────────────────────


def test_cli_v7_optimize_module_importable():
    """V7 optimize module must be importable and expose a Click group."""
    import click
    module = importlib.import_module("clipforge.commands.optimize")
    has_click = any(
        isinstance(getattr(module, attr), (click.Command, click.Group))
        for attr in dir(module) if not attr.startswith("_")
    )
    assert has_click, "clipforge.commands.optimize exposes no Click command/group"


def test_cli_optimize_help():
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "--help"])
    assert result.exit_code == 0
    assert "optimize" in result.output.lower()


def test_cli_optimize_report_empty_store(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "report", "--store", str(store_dir)])
    assert result.exit_code == 0
    assert "No analytics records" in result.output


def test_cli_optimize_simulate_empty_store(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "simulate", "--store", str(store_dir)])
    assert result.exit_code == 0
    assert "No analytics records" in result.output


def _make_analytics_store(tmp_path, n=8, platform="youtube", ctr=3.0, engagement_rate=5.0):
    """Populate a store with n records for CLI tests."""
    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore

    store_dir = tmp_path / "store"
    store = AnalyticsStore(store_dir)
    for i in range(n):
        store.save(ContentAnalytics(
            platform=platform,
            views=1000 + i * 100,
            likes=50,
            comments=10,
            shares=5,
            ctr=ctr,
            retention_pct=50.0,
            engagement_rate=engagement_rate,
            template_ref="tmpl-a",
            campaign_name="Q1",
            data_source="api",
            published_at=f"2024-0{(i % 6) + 1}-{(i % 28) + 1:02d}T12:00:00+00:00",
            fetched_at=f"2024-0{(i % 6) + 1}-{(i % 28) + 2:02d}T10:00:00+00:00",
        ))
    return store_dir


def test_cli_optimize_report_with_records(tmp_path):
    store_dir = _make_analytics_store(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "report", "--store", str(store_dir)])
    assert result.exit_code == 0
    assert "records" in result.output.lower()
    assert "Next video brief:" in result.output
    assert "Checklist:" in result.output


def test_cli_optimize_report_json(tmp_path):
    store_dir = _make_analytics_store(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "report", "--store", str(store_dir), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "source_records" in data
    assert "recommendations" in data
    assert "trend" in data
    assert "next_video_brief" in data
    assert "action_checklist" in data["next_video_brief"]


def test_cli_optimize_report_low_ctr_produces_recs(tmp_path):
    """Low CTR should trigger at least one recommendation."""
    store_dir = _make_analytics_store(tmp_path, ctr=0.4, n=6)
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "report", "--store", str(store_dir), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    ctr_recs = [r for r in data["recommendations"] if r["category"] == "ctr"]
    assert len(ctr_recs) >= 1


def test_cli_optimize_report_platform_filter(tmp_path):
    store_dir = _make_analytics_store(tmp_path, platform="tiktok", n=6)
    runner = CliRunner()
    result = runner.invoke(main, [
        "optimize", "report", "--store", str(store_dir),
        "--platform", "tiktok", "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["filters_applied"].get("platform") == "tiktok"


def test_cli_optimize_report_last_n_filter(tmp_path):
    store_dir = _make_analytics_store(tmp_path, n=10)
    runner = CliRunner()
    result = runner.invoke(main, [
        "optimize", "report", "--store", str(store_dir),
        "--last-n", "4", "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["source_records"] == 4


def test_cli_optimize_report_saves_output_file(tmp_path):
    store_dir = _make_analytics_store(tmp_path)
    output_file = tmp_path / "notes.json"
    runner = CliRunner()
    result = runner.invoke(main, [
        "optimize", "report", "--store", str(store_dir),
        "--output", str(output_file),
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert "recommendations" in data


def test_cli_optimize_apply_saves_file(tmp_path):
    store_dir = _make_analytics_store(tmp_path)
    output_file = tmp_path / "opt_notes.json"
    runner = CliRunner()
    result = runner.invoke(main, [
        "optimize", "apply",
        "--store", str(store_dir),
        "--output", str(output_file),
        "--yes",
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert "report_id" in data


def test_cli_optimize_apply_empty_store_exits_cleanly(tmp_path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    output_file = tmp_path / "notes.json"
    runner = CliRunner()
    result = runner.invoke(main, [
        "optimize", "apply",
        "--store", str(store_dir),
        "--output", str(output_file),
        "--yes",
    ])
    assert result.exit_code == 0
    assert not output_file.exists()


def test_cli_optimize_simulate_no_file_written(tmp_path):
    store_dir = _make_analytics_store(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["optimize", "simulate", "--store", str(store_dir)])
    assert result.exit_code == 0
    # simulate never writes files
    assert not any(tmp_path.glob("*.json")) or all(
        f.parent == store_dir for f in tmp_path.rglob("*.json")
    )
