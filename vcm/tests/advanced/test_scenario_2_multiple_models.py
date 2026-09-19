"""Scenario 2: Multiple Models, Same Dataset."""

from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.db.database import Database


def test_scenario_2_multiple_models_same_dataset(iris_project):
    """Verify VCM can find and compare multiple models on the same dataset."""
    runner = CliRunner()

    # Train v1
    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v1",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=10",
        "--params", "max_depth=5",
        "--params", "random_state=42",
    ])

    # Train v2
    with open("training_scripts/train_model_v2.py", "w") as f:
        with open("training_scripts/train_model_v1.py", "r") as src:
            f.write(src.read().replace("iris_classifier_v1.pkl", "iris_classifier_v2.pkl"))

    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v2",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v2.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=20",
        "--params", "max_depth=10",
        "--params", "random_state=42",
    ])

    # Train v3
    with open("training_scripts/train_model_v3.py", "w") as f:
        with open("training_scripts/train_model_v1.py", "r") as src:
            f.write(src.read().replace("iris_classifier_v1.pkl", "iris_classifier_v3.pkl"))

    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v3",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v3.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=50",
        "--params", "max_depth=15",
        "--params", "random_state=42",
    ])

    # Query database
    db = Database(".vcm/vcm.db")
    models = db.query_by_dataset("data/iris_train_v1.0.csv")

    assert len(models) >= 3

    # Verify each model has dataset
    for m in models:
        meta_dict = m.to_dict()
        assert "iris_train_v1.0.csv" in str(meta_dict["data"]["dvc_files"])

    # Find best model
    best = max(models, key=lambda m: float(m.metrics.get("accuracy", 0.0)))
    assert best.model_name in ["iris_classifier_v1", "iris_classifier_v2", "iris_classifier_v3"]
    assert float(best.metrics["accuracy"]) >= 0.90

    # Verify hyperparameters differ
    hparams = [m.hyperparameters.get("n_estimators") for m in models]
    assert len(set(hparams)) > 1
