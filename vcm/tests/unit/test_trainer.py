import os
import pytest

from vcm.trainer import ModelTracker
from vcm.db.database import Database
from vcm.config import VCMConfig


@pytest.fixture
def tracker_env(tmp_path):
    """Setup environment for ModelTracker unit tests."""
    db_path = str(tmp_path / ".vcm" / "vcm.db")
    config = VCMConfig(
        config_path=str(tmp_path / ".vcmconfig.yaml"),
        database_path=db_path,
        models_dir=str(tmp_path / "models"),
    )
    config.save()
    db = Database(db_path=db_path)
    db.init()
    os.makedirs(tmp_path / "models", exist_ok=True)
    return {
        "root": tmp_path,
        "db": db,
        "config": config,
    }


def test_model_tracker_manual_log(tracker_env):
    """Test manual log_model recording."""
    env = tracker_env
    root = env["root"]
    model_file = root / "models" / "manual_model.pkl"
    model_file.write_bytes(b"dummy binary weights")

    tracker = ModelTracker(config=env["config"])
    meta = tracker.log_model(
        model_path=str(model_file),
        model_name="manual_model",
        metrics={"accuracy": 0.93, "f1_score": 0.91},
        hyperparameters={"lr": 0.001, "epochs": 10},
    )

    assert meta.model_name == "manual_model"
    assert meta.metrics["accuracy"] == 0.93

    # Check that .vcm.json file was written
    vcm_json = str(model_file) + ".vcm.json"
    assert os.path.exists(vcm_json)

    # Check DB record
    stored = env["db"].get_model_by_name("manual_model")
    assert stored is not None
    assert stored.model_hash == meta.model_hash


def test_model_tracker_context_manager(tracker_env):
    """Test context manager usage of ModelTracker."""
    env = tracker_env
    root = env["root"]
    model_file = root / "models" / "ctx_model.pkl"

    tracker = ModelTracker(config=env["config"])

    with tracker.track(
        model_name="ctx_model",
        model_path=str(model_file),
        hyperparameters={"batch_size": 64},
    ) as session:
        # Simulate training work
        model_file.write_bytes(b"context manager weights")
        session.set_metrics({"accuracy": 0.95, "f1_score": 0.94})

    assert os.path.exists(str(model_file) + ".vcm.json")
    stored = env["db"].get_model_by_name("ctx_model")
    assert stored is not None
    assert stored.metrics["accuracy"] == 0.95


def test_model_tracker_run_script(tracker_env):
    """Test training script execution and auto-capture."""
    env = tracker_env
    root = env["root"]
    models_dir = root / "models"

    # Create dummy train.py script
    script_file = root / "train.py"
    script_content = f"""
import json, sys
# Create model file
with open(r"{models_dir / 'script_model.pkl'}", "wb") as f:
    f.write(b"script trained model weights")
# Create metrics.json
with open(r"{root / 'metrics.json'}", "w") as f:
    json.dump({{"accuracy": 0.965, "f1_score": 0.958}}, f)
print("Training finished successfully")
"""
    script_file.write_text(script_content)

    tracker = ModelTracker(config=env["config"])
    meta = tracker.run_and_track(
        script_path=str(script_file),
        model_name="script_model",
        metrics_path=str(root / "metrics.json"),
        model_file=str(models_dir / "script_model.pkl"),
        params=["lr=0.0001", "epochs=25"],
    )

    assert meta.model_name == "script_model"
    assert meta.metrics["accuracy"] == 0.965
    assert meta.hyperparameters["lr"] == 0.0001
    assert os.path.exists(str(models_dir / "script_model.pkl.vcm.json"))
