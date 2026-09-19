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
    analysis_cmd,
    config_cmd,
    reproduce_cmd,
    deploy_cmd,
    audit_cmd,
    version_cmd,
)
from vcm.cli.session_commands import session_group
from vcm.cli.timeline_commands import (
    timeline_group,
    timeline_reason_standalone_cmd,
)
from vcm.cli.mlflow_commands import mlflow_group


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
cli.add_command(session_group)
cli.add_command(analysis_cmd)
cli.add_command(config_cmd)
cli.add_command(reproduce_cmd)
cli.add_command(deploy_cmd)
cli.add_command(audit_cmd)
cli.add_command(version_cmd)
cli.add_command(timeline_group, name="timeline")
cli.add_command(timeline_reason_standalone_cmd, name="timeline-reason")
cli.add_command(mlflow_group, name="mlflow")


if __name__ == "__main__":
    cli()
