"""CLI Test 2 & 3: vcm train command."""

import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli


def test_cli_2_vcm_train_basic(tmp_path):
    """CLI-2: vcm train captures metadata."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)
        os.makedirs("data", exist_ok=True)

        with open("data/test.csv", "w") as f:
            f.write("a,b\n1,2\n")

        with open("metrics.json", "w") as f:
            json.dump({"accuracy": 0.942, "f1_score": 0.928}, f)

        with open("test_train.py", "w") as f:
            f.write("""
with open('models/test_v1.pkl', 'wb') as f:
    f.write(b'test model weights')
""")

        result = runner.invoke(cli, [
            "train",
            "--model-name", "test_v1",
            "--dataset", "data/test.csv",
            "--script", "test_train.py",
            "--metrics", "metrics.json",
        ])

        assert result.exit_code == 0
        assert "Model tracked successfully" in result.output
        assert os.path.exists("models/test_v1.pkl.vcm.json")


def test_cli_3_vcm_train_with_hyperparameters(tmp_path):
    """CLI-3: vcm train accepts hyperparameters."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        with open("test_train2.py", "w") as f:
            f.write("""
with open('models/test_v2.pkl', 'wb') as f:
    f.write(b'test v2 model weights')
""")

        result = runner.invoke(cli, [
            "train",
            "--model-name", "test_v2",
            "--script", "test_train2.py",
            "--params", "lr=0.001",
            "--params", "epochs=50",
            "--params", "batch_size=32",
        ])

        assert result.exit_code == 0
        assert "Model tracked successfully" in result.output

        with open("models/test_v2.pkl.vcm.json", "r") as f:
            meta = json.load(f)
        assert meta["hyperparameters"]["lr"] == 0.001
        assert meta["hyperparameters"]["epochs"] == 50
        assert meta["hyperparameters"]["batch_size"] == 32
