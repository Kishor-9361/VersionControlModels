"""VCM (Version Control Models) - Model DNA Version Control Platform."""

__version__ = "1.0.0"
__author__ = "VCM Team"

from vcm.models.metadata import (
    MetadataModel,
    CodeInfo,
    DataInfo,
    DVCFileInfo,
    TrainingInfo,
    EnvironmentInfo,
    ValidationError,
)
from vcm.db.database import Database, DatabaseError
from vcm.config import VCMConfig
from vcm.utils.environment import EnvironmentCapture
from vcm.utils.metrics_loader import MetricsLoader
from vcm.utils.hashing import compute_file_hash, compute_data_hash

__all__ = [
    "MetadataModel",
    "CodeInfo",
    "DataInfo",
    "DVCFileInfo",
    "TrainingInfo",
    "EnvironmentInfo",
    "ValidationError",
    "Database",
    "DatabaseError",
    "VCMConfig",
    "EnvironmentCapture",
    "MetricsLoader",
    "compute_file_hash",
    "compute_data_hash",
]
