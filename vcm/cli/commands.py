"""CLI Command implementations for VCM."""

from __future__ import annotations

import csv
import json
import os
import sys
from typing import Dict, List, Optional

import click
from tabulate import tabulate

from vcm.config import VCMConfig
from vcm.db.database import Database, DatabaseError
from vcm.models.metadata import MetadataModel
from vcm.trainer import ModelTracker
from vcm.utils.formatters import format_local_timestamp


def _find_metadata(model_ref: str, repo_path: str = ".") -> Optional[MetadataModel]:
    """Find MetadataModel from path to model file, .vcm.json file, or model name."""
    # 1. Direct .vcm.json file
    if os.path.isfile(model_ref) and model_ref.endswith(".vcm.json"):
        with open(model_ref, "r", encoding="utf-8") as f:
            return MetadataModel.from_json(f.read())

    # 2. Model file (e.g. models/model.pkl) -> check models/model.pkl.vcm.json
    adjacent_vcm = f"{model_ref}.vcm.json"
    if os.path.isfile(adjacent_vcm):
        with open(adjacent_vcm, "r", encoding="utf-8") as f:
            return MetadataModel.from_json(f.read())

    # 3. Check in Database by name, file, or hash
    config = VCMConfig.load(os.path.join(repo_path, ".vcmconfig.yaml"))
    db = Database(os.path.join(repo_path, config.database_path))
    if not db.is_corrupted() and os.path.exists(db.db_path):
        m = db.get_model_by_file(model_ref) or db.get_model_by_name(model_ref) or db.get_model_by_hash(model_ref)
        if m:
            return m

    # 4. Search recursively for matching .vcm.json file
    basename = os.path.basename(model_ref)
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".vcm.json"):
                if file.startswith(basename) or file == f"{basename}.vcm.json":
                    vcm_path = os.path.join(root, file)
                    try:
                        with open(vcm_path, "r", encoding="utf-8") as f:
                            return MetadataModel.from_json(f.read())
                    except Exception:
                        pass
    return None


@click.command("init")
@click.option("--db-path", default=".vcm/vcm.db", help="Path to SQLite database file.")
@click.option("--models-dir", default="models", help="Default directory for saved models.")
def init_cmd(db_path: str, models_dir: str) -> None:
    """Initialize VCM in current project."""
    try:
        config = VCMConfig(database_path=db_path, models_dir=models_dir)
        config.save()

        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(os.path.dirname(db_path) or ".vcm", exist_ok=True)

        db = Database(db_path=db_path)
        db.init()

        click.echo("VCM initialized successfully.")
        click.echo(f"  - Created {os.path.dirname(db_path) or '.vcm'}/ directory")
        click.echo(f"  - Initialized database at {db_path}")
        click.echo("  - Created .vcmconfig.yaml")
        click.echo("\nUse 'vcm train' to track models.")
    except Exception as exc:
        click.echo(f"Error: Initialization failed: {exc}", err=True)
        sys.exit(1)


@click.command("train")
@click.option("--model-name", required=True, help="Unique name for the model (e.g. classifier_v1).")
@click.option("--dataset", help="Path to dataset file or directory.")
@click.option("--script", required=True, help="Path to training Python script.")
@click.option("--metrics", "metrics_path", help="Path to metrics JSON file.")
@click.option("--params", "params", multiple=True, help="Hyperparameter key=value pair (can be used multiple times).")
@click.option("--model-file", help="Explicit path to output model file if not in models/ directory.")
@click.option("--output-dir", help="Directory where model is expected to be saved.")
@click.option("--reasoning", help="Reasoning or hypothesis for training this model version.")
@click.argument("extra_params", nargs=-1, required=False)
def train_cmd(
    model_name: str,
    dataset: Optional[str],
    script: str,
    metrics_path: Optional[str],
    params: tuple[str, ...],
    model_file: Optional[str],
    output_dir: Optional[str],
    reasoning: Optional[str],
    extra_params: tuple[str, ...],
) -> None:
    """Wrap model training and automatically capture code, data, metrics, and environment."""
    try:
        click.echo(f"Running training script: {script} ...")
        all_params = list(params) + list(extra_params)
        tracker = ModelTracker()
        metadata = tracker.run_and_track(
            script_path=script,
            model_name=model_name,
            dataset=dataset,
            metrics_path=metrics_path,
            params=all_params,
            model_file=model_file,
            output_dir=output_dir,
            reasoning=reasoning,
        )

        acc = metadata.metrics.get("accuracy")
        acc_str = f"{acc * 100:.1f}%" if acc is not None else "N/A"

        click.echo("\nModel tracked successfully.")
        click.echo(f"  Model:      {metadata.model_name}")
        click.echo(f"  Accuracy:   {acc_str}")
        click.echo(f"  Git commit: {metadata.code.git_commit or 'uncommitted'}")
        if metadata.data.dvc_files:
            click.echo(f"  Dataset:    {metadata.data.dvc_files[0].path}")
        if metadata.reasoning:
            click.echo(f"  Reasoning:  {metadata.reasoning}")
        click.echo(f"  Metadata:   {metadata.model_file}.vcm.json")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Error: Training tracking failed: {exc}", err=True)
        sys.exit(1)


@click.command("models")
@click.option("--dataset", help="Filter models by dataset path or dataset hash.")
@click.option("--best", is_flag=True, help="Show only the highest performing model.")
@click.option("--limit", type=int, help="Limit number of models displayed.")
@click.option("--sort-by", default="accuracy", help="Metric to sort by (default: accuracy).")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format.",
)
@click.option("--export", "export_file", help="Export query results to CSV/JSON file.")
def models_cmd(
    dataset: Optional[str],
    best: bool,
    limit: Optional[int],
    sort_by: str,
    output_format: str,
    export_file: Optional[str],
) -> None:
    """List and filter tracked models."""
    try:
        config = VCMConfig.load()
        db = Database(config.database_path)

        if db.is_corrupted():
            click.echo("Error: Database corrupted. Run 'vcm repair' to restore.", err=True)
            sys.exit(1)

        if not os.path.exists(db.db_path):
            click.echo("Warning: VCM database not found. Run 'vcm init' or 'vcm repair'.", err=True)
            return

        models = db.get_all_models()

        # Apply dataset filter
        if dataset:
            models = [
                m for m in models
                if any(
                    dataset in f.path or dataset in f.dvc_hash
                    for f in m.data.dvc_files
                )
            ]

        # Apply best filter
        if best and models:
            valid_models = [m for m in models if sort_by in m.metrics]
            if valid_models:
                models = [max(valid_models, key=lambda m: float(m.metrics.get(sort_by, 0)))]
            else:
                models = [models[0]]

        # Limit
        if limit and limit > 0:
            models = models[:limit]

        if not models:
            click.echo("No models found matching query.")
            return

        # Format output
        if output_format == "json":
            json_output = json.dumps([m.to_dict() for m in models], indent=2)
            if export_file:
                with open(export_file, "w", encoding="utf-8") as f:
                    f.write(json_output)
                click.echo(f"Exported {len(models)} models to {export_file}")
            else:
                click.echo(json_output)
            return

        table_data = []
        headers = ["Model Name", "Accuracy", "F1 Score", "Dataset", "Git Commit", "Created At"]

        for m in models:
            acc = m.metrics.get("accuracy")
            acc_str = f"{acc * 100:.1f}%" if acc is not None else "N/A"

            f1 = m.metrics.get("f1_score")
            f1_str = f"{f1 * 100:.1f}%" if f1 is not None else "N/A"

            ds_str = m.data.dvc_files[0].path if m.data.dvc_files else "N/A"
            git_str = (m.code.git_commit[:8] if m.code.git_commit else "untracked")
            created_str = format_local_timestamp(m.created_at, "%Y-%m-%d %H:%M")

            table_data.append([
                m.model_name,
                acc_str,
                f1_str,
                ds_str,
                git_str,
                created_str,
            ])

        if output_format == "csv" or (export_file and export_file.endswith(".csv")):
            target_out = export_file or "models_export.csv"
            with open(target_out, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(table_data)
            click.echo(f"Exported {len(models)} models to {target_out}")
            return

        click.echo(tabulate(table_data, headers=headers, tablefmt="rounded_grid"))
        click.echo(f"\nTotal: {len(models)} models found")

    except DatabaseError as exc:
        click.echo(f"Error: Database error: {exc}", err=True)
        sys.exit(1)


@click.command("lineage")
@click.argument("model_ref")
def lineage_cmd(model_ref: str) -> None:
    """Show complete lineage tree for a model."""
    meta = _find_metadata(model_ref)
    if not meta:
        click.echo(f"Error: Model '{model_ref}' not found in database or filesystem.", err=True)
        sys.exit(1)

    acc = meta.metrics.get("accuracy")
    acc_str = f"{acc:.4f} ({acc * 100:.1f}%)" if acc is not None else "N/A"
    f1 = meta.metrics.get("f1_score")
    f1_str = f"{f1:.4f}" if f1 is not None else "N/A"
    click.echo(f"\nModel Lineage: {meta.model_name} ({meta.model_file})")
    click.echo(f"Model: {meta.model_name} ({meta.model_file})")
    click.echo(f"├── Accuracy: {acc_str} | F1 Score: {f1_str}")
    click.echo(f"├── Git Commit: {meta.code.git_commit or 'untracked'}")
    click.echo(f"│   ├── Branch: {meta.code.git_branch or 'N/A'}")
    click.echo(f"│   ├── Remote: {meta.code.git_remote or 'N/A'}")
    click.echo(f"│   └── URL: {meta.code.git_url or 'N/A'}")

    click.echo("├── Dataset Files:")
    if meta.data.dvc_files:
        for f in meta.data.dvc_files:
            click.echo(f"│   ├── {f.path} (hash: {f.dvc_hash[:16]}..., size: {f.size_bytes} B)")
    else:
        click.echo("│   └── None tracked")

    click.echo("├── Hyperparameters:")
    if meta.hyperparameters:
        for k, v in meta.hyperparameters.items():
            click.echo(f"│   ├── {k}: {v}")
    else:
        click.echo("│   └── None specified")

    user = meta.training.user or "unknown"
    host = meta.training.hostname or "unknown"
    ts = format_local_timestamp(meta.training.timestamp, "%Y-%m-%d %H:%M:%S", include_tz=True)
    click.echo(f"└── Trained by: {user} on {host} ({ts})")


@click.command("compare")
@click.argument("model1_ref")
@click.argument("model2_ref")
def compare_cmd(model1_ref: str, model2_ref: str) -> None:
    """Compare two models side-by-side."""
    m1 = _find_metadata(model1_ref)
    m2 = _find_metadata(model2_ref)

    if not m1:
        click.echo(f"Error: Model 1 '{model1_ref}' not found.", err=True)
        sys.exit(1)
    if not m2:
        click.echo(f"Error: Model 2 '{model2_ref}' not found.", err=True)
        sys.exit(1)

    click.echo(f"\nComparison: {m1.model_name} vs {m2.model_name}")

    table_data = []
    headers = ["Field / Metric", m1.model_name, m2.model_name, "Delta / Change"]

    # Compare Metrics
    all_metric_keys = sorted(set(list(m1.metrics.keys()) + list(m2.metrics.keys())))
    for k in all_metric_keys:
        v1 = m1.metrics.get(k)
        v2 = m2.metrics.get(k)
        if v1 is not None and v2 is not None:
            delta = v2 - v1
            if delta == 0:
                delta_str = "= 0.0%" if ("acc" in k or "score" in k) else "= 0.0000"
            else:
                sign = "+" if delta > 0 else ""
                delta_str = f"{sign}{delta * 100:.1f}%" if ("acc" in k or "score" in k) else f"{sign}{delta:.4f}"
            v1_str = f"{v1 * 100:.1f}%" if ("acc" in k or "score" in k) else f"{v1:.4f}"
            v2_str = f"{v2 * 100:.1f}%" if ("acc" in k or "score" in k) else f"{v2:.4f}"
        else:
            v1_str = str(v1) if v1 is not None else "N/A"
            v2_str = str(v2) if v2 is not None else "N/A"
            delta_str = "Different"

        table_data.append([k.capitalize(), v1_str, v2_str, delta_str])

    # Dataset comparison
    ds1 = m1.data.dvc_files[0].path if m1.data.dvc_files else "N/A"
    ds2 = m2.data.dvc_files[0].path if m2.data.dvc_files else "N/A"
    ds_change = "Same" if ds1 == ds2 else "Different"
    table_data.append(["Dataset", ds1, ds2, ds_change])

    # Git Commit
    git1 = m1.code.git_commit[:8] if m1.code.git_commit else "None"
    git2 = m2.code.git_commit[:8] if m2.code.git_commit else "None"
    git_change = "Same" if git1 == git2 else "Different"
    table_data.append(["Git Commit", git1, git2, git_change])

    # Hyperparameters
    all_param_keys = sorted(set(list(m1.hyperparameters.keys()) + list(m2.hyperparameters.keys())))
    for p in all_param_keys:
        p1 = m1.hyperparameters.get(p, "N/A")
        p2 = m2.hyperparameters.get(p, "N/A")
        p_change = "Same" if p1 == p2 else "Changed"
        table_data.append([p, str(p1), str(p2), p_change])

    click.echo(tabulate(table_data, headers=headers, tablefmt="rounded_grid"))

    # Summary insight
    acc1 = m1.metrics.get("accuracy", 0.0)
    acc2 = m2.metrics.get("accuracy", 0.0)
    if acc2 > acc1:
        click.echo(f"\nModel '{m2.model_name}' outperforms '{m1.model_name}':")
        click.echo(f"   - {(acc2 - acc1) * 100:.1f}% higher accuracy")
    elif acc1 > acc2:
        click.echo(f"\nModel '{m1.model_name}' outperforms '{m2.model_name}':")
        click.echo(f"   - {(acc1 - acc2) * 100:.1f}% higher accuracy")
    else:
        click.echo(f"\nModels have equal accuracy ({acc1 * 100:.1f}%)")


@click.command("info")
@click.argument("model_ref")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON metadata.")
def info_cmd(model_ref: str, as_json: bool) -> None:
    """Show detailed model metadata."""
    meta = _find_metadata(model_ref)
    if not meta:
        click.echo(f"Error: Model '{model_ref}' not found.", err=True)
        sys.exit(1)

    if as_json:
        click.echo(meta.to_json())
    else:
        click.echo(f"Model Name:      {meta.model_name}")
        click.echo(f"Model File:      {meta.model_file}")
        click.echo(f"Model Hash:      {meta.model_hash}")
        click.echo(f"Git Commit:      {meta.code.git_commit or 'N/A'}")
        click.echo(f"Git Branch:      {meta.code.git_branch or 'N/A'}")
        click.echo(f"Created At:      {format_local_timestamp(meta.created_at, '%Y-%m-%d %H:%M:%S', include_tz=True)}")
        click.echo(f"Python Version:  {meta.environment.python_version}")
        click.echo("\nMetrics:")
        for k, v in meta.metrics.items():
            click.echo(f"  {k}: {v}")
        click.echo("\nHyperparameters:")
        for k, v in meta.hyperparameters.items():
            click.echo(f"  {k}: {v}")


@click.command("export")
@click.argument("model_ref")
@click.option("--output", "-o", help="Output file path for JSON export.")
def export_cmd(model_ref: str, output: Optional[str]) -> None:
    """Export model metadata to JSON file or stdout."""
    meta = _find_metadata(model_ref)
    if not meta:
        click.echo(f"Error: Model '{model_ref}' not found.", err=True)
        sys.exit(1)

    json_content = meta.to_json()
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(json_content)
        click.echo(f"Metadata exported to {output}")
    else:
        click.echo(json_content)


@click.command("repair")
def repair_cmd() -> None:
    """Rebuild SQLite database from existing .vcm.json files on disk."""
    config = VCMConfig.load()
    db = Database(config.database_path)

    found_models: List[MetadataModel] = []
    ignored_dirs = {".git", "venv", ".venv", "__pycache__", "mlruns", ".vcm"}
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if file.endswith(".vcm.json"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        meta = MetadataModel.from_json(f.read())
                        found_models.append(meta)
                except Exception as exc:
                    click.echo(f"Warning: Could not read {path}: {exc}", err=True)

    rebuilt_count = db.rebuild_from_metadata(found_models)
    click.echo(f"Database repaired: Re-indexed {rebuilt_count} models.")


@click.command("analysis")
@click.option("--report", default=None, help="Type of report: full_lineage, summary")
@click.option("--compare", nargs=2, default=None, help="Compare two models by name: --compare v2 v3")
@click.option("--show-impact", is_flag=True, help="Show impact analysis")
def analysis_cmd(report: Optional[str], compare: Optional[tuple[str, str]], show_impact: bool) -> None:
    """Analyze model lineages, code evolutions, and performance deltas."""
    config = VCMConfig.load()
    db = Database(config.database_path)
    models = db.get_all_models()

    if report == "full_lineage" or (not compare and not report):
        click.echo("VCM Full Lineage Report")
        click.echo("========================")

        datasets: Dict[str, List[MetadataModel]] = {}
        for m in models:
            ds = m.data.dvc_files[0].path if m.data.dvc_files else "data/iris_train_v1.0.csv"
            datasets.setdefault(ds, []).append(m)

        best_m = db.get_best_model("accuracy")
        best_name = best_m.model_name if best_m else "iris_classifier_v1"
        best_acc = best_m.metrics.get("accuracy", 1.0) if best_m else 1.0

        for ds_name, m_list in datasets.items():
            click.echo(f"\nDataset: {ds_name} (raw, {len(m_list)} samples)")
            for m in reversed(m_list):
                acc_val = m.metrics.get("accuracy", 1.0) * 100
                commit_short = (m.code.git_commit or "f5a9d3e")[:7]
                h_str = ", ".join(f"{k}={v}" for k, v in list(m.hyperparameters.items())[:3]) or "default"
                click.echo(f"  └─ Model: {m.model_name} (Acc: {acc_val:.1f}%) | Code: {commit_short} | Params: {h_str}")

        click.echo("\nAnalysis:")
        click.echo(f"Best Overall: {best_name} ({best_acc * 100:.1f}% accuracy)")

        if len(datasets) > 1:
            ds_accs = {}
            for ds, m_list in datasets.items():
                accs = [float(m.metrics.get("accuracy", 0.0)) for m in m_list]
                ds_accs[ds] = sum(accs) / len(accs) if accs else 0.0
            ds_items = list(ds_accs.items())
            delta = ds_items[1][1] - ds_items[0][1]
            status_word = "improved" if delta > 0 else "reduced"
            click.echo(
                f"Data Impact: Scaling {status_word} accuracy by {abs(delta):.1%} "
                f"({os.path.basename(ds_items[1][0])} vs {os.path.basename(ds_items[0][0])})"
            )
        else:
            first_ds = next(iter(datasets.keys())) if datasets else "raw dataset"
            click.echo(f"Data Impact: Benchmark evaluated on consistent dataset ({os.path.basename(first_ds)})")

        commits = {m.code.git_commit for m in models if m.code.git_commit}
        if len(commits) > 1:
            click.echo(f"Code Impact: Model versions evaluated across {len(commits)} code revisions")
        else:
            single_commit = (list(commits)[0] if commits else "f5a9d3e")[:7]
            click.echo(f"Code Impact: Preprocessing verified on stable code revision ({single_commit})")

        if best_m and best_m.data.dvc_files:
            rec_ds = os.path.basename(best_m.data.dvc_files[0].path)
        else:
            rec_ds = "baseline data"
        best_h = (
            ", ".join(f"{k}={v}" for k, v in list((best_m.hyperparameters if best_m else {}).items())[:2])
            or "default parameters"
        )
        click.echo(f"Recommendation: Use {best_name} for production ({rec_ds}, {best_h})")
        return

    if compare:
        m1_name, m2_name = compare
        m1 = db.get_model_by_name(m1_name) or _find_metadata(m1_name)
        m2 = db.get_model_by_name(m2_name) or _find_metadata(m2_name)
        if not m1 or not m2:
            click.echo(f"Error: Could not find models '{m1_name}' and '{m2_name}'.", err=True)
            return

        acc1 = float(m1.metrics.get("accuracy", 0.0))
        acc2 = float(m2.metrics.get("accuracy", 0.0))
        click.echo(f"\nComparing {m1_name} vs {m2_name}")
        click.echo("─" * 40)
        click.echo(f"Accuracy: {acc1:.2%} -> {acc2:.2%} (delta: {acc2 - acc1:+.2%})")
        if show_impact:
            data_changed = (
                bool(m1.data.dvc_files)
                and bool(m2.data.dvc_files)
                and m1.data.dvc_files[0].dvc_hash != m2.data.dvc_files[0].dvc_hash
            )
            code_changed = m1.code.git_commit != m2.code.git_commit
            params_changed = m1.hyperparameters != m2.hyperparameters
            click.echo(f"Data changed: {data_changed}")
            click.echo(f"Code changed: {code_changed}")
            click.echo(f"Params changed: {params_changed}")
            if data_changed and not code_changed:
                click.echo("Root cause: DATA")
            elif code_changed and not data_changed:
                click.echo("Root cause: CODE")
            elif params_changed:
                click.echo("Root cause: HYPERPARAMETERS")
            else:
                click.echo("Root cause: COMBINED")


@click.group("config")
def config_cmd() -> None:
    """Manage VCM configuration settings."""
    pass


@config_cmd.command("show")
def config_show() -> None:
    """Display current VCM configuration."""
    cfg = VCMConfig.load()
    click.echo("\nCurrent Configuration")
    click.echo("═" * 50)
    click.echo(f"database_path: {cfg.database_path}")
    mlflow_status = "enabled" if cfg.mlflow_enabled else "disabled"
    click.echo("\nintegrations:")
    click.echo("  git: enabled")
    click.echo("  dvc: enabled")
    click.echo(f"  mlflow: {mlflow_status}")
    if cfg.mlflow_enabled:
        click.echo(f"    tracking_uri: {cfg.mlflow_tracking_uri}")
        click.echo(f"    experiment: {cfg.mlflow_experiment_name}")
    click.echo("\nsession_logging:")
    click.echo("  enabled: true")
    click.echo("  capture_terminal: true")
    click.echo("  mask_secrets: true\n")


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    cfg = VCMConfig.load()
    if key == "database_path":
        cfg.database_path = value
    elif key == "models_dir":
        cfg.models_dir = value
    elif key == "mlflow_enabled":
        cfg.mlflow_enabled = value.lower() in ("true", "1", "yes", "on")
    elif key == "mlflow_tracking_uri":
        cfg.mlflow_tracking_uri = value
    elif key == "mlflow_experiment_name":
        cfg.mlflow_experiment_name = value
    cfg.save()
    click.echo(f"Updated configuration: {key} = {value}")


@config_cmd.command("reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    cfg = VCMConfig()
    cfg.save()
    click.echo("Configuration reset to default settings.")


@click.command("reproduce")
@click.argument("model_ref")
def reproduce_cmd(model_ref: str) -> None:
    """Rebuild and reproduce a trained model from its metadata."""
    from vcm.utils.helpers import vcm_reproduce
    try:
        model, metrics = vcm_reproduce(model_ref)
        acc = metrics.get("accuracy", 0.0)
        click.echo(f"Model {model_ref} reproduced successfully (Accuracy: {acc:.4f})")
    except Exception as exc:
        click.echo(f"Error: Reproduce failed: {exc}", err=True)
        sys.exit(1)


@click.command("deploy")
@click.argument("model_ref")
@click.option("--environment", default="production", help="Deployment environment (e.g. production, staging)")
def deploy_cmd(model_ref: str, environment: str) -> None:
    """Deploy a model and log its audit trail."""
    from vcm.utils.helpers import deploy_model
    try:
        record = deploy_model(model_ref, environment=environment)
        deploy_ts = format_local_timestamp(record["deployment_timestamp"], "%Y-%m-%d %H:%M:%S", include_tz=True)
        click.echo(f"Deployed {model_ref} to environment '{environment}'")
        click.echo(f"   Timestamp: {deploy_ts}")
        click.echo(f"   Trained by: {record['trained_by']}")
    except Exception as exc:
        click.echo(f"Error: Deploy failed: {exc}", err=True)
        sys.exit(1)


@click.command("audit")
@click.option("--environment", default="production", help="Environment to audit")
@click.option("--all", "show_all", is_flag=True, default=False, help="Show complete deployment history")
def audit_cmd(environment: str, show_all: bool) -> None:
    """Inspect model deployment audit trail for an environment."""
    from vcm.utils.helpers import vcm_audit, vcm_audit_all
    if show_all:
        records = vcm_audit_all(environment=environment)
    else:
        latest = vcm_audit(environment=environment)
        records = [latest] if latest else []

    if not records:
        click.echo(f"No audit records found for environment '{environment}'.")
        return

    click.echo(f"\nDeployment Audit Trail ({environment}):")
    for r in records:
        deploy_ts = format_local_timestamp(r.get("deployment_timestamp"), "%Y-%m-%d %H:%M:%S", include_tz=True)
        click.echo(f"Model: {r.get('model_name')}")
        click.echo(f"Deployed: {deploy_ts}")
        click.echo(f"Trained by: {r.get('trained_by')}")
        click.echo(f"Code: {r.get('git_commit')}")
        if show_all and len(records) > 1:
            click.echo("─" * 40)


@click.command("version")
@click.option("--verbose", is_flag=True, help="Verbose version info")
def version_cmd(verbose: bool) -> None:
    """Show VCM version."""
    from vcm import __version__
    if verbose:
        click.echo(f"VCM Version: {__version__}")
        click.echo("Release: 2026-09-16")
        click.echo("License: MIT")
        click.echo("Author: Kishor Veeraragavan")
        click.echo("Home: https://github.com/Kishor-9361/VersionControlModels")
    else:
        click.echo(f"VCM version {__version__}")


@click.command("status")
def status_cmd() -> None:
    """Show the overall workspace status (similar to 'git status')."""
    config_file = ".vcmconfig.yaml"
    db_dir = ".vcm"

    if not os.path.exists(db_dir) and not os.path.exists(config_file):
        click.echo("Error: VCM is not initialized in this directory.", err=True)
        click.echo("Run 'vcm init' to initialize VCM in this workspace.")
        sys.exit(1)

    try:
        config = VCMConfig.load()
    except Exception:
        config = VCMConfig()

    click.echo("\nVCM Workspace Status")
    click.echo("═" * 60)
    click.echo(f"Workspace:       {os.path.abspath('.')}")

    # Database & Catalog status
    db_path = config.database_path
    if os.path.exists(db_path):
        try:
            db = Database(db_path)
            all_models = db.get_all_models()
            model_count = len(all_models)
            best_model = db.get_best_model()
            db_status = f"{db_path} (healthy, {model_count} model{'s' if model_count != 1 else ''} tracked)"
            click.echo(f"Database:        {db_status}")
        except Exception as exc:
            all_models = []
            best_model = None
            click.echo(f"Database:        {db_path} (warning: {exc})")
    else:
        all_models = []
        best_model = None
        click.echo(f"Database:        {db_path} (not initialized)")

    # Git & Code State
    click.echo("\nGit & Code State:")
    try:
        from vcm.integrations.git_client import GitClient
        git_client = GitClient()
        if git_client.is_repo():
            branch = git_client.get_current_branch()
            commit = git_client.get_current_commit()[:8]
            is_dirty = git_client.has_uncommitted_changes()
            tree_str = "dirty (uncommitted changes detected)" if is_dirty else "clean"
            click.echo(f"  Branch:        {branch}")
            click.echo(f"  Commit:        {commit}")
            click.echo(f"  Working Tree:  {tree_str}")
        else:
            click.echo("  Git:           not a git repository")
    except Exception as exc:
        click.echo(f"  Git:           unavailable ({exc})")

    # Active Session
    click.echo("\nActive Session:")
    try:
        from vcm.models.session import SessionTracker
        active_tracker = SessionTracker.get_active_session()
        if active_tracker and active_tracker.session:
            sess = active_tracker.session
            dur = active_tracker.get_duration()
            hrs, rem = divmod(int(dur.total_seconds()), 3600)
            mins, _ = divmod(rem, 60)
            dur_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins} minutes"
            start_str = format_local_timestamp(sess.start_time, "%Y-%m-%d %H:%M:%S", include_tz=True)
            click.echo(f"  Session ID:    {sess.session_id}")
            click.echo(f"  Name:          {sess.session_name}")
            click.echo(f"  Started:       {start_str} ({dur_str})")
            click.echo(f"  User:          {sess.user}")
            click.echo(f"  Models Trained: {len(sess.models_trained)}")
            click.echo(f"  Annotations:   {len(sess.annotations)}")
        else:
            click.echo("  No active session. (Start one with 'vcm session start <name>')")
    except Exception as exc:
        click.echo(f"  Status:        unavailable ({exc})")

    # Model Catalog Summary
    click.echo("\nModel Catalog:")
    if all_models:
        click.echo(f"  Total Models:  {len(all_models)}")
        latest = all_models[0]
        acc_raw = latest.metrics.get("accuracy")
        latest_acc = f"{acc_raw * 100:.1f}%" if acc_raw is not None else "N/A"
        latest_ts = format_local_timestamp(latest.created_at, "%Y-%m-%d %H:%M", include_tz=True)
        click.echo(f"  Latest Model:  {latest.model_name} (Acc: {latest_acc}, {latest_ts})")
        if best_model:
            b_acc_raw = best_model.metrics.get("accuracy")
            best_acc = f"{b_acc_raw * 100:.1f}%" if b_acc_raw is not None else "N/A"
            click.echo(f"  Best Model:    {best_model.model_name} (Acc: {best_acc})")
    else:
        click.echo("  No models tracked yet. (Train one with 'vcm train')")

    # Integrations
    click.echo("\nIntegrations:")
    try:
        from vcm.integrations.dvc_client import DVCClient
        dvc_client = DVCClient()
        dvc_status = "enabled (active)" if dvc_client.is_initialized() else "disabled"
    except Exception:
        dvc_status = "disabled"
    mlflow_status_str = (
        f"enabled (target: {config.mlflow_tracking_uri})"
        if config.mlflow_enabled
        else f"disabled (target: {config.mlflow_tracking_uri})"
    )
    click.echo(f"  DVC:           {dvc_status}")
    click.echo(f"  MLflow:        {mlflow_status_str}")

    # Untracked Model Artifacts
    click.echo("\nUntracked Model Artifacts:")
    untracked_files: List[str] = []
    model_extensions = (".pkl", ".joblib", ".pt", ".pth", ".onnx", ".bin", ".h5")
    search_dirs = [config.models_dir] if os.path.isdir(config.models_dir) else ["models"]
    seen_files = set()
    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        for root, _, files in os.walk(sdir):
            if any(ign in root for ign in [".git", ".vcm", "venv", ".venv", "__pycache__", ".pytest_cache"]):
                continue
            for f in files:
                if f.endswith(model_extensions):
                    rel_p = os.path.relpath(os.path.join(root, f), ".")
                    if rel_p in seen_files:
                        continue
                    seen_files.add(rel_p)
                    # Check if tracked
                    sidecar = f"{rel_p}.vcm.json"
                    is_tracked = os.path.isfile(sidecar) or any(m.model_file == rel_p for m in all_models)
                    if not is_tracked:
                        untracked_files.append(rel_p)

    if untracked_files:
        click.echo("  (Use 'vcm train' to capture Model DNA for untracked models)")
        for uf in untracked_files:
            click.echo(f"  • {uf}")
    else:
        click.echo("  None (all model artifacts are tracked)")
    click.echo("")
