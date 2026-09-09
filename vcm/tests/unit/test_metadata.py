"""Unit tests for MetadataModel (UT-1.1 to UT-1.5)."""

import json
import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError

from vcm.models.metadata import (
    MetadataModel,
    CodeInfo,
    DataInfo,
    DVCFileInfo,
    TrainingInfo,
    EnvironmentInfo,
    ValidationError,
)


def test_ut_1_1_metadata_model_initialization():
    """UT-1.1: MetadataModel can be created with required fields."""
    metadata = MetadataModel(
        model_name="classifier_v1",
        model_hash="sha256:abc123",
        metrics={"accuracy": 0.94},
    )

    assert metadata.model_name == "classifier_v1"
    assert metadata.model_hash == "sha256:abc123"
    assert metadata.metrics == {"accuracy": 0.94}
    assert metadata.metadata_version == "1.0"
    assert metadata.created_at is not None
    assert isinstance(metadata.created_at, datetime)
    assert metadata.code is not None
    assert metadata.data is not None
    assert metadata.training is not None
    assert metadata.environment is not None


def test_ut_1_2_metadata_model_json_serialization():
    """UT-1.2: MetadataModel can serialize to JSON."""
    dvc_file = DVCFileInfo(
        path="data/train.csv",
        dvc_hash="xyz789",
        size_bytes=1024,
        timestamp="2024-01-15T10:30:00Z",
    )
    metadata = MetadataModel(
        model_name="classifier_v2",
        model_hash="sha256:abc123",
        model_file="models/classifier_v2.pkl",
        code=CodeInfo(
            git_commit="abc123def456",
            git_branch="main",
            git_remote="origin",
            git_url="https://github.com/user/repo",
        ),
        data=DataInfo(dvc_files=[dvc_file]),
        training=TrainingInfo(
            timestamp="2024-01-15T10:45:32Z",
            duration_seconds=3600.0,
            user="alice",
            hostname="ml-box",
        ),
        hyperparameters={"lr": 0.001, "epochs": 50},
        metrics={"accuracy": 0.942, "f1_score": 0.928},
        environment=EnvironmentInfo(
            python_version="3.9.1",
            libraries={"torch": "2.0.1", "pandas": "2.0.0"},
        ),
    )

    data_dict = metadata.to_dict()
    assert isinstance(data_dict, dict)
    assert data_dict["model_name"] == "classifier_v2"
    assert data_dict["code"]["git_commit"] == "abc123def456"
    assert len(data_dict["data"]["dvc_files"]) == 1
    assert data_dict["metrics"]["accuracy"] == 0.942

    json_str = metadata.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["model_name"] == "classifier_v2"
    assert parsed["metadata_version"] == "1.0"


def test_ut_1_3_metadata_model_json_deserialization():
    """UT-1.3: MetadataModel can deserialize from JSON."""
    raw_json = json.dumps({
        "model_name": "emotion_classifier_v2",
        "model_hash": "sha256:abc123def",
        "model_file": "models/emotion_classifier_v2.pkl",
        "code": {
            "git_commit": "abc123def456",
            "git_branch": "main",
            "git_remote": "origin",
            "git_url": "https://github.com/user/repo"
        },
        "data": {
            "dvc_files": [
                {
                    "path": "data/train.csv",
                    "dvc_hash": "xyz789",
                    "size_bytes": 1024000,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            ]
        },
        "training": {
            "timestamp": "2024-01-15T10:45:32Z",
            "duration_seconds": 3600,
            "user": "alice",
            "hostname": "ml-workstation-1"
        },
        "hyperparameters": {
            "learning_rate": 0.001,
            "epochs": 50,
            "batch_size": 32,
            "random_seed": 42
        },
        "metrics": {
            "accuracy": 0.942,
            "f1_score": 0.928
        },
        "environment": {
            "python_version": "3.9.1",
            "libraries": {
                "torch": "2.0.1",
                "scikit-learn": "1.2.0"
            }
        },
        "metadata_version": "1.0",
        "created_at": "2024-01-15T10:45:32Z"
    })

    model = MetadataModel.from_json(raw_json)
    assert model.model_name == "emotion_classifier_v2"
    assert model.model_hash == "sha256:abc123def"
    assert model.code.git_commit == "abc123def456"
    assert model.code.git_branch == "main"
    assert len(model.data.dvc_files) == 1
    assert model.data.dvc_files[0].path == "data/train.csv"
    assert model.metrics["accuracy"] == 0.942
    assert model.hyperparameters["learning_rate"] == 0.001
    assert isinstance(model.created_at, datetime)


def test_ut_1_4_metadata_model_field_validation():
    """UT-1.4: MetadataModel rejects invalid data."""
    # model_name cannot be empty or None
    with pytest.raises(ValidationError, match="model_name"):
        MetadataModel(model_name="", model_hash="sha256:123", metrics={})

    # accuracy or metrics must be numbers
    with pytest.raises(ValidationError, match="numeric"):
        MetadataModel(
            model_name="test",
            model_hash="sha256:123",
            metrics={"accuracy": "not_a_number"},  # type: ignore
        )

    # Empty metrics is allowed
    valid_empty_metrics = MetadataModel(
        model_name="test_model",
        model_hash="sha256:123",
        metrics={},
    )
    assert valid_empty_metrics.metrics == {}

    # Invalid code info
    with pytest.raises(ValidationError):
        MetadataModel(
            model_name="test",
            model_hash="sha256:123",
            code=CodeInfo(git_commit="", git_branch="main"),  # empty commit string
        )


def test_ut_1_5_metadata_model_immutability():
    """UT-1.5: Metadata object is immutable after creation."""
    metadata = MetadataModel(
        model_name="test_model",
        model_hash="sha256:123",
        metrics={"accuracy": 0.90},
    )

    with pytest.raises((FrozenInstanceError, AttributeError)):
        metadata.accuracy = 0.50


def test_metadata_model_edge_cases_and_coverage():
    """Test edge cases to ensure >95% test coverage."""
    # Test from_dict on submodels with None
    assert CodeInfo.from_dict(None) == CodeInfo()
    assert DataInfo.from_dict(None) == DataInfo()
    assert TrainingInfo.from_dict(None) == TrainingInfo()
    assert EnvironmentInfo.from_dict(None) == EnvironmentInfo()

    # Test DVCFileInfo validation
    with pytest.raises(ValidationError):
        DVCFileInfo(path="", dvc_hash="123")
    with pytest.raises(ValidationError):
        DVCFileInfo(path="data.csv", dvc_hash="123", size_bytes=-1)

    # Test DataInfo with existing DVCFileInfo objects
    dvc_obj = DVCFileInfo(path="a.csv", dvc_hash="h1")
    data_info = DataInfo.from_dict({"dvc_files": [dvc_obj]})
    assert len(data_info.dvc_files) == 1

    # Test invalid json in from_json
    with pytest.raises(ValidationError, match="Invalid JSON"):
        MetadataModel.from_json("invalid json string {")

    # Test invalid dict in from_dict
    with pytest.raises(ValidationError, match="dictionary"):
        MetadataModel.from_dict("not a dict")

    # Test validation error on empty model_hash
    with pytest.raises(ValidationError, match="model_hash"):
        MetadataModel(model_name="m1", model_hash="", metrics={})

    # Test validation error on non-dict metrics
    with pytest.raises(ValidationError, match="metrics"):
        MetadataModel(model_name="m1", model_hash="h1", metrics="invalid")

    # Test validation error on non-dict hyperparameters
    with pytest.raises(ValidationError, match="hyperparameters"):
        MetadataModel(model_name="m1", model_hash="h1", metrics={}, hyperparameters="invalid")

    # Test validation error on empty metadata_version
    with pytest.raises(ValidationError, match="metadata_version"):
        MetadataModel(model_name="m1", model_hash="h1", metrics={}, metadata_version="")

    # Test validation error on created_at not datetime
    with pytest.raises(ValidationError, match="created_at"):
        MetadataModel(model_name="m1", model_hash="h1", metrics={}, created_at="2024-01-01")

    # Test from_dict with ISO string date and invalid date string fallback
    m_iso = MetadataModel.from_dict({
        "model_name": "m1",
        "model_hash": "h1",
        "created_at": "invalid_date_format",
    })
    assert isinstance(m_iso.created_at, datetime)

    m_dt = MetadataModel.from_dict({
        "model_name": "m1",
        "model_hash": "h1",
        "created_at": datetime.now(),
    })
    assert isinstance(m_dt.created_at, datetime)
