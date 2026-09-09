import json
import os
from click.testing import CliRunner
from vcm.cli.main import cli
from vcm.db.database import Database
from vcm.trainer import ModelTracker


def test_eh_1_git_not_initialized(tmp_path):
    """EH-1: Graceful handling when Git is not initialized."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        with open("train.py", "w") as f:
            f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'w')\n")

        with open("metrics.json", "w") as f:
            json.dump({"accuracy": 0.85}, f)

        # Non-git directory training should succeed with git_commit=None
        result = runner.invoke(cli, [
            "train",
            "--model-name", "m1",
            "--script", "train.py",
            "--metrics", "metrics.json",
        ])
        assert result.exit_code == 0
        assert "Model tracked successfully" in result.output

        with open("models/m1.pkl.vcm.json", "r") as f:
            meta = json.load(f)
        assert meta["code"]["git_commit"] is None


def test_eh_2_dvc_not_installed(tmp_path):
    """EH-2: Graceful handling when DVC is not installed or repo is not DVC-initialized."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        with open("train.py", "w") as f:
            f.write("with open('models/m_dvc.pkl', 'wb') as f: f.write(b'w')\n")

        result = runner.invoke(cli, [
            "train",
            "--model-name", "m_dvc",
            "--script", "train.py",
        ])
        assert result.exit_code == 0
        with open("models/m_dvc.pkl.vcm.json", "r") as f:
            meta = json.load(f)
        assert meta["data"]["dvc_files"] == []


def test_eh_3_model_file_not_found(tmp_path):
    """EH-3: Clear error when training script doesn't produce model file."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        with open("bad_script.py", "w") as f:
            f.write("print('script ran but saved nothing')\n")

        result = runner.invoke(cli, [
            "train",
            "--model-name", "missing_model",
            "--script", "bad_script.py",
        ])
        assert result.exit_code != 0
        assert "Model file not created by training script" in result.output

        # Verify no database entry was created
        db = Database(".vcm/vcm.db")
        assert db.get_model_by_name("missing_model") is None


def test_eh_4_corrupted_database(tmp_path):
    """EH-4: Recover from corrupted .vcm/vcm.db via vcm repair."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        with open("train.py", "w") as f:
            f.write("with open('models/m_recover.pkl', 'wb') as f: f.write(b'weights')\n")
        with open("metrics.json", "w") as f:
            json.dump({"accuracy": 0.95}, f)

        runner.invoke(cli, [
            "train",
            "--model-name", "m_recover",
            "--script", "train.py",
            "--metrics", "metrics.json",
        ])

        # Verify .vcm.json exists
        assert os.path.exists("models/m_recover.pkl.vcm.json")

        # Corrupt the database file
        with open(".vcm/vcm.db", "w") as f:
            f.write("corrupted garbage database content")

        # Models query should report corrupted
        result_err = runner.invoke(cli, ["models"])
        assert "Database corrupted" in result_err.output or result_err.exit_code != 0

        # Repair command should rebuild from .vcm.json
        result_repair = runner.invoke(cli, ["repair"])
        assert result_repair.exit_code == 0
        assert "Database repaired" in result_repair.output

        # Now query should succeed
        result_ok = runner.invoke(cli, ["models"])
        assert result_ok.exit_code == 0
        assert "m_recover" in result_ok.output


def test_eh_5_duplicate_model_name(tmp_path):
    """EH-5: Handle duplicate model names gracefully."""
    tracker = ModelTracker(repo_path=str(tmp_path))
    unique1 = tracker._get_unique_model_name("classifier_v1")
    assert unique1 == "classifier_v1"
