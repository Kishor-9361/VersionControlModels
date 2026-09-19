"""Integration tests for Model Evolution Timeline end-to-end tracking workflows."""

import os
from click.testing import CliRunner
import pytest

from vcm.cli.main import cli
from vcm.config import VCMConfig
from vcm.db.database import Database
from vcm.models.session import SessionTracker
from vcm.trainer import ModelTracker


@pytest.fixture
def repo_setup(tmp_path):
    """Setup clean working repo for integration testing."""
    cur = os.getcwd()
    os.chdir(tmp_path)
    try:
        config = VCMConfig(database_path=str(tmp_path / ".vcm" / "vcm.db"))
        config.save(str(tmp_path / ".vcmconfig.yaml"))
        db = Database(config.database_path)
        db.init()

        # Create dummy model artifacts
        os.makedirs(tmp_path / "models", exist_ok=True)
        for name in ["v1.pkl", "v2.pkl", "v3.pkl"]:
            p = tmp_path / "models" / name
            with open(p, "wb") as f:
                f.write(b"dummy_weights_" + name.encode())

        yield tmp_path, db
    finally:
        os.chdir(cur)


def test_full_timeline_workflow(repo_setup):
    """End-to-end timeline tracking workflow with ModelTracker and reasoning."""
    tmp_path, db = repo_setup
    tracker = ModelTracker(repo_path=str(tmp_path))

    # Train/log first model (baseline)
    tracker.log_model(
        model_path=str(tmp_path / "models" / "v1.pkl"),
        model_name="v1",
        metrics={"accuracy": 0.910},
    )

    # Train/log second model with reasoning
    tracker.log_model(
        model_path=str(tmp_path / "models" / "v2.pkl"),
        model_name="v2",
        metrics={"accuracy": 0.925},
        reasoning="Lower learning rate",
    )

    # Train/log third model with reasoning
    tracker.log_model(
        model_path=str(tmp_path / "models" / "v3.pkl"),
        model_name="v3",
        metrics={"accuracy": 0.932},
        reasoning="Feature engineering",
    )

    # Get timeline
    timeline = db.get_model_timeline()

    # Verify ordering
    assert len(timeline.entries) == 3
    assert timeline.entries[0].model_name == "v1"
    assert timeline.entries[1].model_name == "v2"
    assert timeline.entries[2].model_name == "v3"

    # Verify reasoning captured
    assert timeline.entries[1].reasoning == "Lower learning rate"
    assert timeline.entries[2].reasoning == "Feature engineering"

    # Verify metrics and improvements
    assert timeline.best_model == "v3"
    assert timeline.accuracy_improvement == pytest.approx(0.022)


def test_timeline_cli_output(repo_setup):
    """CLI timeline command produces expected formatted output."""
    tmp_path, db = repo_setup
    tracker = ModelTracker(repo_path=str(tmp_path))

    tracker.log_model(
        model_path=str(tmp_path / "models" / "v1.pkl"),
        model_name="v1",
        metrics={"accuracy": 0.91},
    )
    tracker.log_model(
        model_path=str(tmp_path / "models" / "v2.pkl"),
        model_name="v2",
        metrics={"accuracy": 0.925},
        reasoning="Lower learning rate",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["timeline", "--show-reasoning", "--format", "table"])

    assert result.exit_code == 0
    assert "Model Evolution Timeline" in result.output
    assert "v1" in result.output
    assert "v2" in result.output
    assert "Lower learning rate" in result.output


def test_timeline_html_export(repo_setup):
    """Timeline exported as interactive HTML file."""
    tmp_path, db = repo_setup
    tracker = ModelTracker(repo_path=str(tmp_path))

    tracker.log_model(
        model_path=str(tmp_path / "models" / "v1.pkl"),
        model_name="v1",
        metrics={"accuracy": 0.91},
    )

    export_file = str(tmp_path / "timeline.html")
    runner = CliRunner()
    result = runner.invoke(cli, ["timeline", "--format", "html", "--output", export_file])

    assert result.exit_code == 0
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "<!DOCTYPE html>" in content
        assert "accuracy" in content.lower()


def test_timeline_with_session_integration(repo_setup):
    """Verify models logged inside a session carry session_id into timeline."""
    tmp_path, db = repo_setup
    tracker = ModelTracker(repo_path=str(tmp_path))

    # Start a development session
    session_tracker = SessionTracker(
        session_name="Sprint_Experimentation",
        repo_path=str(tmp_path),
        db_path=db.db_path,
    )
    session_tracker.start()

    tracker.log_model(
        model_path=str(tmp_path / "models" / "v1.pkl"),
        model_name="v1",
        metrics={"accuracy": 0.90},
    )
    tracker.log_model(
        model_path=str(tmp_path / "models" / "v2.pkl"),
        model_name="v2",
        metrics={"accuracy": 0.93},
        reasoning="Batch normalization added",
    )

    session_tracker.end()

    # Query timeline filtered by session
    timeline = db.get_model_timeline(session_id=session_tracker.session_id)
    assert len(timeline.entries) == 2
    assert all(e.session_id == session_tracker.session_id for e in timeline.entries)
    assert timeline.best_model == "v2"
    assert timeline.accuracy_improvement == pytest.approx(0.03)
