"""Model training wrapper and automated metadata tracker."""

from __future__ import annotations

import functools
import getpass
import logging
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generator, List, Optional

from vcm.config import VCMConfig
from vcm.db.database import Database
from vcm.integrations.dvc_client import DVCClient
from vcm.integrations.git_client import GitClient
from vcm.models.metadata import (
    EnvironmentInfo,
    MetadataModel,
    TrainingInfo,
)
from vcm.models.session import SessionInfo, SessionTracker
from vcm.utils.environment import EnvironmentCapture
from vcm.utils.hashing import compute_file_hash
from vcm.utils.metrics_loader import MetricsLoader

logger = logging.getLogger(__name__)


class TrackingSession:
    """Active training tracking session inside context manager."""

    def __init__(
        self,
        tracker: ModelTracker,
        model_name: str,
        model_path: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.tracker = tracker
        self.model_name = model_name
        self.model_path = model_path
        self.hyperparameters = hyperparameters or {}
        self.metrics: Dict[str, float] = {}
        self.start_time = time.time()

    def set_metrics(self, metrics: Dict[str, Any]) -> None:
        """Record training metrics."""
        self.metrics = MetricsLoader.from_dict(metrics)

    def set_hyperparameters(self, params: Dict[str, Any]) -> None:
        """Record or update hyperparameters."""
        self.hyperparameters.update(params)


class ModelTracker:
    """Tracks machine learning models, environment state, git commits, and DVC datasets."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        config: Optional[VCMConfig] = None,
        repo_path: str = ".",
    ) -> None:
        self.repo_path = os.path.abspath(repo_path)
        self.config = config or VCMConfig.load(os.path.join(self.repo_path, ".vcmconfig.yaml"))
        self.db_path = db_path or self.config.database_path
        if not os.path.isabs(self.db_path):
            self.db_path = os.path.join(self.repo_path, self.db_path)

        self.db = Database(db_path=self.db_path)
        self.git_client = GitClient(repo_path=self.repo_path)
        self.dvc_client = DVCClient(repo_path=self.repo_path)

    def _get_unique_model_name(self, base_name: str) -> str:
        """Handle duplicate model names via automatic versioning if needed."""
        try:
            self.db.init()
            existing = self.db.get_model_by_name(base_name)
            if not existing:
                return base_name

            count = 1
            while True:
                candidate = f"{base_name}_{count:03d}"
                if not self.db.get_model_by_name(candidate):
                    return candidate
                count += 1
        except Exception:
            return base_name

    def log_model(
        self,
        model_path: str,
        model_name: str,
        metrics: Optional[Dict[str, Any]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        dataset_path: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        reasoning: Optional[str] = None,
    ) -> MetadataModel:
        """Capture metadata, create .vcm.json file, and insert into SQLite database."""
        abs_model_path = os.path.abspath(model_path) if not os.path.isabs(model_path) else model_path
        if not os.path.exists(abs_model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        # Ensure database is initialized
        self.db.init()

        # Compute model hash
        model_hash = compute_file_hash(abs_model_path)

        # Relative model path for portability
        rel_model_path = os.path.relpath(abs_model_path, self.repo_path)

        # Code info from Git
        code_info = self.git_client.get_safe_code_info()

        # Data info from DVC or direct dataset path
        data_info = self.dvc_client.get_data_info(dataset_path=dataset_path)

        # Environment info
        env_dict = EnvironmentCapture.capture_all()
        env_info = EnvironmentInfo(
            python_version=env_dict["python_version"],
            libraries=env_dict["libraries"],
        )

        # Training context
        training_info = TrainingInfo(
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=duration_seconds,
            user=env_dict["system"].get("user", getpass.getuser()),
            hostname=env_dict["system"].get("hostname", socket.gethostname()),
        )

        parsed_metrics = MetricsLoader.from_dict(metrics or {})
        parsed_hyperparams = dict(hyperparameters or {})

        # Active session handling
        session_info: Optional[SessionInfo] = None
        session_annotations: List[Dict[str, Any]] = []
        changes_from_prev: Optional[Dict[str, Any]] = None

        active_tracker = SessionTracker.get_active_session(repo_path=self.repo_path)
        if active_tracker is not None:
            prev_model_name = active_tracker.last_model_name
            pos = len(active_tracker.session.models_trained) + 1
            session_info = SessionInfo(
                session_id=active_tracker.session_id,
                session_name=active_tracker.session_name,
                session_start=active_tracker.session.start_time.isoformat(),
                position_in_session=pos,
                previous_model=prev_model_name,
                previous_model_in_session=prev_model_name,
                session_best_model=active_tracker.session.best_model,
            )
            session_annotations = [a.to_dict() for a in active_tracker.session.annotations]

            # If previous model exists, update previous model's next_model link
            if prev_model_name:
                prev_meta = self.db.get_model_by_name(prev_model_name)
                if prev_meta is not None:
                    updated_prev_session = None
                    if prev_meta.session is not None:
                        prev_d = prev_meta.session.to_dict()
                        prev_d["next_model"] = model_name
                        prev_d["next_model_in_session"] = model_name
                        updated_prev_session = SessionInfo.from_dict(prev_d)
                    else:
                        updated_prev_session = SessionInfo(
                            session_id=active_tracker.session_id,
                            session_name=active_tracker.session_name,
                            next_model=model_name,
                            next_model_in_session=model_name,
                        )

                    new_prev_meta = MetadataModel(
                        model_name=prev_meta.model_name,
                        model_hash=prev_meta.model_hash,
                        model_file=prev_meta.model_file,
                        code=prev_meta.code,
                        data=prev_meta.data,
                        training=prev_meta.training,
                        hyperparameters=prev_meta.hyperparameters,
                        metrics=prev_meta.metrics,
                        environment=prev_meta.environment,
                        metadata_version=prev_meta.metadata_version,
                        created_at=prev_meta.created_at,
                        session=updated_prev_session,
                        session_annotations=prev_meta.session_annotations,
                        changes_from_previous=prev_meta.changes_from_previous,
                    )
                    prev_id = self.db.get_model_id_by_hash(prev_meta.model_hash)
                    if prev_id is not None:
                        self.db.update_model(prev_id, new_prev_meta)

                    prev_file_path = os.path.join(self.repo_path, f"{prev_meta.model_file}.vcm.json")
                    if os.path.exists(prev_file_path):
                        try:
                            with open(prev_file_path, "w", encoding="utf-8") as pf:
                                pf.write(new_prev_meta.to_json())
                        except Exception:
                            pass

                    alt_prev_json = f"{prev_meta.model_name}.pkl.vcm.json"
                    if os.path.exists(alt_prev_json):
                        try:
                            with open(alt_prev_json, "w", encoding="utf-8") as pf:
                                pf.write(new_prev_meta.to_json())
                        except Exception:
                            pass

                    changes_from_prev = {
                        "hyperparameters": {
                            k: f"{prev_meta.hyperparameters.get(k)} -> {v}"
                            for k, v in parsed_hyperparams.items()
                            if prev_meta.hyperparameters.get(k) != v
                        },
                        "code": {
                            "git_commit": f"{prev_meta.code.git_commit} -> {code_info.git_commit}",
                        },
                    }

        metadata = MetadataModel(
            model_name=model_name,
            model_hash=model_hash,
            model_file=rel_model_path,
            code=code_info,
            data=data_info,
            training=training_info,
            hyperparameters=parsed_hyperparams,
            metrics=parsed_metrics,
            environment=env_info,
            session=session_info,
            session_annotations=session_annotations,
            changes_from_previous=changes_from_prev,
            reasoning=reasoning,
        )

        # Save .vcm.json attached to the model file
        json_file_path = f"{abs_model_path}.vcm.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            f.write(metadata.to_json())

        # Index in SQLite (upsert if model hash already exists)
        existing_id = self.db.get_model_id_by_hash(model_hash)
        if existing_id is not None:
            self.db.update_model(existing_id, metadata)
            inserted_id = existing_id
        else:
            inserted_id = self.db.insert_model(metadata)

        if reasoning and inserted_id is not None:
            try:
                self.db.add_reasoning(
                    inserted_id,
                    reasoning=reasoning,
                    user=training_info.user or "",
                    force=True,
                )
            except Exception:
                pass

        # Log into active session if active
        if active_tracker is not None:
            active_tracker.log_model(
                model_meta=metadata,
                model_name=model_name,
                metrics=parsed_metrics,
            )
            if inserted_id is not None:
                try:
                    pos = session_info.position_in_session if session_info and session_info.position_in_session else 1
                    self.db.link_model_to_session(
                        active_tracker.session_id,
                        inserted_id,
                        position=pos,
                    )
                except Exception:
                    pass

        return metadata

    @contextmanager
    def track(
        self,
        model_name: str,
        model_path: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
        dataset_path: Optional[str] = None,
    ) -> Generator[TrackingSession, None, None]:
        """Context manager mode for tracking training runs."""
        session = TrackingSession(
            tracker=self,
            model_name=model_name,
            model_path=model_path,
            hyperparameters=hyperparameters,
        )
        start_time = time.time()
        try:
            yield session
        finally:
            duration = time.time() - start_time
            if os.path.exists(model_path):
                self.log_model(
                    model_path=model_path,
                    model_name=model_name,
                    metrics=session.metrics,
                    hyperparameters=session.hyperparameters,
                    dataset_path=dataset_path,
                    duration_seconds=duration,
                )

    @classmethod
    def track_function(
        cls,
        model_name: str,
        model_path: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
        dataset_path: Optional[str] = None,
    ) -> Callable[..., Any]:
        """Decorator mode for model tracking."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                tracker = cls()
                with tracker.track(
                    model_name=model_name,
                    model_path=model_path,
                    hyperparameters=hyperparameters,
                    dataset_path=dataset_path,
                ) as session:
                    result = func(*args, **kwargs)
                    if isinstance(result, dict):
                        session.set_metrics(result)
                    return result
            return wrapper
        return decorator

    def run_and_track(
        self,
        script_path: str,
        model_name: str,
        dataset: Optional[str] = None,
        metrics_path: Optional[str] = None,
        params: Optional[List[str]] = None,
        model_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> MetadataModel:
        """Execute user's training script as subprocess and capture all outputs & metadata."""
        abs_script = os.path.abspath(script_path) if not os.path.isabs(script_path) else script_path
        if not os.path.exists(abs_script):
            raise FileNotFoundError(f"Training script not found: {script_path}")

        # Parse CLI key=value parameters
        hyperparameters = MetricsLoader.parse_cli_params(params or [])

        start_time = time.time()

        # Run user's training script with forwarded flags and hyperparameters
        cmd = [sys.executable, abs_script]
        expected_output = model_file or os.path.join(self.config.models_dir, f"{model_name}.pkl")
        cmd.extend(["--output", expected_output])
        if dataset:
            cmd.extend(["--dataset", dataset])
        if metrics_path:
            cmd.extend(["--metrics-out", metrics_path])
        for k, v in hyperparameters.items():
            cmd.extend([f"--{k.replace('_', '-')}", str(v)])

        proc = subprocess.run(cmd, cwd=self.repo_path, capture_output=False)
        if proc.returncode != 0:
            raise RuntimeError(f"Training script {script_path} failed with exit code {proc.returncode}")

        duration = time.time() - start_time

        # Read metrics
        metrics: Dict[str, float] = {}
        if metrics_path:
            metrics = MetricsLoader.from_json_file(metrics_path)

        # Locate output model file
        target_model_file = None
        if model_file and os.path.exists(model_file):
            target_model_file = model_file
        else:
            # Check models directory or default extensions (.pkl, .pt, .onnx, .bin)
            models_dir = output_dir or self.config.models_dir
            candidate_paths = [
                os.path.join(models_dir, f"{model_name}.pkl"),
                os.path.join(models_dir, f"{model_name}.pt"),
                os.path.join(models_dir, f"{model_name}.bin"),
                os.path.join(self.repo_path, f"{model_name}.pkl"),
            ]
            for p in candidate_paths:
                if os.path.exists(p):
                    target_model_file = p
                    break

        if not target_model_file or not os.path.exists(target_model_file):
            expected = model_file or os.path.join(self.config.models_dir, f"{model_name}.pkl")
            raise FileNotFoundError(
                f"Model file not created by training script. Expected model at '{expected}'"
            )

        return self.log_model(
            model_path=target_model_file,
            model_name=model_name,
            metrics=metrics,
            hyperparameters=hyperparameters,
            dataset_path=dataset,
            duration_seconds=duration,
            reasoning=reasoning,
        )
