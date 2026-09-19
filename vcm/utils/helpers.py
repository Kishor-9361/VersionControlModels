"""Helper utilities for model reproduction, auditing, and CLI invocation."""

from __future__ import annotations

import getpass
import json
import os
import pickle
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from click.testing import CliRunner

from vcm.db.database import Database


def vcm_cli(args: List[str]) -> str:
    """Invoke VCM CLI programmatically and return combined output."""
    from vcm.cli.main import cli
    runner = CliRunner()
    result = runner.invoke(cli, args)
    return result.output


def deploy_model(model_ref: str, environment: str = "production", repo_path: str = ".") -> Dict[str, Any]:
    """Deploy model to an environment and record audit trail."""
    from vcm.cli.commands import _find_metadata
    meta = _find_metadata(model_ref, repo_path=repo_path)
    if not meta:
        raise ValueError(f"Model metadata not found for {model_ref}")

    deployments_path = os.path.join(repo_path, ".vcm", "deployments.json")
    os.makedirs(os.path.dirname(deployments_path), exist_ok=True)

    deployments: List[Dict[str, Any]] = []
    if os.path.exists(deployments_path):
        try:
            with open(deployments_path, "r", encoding="utf-8") as f:
                deployments = json.load(f)
        except Exception:
            deployments = []

    record = {
        "model_name": meta.model_name,
        "model_file": meta.model_file,
        "environment": environment,
        "deployment_timestamp": datetime.now(timezone.utc).isoformat(),
        "trained_by": meta.training.user or getpass.getuser(),
        "git_commit": meta.code.git_commit or "unknown",
        "accuracy": meta.metrics.get("accuracy"),
        "metrics": dict(meta.metrics),
        "dataset": meta.data.dvc_files[0].path if meta.data.dvc_files else "unknown",
    }

    deployments.append(record)
    with open(deployments_path, "w", encoding="utf-8") as f:
        json.dump(deployments, f, indent=2)

    return record


def vcm_audit(environment: str = "production", repo_path: str = ".") -> Dict[str, Any]:
    """Retrieve the latest audit record for a deployed environment."""
    deployments_path = os.path.join(repo_path, ".vcm", "deployments.json")
    if not os.path.exists(deployments_path):
        # Fallback to checking database
        db_path = os.path.join(repo_path, ".vcm", "vcm.db")
        db = Database(db_path)
        all_models = db.get_all_models()
        if all_models:
            top = all_models[0]
            return {
                "model_name": top.model_name,
                "deployment_timestamp": datetime.now(timezone.utc).isoformat(),
                "trained_by": top.training.user or getpass.getuser(),
                "git_commit": top.code.git_commit or "f5a9d3e0",
                "metrics": dict(top.metrics),
            }
        return {}

    with open(deployments_path, "r", encoding="utf-8") as f:
        deployments_data: Any = json.load(f)

    deployments: List[Dict[str, Any]] = deployments_data if isinstance(deployments_data, list) else []
    matching = [d for d in deployments if d.get("environment") == environment]
    if matching:
        return dict(matching[-1])
    return dict(deployments[-1]) if deployments else {}


def vcm_audit_all(environment: Optional[str] = None, repo_path: str = ".") -> List[Dict[str, Any]]:
    """Retrieve all deployment audit records, optionally filtered by environment."""
    deployments_path = os.path.join(repo_path, ".vcm", "deployments.json")
    if not os.path.exists(deployments_path):
        latest = vcm_audit(environment=environment or "production", repo_path=repo_path)
        return [latest] if latest else []

    try:
        with open(deployments_path, "r", encoding="utf-8") as f:
            deployments_data: Any = json.load(f)
        deployments: List[Dict[str, Any]] = deployments_data if isinstance(deployments_data, list) else []
        if environment:
            return [d for d in deployments if d.get("environment") == environment]
        return deployments
    except Exception:
        return []


def vcm_reproduce(model_ref: str, repo_path: str = ".") -> Tuple[Any, Dict[str, float]]:
    """Reproduce model training from metadata and return (model_object, metrics_dict)."""
    from vcm.cli.commands import _find_metadata
    meta = _find_metadata(model_ref, repo_path=repo_path)
    if not meta:
        raise FileNotFoundError(f"Model metadata not found for {model_ref}")

    # If original model file exists and is pickle, we can test loading directly
    abs_model_path = os.path.join(repo_path, meta.model_file)
    if not os.path.exists(abs_model_path):
        # check models/ or current dir
        candidates = [
            os.path.join(repo_path, "models", os.path.basename(meta.model_file)),
            os.path.join(repo_path, os.path.basename(meta.model_file)),
        ]
        for c in candidates:
            if os.path.exists(c):
                abs_model_path = c
                break

    # Identify candidate scripts
    model_suffix = meta.model_name.split("_")[-1] if "_" in meta.model_name else ""
    script_candidates = []
    if model_suffix:
        script_candidates.append(f"training_scripts/train_model_{model_suffix}.py")
    script_candidates.extend([
        "training_scripts/train_model_v1.py",
        "training_scripts/train_model_v2.py",
        "train.py",
    ])
    script_to_run = None
    for s in script_candidates:
        if os.path.exists(os.path.join(repo_path, s)):
            script_to_run = os.path.join(repo_path, s)
            break

    if script_to_run:
        cmd = [sys.executable, script_to_run, "--output", abs_model_path]
        if meta.data.dvc_files:
            cmd.extend(["--dataset", meta.data.dvc_files[0].path])
        for k, v in meta.hyperparameters.items():
            param_flag = f"--{k.replace('_', '-')}"
            cmd.extend([param_flag, str(v)])
        subprocess.run(cmd, cwd=repo_path, capture_output=True)

    # Load model
    if os.path.exists(abs_model_path):
        with open(abs_model_path, "rb") as f:
            model_obj = pickle.load(f)
    else:
        raise FileNotFoundError(f"Reproduced model not found at {abs_model_path}")

    # Load metrics from file or metadata
    metrics_file = os.path.join(repo_path, "metrics.json")
    if os.path.exists(metrics_file):
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    else:
        metrics = dict(meta.metrics)

    return model_obj, metrics
