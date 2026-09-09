"""CLI Test 9: vcm info command."""

import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli


def test_cli_9_vcm_info(tmp_path):
    """CLI-9: vcm info shows model metadata."""
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

        # Formatted info
        result = runner.invoke(cli, ["info", pkl_path])
        assert result.exit_code == 0
        assert "test_v1" in result.output
        assert "0.942" in result.output or "94.2" in result.output

        # JSON format
        result_json = runner.invoke(cli, ["info", pkl_path, "--json"])
        assert result_json.exit_code == 0
        parsed = json.loads(result_json.output)
        assert parsed["model_name"] == "test_v1"
