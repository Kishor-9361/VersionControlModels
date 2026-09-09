"""CLI Command implementations for VCM."""

from __future__ import annotations

import csv
import json
import os
import sys
from typing import List, Optional

import click
from tabulate import tabulate

from vcm.config import VCMConfig
from vcm.db.database import Database, DatabaseError
from vcm.models.metadata import MetadataModel
from vcm.trainer import ModelTracker


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

        click.echo("✅ VCM initialized successfully")
        click.echo(f"   - Created {os.path.dirname(db_path) or '.vcm'}/ directory")
        click.echo(f"   - Initialized database at {db_path}")
        click.echo("   - Created .vcmconfig.yaml")
        click.echo("\nUse 'vcm train' to track models")
    except Exception as exc:
        click.echo(f"❌ Initialization failed: {exc}", err=True)
        sys.exit(1)


@click.command("train")
@click.option("--model-name", required=True, help="Unique name for the model (e.g. classifier_v1).")
@click.option("--dataset", help="Path to dataset file or directory.")
@click.option("--script", required=True, help="Path to training Python script.")
@click.option("--metrics", "metrics_path", help="Path to metrics JSON file.")
@click.option("--params", "params", multiple=True, help="Hyperparameter key=value pair (can be used multiple times).")
@click.option("--model-file", help="Explicit path to output model file if not in models/ directory.")
@click.option("--output-dir", help="Directory where model is expected to be saved.")
def train_cmd(
    model_name: str,
    dataset: Optional[str],
    script: str,
    metrics_path: Optional[str],
    params: tuple[str, ...],
    model_file: Optional[str],
    output_dir: Optional[str],
) -> None:
    """Wrap model training and automatically capture code, data, metrics, and environment."""
    try:
        click.echo(f"Running training script: {script} ...")
        tracker = ModelTracker()
        metadata = tracker.run_and_track(
            script_path=script,
            model_name=model_name,
            dataset=dataset,
            metrics_path=metrics_path,
            params=list(params),
            model_file=model_file,
            output_dir=output_dir,
        )

        acc = metadata.metrics.get("accuracy")
        acc_str = f"{acc * 100:.1f}%" if acc is not None else "N/A"

        click.echo("\n✅ Model tracked successfully")
        click.echo(f"   Model: {metadata.model_name}")
        click.echo(f"   Accuracy: {acc_str}")
        click.echo(f"   Git commit: {metadata.code.git_commit or 'uncommitted'}")
        if metadata.data.dvc_files:
            click.echo(f"   Dataset: {metadata.data.dvc_files[0].path}")
        click.echo(f"   Metadata: {metadata.model_file}.vcm.json")
    except FileNotFoundError as exc:
        click.echo(f"❌ Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"❌ Training tracking failed: {exc}", err=True)
        sys.exit(1)


@click.command("models")
@click.option("--dataset", help="Filter models by dataset path or dataset hash.")
@click.option("--best", is_flag=True, help="Show only the highest performing model.")
@click.option("--limit", type=int, help="Limit number of models displayed.")
@click.option("--sort-by", default="accuracy", help="Metric to sort by (default: accuracy).")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format.")
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
            click.echo("❌ Database corrupted. Run: vcm repair", err=True)
            sys.exit(1)

        if not os.path.exists(db.db_path):
            click.echo("⚠️ VCM database not found. Run 'vcm init' or 'vcm repair'.", err=True)
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
            created_str = m.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(m.created_at, "strftime") else str(m.created_at)[:16]

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
        click.echo(f"❌ Database error: {exc}", err=True)
        sys.exit(1)


@click.command("lineage")
@click.argument("model_ref")
def lineage_cmd(model_ref: str) -> None:
    """Show complete lineage tree for a model."""
    meta = _find_metadata(model_ref)
    if not meta:
        click.echo(f"❌ Model '{model_ref}' not found in database or filesystem.", err=True)
        sys.exit(1)

    acc = meta.metrics.get("accuracy")
    acc_str = f"{acc:.4f} ({acc * 100:.1f}%)" if acc is not None else "N/A"
    f1 = meta.metrics.get("f1_score")
    f1_str = f"{f1:.4f}" if f1 is not None else "N/A"

    click.echo(f"\n📦 Model: {meta.model_name} ({meta.model_file})")
    click.echo(f"├── 💾 Accuracy: {acc_str} | F1 Score: {f1_str}")
    click.echo(f"├── 🎯 Git Commit: {meta.code.git_commit or 'untracked'}")
    click.echo(f"│   ├── Branch: {meta.code.git_branch or 'N/A'}")
    click.echo(f"│   ├── Remote: {meta.code.git_remote or 'N/A'}")
    click.echo(f"│   └── URL: {meta.code.git_url or 'N/A'}")

    click.echo("├── 📊 Dataset Files:")
    if meta.data.dvc_files:
        for f in meta.data.dvc_files:
            click.echo(f"│   ├── {f.path} (hash: {f.dvc_hash[:16]}..., size: {f.size_bytes} B)")
    else:
        click.echo("│   └── None tracked")

    click.echo("├── ⚙️ Hyperparameters:")
    if meta.hyperparameters:
        for k, v in meta.hyperparameters.items():
            click.echo(f"│   ├── {k}: {v}")
    else:
        click.echo("│   └── None specified")

    user = meta.training.user or "unknown"
    host = meta.training.hostname or "unknown"
    ts = meta.training.timestamp or "unknown"
    click.echo(f"└── 👤 Trained by: {user} on {host} ({ts})")


@click.command("compare")
@click.argument("model1_ref")
@click.argument("model2_ref")
def compare_cmd(model1_ref: str, model2_ref: str) -> None:
    """Compare two models side-by-side."""
    m1 = _find_metadata(model1_ref)
    m2 = _find_metadata(model2_ref)

    if not m1:
        click.echo(f"❌ Model 1 '{model1_ref}' not found.", err=True)
        sys.exit(1)
    if not m2:
        click.echo(f"❌ Model 2 '{model2_ref}' not found.", err=True)
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
            sign = "+" if delta >= 0 else ""
            arrow = "⬆" if delta > 0 else ("⬇" if delta < 0 else "=")
            delta_str = f"{sign}{delta * 100:.1f}% {arrow}" if ("acc" in k or "score" in k) else f"{sign}{delta:.4f} {arrow}"
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
        click.echo(f"\n📈 Model '{m2.model_name}' is better:")
        click.echo(f"   • {(acc2 - acc1) * 100:.1f}% higher accuracy")
    elif acc1 > acc2:
        click.echo(f"\n📈 Model '{m1.model_name}' is better:")
        click.echo(f"   • {(acc1 - acc2) * 100:.1f}% higher accuracy")
    else:
        click.echo(f"\n⚖️ Models have equal accuracy ({acc1 * 100:.1f}%)")


@click.command("info")
@click.argument("model_ref")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON metadata.")
def info_cmd(model_ref: str, as_json: bool) -> None:
    """Show detailed model metadata."""
    meta = _find_metadata(model_ref)
    if not meta:
        click.echo(f"❌ Model '{model_ref}' not found.", err=True)
        sys.exit(1)

    if as_json:
        click.echo(meta.to_json())
    else:
        click.echo(f"Model Name:      {meta.model_name}")
        click.echo(f"Model File:      {meta.model_file}")
        click.echo(f"Model Hash:      {meta.model_hash}")
        click.echo(f"Git Commit:      {meta.code.git_commit or 'N/A'}")
        click.echo(f"Git Branch:      {meta.code.git_branch or 'N/A'}")
        click.echo(f"Created At:      {meta.created_at}")
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
        click.echo(f"❌ Model '{model_ref}' not found.", err=True)
        sys.exit(1)

    json_content = meta.to_json()
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(json_content)
        click.echo(f"✅ Metadata exported to {output}")
    else:
        click.echo(json_content)


@click.command("repair")
def repair_cmd() -> None:
    """Rebuild SQLite database from existing .vcm.json files on disk."""
    config = VCMConfig.load()
    db = Database(config.database_path)

    found_models: List[MetadataModel] = []
    for root, _, files in os.walk("."):
        if any(ignored in root for ignored in [".git", "venv", ".venv", "__pycache__"]):
            continue
        for file in files:
            if file.endswith(".vcm.json"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        meta = MetadataModel.from_json(f.read())
                        found_models.append(meta)
                except Exception as exc:
                    click.echo(f"⚠️ Warning: Could not read {path}: {exc}", err=True)

    rebuilt_count = db.rebuild_from_metadata(found_models)
    click.echo(f"✅ Database repaired: Re-indexed {rebuilt_count} models.")
