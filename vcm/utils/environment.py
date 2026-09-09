"""Environment and library dependency capture utilities."""

from __future__ import annotations

import getpass
import importlib.metadata
import platform
import socket
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Standard key ML & data packages to automatically track if installed
KEY_LIBRARIES = [
    "torch",
    "torchvision",
    "torchaudio",
    "scikit-learn",
    "sklearn",
    "pandas",
    "numpy",
    "scipy",
    "tensorflow",
    "keras",
    "xgboost",
    "lightgbm",
    "catboost",
    "transformers",
    "datasets",
    "accelerate",
    "optuna",
    "dvc",
    "GitPython",
    "click",
    "pyyaml",
]


class EnvironmentCapture:
    """Captures Python runtime, installed libraries, and system information."""

    @staticmethod
    def get_python_version() -> str:
        """Return the current Python version string (e.g. '3.9.1')."""
        return platform.python_version()

    @staticmethod
    def get_libraries(packages: Optional[List[str]] = None) -> Dict[str, str]:
        """Return a dictionary of {package_name: version} for installed libraries."""
        target_pkgs = packages if packages is not None else KEY_LIBRARIES
        installed: Dict[str, str] = {}

        for pkg in target_pkgs:
            try:
                version = importlib.metadata.version(pkg)
                installed[pkg] = version
            except importlib.metadata.PackageNotFoundError:
                continue
            except Exception:
                continue

        return installed

    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Return system context including hostname, OS, user, and timestamp."""
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "localhost"

        try:
            user = getpass.getuser()
        except Exception:
            user = "unknown"

        return {
            "hostname": hostname,
            "os": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "user": user,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def capture_all(cls, packages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Bundle all environment information into a dictionary."""
        return {
            "python_version": cls.get_python_version(),
            "libraries": cls.get_libraries(packages),
            "system": cls.get_system_info(),
        }
