"""CLI tests for vcm timeline, vcm timeline-reason, and vcm timeline analyze."""

import json
import os
import pytest
from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.config import VCMConfig
from vcm.db.database import Database
from vcm.models.metadata import MetadataModel


@pytest.fixture
def cli_runner(tmp_path):
    """Setup isolated test repository with initialized VCM database and config."""
    runner = CliRunner()
    current_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Initialize VCM
        config = VCMConfig(database_path=str(tmp_path / ".vcm" / "vcm.db"))
        config.save(str(tmp_path / ".vcmconfig.yaml"))
        db = Database(config.database_path)
        db.init()

        # Seed models
        m1 = MetadataModel(
            model_name="v1",
            model_hash="hash_v1",
            model_file="models/v1.pkl",
            metrics={"accuracy": 0.912},
        )
        m2 = MetadataModel(
            model_name="v2",
            model_hash="hash_v2",
            model_file="models/v2.pkl",
            metrics={"accuracy": 0.928},
            reasoning="Testing lower learning rate",
        )
        m3 = MetadataModel(
            model_name="v3",
            model_hash="hash_v3",
            model_file="models/v3.pkl",
            metrics={"accuracy": 0.931},
            reasoning="Added feature scaling",
        )
        db.insert_model(m1)
        db.insert_model(m2)
        db.insert_model(m3)

        yield runner
    finally:
        os.chdir(current_dir)


def test_cli_timeline_table(cli_runner):
    """Verify vcm timeline displays progression table."""
    result = cli_runner.invoke(cli, ["timeline"])
    assert result.exit_code == 0
    assert "Model Evolution Timeline" in result.output
    assert "v1" in result.output
    assert "v2" in result.output
    assert "v3" in result.output
    assert "91.2%" in result.output
    assert "93.1%" in result.output
    assert "Summary" in result.output


def test_cli_timeline_show_reasoning(cli_runner):
    """Verify vcm timeline --show-reasoning displays reasons."""
    result = cli_runner.invoke(cli, ["timeline", "--show-reasoning"])
    assert result.exit_code == 0
    assert "Testing lower learning rate" in result.output
    assert "Added feature scaling" in result.output


def test_cli_timeline_json_format(cli_runner):
    """Verify vcm timeline --format json returns valid JSON."""
    result = cli_runner.invoke(cli, ["timeline", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_models"] == 3
    assert data["best_model"] == "v3"
    assert len(data["entries"]) == 3


def test_cli_timeline_csv_format(cli_runner):
    """Verify vcm timeline --format csv outputs CSV header and entries."""
    result = cli_runner.invoke(cli, ["timeline", "--format", "csv"])
    assert result.exit_code == 0
    assert "position,model_name,accuracy" in result.output
    assert "v1,0.912" in result.output


def test_cli_timeline_ascii_format(cli_runner):
    """Verify vcm timeline --format ascii outputs chart."""
    result = cli_runner.invoke(cli, ["timeline", "--format", "ascii"])
    assert result.exit_code == 0
    assert "Model Accuracy Over Time" in result.output
    assert "v1" in result.output
    assert "v3" in result.output


def test_cli_timeline_html_export(cli_runner, tmp_path):
    """Verify vcm timeline --format html --output exports valid HTML file."""
    html_file = str(tmp_path / "timeline.html")
    result = cli_runner.invoke(cli, ["timeline", "--format", "html", "--output", html_file])
    assert result.exit_code == 0
    assert os.path.exists(html_file)
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "<!DOCTYPE html>" in content
        assert "Model Evolution Timeline" in content
        assert "accuracy" in content.lower()


def test_cli_timeline_analyze(cli_runner):
    """Verify vcm timeline analyze command generates trajectory and insights report."""
    result = cli_runner.invoke(cli, ["timeline", "analyze"])
    assert result.exit_code == 0
    assert "Timeline Analysis Report" in result.output
    assert "Improvement Trajectory" in result.output
    assert "Root Cause Analysis" in result.output
    assert "Experiment Efficiency" in result.output


def test_cli_timeline_reason_standalone(cli_runner):
    """Verify adding, viewing, and overriding reasoning via vcm timeline-reason."""
    # Add reasoning
    res_add = cli_runner.invoke(cli, ["timeline-reason", "v1", "Baseline random forest"])
    assert res_add.exit_code == 0
    assert "Added reasoning to v1" in res_add.output

    # View reasoning with --show
    res_show = cli_runner.invoke(cli, ["timeline-reason", "v1", "--show"])
    assert res_show.exit_code == 0
    assert "Baseline random forest" in res_show.output

    # Update with --force
    res_force = cli_runner.invoke(cli, ["timeline-reason", "v1", "Updated baseline notes", "--force"])
    assert res_force.exit_code == 0
    assert "Added reasoning to v1" in res_force.output

    # Check updated view
    res_show2 = cli_runner.invoke(cli, ["timeline-reason", "v1", "--show"])
    assert "Updated baseline notes" in res_show2.output


def test_cli_timeline_reason_subcommand(cli_runner):
    """Verify vcm timeline reason subcommand works equivalently."""
    result = cli_runner.invoke(cli, ["timeline", "reason", "v2", "Tuned hyperparameters", "--force"])
    assert result.exit_code == 0
    assert "Added reasoning to v2" in result.output


def test_cli_timeline_show_subcommand(cli_runner):
    """Verify explicit vcm timeline show subcommand."""
    result = cli_runner.invoke(cli, ["timeline", "show", "--highlight-best"])
    assert result.exit_code == 0
    assert "Model Evolution Timeline" in result.output
    assert "[BEST]" in result.output


def test_cli_timeline_accuracy_range_filter(cli_runner):
    """Verify vcm timeline --accuracy-range filters models."""
    result = cli_runner.invoke(cli, ["timeline", "--accuracy-range", "0.92-0.94"])
    assert result.exit_code == 0
    assert "v2" in result.output
    assert "v3" in result.output
    assert "v1" not in result.output


def test_cli_timeline_show_changes(cli_runner):
    """Verify vcm timeline --show-changes option."""
    result = cli_runner.invoke(cli, ["timeline", "--show-changes"])
    assert result.exit_code == 0
    assert "Model Evolution Timeline" in result.output


def test_cli_timeline_reason_missing_text(cli_runner):
    """Verify error output when reasoning text is omitted without --show."""
    result = cli_runner.invoke(cli, ["timeline-reason", "v1"])
    assert result.exit_code != 0
    assert "REASONING text is required" in result.output


def test_cli_timeline_reason_show_unannotated(cli_runner):
    """Verify vcm timeline-reason --show on model with no reasoning."""
    result = cli_runner.invoke(cli, ["timeline-reason", "v1", "--show"])
    assert result.exit_code == 0
    assert "No reasoning recorded for v1" in result.output


def test_cli_timeline_analyze_output_file(cli_runner, tmp_path):
    """Verify vcm timeline analyze --output writes file."""
    analysis_file = str(tmp_path / "analysis.txt")
    result = cli_runner.invoke(cli, ["timeline", "analyze", "--output", analysis_file])
    assert result.exit_code == 0
    assert os.path.exists(analysis_file)
    with open(analysis_file, "r", encoding="utf-8") as f:
        assert "Timeline Analysis Report" in f.read()
