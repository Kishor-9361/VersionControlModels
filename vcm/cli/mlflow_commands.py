"""CLI commands for MLflow tracking integration."""

from __future__ import annotations

import sys
from typing import Optional

import click

from vcm.config import VCMConfig
from vcm.integrations.mlflow_client import MLflowClient


@click.group(name="mlflow")
def mlflow_group() -> None:
    """Manage MLflow experiment tracking integration."""
    pass


@mlflow_group.command(name="status")
def mlflow_status() -> None:
    """Display MLflow integration status and connection configuration."""
    cfg = VCMConfig.load()
    sdk_installed = MLflowClient.is_sdk_installed()

    click.echo("\nMLflow Integration Status")
    click.echo("═" * 50)
    status_str = "enabled" if cfg.mlflow_enabled else "disabled"
    click.echo(f"Status:          {status_str}")
    click.echo(f"Tracking URI:    {cfg.mlflow_tracking_uri}")
    click.echo(f"Experiment:      {cfg.mlflow_experiment_name}")
    sdk_status = "installed (native SDK active)" if sdk_installed else "not installed (using offline filestore)"
    click.echo(f"Python SDK:      {sdk_status}")
    if not sdk_installed:
        click.echo("Note: Install mlflow with 'pip install mlflow' for live remote server logging.")


@mlflow_group.command(name="enable")
def mlflow_enable() -> None:
    """Enable MLflow tracking in VCM configuration."""
    cfg = VCMConfig.load()
    cfg.mlflow_enabled = True
    cfg.save()
    click.echo("MLflow integration enabled.")


@mlflow_group.command(name="disable")
def mlflow_disable() -> None:
    """Disable MLflow tracking in VCM configuration."""
    cfg = VCMConfig.load()
    cfg.mlflow_enabled = False
    cfg.save()
    click.echo("MLflow integration disabled.")


@mlflow_group.command(name="sync")
@click.argument("model_name", required=False, default=None)
@click.option("--all", "sync_all_models", is_flag=True, default=False, help="Sync all models in workspace")
def mlflow_sync(model_name: Optional[str], sync_all_models: bool) -> None:
    """Sync model parameters, metrics, and DNA tags to MLflow."""
    from vcm.cli.commands import _find_metadata
    from vcm.db.database import Database

    client = MLflowClient()

    if sync_all_models or not model_name:
        results = client.sync_all()
        if not results:
            # Fallback: check database directly
            cfg = VCMConfig.load()
            db = Database(cfg.database_path)
            models = db.get_all_models()
            for m in models:
                res = client.sync_model(m)
                results.append(res)

        if not results:
            click.echo("No models found to sync to MLflow.")
            return

        click.echo(f"\nSynced {len(results)} model(s) to MLflow:")
        for r in results:
            click.echo(f"  • {r['model_name']} -> run_id: {r['run_id']} ({r['mode']})")
        click.echo(f"Target: {client.tracking_uri} [Experiment: {client.experiment_name}]\n")
        return

    meta = _find_metadata(model_name)
    if not meta:
        click.echo(f"Error: Model metadata not found for '{model_name}'.", err=True)
        sys.exit(1)

    res = client.sync_model(meta)
    click.echo(f"Model '{model_name}' synced to MLflow successfully.")
    click.echo(f"   Run ID:      {res['run_id']}")
    click.echo(f"   Mode:        {res['mode']}")
    click.echo(f"   Destination: {res['tracking_uri']}")
    click.echo(f"   Experiment:  {res['experiment_name']}")
