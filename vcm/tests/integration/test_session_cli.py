"""Integration tests for all VCM Session CLI commands."""

import json
import os
from click.testing import CliRunner

from vcm.cli.main import cli


def test_session_cli_full_lifecycle(tmp_path):
    """Full lifecycle: start -> annotate -> train -> models -> info -> logs -> end."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    # 1. Start session
    res_start = runner.invoke(cli, ["session", "start", "Tuesday experiments"])
    assert res_start.exit_code == 0
    assert "Tuesday experiments" in res_start.output

    # 2. Annotate
    res_ann = runner.invoke(cli, ["session", "annotate", "Beginning baseline run"])
    assert res_ann.exit_code == 0
    assert "Annotation recorded" in res_ann.output

    # 3. Train models
    os.makedirs("models", exist_ok=True)
    with open("train.py", "w") as f:
        f.write("with open('models/m1.pkl', 'wb') as f: f.write(b'weights')\n")
    with open("metrics.json", "w") as f:
        json.dump({"accuracy": 0.912}, f)

    res_train1 = runner.invoke(cli, [
        "train",
        "--model-name", "m1",
        "--script", "train.py",
        "--metrics", "metrics.json",
    ])
    assert res_train1.exit_code == 0

    # 4. View models during session
    res_m = runner.invoke(cli, ["session", "models", "Tuesday experiments"])
    assert res_m.exit_code == 0
    assert "m1" in res_m.output

    # 5. End session
    res_end = runner.invoke(cli, ["session", "end"])
    assert res_end.exit_code == 0
    assert "Session ended" in res_end.output

    # 6. Session info
    res_info = runner.invoke(cli, ["session", "info", "Tuesday experiments"])
    assert res_info.exit_code == 0
    assert "Tuesday experiments" in res_info.output
    assert "m1" in res_info.output

    # 7. Session logs
    res_logs = runner.invoke(cli, ["session", "logs", "Tuesday experiments"])
    assert res_logs.exit_code == 0

    # 8. Session list
    res_list = runner.invoke(cli, ["session", "list"])
    assert res_list.exit_code == 0
    assert "Tuesday experiments" in res_list.output


def test_session_cli_compare(tmp_path):
    """Compare two sessions via CLI."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    # Session 1
    runner.invoke(cli, ["session", "start", "SessionAlpha"])
    runner.invoke(cli, ["session", "end"])

    # Session 2
    runner.invoke(cli, ["session", "start", "SessionBeta"])
    runner.invoke(cli, ["session", "end"])

    res_comp = runner.invoke(cli, ["session", "compare", "SessionAlpha", "SessionBeta"])
    assert res_comp.exit_code == 0
    assert "Session Comparison" in res_comp.output


def test_session_cli_export(tmp_path):
    """Export session as JSON and HTML via CLI."""
    os.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    runner.invoke(cli, ["session", "start", "ExportSession"])
    runner.invoke(cli, ["session", "annotate", "Export test note"])
    runner.invoke(cli, ["session", "end"])

    res_export_json = runner.invoke(cli, ["session", "export", "ExportSession", "--format", "json"])
    assert res_export_json.exit_code == 0
    assert os.path.exists("sessions/ExportSession.json")

    res_export_html = runner.invoke(cli, ["session", "export", "ExportSession", "--format", "html"])
    assert res_export_html.exit_code == 0
    assert os.path.exists("sessions/ExportSession.html")
