"""MLflow integration client supporting native SDK and zero-dependency offline logging."""

from __future__ import annotations

import getpass
import importlib
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from vcm.config import VCMConfig
from vcm.models.metadata import MetadataModel


class MLflowClient:
    """Client for logging VCM Model DNA into MLflow tracking servers or local directories."""

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: Optional[str] = None,
        repo_path: str = ".",
    ) -> None:
        self.repo_path = repo_path
        config = VCMConfig.load(os.path.join(repo_path, ".vcmconfig.yaml"))
        self.tracking_uri = tracking_uri or config.mlflow_tracking_uri or "file:./mlruns"
        self.experiment_name = experiment_name or config.mlflow_experiment_name or "Default"
        self.enabled = config.mlflow_enabled

    @staticmethod
    def is_sdk_installed() -> bool:
        """Check if native mlflow library is installed."""
        try:
            importlib.import_module("mlflow")
            return True
        except ImportError:
            return False

    def sync_model(self, meta: MetadataModel, run_name: Optional[str] = None) -> Dict[str, Any]:
        """Sync a VCM model metadata record to MLflow."""
        if self.is_sdk_installed():
            return self._sync_with_sdk(meta, run_name=run_name)
        return self._sync_offline(meta, run_name=run_name)

    def _sync_with_sdk(self, meta: MetadataModel, run_name: Optional[str] = None) -> Dict[str, Any]:
        """Sync model using native MLflow Python library."""
        mlflow: Any = importlib.import_module("mlflow")

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

        r_name = run_name or meta.model_name
        with mlflow.start_run(run_name=r_name) as run:
            run_id = str(run.info.run_id)

            # Log Hyperparameters
            if meta.hyperparameters:
                sanitized_params = {str(k): str(v) for k, v in meta.hyperparameters.items()}
                mlflow.log_params(sanitized_params)

            # Log Metrics
            if meta.metrics:
                for k, v in meta.metrics.items():
                    if isinstance(v, (int, float)):
                        mlflow.log_metric(str(k), float(v))

            # Log VCM Model DNA Tags
            tags: Dict[str, str] = {
                "vcm.model_name": meta.model_name,
                "vcm.model_hash": meta.model_hash,
                "vcm.git_commit": meta.code.git_commit or "unknown",
                "vcm.branch": meta.code.git_branch or "main",
                "vcm.user": meta.training.user or getpass.getuser(),
                "vcm.version": meta.metadata_version,
            }
            if meta.data.dvc_files:
                tags["vcm.dataset_path"] = meta.data.dvc_files[0].path
                tags["vcm.dataset_hash"] = meta.data.dvc_files[0].dvc_hash
            if meta.reasoning:
                tags["vcm.reasoning"] = meta.reasoning

            mlflow.set_tags(tags)

            # Log artifact if exists
            abs_model = os.path.join(self.repo_path, meta.model_file)
            if os.path.exists(abs_model):
                mlflow.log_artifact(abs_model, artifact_path="model")

            return {
                "status": "success",
                "mode": "native_sdk",
                "run_id": run_id,
                "tracking_uri": self.tracking_uri,
                "experiment_name": self.experiment_name,
                "model_name": meta.model_name,
            }

    def _sync_offline(self, meta: MetadataModel, run_name: Optional[str] = None) -> Dict[str, Any]:
        """Log model in standard MLflow file store format without external dependencies."""
        runs_dir = self.tracking_uri.replace("file:", "") if self.tracking_uri.startswith("file:") else "./mlruns"
        if not os.path.isabs(runs_dir):
            runs_dir = os.path.join(self.repo_path, runs_dir)

        exp_id = "0"
        exp_dir = os.path.join(runs_dir, exp_id)
        os.makedirs(exp_dir, exist_ok=True)

        # Ensure experiment meta.yaml
        exp_meta_file = os.path.join(exp_dir, "meta.yaml")
        if not os.path.exists(exp_meta_file):
            with open(exp_meta_file, "w", encoding="utf-8") as f:
                f.write(f"artifact_location: {exp_dir}\n")
                f.write(f"creation_time: {int(time.time() * 1000)}\n")
                f.write(f"experiment_id: '{exp_id}'\n")
                f.write(f"last_update_time: {int(time.time() * 1000)}\n")
                f.write("lifecycle_stage: active\n")
                f.write(f"name: {self.experiment_name}\n")

        run_id = uuid.uuid4().hex
        run_dir = os.path.join(exp_dir, run_id)
        params_dir = os.path.join(run_dir, "params")
        metrics_dir = os.path.join(run_dir, "metrics")
        tags_dir = os.path.join(run_dir, "tags")
        artifacts_dir = os.path.join(run_dir, "artifacts")

        for d in (params_dir, metrics_dir, tags_dir, artifacts_dir):
            os.makedirs(d, exist_ok=True)

        now_ms = int(time.time() * 1000)

        # Write run meta.yaml
        with open(os.path.join(run_dir, "meta.yaml"), "w", encoding="utf-8") as f:
            f.write(f"artifact_uri: {artifacts_dir}\n")
            f.write(f"end_time: {now_ms}\n")
            f.write(f"experiment_id: '{exp_id}'\n")
            f.write("lifecycle_stage: active\n")
            f.write(f"run_id: {run_id}\n")
            f.write(f"run_name: {run_name or meta.model_name}\n")
            f.write(f"run_uuid: {run_id}\n")
            f.write(f"start_time: {now_ms}\n")
            f.write("status: 3\n")
            f.write(f"user_id: {meta.training.user or getpass.getuser()}\n")

        # Write params
        for k, v in meta.hyperparameters.items():
            param_file = os.path.join(params_dir, str(k))
            with open(param_file, "w", encoding="utf-8") as f:
                f.write(str(v))

        # Write metrics
        for k, v in meta.metrics.items():
            if isinstance(v, (int, float)):
                metric_file = os.path.join(metrics_dir, str(k))
                with open(metric_file, "w", encoding="utf-8") as f:
                    f.write(f"{now_ms} {v} 0\n")

        # Write tags
        tags: Dict[str, str] = {
            "mlflow.runName": run_name or meta.model_name,
            "mlflow.user": meta.training.user or getpass.getuser(),
            "vcm.model_name": meta.model_name,
            "vcm.model_hash": meta.model_hash,
            "vcm.git_commit": meta.code.git_commit or "unknown",
            "vcm.branch": meta.code.git_branch or "main",
        }
        if meta.data.dvc_files:
            tags["vcm.dataset_path"] = meta.data.dvc_files[0].path
            tags["vcm.dataset_hash"] = meta.data.dvc_files[0].dvc_hash
        if meta.reasoning:
            tags["vcm.reasoning"] = meta.reasoning

        for k, v in tags.items():
            tag_file = os.path.join(tags_dir, str(k))
            with open(tag_file, "w", encoding="utf-8") as f:
                f.write(str(v))

        # Copy sidecar to artifacts
        sidecar_dest = os.path.join(artifacts_dir, f"{meta.model_name}.vcm.json")
        with open(sidecar_dest, "w", encoding="utf-8") as f:
            json.dump(meta.to_dict(), f, indent=2)

        return {
            "status": "success",
            "mode": "offline_filestore",
            "run_id": run_id,
            "tracking_uri": self.tracking_uri,
            "experiment_name": self.experiment_name,
            "model_name": meta.model_name,
        }

    def sync_all(self) -> List[Dict[str, Any]]:
        """Sync all tracked models in local SQLite index to MLflow."""
        from vcm.db.database import Database
        config = VCMConfig.load(os.path.join(self.repo_path, ".vcmconfig.yaml"))
        db_path = os.path.join(self.repo_path, config.database_path)
        if not os.path.exists(db_path):
            return []

        db = Database(db_path)
        models = db.get_all_models()
        results = []
        for m in models:
            res = self.sync_model(m)
            results.append(res)
        return results
