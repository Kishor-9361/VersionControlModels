"""Configuration management for VCM (.vcmconfig.yaml)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class VCMConfig:
    """Represents configuration loaded from or saved to .vcmconfig.yaml."""

    config_path: str = ".vcmconfig.yaml"
    version: str = "1.0"
    database_path: str = ".vcm/vcm.db"
    models_dir: str = "models"
    git_enabled: bool = True
    dvc_enabled: bool = True
    mlflow_enabled: bool = False
    mlflow_tracking_uri: str = "file:./mlruns"
    mlflow_experiment_name: str = "Default"
    auto_tracking: Dict[str, Any] = field(
        default_factory=lambda: {
            "capture_environment": True,
            "capture_terminal": False,
        }
    )

    def is_initialized(self) -> bool:
        """Return True if the configuration file exists on disk."""
        return os.path.exists(self.config_path)

    def get_enabled_integrations(self) -> List[str]:
        """Return a list of enabled integration names."""
        enabled = []
        if self.git_enabled:
            enabled.append("git")
        if self.dvc_enabled:
            enabled.append("dvc")
        if self.mlflow_enabled:
            enabled.append("mlflow")
        return enabled

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary suitable for YAML serialization."""
        return {
            "vcm": {
                "version": self.version,
                "database_path": self.database_path,
                "models_dir": self.models_dir,
            },
            "integrations": {
                "git": {"enabled": self.git_enabled},
                "dvc": {"enabled": self.dvc_enabled},
                "mlflow": {
                    "enabled": self.mlflow_enabled,
                    "tracking_uri": self.mlflow_tracking_uri,
                    "experiment_name": self.mlflow_experiment_name,
                },
            },
            "auto_tracking": dict(self.auto_tracking),
        }

    def save(self, path: Optional[str] = None) -> None:
        """Write current configuration to YAML file."""
        target_path = path or self.config_path
        self.config_path = target_path
        parent = os.path.dirname(target_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, config_path: str = ".vcmconfig.yaml") -> VCMConfig:
        """Load configuration from YAML file or return defaults if not found/invalid."""
        if not os.path.exists(config_path):
            return cls(config_path=config_path)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return cls(config_path=config_path)

            vcm_sec = data.get("vcm", {})
            int_sec = data.get("integrations", {})
            auto_sec = data.get("auto_tracking", {})
            mlflow_sec = int_sec.get("mlflow", {})

            return cls(
                config_path=config_path,
                version=str(vcm_sec.get("version", "1.0")),
                database_path=str(vcm_sec.get("database_path", ".vcm/vcm.db")),
                models_dir=str(vcm_sec.get("models_dir", "models")),
                git_enabled=bool(int_sec.get("git", {}).get("enabled", True)),
                dvc_enabled=bool(int_sec.get("dvc", {}).get("enabled", True)),
                mlflow_enabled=bool(mlflow_sec.get("enabled", False)),
                mlflow_tracking_uri=str(mlflow_sec.get("tracking_uri", "file:./mlruns")),
                mlflow_experiment_name=str(mlflow_sec.get("experiment_name", "Default")),
                auto_tracking=dict(auto_sec) if isinstance(auto_sec, dict) else {},
            )
        except Exception:
            return cls(config_path=config_path)
