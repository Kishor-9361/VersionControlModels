"""CLI Test 4, 5, 6: vcm models command."""

import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli


def _seed_models(runner):
    """Seed test models into isolated project."""
    runner.invoke(cli, ["init"])
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    models_data = [
        ("classifier_v1", 0.925, "data/train_v2.0.csv"),
        ("classifier_v2", 0.942, "data/train_v2.1.csv"),
        ("classifier_v4", 0.940, "data/train_v2.1.csv"),
    ]

    for name, acc, dataset in models_data:
        pkl_path = f"models/{name}.pkl"
        with open(pkl_path, "wb") as f:
            f.write(f"weights {name}".encode())
        with open(dataset, "w") as f:
            f.write("a,b\n")

        with open(f"{name}_train.py", "w") as f:
            f.write("pass\n")

        with open(f"{name}_metrics.json", "w") as f:
            json.dump({"accuracy": acc, "f1_score": acc - 0.01}, f)

        runner.invoke(cli, [
            "train",
            "--model-name", name,
            "--dataset", dataset,
            "--script", f"{name}_train.py",
            "--metrics", f"{name}_metrics.json",
            "--model-file", pkl_path,
        ])


def test_cli_4_vcm_models_list_all(tmp_path):
    """CLI-4: vcm models lists all tracked models."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_models(runner)
        result = runner.invoke(cli, ["models"])
        assert result.exit_code == 0
        assert "classifier_v1" in result.output
        assert "classifier_v2" in result.output
        assert "classifier_v4" in result.output


def test_cli_5_vcm_models_filter_dataset(tmp_path):
    """CLI-5: vcm models filters by dataset."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_models(runner)
        result = runner.invoke(cli, ["models", "--dataset", "data/train_v2.1.csv"])
        assert result.exit_code == 0
        assert "classifier_v2" in result.output
        assert "classifier_v4" in result.output
        assert "classifier_v1" not in result.output


def test_cli_6_vcm_models_best(tmp_path):
    """CLI-6: vcm models --best shows highest accuracy model."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _seed_models(runner)
        result = runner.invoke(cli, ["models", "--best"])
        assert result.exit_code == 0
        assert "classifier_v2" in result.output
        assert "94.2" in result.output or "0.942" in result.output
