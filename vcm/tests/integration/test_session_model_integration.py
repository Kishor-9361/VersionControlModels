"""Integration tests for Session Tracking and Model Metadata integration."""

import json
import os
from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.models.session import SessionComparator, SessionTracker
from vcm.trainer import ModelTracker


def test_session_model_metadata_linkage(tmp_path):
    """Model metadata includes session context."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    with SessionTracker("integration_test", repo_path=str(tmp_path)):
        os.makedirs("models", exist_ok=True)
        with open("models/v1.pkl", "wb") as f:
            f.write(b"model bytes")
        with open("metrics.json", "w") as f:
            json.dump({"accuracy": 0.92}, f)

        tracker = ModelTracker(repo_path=str(tmp_path))
        tracker.log_model(
            model_path="models/v1.pkl",
            model_name="v1",
            metrics={"accuracy": 0.92},
        )

    # Load metadata
    with open("models/v1.pkl.vcm.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    assert metadata["session"]["session_name"] == "integration_test"
    assert metadata["session"]["position_in_session"] == 1


def test_session_model_chain_creation(tmp_path):
    """Models are linked in a session sequence."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    with SessionTracker("chain_test", repo_path=str(tmp_path)):
        os.makedirs("models", exist_ok=True)
        tracker = ModelTracker(repo_path=str(tmp_path))

        for i in range(3):
            name = f"v{i+1}"
            m_path = f"models/{name}.pkl"
            with open(m_path, "wb") as f:
                f.write(f"model bytes {name}".encode())
            tracker.log_model(
                model_path=m_path,
                model_name=name,
                metrics={"accuracy": 0.90 + i * 0.02},
            )

    with open("models/v1.pkl.vcm.json", "r", encoding="utf-8") as f:
        meta_v1 = json.load(f)
    with open("models/v2.pkl.vcm.json", "r", encoding="utf-8") as f:
        meta_v2 = json.load(f)

    assert meta_v1["session"]["next_model"] == "v2"
    assert meta_v2["session"]["previous_model"] == "v1"


def test_vcm_train_with_session_active(tmp_path):
    """vcm train CLI auto-joins active session."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    session = SessionTracker("train_integration", repo_path=str(tmp_path))
    session.start()

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/v1.pkl', 'wb') as f: f.write(b'weights')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.94}, f)

    # Run vcm train
    res = runner.invoke(cli, [
        "train",
        "--model-name", "v1",
        "--script", "train.py",
        "--metrics", "metrics.json",
    ])
    assert res.exit_code == 0

    session.end()

    models = session.get_models()
    assert any(m.name == "v1" for m in models)


def test_session_comparison_with_metadata(tmp_path):
    """Compare sessions using model metadata."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    # Session 1: 5 models
    s1 = SessionTracker("session_1", repo_path=str(tmp_path))
    s1.start()
    for i in range(5):
        s1.log_model({"name": f"m1_{i}", "accuracy": 0.90 + (i * 0.01)})
    s1.end()

    # Session 2: 3 models
    s2 = SessionTracker("session_2", repo_path=str(tmp_path))
    s2.start()
    for i in range(3):
        s2.log_model({"name": f"m2_{i}", "accuracy": 0.88 + (i * 0.01)})
    s2.end()

    comp = SessionComparator.compare(s1, s2)
    assert comp["s1_models_count"] == 5
    assert comp["s2_models_count"] == 3
    assert comp["s1_best_accuracy"] > comp["s2_best_accuracy"]


def test_session_export_includes_models(tmp_path):
    """Session export includes all model metadata."""
    with SessionTracker("export_test", repo_path=str(tmp_path)) as session:
        session.log_model({"name": "v1", "accuracy": 0.91})
        session.log_model({"name": "v2", "accuracy": 0.93})

    export = session.export_json()
    parsed = json.loads(export)

    assert len(parsed["models"]) == 2
    assert parsed["models"][0]["name"] == "v1"
    assert parsed["best_model"]["name"] == "v2"


def test_session_cli_integration(tmp_path):
    """CLI commands work seamlessly with sessions."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    res_start = runner.invoke(cli, ["session", "start", "cli_test"])
    assert res_start.exit_code == 0

    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/v1.pkl', 'wb') as f: f.write(b'weights')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.95}, f)

    runner.invoke(cli, [
        "train",
        "--model-name", "v1",
        "--script", "train.py",
        "--metrics", "metrics.json",
    ])

    res_end = runner.invoke(cli, ["session", "end"])
    assert res_end.exit_code == 0

    res_models = runner.invoke(cli, ["session", "models", "cli_test"])
    assert "v1" in res_models.output
