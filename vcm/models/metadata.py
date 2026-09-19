"""Metadata schema, serialization, and validation for VCM."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from vcm.models.session import SessionInfo


class ValidationError(Exception):
    """Raised when metadata validation fails."""
    pass


@dataclass(frozen=True)
class CodeInfo:
    """Git and code versioning metadata."""
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    git_remote: Optional[str] = None
    git_url: Optional[str] = None

    def __post_init__(self) -> None:
        if self.git_commit is not None and not isinstance(self.git_commit, str):
            raise ValidationError("git_commit must be a string")
        if self.git_commit == "":
            raise ValidationError("git_commit cannot be an empty string")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "git_commit": self.git_commit,
            "git_branch": self.git_branch,
            "git_remote": self.git_remote,
            "git_url": self.git_url,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> CodeInfo:
        if not data:
            return cls()
        return cls(
            git_commit=data.get("git_commit"),
            git_branch=data.get("git_branch"),
            git_remote=data.get("git_remote"),
            git_url=data.get("git_url"),
        )


@dataclass(frozen=True)
class DVCFileInfo:
    """Metadata for a single DVC-tracked file or directory."""
    path: str
    dvc_hash: str
    size_bytes: int = 0
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.path or not isinstance(self.path, str):
            raise ValidationError("DVC file path must be a non-empty string")
        if not isinstance(self.size_bytes, int) or self.size_bytes < 0:
            raise ValidationError("DVC file size_bytes must be a non-negative integer")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "dvc_hash": self.dvc_hash,
            "size_bytes": self.size_bytes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DVCFileInfo:
        return cls(
            path=str(data.get("path", "")),
            dvc_hash=str(data.get("dvc_hash", "")),
            size_bytes=int(data.get("size_bytes", 0)),
            timestamp=data.get("timestamp"),
        )


@dataclass(frozen=True)
class DataInfo:
    """Dataset versioning metadata."""
    dvc_files: List[DVCFileInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dvc_files": [f.to_dict() for f in self.dvc_files]
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> DataInfo:
        if not data or "dvc_files" not in data:
            return cls()
        files = [
            DVCFileInfo.from_dict(f) if isinstance(f, dict) else f
            for f in data.get("dvc_files", [])
        ]
        return cls(dvc_files=files)


@dataclass(frozen=True)
class TrainingInfo:
    """Training run context and execution details."""
    timestamp: Optional[str] = None
    duration_seconds: Optional[float] = None
    user: Optional[str] = None
    hostname: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "user": self.user,
            "hostname": self.hostname,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> TrainingInfo:
        if not data:
            return cls()
        return cls(
            timestamp=data.get("timestamp"),
            duration_seconds=(
                float(data["duration_seconds"])
                if data.get("duration_seconds") is not None
                else None
            ),
            user=data.get("user"),
            hostname=data.get("hostname"),
        )


@dataclass(frozen=True)
class EnvironmentInfo:
    """Python runtime and library environment metadata."""
    python_version: str = "unknown"
    libraries: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "python_version": self.python_version,
            "libraries": dict(self.libraries),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> EnvironmentInfo:
        if not data:
            return cls()
        return cls(
            python_version=str(data.get("python_version", "unknown")),
            libraries=dict(data.get("libraries", {})),
        )


@dataclass(frozen=True)
class MetadataModel:
    """Immutable Model DNA Metadata record matching VCM MVP specification."""
    model_name: str
    model_hash: str
    model_file: str = ""
    code: CodeInfo = field(default_factory=CodeInfo)
    data: DataInfo = field(default_factory=DataInfo)
    training: TrainingInfo = field(default_factory=TrainingInfo)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Union[int, float]] = field(default_factory=dict)
    environment: EnvironmentInfo = field(default_factory=EnvironmentInfo)
    metadata_version: str = "1.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session: Optional[SessionInfo] = None
    session_annotations: List[Dict[str, Any]] = field(default_factory=list)
    changes_from_previous: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    evolution: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.model_name or not isinstance(self.model_name, str) or not self.model_name.strip():
            raise ValidationError("model_name must be a non-empty string")
        if not self.model_hash or not isinstance(self.model_hash, str) or not self.model_hash.strip():
            raise ValidationError("model_hash must be a non-empty string")
        if not isinstance(self.metrics, dict):
            raise ValidationError("metrics must be a dictionary")
        for k, v in self.metrics.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise ValidationError(f"metric '{k}' must be numeric (int or float), got {type(v).__name__}")
        if not isinstance(self.hyperparameters, dict):
            raise ValidationError("hyperparameters must be a dictionary")
        if not isinstance(self.metadata_version, str) or not self.metadata_version:
            raise ValidationError("metadata_version must be a non-empty string")
        if not isinstance(self.created_at, datetime):
            raise ValidationError("created_at must be a datetime instance")

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary with ISO-formatted datetimes."""
        created_str = (
            self.created_at.isoformat()
            if isinstance(self.created_at, datetime)
            else str(self.created_at)
        )
        d: Dict[str, Any] = {
            "model_name": self.model_name,
            "model_hash": self.model_hash,
            "model_file": self.model_file,
            "code": self.code.to_dict(),
            "data": self.data.to_dict(),
            "training": self.training.to_dict(),
            "hyperparameters": dict(self.hyperparameters),
            "metrics": dict(self.metrics),
            "environment": self.environment.to_dict(),
            "metadata_version": self.metadata_version,
            "created_at": created_str,
        }
        if self.session is not None:
            d["session"] = self.session.to_dict()
        if self.session_annotations:
            d["session_annotations"] = list(self.session_annotations)
        if self.changes_from_previous is not None:
            d["changes_from_previous"] = dict(self.changes_from_previous)
        if self.reasoning is not None:
            d["reasoning"] = self.reasoning
        if self.evolution is not None:
            d["evolution"] = dict(self.evolution)
        return d

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style subscripting for test compatibility."""
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dictionary-style get for test compatibility."""
        return self.to_dict().get(key, default)

    def to_json(self, indent: int = 2) -> str:
        """Serialize metadata object to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetadataModel:
        """Create a MetadataModel instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")

        created_raw = data.get("created_at")
        if isinstance(created_raw, datetime):
            created_at = created_raw
        elif isinstance(created_raw, str):
            try:
                # Handle ISO format with Z or timezone offset
                created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now(timezone.utc)
        else:
            created_at = datetime.now(timezone.utc)

        session_data = data.get("session")
        if session_data:
            from vcm.models.session import SessionInfo
            session_info = SessionInfo.from_dict(session_data)
        else:
            session_info = None

        return cls(
            model_name=data.get("model_name", ""),
            model_hash=data.get("model_hash", ""),
            model_file=data.get("model_file", ""),
            code=CodeInfo.from_dict(data.get("code")),
            data=DataInfo.from_dict(data.get("data")),
            training=TrainingInfo.from_dict(data.get("training")),
            hyperparameters=dict(data.get("hyperparameters", {})),
            metrics=dict(data.get("metrics", {})),
            environment=EnvironmentInfo.from_dict(data.get("environment")),
            metadata_version=str(data.get("metadata_version", "1.0")),
            created_at=created_at,
            session=session_info,
            session_annotations=list(data.get("session_annotations", [])),
            changes_from_previous=data.get("changes_from_previous"),
            reasoning=data.get("reasoning"),
            evolution=data.get("evolution"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> MetadataModel:
        """Deserialize JSON string to a MetadataModel instance."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSON string: {exc}") from exc
        return cls.from_dict(data)
