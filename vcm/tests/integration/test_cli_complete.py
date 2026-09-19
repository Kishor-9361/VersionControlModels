"""Comprehensive CLI tests covering all commands, options, and output formats."""

import json
import os
from click.testing import CliRunner

from vcm.cli.main import cli


def test_cli_init(tmp_path):
    """vcm init creates all necessary database and configuration files."""
    os.chdir(tmp_path)
    runner = CliRunner()
    res = runner.invoke(cli, ["init"])
    assert res.exit_code == 0
    assert os.path.exists(".vcm/vcm.db")
    assert os.path.exists(".vcmconfig.yaml")


def test_cli_train(tmp_path):
    """vcm train runs and tracks metadata successfully."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/test_v1.pkl', 'wb') as f: f.write(b'weights')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.945}, f)

    res = runner.invoke(cli, [
        "train",
        "--model-name", "test_v1",
        "--script", "train.py",
        "--metrics", "metrics.json",
    ])
    assert res.exit_code == 0
    assert "Model tracked" in res.output
    assert os.path.exists("models/test_v1.pkl.vcm.json")


def test_cli_models_query(tmp_path):
    """vcm models query works for all and best models."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.91}, f)
    runner.invoke(cli, ["train", "--model-name", "m1", "--script", "train.py", "--metrics", "metrics.json"])

    res_all = runner.invoke(cli, ["models"])
    assert res_all.exit_code == 0
    assert "m1" in res_all.output

    res_best = runner.invoke(cli, ["models", "--best"])
    assert res_best.exit_code == 0
    assert "m1" in res_best.output


def test_cli_compare(tmp_path):
    """vcm compare works across models."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/v1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.91}, f)
    runner.invoke(cli, ["train", "--model-name", "v1", "--script", "train.py", "--metrics", "metrics.json"])

    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.95}, f)
    with open("train.py", "w") as f:
        f.write("with open('models/v2.pkl', 'wb') as f: f.write(b'w2')\n")
    runner.invoke(cli, ["train", "--model-name", "v2", "--script", "train.py", "--metrics", "metrics.json"])

    res = runner.invoke(cli, ["compare", "models/v1.pkl", "models/v2.pkl"])
    assert res.exit_code == 0
    assert "Comparison" in res.output or "outperforms" in res.output or "v1" in res.output


def test_cli_lineage(tmp_path):
    """vcm lineage shows model lineage and metadata."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/v1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.92}, f)
    runner.invoke(cli, ["train", "--model-name", "v1", "--script", "train.py", "--metrics", "metrics.json"])

    res = runner.invoke(cli, ["lineage", "models/v1.pkl"])
    assert res.exit_code == 0
    assert "Lineage" in res.output
    assert "v1" in res.output


def test_cli_session_start_and_end(tmp_path):
    """Session start and end via CLI."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    res_start = runner.invoke(cli, ["session", "start", "cli_test"])
    assert res_start.exit_code == 0
    assert "Session started" in res_start.output

    res_end = runner.invoke(cli, ["session", "end"])
    assert res_end.exit_code == 0
    assert "Session ended" in res_end.output


def test_cli_session_info_and_models(tmp_path):
    """Session info and models query via CLI."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    runner.invoke(cli, ["session", "start", "my_sess"])
    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.93}, f)
    runner.invoke(cli, ["train", "--model-name", "m1", "--script", "train.py", "--metrics", "metrics.json"])
    runner.invoke(cli, ["session", "end"])

    res_info = runner.invoke(cli, ["session", "info", "my_sess"])
    assert res_info.exit_code == 0
    assert "my_sess" in res_info.output

    res_models = runner.invoke(cli, ["session", "models", "my_sess"])
    assert res_models.exit_code == 0
    assert "m1" in res_models.output


def test_cli_json_output(tmp_path):
    """CLI can output JSON for automated workflows."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.93}, f)
    runner.invoke(cli, ["train", "--model-name", "m1", "--script", "train.py", "--metrics", "metrics.json"])

    res = runner.invoke(cli, ["models", "--format", "json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert len(data) >= 1
    assert data[0]["model_name"] == "m1"


def test_cli_error_handling(tmp_path):
    """CLI displays clean, helpful errors for non-existent files."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    res = runner.invoke(cli, ["train", "--model-name", "test", "--script", "nonexistent.py"])
    assert res.exit_code != 0
    assert "Error" in res.output or "not found" in res.output


def test_cli_help():
    """CLI help works and describes available commands."""
    runner = CliRunner()
    res = runner.invoke(cli, ["--help"])
    assert res.exit_code == 0
    assert "train" in res.output
    assert "models" in res.output
    assert "session" in res.output


def test_cli_version():
    """CLI version displays version info."""
    runner = CliRunner()
    res = runner.invoke(cli, ["version", "--verbose"])
    assert res.exit_code == 0
    assert "VCM Version: 1.0.0" in res.output


def test_cli_config(tmp_path):
    """CLI config commands manage project configuration."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    res_show = runner.invoke(cli, ["config", "show"])
    assert res_show.exit_code == 0
    assert "database_path" in res_show.output

    res_set = runner.invoke(cli, ["config", "set", "models_dir", "custom_models"])
    assert res_set.exit_code == 0
    assert "Updated" in res_set.output

    res_reset = runner.invoke(cli, ["config", "reset"])
    assert res_reset.exit_code == 0


def test_cli_analysis(tmp_path):
    """CLI analysis command generates reports."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.95}, f)
    runner.invoke(cli, ["train", "--model-name", "m1", "--script", "train.py", "--metrics", "metrics.json"])

    res = runner.invoke(cli, ["analysis", "--report", "full_lineage"])
    assert res.exit_code == 0
    assert "VCM Full Lineage Report" in res.output


def test_cli_deploy_and_audit(tmp_path):
    """CLI deploy and audit commands record deployment history."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'w1')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.95}, f)
    runner.invoke(cli, ["train", "--model-name", "m1", "--script", "train.py", "--metrics", "metrics.json"])

    res_deploy = runner.invoke(cli, ["deploy", "models/m1.pkl", "--environment", "production"])
    assert res_deploy.exit_code == 0
    assert "Deployed" in res_deploy.output

    res_audit = runner.invoke(cli, ["audit", "--environment", "production"])
    assert res_audit.exit_code == 0
    assert "Audit Trail" in res_audit.output
    assert "m1" in res_audit.output
