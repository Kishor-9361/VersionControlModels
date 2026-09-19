"""Scenario 1: Single Model Training with Data Versioning."""

import json
import os
from click.testing import CliRunner

from vcm.cli.main import cli


def test_scenario_1_single_model_training(iris_project):
    """Verify all metadata captured for single model."""
    runner = CliRunner()

    result = runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v1",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=10",
        "--params", "max_depth=5",
        "--params", "random_state=42",
    ])
    assert result.exit_code == 0
    assert "Model tracked successfully" in result.output

    # Load and inspect metadata
    metadata_path = "models/iris_classifier_v1.pkl.vcm.json"
    assert os.path.exists(metadata_path)

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Code tracking
    assert metadata["code"]["git_commit"] is not None
    assert len(metadata["code"]["git_commit"]) == 40
    assert metadata["code"]["git_branch"] is not None

    # Data tracking
    assert len(metadata["data"]["dvc_files"]) >= 1
    assert any("iris_train_v1.0.csv" in f["path"] for f in metadata["data"]["dvc_files"])
    assert all("dvc_hash" in f for f in metadata["data"]["dvc_files"])

    # Metrics
    assert metadata["metrics"]["accuracy"] >= 0.90
    for m in ["accuracy", "precision", "recall", "f1_score"]:
        assert m in metadata["metrics"]

    # Hyperparameters
    assert metadata["hyperparameters"]["n_estimators"] == 10
    assert metadata["hyperparameters"]["max_depth"] == 5

    # Environment
    assert "scikit-learn" in metadata["environment"]["libraries"]
    assert metadata["environment"]["python_version"].startswith("3.")

    # Training context
    assert metadata["training"]["duration_seconds"] < 60
    assert metadata["training"]["user"] is not None
