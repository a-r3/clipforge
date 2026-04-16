"""project command — manage ClipForge project folders."""

from __future__ import annotations

import sys

import click


@click.group("project")
def project_cmd() -> None:
    """Manage ClipForge project folders.

    A project keeps scripts, config, profile, output, and assets together
    in one place. Set project-level defaults once, reuse across builds.

    Examples:

      clipforge project init --name TechBrief --platform reels
      clipforge project info --path ./techbrief
      clipforge project build --path ./techbrief --script-file scripts/ep1.txt
    """


@project_cmd.command("init")
@click.option("--path", "-p", default=".", show_default=True,
              help="Where to create the project folder.")
@click.option("--name", "-n", default="",
              help="Project name. Defaults to the folder name.")
@click.option("--platform", default="reels",
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Default platform for this project.")
@click.option("--style", default=None,
              type=click.Choice(["clean", "bold", "minimal", "cinematic"]),
              help="Default style. Auto-selected from platform if omitted.")
@click.option("--brand-name", "-b", default="",
              help="Brand name for this project.")
def project_init(path: str, name: str, platform: str, style: str | None, brand_name: str) -> None:
    """Create a new ClipForge project folder.

    Sets up the project structure and writes a project.json with your defaults.

    Example:

      clipforge project init --path ./my-channel --name MyChannel --platform reels
    """
    from clipforge.project import ClipForgeProject

    resolved_style = style or ("bold" if platform in ("reels", "tiktok") else "clean")

    try:
        project = ClipForgeProject.init(
            path=path,
            name=name,
            platform=platform,
            style=resolved_style,
            brand_name=brand_name,
        )
        project.save()
    except Exception as exc:
        click.echo(f"  Error creating project: {exc}", err=True)
        sys.exit(1)

    click.echo()
    click.echo(f"  Project created: {project.path}")
    click.echo(f"  Name    : {project.name}")
    click.echo(f"  Platform: {project.platform}  style={project.style}")
    if brand_name:
        click.echo(f"  Brand   : {brand_name}")
    click.echo()
    click.echo("  Folder structure:")
    click.echo(f"    {project.path}/scripts/   ← put your .txt scripts here")
    click.echo(f"    {project.path}/output/    ← rendered videos land here")
    click.echo(f"    {project.path}/assets/    ← music, logo, stock cache")
    click.echo(f"    {project.path}/project.json")
    click.echo()
    click.echo("  Next:")
    click.echo(f"    Add a script:  cp myscript.txt {project.path}/scripts/")
    click.echo(f"    Build:         clipforge project build --path {project.path}")
    click.echo()


@project_cmd.command("info")
@click.option("--path", "-p", default=".", show_default=True,
              help="Path to the project folder.")
def project_info(path: str) -> None:
    """Show project metadata and contents.

    Example:

      clipforge project info --path ./my-channel
    """
    from clipforge.project import ClipForgeProject

    try:
        project = ClipForgeProject.load(path)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    scripts = project.list_scripts()
    outputs = list(project.output_dir().glob("*.mp4")) if project.output_dir().exists() else []

    click.echo()
    click.echo(f"  Project: {project.name}")
    click.echo("  " + "─" * 40)
    click.echo(f"  Path     : {project.path}")
    click.echo(f"  Platform : {project.platform}  style={project.style}")
    if project.brand_name:
        click.echo(f"  Brand    : {project.brand_name}")
    click.echo(f"  Created  : {project.created_at[:10]}")
    click.echo(f"  Updated  : {project.updated_at[:10]}")
    click.echo()
    click.echo(f"  Scripts  : {len(scripts)} file(s)")
    for s in scripts[:5]:
        click.echo(f"    {s.name}")
    if len(scripts) > 5:
        click.echo(f"    ... and {len(scripts) - 5} more")
    click.echo()
    click.echo(f"  Outputs  : {len(outputs)} video(s)")
    for o in outputs[:5]:
        size_kb = o.stat().st_size // 1024 if o.exists() else 0
        click.echo(f"    {o.name}  ({size_kb} KB)")
    if len(outputs) > 5:
        click.echo(f"    ... and {len(outputs) - 5} more")
    click.echo()


@project_cmd.command("build")
@click.option("--path", "-p", default=".", show_default=True,
              help="Path to the project folder.")
@click.option("--script-file", "-s", default=None,
              help="Script to build. Relative paths are resolved from project/scripts/.")
@click.option("--output", "-o", default=None,
              help="Output video path. Defaults to project/output/<script-name>.mp4")
@click.option("--platform", default=None,
              type=click.Choice(["reels", "tiktok", "youtube-shorts", "youtube", "landscape"]),
              help="Override platform (default: project default).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview the plan without rendering.")
def project_build(
    path: str,
    script_file: str | None,
    output: str | None,
    platform: str | None,
    dry_run: bool,
) -> None:
    """Build a video from a project's script.

    If --script-file is not given and the project has exactly one script,
    it is used automatically.

    Example:

      clipforge project build --path ./my-channel --script-file ep1.txt
    """
    import os
    from pathlib import Path as P

    from clipforge.project import ClipForgeProject

    try:
        project = ClipForgeProject.load(path)
    except FileNotFoundError as exc:
        click.echo(f"  Error: {exc}", err=True)
        sys.exit(1)

    # Resolve script file
    resolved_script: str | None = script_file
    if resolved_script is None:
        scripts = project.list_scripts()
        if len(scripts) == 1:
            resolved_script = str(scripts[0])
            click.echo(f"  Auto-selected script: {scripts[0].name}")
        elif len(scripts) == 0:
            click.echo(
                f"  Error: No scripts found in {project.scripts_dir()}.\n"
                f"  Add a .txt file there, or pass --script-file.",
                err=True,
            )
            sys.exit(1)
        else:
            click.echo("  Multiple scripts found. Specify one with --script-file:")
            for s in scripts:
                click.echo(f"    {s.name}")
            sys.exit(1)
    else:
        # Resolve relative to project/scripts/ if not absolute
        sp = P(resolved_script)
        if not sp.is_absolute() and not sp.exists():
            candidate = project.scripts_dir() / sp
            if candidate.exists():
                resolved_script = str(candidate)

    if not os.path.exists(resolved_script):
        click.echo(f"  Error: Script not found: {resolved_script}", err=True)
        sys.exit(1)

    # Build output path
    if output is None:
        stem = P(resolved_script).stem
        output = str(project.output_dir() / f"{stem}.mp4")
        project.output_dir().mkdir(parents=True, exist_ok=True)

    overrides: dict = {"script_file": resolved_script, "output": output}
    if platform:
        overrides["platform"] = platform

    config = project.build_config(overrides=overrides)

    # Hand off to the make pipeline
    from clipforge.ai.factory import AIFactory
    from clipforge.commands.make import _echo_selected_settings, _print_dry_run
    from clipforge.scene_planner import ScenePlanner
    from clipforge.script_parser import ScriptParser

    click.echo()
    click.echo(f"  Project : {project.name}")

    with open(resolved_script, encoding="utf-8") as f:
        script_text = f.read()

    parser = ScriptParser(max_scenes=config.get("max_scenes", 15))
    scenes = parser.parse(script_text)
    scene_dicts = [s.to_dict() for s in scenes]

    _echo_selected_settings(config)
    click.echo(f"  Scenes parsed  : {len(scenes)}")

    ai_provider = AIFactory.from_config(config)
    planner = ScenePlanner(ai_mode=config.get("ai_mode", "off"), ai_provider=ai_provider)
    planned = planner.plan(scene_dicts)

    if dry_run:
        _print_dry_run(planned, config)
        return

    click.echo(f"\n  Rendering → {output}")
    try:
        from clipforge.builder import VideoBuilder
        builder = VideoBuilder()
        summary = builder.build(planned, config, output)
        summary.print()
    except Exception as exc:
        click.echo(f"\n  Error: {exc}", err=True)
        sys.exit(1)
