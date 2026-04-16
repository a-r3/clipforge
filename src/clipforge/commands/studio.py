"""studio command — interactive TUI using rich."""

from __future__ import annotations

from pathlib import Path

import click


def _read_manifest_id(path: str) -> str:
    """Read the manifest_id from a manifest JSON file, or return empty string."""
    try:
        import json
        return json.loads(Path(path).read_text(encoding="utf-8")).get("manifest_id", "")
    except Exception:
        return ""


def _invoke(args: list[str]) -> int:
    """Invoke a clipforge sub-command in-process and return exit code."""
    from click.testing import CliRunner

    from clipforge.cli import main
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, args, catch_exceptions=False)
    if result.output:
        click.echo(result.output, nl=False)
    return result.exit_code


@click.command("studio")
def studio() -> None:
    """Launch the ClipForge interactive studio (TUI).

    An interactive workspace for common tasks: build videos, generate
    social packs, preview scene plans, and run system checks — all
    without memorising CLI flags.
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm, Prompt
        from rich.table import Table

        console = Console()
        _studio_rich(console, Panel, Table, Prompt, Confirm)

    except ImportError:
        _studio_plain()


# ---------------------------------------------------------------------------
# Rich TUI
# ---------------------------------------------------------------------------

def _studio_rich(console, Panel, Table, Prompt, Confirm) -> None:  # noqa: N803
    """Full rich-powered interactive studio."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]ClipForge Studio[/bold cyan]\n"
        "[dim]Interactive workspace — no flags needed[/dim]",
        border_style="cyan",
    ))

    while True:
        console.print()
        table = Table(title="", show_header=False, box=None, padding=(0, 2))
        table.add_row("[bold cyan][1][/bold cyan]", "Build a video")
        table.add_row("[bold cyan][2][/bold cyan]", "Preview scene breakdown")
        table.add_row("[bold cyan][3][/bold cyan]", "Generate social pack")
        table.add_row("[bold cyan][4][/bold cyan]", "Create thumbnail")
        table.add_row("[bold cyan][5][/bold cyan]", "List presets")
        table.add_row("[bold cyan][6][/bold cyan]", "List templates")
        table.add_row("[bold cyan][7][/bold cyan]", "Run doctor check")
        table.add_row("[bold cyan][8][/bold cyan]", "Publish prep (manifest + queue)")
        table.add_row("[bold cyan][9][/bold cyan]", "Analytics summary")
        table.add_row("[bold cyan][0][/bold cyan]", "Optimize — content recommendations")
        table.add_row("[bold cyan][q][/bold cyan]", "Quit")
        console.print(table)

        choice = Prompt.ask(
            "\n  Choice",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "q"],
            show_choices=False,
        )
        console.print()

        if choice == "q":
            console.print("[dim]  Goodbye![/dim]")
            break

        elif choice == "1":
            _studio_build(console, Prompt, Confirm)

        elif choice == "2":
            script = Prompt.ask("  Script file path")
            _invoke(["scenes", "--script-file", script])

        elif choice == "3":
            _studio_social_pack(console, Prompt)

        elif choice == "4":
            _studio_thumbnail(console, Prompt)

        elif choice == "5":
            _invoke(["presets"])

        elif choice == "6":
            _invoke(["templates", "list"])

        elif choice == "7":
            _invoke(["doctor"])

        elif choice == "8":
            _studio_publish_prep(console, Prompt, Confirm)

        elif choice == "9":
            _studio_analytics(console, Prompt)

        elif choice == "0":
            _studio_optimize(console, Prompt)


def _studio_build(console, Prompt, Confirm) -> None:
    """Studio sub-flow: build a video with a preview-before-render step."""
    console.print("  [bold]Build a video[/bold]\n")

    # Script file — offer to list available scripts
    script = Prompt.ask("  Script file path", default="examples/script_example.txt")
    if not Path(script).exists():
        console.print(f"  [red]File not found:[/red] {script}")
        return

    platform = Prompt.ask(
        "  Platform",
        choices=["reels", "tiktok", "youtube-shorts", "youtube", "landscape"],
        default="reels",
    )
    output = Prompt.ask("  Output video path", default="output/video.mp4")

    # Optional settings
    style = Prompt.ask(
        "  Style",
        choices=["clean", "bold", "minimal", "cinematic"],
        default="bold" if platform in ("reels", "tiktok") else "clean",
    )
    audio = Prompt.ask(
        "  Audio mode",
        choices=["silent", "music", "voiceover", "voiceover+music"],
        default="silent",
    )
    optimization_report = Prompt.ask(
        "  Optimization report path (optional)",
        default="",
    )

    # Dry-run preview first
    console.print("\n  [dim]Previewing scene plan...[/dim]")
    cmd = [
        "make", "--script-file", script,
        "--platform", platform,
        "--style", style,
        "--audio-mode", audio,
        "--output", output,
        "--dry-run",
    ]
    if optimization_report:
        cmd += ["--optimization-report", optimization_report]
    rc = _invoke(cmd)
    if rc != 0:
        console.print("  [red]Preview failed. Check your script file.[/red]")
        return

    console.print()
    confirmed = Confirm.ask("  Render this video?", default=False)
    if not confirmed:
        console.print("  [dim]Cancelled.[/dim]")
        return

    console.print("\n  [bold]Rendering...[/bold]")
    cmd = [
        "make", "--script-file", script,
        "--platform", platform,
        "--style", style,
        "--audio-mode", audio,
        "--output", output,
    ]
    if optimization_report:
        cmd += ["--optimization-report", optimization_report]
    _invoke(cmd)


def _studio_social_pack(console, Prompt) -> None:
    """Studio sub-flow: generate a social pack."""
    console.print("  [bold]Generate social pack[/bold]\n")
    script = Prompt.ask("  Script file path", default="examples/script_example.txt")
    if not Path(script).exists():
        console.print(f"  [red]File not found:[/red] {script}")
        return
    platform = Prompt.ask(
        "  Platform",
        choices=["reels", "tiktok", "youtube-shorts", "youtube"],
        default="reels",
    )
    brand = Prompt.ask("  Brand name (optional)", default="")
    optimization_report = Prompt.ask("  Optimization report path (optional)", default="")
    cmd = ["social-pack", "--script-file", script, "--platform", platform]
    if brand:
        cmd += ["--brand-name", brand]
    if optimization_report:
        cmd += ["--optimization-report", optimization_report]
    _invoke(cmd)


def _studio_thumbnail(console, Prompt) -> None:
    """Studio sub-flow: create a thumbnail."""
    console.print("  [bold]Create thumbnail[/bold]\n")
    text = Prompt.ask("  Thumbnail text")
    platform = Prompt.ask(
        "  Platform",
        choices=["reels", "tiktok", "youtube-shorts", "youtube"],
        default="reels",
    )
    style = Prompt.ask(
        "  Style",
        choices=["clean", "bold", "minimal"],
        default="bold",
    )
    output = Prompt.ask("  Output path", default="output/thumb.jpg")
    _invoke(["thumbnail", "--text", text, "--platform", platform, "--style", style, "--output", output])


def _studio_publish_prep(console, Prompt, Confirm) -> None:
    """Studio sub-flow: create a manifest, validate, dry-run, and optionally publish."""
    console.print("  [bold]Publish prep[/bold]\n")
    console.print("  [dim]Prepare and optionally publish a rendered video.[/dim]\n")

    video = Prompt.ask("  Video file path", default="output/video.mp4")
    if not Path(video).exists():
        console.print(f"  [red]File not found:[/red] {video}")
        return

    platform = Prompt.ask(
        "  Platform",
        choices=["reels", "tiktok", "youtube-shorts", "youtube", "landscape"],
        default="reels",
    )
    job_name = Prompt.ask("  Job name (short label)", default=Path(video).stem)
    optimization_report = Prompt.ask("  Optimization report path (optional)", default="")
    manifest_out = Prompt.ask(
        "  Save manifest to",
        default=f"{job_name}.manifest.json",
    )

    # 1. Create manifest
    cmd = [
        "publish-manifest", "create",
        "--video-file", video,
        "--platform", platform,
        "--job-name", job_name,
        "--output", manifest_out,
    ]
    if optimization_report:
        cmd += ["--optimization-report", optimization_report]
    rc = _invoke(cmd)
    if rc != 0:
        console.print("  [red]Manifest creation failed.[/red]")
        return

    # 2. Validate
    console.print("\n  [dim]Validating manifest...[/dim]")
    _invoke(["publish-manifest", "validate", manifest_out])

    # 3. Dry-run
    do_dry = Confirm.ask("  Run a publish dry-run?", default=True)
    if do_dry:
        _invoke(["publish", "dry-run", manifest_out])

    # 4. Add to queue
    add_to_q = Confirm.ask("  Add to a publish queue?", default=False)
    q_dir = ""
    if add_to_q:
        q_dir = Prompt.ask("  Queue directory", default="publish_queue")
        if not Path(q_dir).exists():
            create_q = Confirm.ask(
                f"  Queue '{q_dir}' does not exist. Create it?", default=True
            )
            if create_q:
                _invoke(["queue", "init", q_dir])
        _invoke(["queue", "add", q_dir, manifest_out])
        console.print()
        console.print(f"  [dim]Run 'clipforge queue summary {q_dir}' to see the queue.[/dim]")

    # 5. Optionally execute now
    if q_dir:
        do_exec = Confirm.ask("  Execute publish now?", default=False)
        if do_exec:
            _invoke(["queue", "status", q_dir, _read_manifest_id(manifest_out), "ready"])
            _invoke(["publish", "execute", manifest_out,
                     "--queue-dir", q_dir, "--yes"])


def _studio_optimize(console, Prompt) -> None:
    """Studio sub-flow: show optimization recommendations."""
    console.print("  [bold]Content optimization recommendations[/bold]\n")

    store_dir = Prompt.ask("  Analytics store directory", default="analytics_store")
    platform = Prompt.ask(
        "  Filter by platform (leave blank for all)",
        default="",
    )
    last_n_str = Prompt.ask(
        "  Use last N records (0 = all)",
        default="0",
    )
    try:
        last_n = max(0, int(last_n_str))
    except ValueError:
        last_n = 0

    cmd = ["optimize", "report", "--store", store_dir]
    if platform:
        cmd += ["--platform", platform]
    if last_n > 0:
        cmd += ["--last-n", str(last_n)]

    _invoke(cmd)
    console.print()
    console.print(
        "  [dim]Run 'clipforge optimize apply' to save recommendations to a file.[/dim]"
    )


def _studio_analytics(console, Prompt) -> None:
    """Studio sub-flow: show analytics summary for a store directory."""
    console.print("  [bold]Analytics summary[/bold]\n")

    store_dir = Prompt.ask("  Analytics store directory", default="analytics_store")
    platform = Prompt.ask(
        "  Filter by platform (leave blank for all)",
        default="",
    )
    campaign = Prompt.ask(
        "  Filter by campaign (leave blank for all)",
        default="",
    )

    cmd = ["analytics", "summary", "--store", store_dir]
    if platform:
        cmd += ["--platform", platform]
    if campaign:
        cmd += ["--campaign", campaign]

    rc = _invoke(cmd)
    if rc == 0:
        console.print()
        console.print("  [dim]Run 'clipforge analytics compare --by platform' for a full breakdown.[/dim]")


# ---------------------------------------------------------------------------
# Plain-text fallback (no rich installed)
# ---------------------------------------------------------------------------

def _studio_plain() -> None:
    """Minimal interactive menu for environments without rich."""
    click.echo("\nClipForge Studio")
    click.echo("=" * 34)
    click.echo("Available commands:\n")
    commands = [
        ("make --script-file <file>",             "Build a video"),
        ("scenes --script-file <file>",           "Preview scene breakdown"),
        ("social-pack --script-file <file>",      "Generate social content"),
        ("thumbnail --text <text>",               "Create thumbnail"),
        ("doctor",                                "Check system"),
        ("presets",                               "List style presets"),
        ("templates list",                        "List template packs"),
        ("publish-manifest create --video-file",  "Create publish manifest"),
        ("queue summary <queue_dir>",             "Inspect publish queue"),
    ]
    for cmd, desc in commands:
        click.echo(f"  clipforge {cmd:<40} {desc}")
    click.echo()
    click.echo("Run 'pip install rich' for the interactive studio.")
    click.echo()
