"""DVC (Data Version Control) integration for VCM."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional
import yaml

from vcm.models.metadata import DataInfo, DVCFileInfo
from vcm.utils.hashing import compute_file_hash

logger = logging.getLogger(__name__)


class DVCNotInstalledWarning(Warning):
    """Warning issued when DVC is not installed or repository has no DVC setup."""
    pass


class DVCClient:
    """Inspects DVC-tracked dataset files and hashes within a project."""

    def __init__(self, repo_path: str = ".") -> None:
        self.repo_path = os.path.abspath(repo_path)

    def is_initialized(self) -> bool:
        """Return True if project has .dvc directory or dvc.yaml file."""
        dvc_dir = os.path.join(self.repo_path, ".dvc")
        dvc_yaml = os.path.join(self.repo_path, "dvc.yaml")
        return os.path.isdir(dvc_dir) or os.path.isfile(dvc_yaml)

    def get_tracked_files(self) -> List[DVCFileInfo]:
        """Scan repository for .dvc tracking files and return list of DVCFileInfo."""
        if not self.is_initialized():
            return []

        tracked_files: List[DVCFileInfo] = []

        try:
            for root, _, files in os.walk(self.repo_path):
                # Ignore .git, .vcm, venv directories
                if any(ignored in root for ignored in [".git", ".vcm", "venv", ".venv", "__pycache__"]):
                    continue

                for file in files:
                    if file.endswith(".dvc"):
                        dvc_file_path = os.path.join(root, file)
                        try:
                            with open(dvc_file_path, "r", encoding="utf-8") as f:
                                dvc_data = yaml.safe_load(f)
                            if not isinstance(dvc_data, dict):
                                continue

                            outs = dvc_data.get("outs", [])
                            for out in outs:
                                if not isinstance(out, dict):
                                    continue
                                out_rel_path = out.get("path", "")
                                target_abs = os.path.join(root, out_rel_path)
                                target_rel = os.path.relpath(target_abs, self.repo_path)

                                dvc_hash = str(out.get("md5") or out.get("hash") or out.get("etag") or "")
                                size_bytes = int(out.get("size", 0))

                                timestamp = None
                                if os.path.exists(target_abs):
                                    mtime = os.path.getmtime(target_abs)
                                    timestamp = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

                                tracked_files.append(
                                    DVCFileInfo(
                                        path=target_rel,
                                        dvc_hash=dvc_hash,
                                        size_bytes=size_bytes,
                                        timestamp=timestamp,
                                    )
                                )
                        except Exception as exc:
                            logger.warning("Error reading .dvc file %s: %s", dvc_file_path, exc)

            # Also check dvc.lock if present
            lock_path = os.path.join(self.repo_path, "dvc.lock")
            if os.path.isfile(lock_path):
                try:
                    with open(lock_path, "r", encoding="utf-8") as f:
                        lock_data = yaml.safe_load(f)
                    if isinstance(lock_data, dict):
                        stages = lock_data.get("stages", {})
                        for stage_name, stage_info in stages.items():
                            if isinstance(stage_info, dict):
                                for out in stage_info.get("outs", []):
                                    if isinstance(out, dict):
                                        path = out.get("path", "")
                                        dvc_hash = str(out.get("md5") or out.get("hash") or "")
                                        size = int(out.get("size", 0))
                                        tracked_files.append(
                                            DVCFileInfo(
                                                path=path,
                                                dvc_hash=dvc_hash,
                                                size_bytes=size,
                                            )
                                        )
                except Exception as exc:
                    logger.warning("Error reading dvc.lock: %s", exc)

        except Exception as exc:
            logger.warning("DVC file scan encountered error: %s", exc)

        return tracked_files

    def get_file_hash(self, filepath: str) -> Optional[str]:
        """Return DVC hash if tracked by DVC, otherwise calculate SHA-256 or return None."""
        norm_path = os.path.normpath(filepath)
        if not os.path.isabs(norm_path):
            abs_path = os.path.join(self.repo_path, norm_path)
        else:
            abs_path = norm_path
            norm_path = os.path.relpath(abs_path, self.repo_path)

        # Check in DVC tracked files
        for dvc_file in self.get_tracked_files():
            if os.path.normpath(dvc_file.path) == norm_path:
                return dvc_file.dvc_hash

        # Check adjacent .dvc file
        direct_dvc = f"{abs_path}.dvc"
        if os.path.isfile(direct_dvc):
            try:
                with open(direct_dvc, "r", encoding="utf-8") as f:
                    dvc_data = yaml.safe_load(f)
                if isinstance(dvc_data, dict):
                    outs = dvc_data.get("outs", [])
                    if outs and isinstance(outs[0], dict):
                        return str(outs[0].get("md5") or outs[0].get("hash") or "")
            except Exception:
                pass

        # Fallback to direct file hash if file exists
        if os.path.isfile(abs_path):
            try:
                return compute_file_hash(abs_path)
            except Exception:
                return None

        return None

    def get_data_info(self, dataset_path: Optional[str] = None) -> DataInfo:
        """Create a DataInfo object representing DVC-tracked datasets or a specific dataset path."""
        dvc_files = self.get_tracked_files()

        # If a specific dataset was passed and not yet in dvc_files, add it
        if dataset_path:
            norm_target = os.path.normpath(dataset_path)
            already_tracked = any(os.path.normpath(f.path) == norm_target for f in dvc_files)
            if not already_tracked:
                full_path = os.path.join(self.repo_path, dataset_path) if not os.path.isabs(dataset_path) else dataset_path
                if os.path.exists(full_path):
                    h = self.get_file_hash(full_path) or ""
                    size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                    mtime = os.path.getmtime(full_path)
                    dvc_files.append(
                        DVCFileInfo(
                            path=dataset_path,
                            dvc_hash=h,
                            size_bytes=size,
                            timestamp=datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                        )
                    )

        return DataInfo(dvc_files=dvc_files)
