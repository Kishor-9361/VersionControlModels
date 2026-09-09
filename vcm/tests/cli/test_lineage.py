"""CLI Test 7: vcm lineage command."""

import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli


def test_cli_7_vcm_lineage(tmp_path):
    """CLI-7: vcm lineage displays model lineage tree."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        pkl_path = "models/test_v1.pkl"
        with open(pkl_path, "wb") as f:
            f.write(b"model pkl bytes")

        with open("train_script.py", "w") as f:
            f.write("pass\n")

        with open("metrics.json", "w") as f:
            json.dump({"accuracy": 0.942, "f1_score": 0.928}, f)

        runner.invoke(cli, [
            "train",
            "--model-name", "test_v1",
            "--script", "train_script.py",
            "--metrics", "metrics.json",
            "--model-file", pkl_path,
            "--params", "lr=0.001",
        ])

        result = runner.invoke(cli, ["lineage", pkl_path])
        assert result.exit_code == 0
        assert "test_v1" in result.output
        assert "Accuracy" in result.output or "accuracy" in result.output
        assert "0.942" in result.output or "94.2" in result.output
        assert "lr" in result.output
