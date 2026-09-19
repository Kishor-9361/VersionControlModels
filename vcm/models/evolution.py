"""Data models for Model Evolution Timeline tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class ModelDifference:
    """What changed between two consecutive models."""

    code_changed: bool = False
    code_files: List[str] = field(default_factory=list)
    git_commits: List[str] = field(default_factory=list)

    data_changed: bool = False
    data_files: List[str] = field(default_factory=list)
    data_hashes_changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    hyperparams_changed: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)

    environment_changed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "code_changed": self.code_changed,
            "code_files": list(self.code_files),
            "git_commits": list(self.git_commits),
            "data_changed": self.data_changed,
            "data_files": list(self.data_files),
            "data_hashes_changed": dict(self.data_hashes_changed),
            "hyperparams_changed": dict(self.hyperparams_changed),
            "environment_changed": self.environment_changed,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> ModelDifference:
        """Hydrate from dictionary."""
        if not data:
            return cls()
        return cls(
            code_changed=bool(data.get("code_changed", False)),
            code_files=list(data.get("code_files", [])),
            git_commits=list(data.get("git_commits", [])),
            data_changed=bool(data.get("data_changed", False)),
            data_files=list(data.get("data_files", [])),
            data_hashes_changed=dict(data.get("data_hashes_changed", {})),
            hyperparams_changed=dict(data.get("hyperparams_changed", {})),
            environment_changed=bool(data.get("environment_changed", False)),
        )


@dataclass(frozen=True)
class Annotation:
    """User note about a model in timeline."""

    timestamp: datetime
    text: str
    added_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        ts_str = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
        return {
            "timestamp": ts_str,
            "text": self.text,
            "added_by": self.added_by,
        }


@dataclass(frozen=True)
class EvolutionEntry:
    """One step in model evolution progression."""

    position: int
    model_name: str
    model_id: int
    timestamp: datetime
    accuracy: float
    metrics: Dict[str, float] = field(default_factory=dict)

    # Reasoning / context
    reasoning: Optional[str] = None
    reasoning_added_by: Optional[str] = None
    reasoning_timestamp: Optional[datetime] = None

    # Relationships
    previous_model: Optional[str] = None
    next_model: Optional[str] = None
    previous_model_accuracy: Optional[float] = None
    accuracy_improvement: Optional[float] = None

    # Changes from previous
    changes: Optional[ModelDifference] = None

    # Context
    session_id: Optional[str] = None
    git_commit: str = ""

    def __post_init__(self) -> None:
        """Calculate accuracy improvement if delta is not explicitly passed."""
        if self.accuracy_improvement is None and self.previous_model_accuracy is not None:
            delta = self.accuracy - self.previous_model_accuracy
            object.__setattr__(self, "accuracy_improvement", delta)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        ts_str = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
        reasoning_ts_str = (
            self.reasoning_timestamp.isoformat()
            if isinstance(self.reasoning_timestamp, datetime)
            else (str(self.reasoning_timestamp) if self.reasoning_timestamp else None)
        )
        return {
            "position": self.position,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "timestamp": ts_str,
            "accuracy": self.accuracy,
            "metrics": dict(self.metrics),
            "reasoning": self.reasoning,
            "reasoning_added_by": self.reasoning_added_by,
            "reasoning_timestamp": reasoning_ts_str,
            "previous_model": self.previous_model,
            "next_model": self.next_model,
            "previous_model_accuracy": self.previous_model_accuracy,
            "accuracy_improvement": self.accuracy_improvement,
            "changes": self.changes.to_dict() if self.changes else None,
            "session_id": self.session_id,
            "git_commit": self.git_commit,
        }


@dataclass(frozen=True)
class ModelTimeline:
    """Complete evolution progression for models."""

    entries: List[EvolutionEntry]
    total_models: int
    best_model: Optional[str]
    worst_model: Optional[str]
    best_accuracy: float
    worst_accuracy: float
    accuracy_improvement: float
    date_range: Tuple[Optional[datetime], Optional[datetime]]
    session_ids: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        start_str = self.date_range[0].isoformat() if self.date_range[0] else None
        end_str = self.date_range[1].isoformat() if self.date_range[1] else None
        return {
            "entries": [e.to_dict() for e in self.entries],
            "total_models": self.total_models,
            "best_model": self.best_model,
            "worst_model": self.worst_model,
            "best_accuracy": self.best_accuracy,
            "worst_accuracy": self.worst_accuracy,
            "accuracy_improvement": self.accuracy_improvement,
            "date_range": [start_str, end_str],
            "session_ids": list(self.session_ids),
        }
