"""ClipForge CLI entry point.

All commands are registered here using Click groups.
"""

from __future__ import annotations

import click

from clipforge.commands.make import make
from clipforge.commands.scenes import scenes
from clipforge.commands.doctor import doctor
from clipforge.commands.presets import presets_cmd
from clipforge.commands.wizard import wizard
from clipforge.commands.init_config import init_config
from clipforge.commands.init_batch import init_batch
from clipforge.commands.batch import batch
from clipforge.commands.social_pack import social_pack
from clipforge.commands.export_bundle import export_bundle
from clipforge.commands.init_profile import init_profile
from clipforge.commands.thumbnail import thumbnail
from clipforge.commands.studio import studio


@click.group()
@click.version_option(package_name="clipforge")
def main() -> None:
    """ClipForge — turn text scripts into short videos for Reels, TikTok, and Shorts."""


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


if __name__ == "__main__":
    main()
