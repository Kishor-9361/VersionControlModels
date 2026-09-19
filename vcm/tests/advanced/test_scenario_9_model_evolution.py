"""Scenario 9: Model Evolution Tracking and Change Annotations Workflow."""

import os
from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.config import VCMConfig
from vcm.db.database import Database
from vcm.models.timeline import TimelineStore


def test_scenario_9_model_evolution_complete_workflow(iris_project):
    """Real workflow: Track model progression from baseline to recovery with annotations."""
    runner = CliRunner()

    # Step 0: Initialize VCM in repository
    init_res = runner.invoke(cli, ["init"])
    assert init_res.exit_code == 0

    # Step 1: Train baseline model v1
    res_v1 = runner.invoke(cli, [
        "train",
        "--model-name", "v1",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics_v1.json",
        "--params", "n_estimators=5",
        "--params", "max_depth=2",
        "--reasoning", "Baseline random forest model",
    ])
    assert res_v1.exit_code == 0

    # Step 2: Improve with lower learning rate / more estimators (v2)
    res_v2 = runner.invoke(cli, [
        "train",
        "--model-name", "v2",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics_v2.json",
        "--params", "n_estimators=15",
        "--params", "max_depth=4",
    ])
    assert res_v2.exit_code == 0
    # Add reasoning retroactively via CLI
    reason_res2 = runner.invoke(cli, ["timeline-reason", "v2", "Testing lower learning rate with more trees"])
    assert reason_res2.exit_code == 0

    # Step 3: Add feature engineering / tuning (v3)
    res_v3 = runner.invoke(cli, [
        "train",
        "--model-name", "v3",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics_v3.json",
        "--params", "n_estimators=30",
        "--params", "max_depth=4",
        "--reasoning", "Feature engineering: Tuned tree depth and estimators",
    ])
    assert res_v3.exit_code == 0

    # Step 4: Intentional failure/regression attempt (v4)
    res_v4 = runner.invoke(cli, [
        "train",
        "--model-name", "v4",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics_v4.json",
        "--params", "n_estimators=1",
        "--params", "max_depth=1",
    ])
    assert res_v4.exit_code == 0
    reason_res4 = runner.invoke(cli, ["timeline-reason", "v4", "Testing ensemble approach (FAILED - reverted)"])
    assert reason_res4.exit_code == 0

    # Step 5: Recovery model (v5)
    res_v5 = runner.invoke(cli, [
        "train",
        "--model-name", "v5",
        "--dataset", "data/iris_train_v2.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics_v5.json",
        "--params", "n_estimators=40",
        "--params", "max_depth=8",
        "--reasoning", "Back to feature engineering with hyperparameter tuning",
    ])
    assert res_v5.exit_code == 0

    # Verify: CLI timeline display
    timeline_res = runner.invoke(cli, ["timeline", "--show-reasoning"])
    assert timeline_res.exit_code == 0
    timeline_output = timeline_res.output

    assert "Model Evolution Timeline" in timeline_output
    assert "v1" in timeline_output
    assert "v2" in timeline_output
    assert "v3" in timeline_output
    assert "v4" in timeline_output
    assert "v5" in timeline_output
    assert "Testing lower learning rate" in timeline_output
    assert "Feature engineering" in timeline_output
    assert "FAILED" in timeline_output

    # Verify database timeline object
    config = VCMConfig.load()
    db = Database(config.database_path)
    timeline = db.get_model_timeline()

    assert len(timeline.entries) == 5
    assert timeline.entries[0].model_name == "v1"
    assert timeline.entries[4].model_name == "v5"
    assert timeline.entries[1].reasoning == "Testing lower learning rate with more trees"
    assert "FAILED" in (timeline.entries[3].reasoning or "")

    # Verify regression detection
    store = TimelineStore(db)
    issues = store.detect_timeline_gaps(timeline)
    assert any("v4" in issue for issue in issues)

    # Verify HTML export
    html_export = "timeline_report.html"
    export_res = runner.invoke(cli, ["timeline", "--format", "html", "--output", html_export])
    assert export_res.exit_code == 0
    assert os.path.exists(html_export)

    # Verify analyze command
    analyze_res = runner.invoke(cli, ["timeline", "analyze"])
    assert analyze_res.exit_code == 0
    assert "Timeline Analysis Report" in analyze_res.output
    assert "Improvement Trajectory" in analyze_res.output
    assert "Root Cause Analysis" in analyze_res.output
