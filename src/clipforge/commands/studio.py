"""studio command — interactive TUI using rich."""

from __future__ import annotations

import click


@click.command("studio")
def studio() -> None:
    """Launch the ClipForge interactive studio (TUI)."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.prompt import Prompt

        console = Console()

        console.print(Panel.fit(
            "[bold cyan]ClipForge Studio[/bold cyan]\n"
            "[dim]Interactive video creation workspace[/dim]",
            border_style="cyan",
        ))

        while True:
            table = Table(title="Main Menu", show_header=False, box=None)
            table.add_row("[1]", "Create new video")
            table.add_row("[2]", "Parse script")
            table.add_row("[3]", "Generate social pack")
            table.add_row("[4]", "Generate thumbnail")
            table.add_row("[5]", "Run doctor check")
            table.add_row("[6]", "List presets")
            table.add_row("[q]", "Quit")
            console.print(table)

            choice = Prompt.ask("\nChoice", choices=["1", "2", "3", "4", "5", "6", "q"])

            if choice == "q":
                console.print("[dim]Goodbye![/dim]")
                break
            elif choice == "1":
                console.print("[yellow]Use: clipforge make --script-file <file>[/yellow]")
            elif choice == "2":
                script_file = Prompt.ask("Script file path")
                import subprocess, sys
                subprocess.run([sys.executable, "-m", "clipforge", "scenes", "--script-file", script_file])
            elif choice == "3":
                script_file = Prompt.ask("Script file path")
                platform = Prompt.ask("Platform", default="reels")
                brand = Prompt.ask("Brand name", default="")
                import subprocess, sys
                cmd = [sys.executable, "-m", "clipforge", "social-pack",
                       "--script-file", script_file, "--platform", platform]
                if brand:
                    cmd += ["--brand-name", brand]
                subprocess.run(cmd)
            elif choice == "4":
                text = Prompt.ask("Thumbnail text")
                import subprocess, sys
                subprocess.run([sys.executable, "-m", "clipforge", "thumbnail", "--text", text])
            elif choice == "5":
                import subprocess, sys
                subprocess.run([sys.executable, "-m", "clipforge", "doctor"])
            elif choice == "6":
                import subprocess, sys
                subprocess.run([sys.executable, "-m", "clipforge", "presets"])

    except ImportError:
        # Fallback plain-text menu if rich is not available
        click.echo("ClipForge Studio")
        click.echo("=" * 30)
        click.echo("Available commands:")
        click.echo("  clipforge make --script-file <file>")
        click.echo("  clipforge scenes --script-file <file>")
        click.echo("  clipforge social-pack --script-file <file>")
        click.echo("  clipforge thumbnail --text <text>")
        click.echo("  clipforge doctor")
        click.echo("  clipforge presets")
