"""Unit tests for MLflow integration client and CLI commands."""

import json
import os
from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.config import VCMConfig
from vcm.integrations.mlflow_client import MLflowClient
from vcm.models.metadata import MetadataModel


def _create_sample_metadata(tmp_path, name: str = "iris_test_v1") -> MetadataModel:
    meta_dict = {
        "model_name": name,
        "model_hash": "sha256_mock_hash_123456",
        "model_file": f"models/{name}.pkl",
        "code": {
            "git_commit": "abcdef123456",
            "git_branch": "main",
            "repository_url": "https://github.com/example/repo",
        },
        "data": {
            "dvc_files": [{"path": "data/train.csv", "dvc_hash": "hash123"}],
        },
        "training": {
            "timestamp": "2026-09-19T05:00:00+00:00",
            "user": "testuser",
        },
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 5,
        },
        "metrics": {
            "accuracy": 0.96,
            "f1_score": 0.95,
        },
        "environment": {
            "python_version": "3.14.7",
            "libraries": {"scikit-learn": "1.9.0"},
        },
        "metadata_version": "1.0",
        "reasoning": "Baseline ensemble for benchmarking",
    }
    sidecar = tmp_path / f"{name}.vcm.json"
    sidecar.write_text(json.dumps(meta_dict))
    return MetadataModel.from_dict(meta_dict)


def test_mlflow_client_initialization(tmp_path):
    """Verify default configurations and offline mode detection."""
    cfg = VCMConfig(config_path=str(tmp_path / ".vcmconfig.yaml"))
    cfg.save()

    client = MLflowClient(repo_path=str(tmp_path))
    assert client.tracking_uri == "file:./mlruns"
    assert client.experiment_name == "Default"
    assert not client.enabled


def test_mlflow_offline_sync(tmp_path):
    """Verify offline file store writes valid MLflow run structure."""
    meta = _create_sample_metadata(tmp_path)
    mlruns_dir = tmp_path / "mlruns"

    client = MLflowClient(
        tracking_uri=f"file:{mlruns_dir}",
        experiment_name="IrisClassification",
        repo_path=str(tmp_path),
    )

    res = client.sync_model(meta)
    assert res["status"] == "success"
    assert res["mode"] == "offline_filestore"
    assert res["model_name"] == "iris_test_v1"

    # Verify directory structure
    exp_dir = mlruns_dir / "0"
    assert (exp_dir / "meta.yaml").exists()

    run_dir = exp_dir / res["run_id"]
    assert (run_dir / "meta.yaml").exists()
    assert (run_dir / "params" / "n_estimators").read_text() == "100"
    assert (run_dir / "tags" / "vcm.model_name").read_text() == "iris_test_v1"
    assert (run_dir / "tags" / "vcm.git_commit").read_text() == "abcdef123456"
    assert (run_dir / "tags" / "vcm.reasoning").read_text() == "Baseline ensemble for benchmarking"
    assert (run_dir / "artifacts" / "iris_test_v1.vcm.json").exists()


def test_mlflow_cli_status(tmp_path):
    """Verify 'vcm mlflow status' command output."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    res = runner.invoke(cli, ["mlflow", "status"])
    assert res.exit_code == 0
    assert "MLflow Integration Status" in res.output
    assert "Tracking URI:" in res.output
    assert "Experiment:" in res.output


def test_mlflow_cli_enable_disable(tmp_path):
    """Verify 'vcm mlflow enable' and 'vcm mlflow disable' update configuration."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    res_en = runner.invoke(cli, ["mlflow", "enable"])
    assert res_en.exit_code == 0
    assert "MLflow integration enabled" in res_en.output

    cfg = VCMConfig.load(".vcmconfig.yaml")
    assert cfg.mlflow_enabled is True

    res_dis = runner.invoke(cli, ["mlflow", "disable"])
    assert res_dis.exit_code == 0
    assert "MLflow integration disabled" in res_dis.output

    cfg_after = VCMConfig.load(".vcmconfig.yaml")
    assert cfg_after.mlflow_enabled is False


def test_mlflow_cli_sync(tmp_path):
    """Verify 'vcm mlflow sync' logs model to MLflow."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    # Create dummy trained model
    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'weights')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.98}, f)

    runner.invoke(cli, [
        "train",
        "--model-name", "m1",
        "--script", "train.py",
        "--metrics", "metrics.json",
        "--reasoning", "MLflow test run",
    ])

    res_sync = runner.invoke(cli, ["mlflow", "sync", "m1"])
    assert res_sync.exit_code == 0
    assert "Model 'm1' synced to MLflow successfully." in res_sync.output
    assert "Run ID:" in res_sync.output

    res_sync_all = runner.invoke(cli, ["mlflow", "sync", "--all"])
    assert res_sync_all.exit_code == 0
    assert "Synced 1 model(s) to MLflow" in res_sync_all.output
