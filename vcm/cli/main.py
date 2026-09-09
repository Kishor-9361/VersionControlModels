"""VCM CLI Entrypoint."""

import click
from vcm import __version__
from vcm.cli.commands import (
    init_cmd,
    train_cmd,
    models_cmd,
    lineage_cmd,
    compare_cmd,
    info_cmd,
    export_cmd,
    repair_cmd,
)


@click.group()
@click.version_option(version=__version__, prog_name="vcm")
def cli() -> None:
    """VCM (Version Control Models) - Model DNA Version Control Platform."""
    pass


# Register all CLI subcommands
cli.add_command(init_cmd)
cli.add_command(train_cmd)
cli.add_command(models_cmd)
cli.add_command(lineage_cmd)
cli.add_command(compare_cmd)
cli.add_command(info_cmd)
cli.add_command(export_cmd)
cli.add_command(repair_cmd)


if __name__ == "__main__":
    cli()
