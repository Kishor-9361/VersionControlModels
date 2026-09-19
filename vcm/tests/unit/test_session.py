"""Unit tests for SessionTracker and Session Data Models."""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

from vcm.db.database import Database
from vcm.models.metadata import MetadataModel
from vcm.models.session import SessionStore, SessionTracker


def test_session_creation():
    """SessionTracker initializes correctly."""
    session = SessionTracker("test_session")
    assert session.session_id is not None
    assert session.session_name == "test_session"
    assert session.status == "inactive"


def test_session_start_end(tmp_path):
    """Session lifecycle works."""
    db_file = str(tmp_path / "test.db")
    session = SessionTracker("test", repo_path=str(tmp_path), db_path=db_file)
    session.start()
    assert session.status == "active"
    assert session.start_time is not None

    session.end()
    assert session.status == "completed"
    assert session.end_time is not None


def test_session_terminal_capture():
    """Terminal output is captured."""
    with SessionTracker("test") as session:
        print("Test output")
        subprocess.run(["echo", "subprocess output"])

    logs = session.get_terminal_log()
    assert "Test output" in logs or "subprocess output" in logs


def test_session_secret_masking():
    """Sensitive data is masked."""
    with SessionTracker("test") as session:
        print("API_KEY=secret123")
        print("password=mypass")

    logs = session.get_terminal_log()
    assert "secret123" not in logs
    assert "mypass" not in logs
    assert "***MASKED***" in logs


def test_session_model_logging():
    """Models are grouped in session."""
    with SessionTracker("test") as session:
        model1_meta = {"name": "v1", "accuracy": 0.91}
        model2_meta = {"name": "v2", "accuracy": 0.93}

        session.log_model(model1_meta)
        session.log_model(model2_meta)

    models = session.get_models()
    assert len(models) == 2
    assert models[0]["name"] == "v1"
    assert models[1]["name"] == "v2"
    assert models[0].next_model == models[1].name
    assert models[1].previous_model == models[0].name


def test_session_annotations():
    """User annotations saved."""
    with SessionTracker("test") as session:
        session.annotate("Testing approach 1")
        session.annotate("Trying new preprocessing")

    annotations = session.get_annotations()
    assert len(annotations) == 2
    assert "Testing approach 1" in annotations[0].text
    assert "Trying new preprocessing" in annotations[1].text


def test_session_git_tracking(tmp_path):
    """Git commits in session tracked."""
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tester"], check=True, capture_output=True)

    with open("sample.txt", "w") as f:
        f.write("initial")
    subprocess.run(["git", "add", "sample.txt"], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)

    session = SessionTracker("git_test", repo_path=str(tmp_path))
    session.start()

    with open("sample.txt", "w") as f:
        f.write("update")
    subprocess.run(["git", "add", "sample.txt"], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Second commit"], check=True, capture_output=True)

    session.end()
    commits = session.get_commits()
    assert len(commits) >= 1


def test_session_duration_calculation():
    """Session duration calculated correctly."""
    session = SessionTracker("test")
    session.start()
    time.sleep(1.05)
    session.end()

    duration = session.get_duration()
    assert duration.total_seconds() >= 1.0


def test_session_database_storage(tmp_path):
    """Session persisted to database."""
    db_file = str(tmp_path / "vcm.db")
    session = SessionTracker("db_test", repo_path=str(tmp_path), db_path=db_file)
    session_id = session.start()
    session.annotate("test annotation")
    session.end()

    retrieved = SessionStore.get_session(session_id, repo_path=str(tmp_path))
    assert retrieved is not None
    assert retrieved.session_name == "db_test"
    assert len(retrieved.get_annotations()) >= 1


def test_session_export_json():
    """Session exported as JSON."""
    with SessionTracker("test") as session:
        session.log_model({"name": "v1", "accuracy": 0.92})
        session.annotate("test note")

    json_export = session.export_json()
    assert "test" in json_export
    assert "v1" in json_export
    data = json.loads(json_export)
    assert data["session_name"] == "test"
    assert len(data["models"]) == 1


def test_session_export_html():
    """Session exported as HTML report."""
    with SessionTracker("test") as session:
        session.log_model({"name": "v1", "accuracy": 0.92})

    html = session.export_html()
    assert "<html>" in html or "<!DOCTYPE html>" in html
    assert "v1" in html
    assert "0.92" in html or "92.00%" in html


def test_session_retrospective_creation(tmp_path):
    """Retrospective session built from history."""
    db_path = str(tmp_path / ".vcm" / "vcm.db")
    db = Database(db_path)
    db.init()

    m1 = MetadataModel(
        model_name="v1",
        model_hash="hash_m1",
        model_file="models/v1.pkl",
        metrics={"accuracy": 0.90},
    )
    m2 = MetadataModel(
        model_name="v2",
        model_hash="hash_m2",
        model_file="models/v2.pkl",
        metrics={"accuracy": 0.94},
    )

    db.insert_model(m1)
    db.insert_model(m2)

    session = SessionTracker.create_retrospective(
        "past",
        start=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        end=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        repo_path=str(tmp_path),
    )

    assert session is not None
    assert session.session_name == "past"
    assert session.status == "completed"
