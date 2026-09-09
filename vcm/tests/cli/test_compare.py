"""CLI Test 8: vcm compare command."""

import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli


def test_cli_8_vcm_compare(tmp_path):
    """CLI-8: vcm compare shows differences between two models."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        m1_path = "models/classifier_v1.pkl"
        m2_path = "models/classifier_v2.pkl"
        with open(m1_path, "wb") as f:
            f.write(b"model 1 bytes")
        with open(m2_path, "wb") as f:
            f.write(b"model 2 bytes")

        with open("train.py", "w") as f:
            f.write("pass\n")

        with open("m1_metrics.json", "w") as f:
            json.dump({"accuracy": 0.915, "f1_score": 0.902}, f)

        with open("m2_metrics.json", "w") as f:
            json.dump({"accuracy": 0.942, "f1_score": 0.928}, f)

        runner.invoke(cli, [
            "train",
            "--model-name", "classifier_v1",
            "--script", "train.py",
            "--metrics", "m1_metrics.json",
            "--model-file", m1_path,
            "--params", "lr=0.01",
            "--params", "epochs=30",
        ])

        runner.invoke(cli, [
            "train",
            "--model-name", "classifier_v2",
            "--script", "train.py",
            "--metrics", "m2_metrics.json",
            "--model-file", m2_path,
            "--params", "lr=0.001",
            "--params", "epochs=50",
        ])

        result = runner.invoke(cli, ["compare", m1_path, m2_path])
        assert result.exit_code == 0
        assert "classifier_v1" in result.output
        assert "classifier_v2" in result.output
        assert "Accuracy" in result.output or "accuracy" in result.output
        assert "91.5" in result.output or "0.915" in result.output
        assert "94.2" in result.output or "0.942" in result.output
