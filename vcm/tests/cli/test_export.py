"""CLI Test 10: vcm export command."""

import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli


def test_cli_10_vcm_export(tmp_path):
    """CLI-10: vcm export exports metadata to file."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        pkl_path = "models/test_v1.pkl"
        with open(pkl_path, "wb") as f:
            f.write(b"model bytes")

        with open("train.py", "w") as f:
            f.write("pass\n")

        with open("metrics.json", "w") as f:
            json.dump({"accuracy": 0.942}, f)

        runner.invoke(cli, [
            "train",
            "--model-name", "test_v1",
            "--script", "train.py",
            "--metrics", "metrics.json",
            "--model-file", pkl_path,
        ])

        output_file = "model_metadata.json"
        result = runner.invoke(cli, ["export", pkl_path, "--output", output_file])
        assert result.exit_code == 0
        assert os.path.exists(output_file)

        with open(output_file, "r") as f:
            data = json.load(f)
        assert data["model_name"] == "test_v1"
        assert data["metrics"]["accuracy"] == 0.942
