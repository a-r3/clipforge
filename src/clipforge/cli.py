"""ClipForge CLI entry point.

All commands are registered here using Click groups.
"""

from __future__ import annotations

import click

from clipforge import __version__
from clipforge.commands.analytics import analytics_cmd
from clipforge.commands.batch import batch
from clipforge.commands.doctor import doctor
from clipforge.commands.export_bundle import export_bundle
from clipforge.commands.init_batch import init_batch
from clipforge.commands.init_config import init_config
from clipforge.commands.init_profile import init_profile
from clipforge.commands.make import make
from clipforge.commands.optimize import optimize_cmd
from clipforge.commands.presets import presets_cmd
from clipforge.commands.project import project_cmd
from clipforge.commands.publish import publish_cmd
from clipforge.commands.publish_manifest import publish_manifest_cmd
from clipforge.commands.queue import queue_cmd
from clipforge.commands.scenes import scenes
from clipforge.commands.social_pack import social_pack
from clipforge.commands.studio import studio
from clipforge.commands.templates import templates_cmd
from clipforge.commands.thumbnail import thumbnail
from clipforge.commands.wizard import wizard


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """ClipForge — turn text scripts into short videos for Reels, TikTok, and Shorts.

    \b
    Quick start:
      clipforge doctor                          # check your setup
      clipforge wizard                          # create a config interactively
      clipforge make --script-file script.txt   # build a video

    \b
    Preview before rendering:
      clipforge scenes --script-file script.txt
      clipforge make --script-file script.txt --dry-run

    \b
    Common commands:
      make               Build a video from a script
      scenes             Preview scene breakdown
      social-pack        Generate title, caption, and hashtags
      thumbnail          Create a thumbnail image
      wizard             Guided config builder
      doctor             Check system requirements
      presets            List available style presets
      templates          Content template packs (business, AI, motivation...)
      project            Manage reusable project folders
      studio             Interactive TUI workspace
      publish-manifest   Create and validate publish manifests
      queue              Manage local publish queues
      publish            Execute publish jobs (dry-run, execute, retry)
      analytics          Fetch and analyse content performance metrics
      optimize           Data-driven recommendations for next video

    Run any command with --help for details and examples.
    """


main.add_command(make)
main.add_command(scenes)
main.add_command(doctor)
main.add_command(presets_cmd, name="presets")
main.add_command(wizard)
main.add_command(init_config, name="init-config")
main.add_command(init_batch, name="init-batch")
main.add_command(batch)
main.add_command(social_pack, name="social-pack")
main.add_command(export_bundle, name="export-bundle")
main.add_command(init_profile, name="init-profile")
main.add_command(thumbnail)
main.add_command(studio)
main.add_command(templates_cmd, name="templates")
main.add_command(project_cmd, name="project")
main.add_command(publish_manifest_cmd, name="publish-manifest")
main.add_command(queue_cmd, name="queue")
main.add_command(publish_cmd, name="publish")
main.add_command(analytics_cmd, name="analytics")
main.add_command(optimize_cmd, name="optimize")


if __name__ == "__main__":
    main()
