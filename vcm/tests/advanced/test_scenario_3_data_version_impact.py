"""Scenario 3: Data Version Update and Impact Analysis."""

from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.db.database import Database


def test_scenario_3_data_version_impact(iris_project):
    """Verify impact of data version on model performance."""
    runner = CliRunner()

    # Model on v1.0 (raw)
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

    # Model on v2.0 (scaled)
    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v4",
        "--dataset", "data/iris_train_v2.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=10",
        "--params", "max_depth=5",
        "--params", "random_state=42",
    ])

    db = Database(".vcm/vcm.db")

    # Models on v1.0
    v1_models = db.query_by_dataset_version("data/iris_train_v1.0.csv")
    assert len(v1_models) >= 1
    best_v1 = max(v1_models, key=lambda m: float(m.metrics.get("accuracy", 0.0)))

    # Model on v2.0
    v2_models = db.query_by_dataset_version("data/iris_train_v2.0.csv")
    assert len(v2_models) >= 1
    best_v2 = max(v2_models, key=lambda m: float(m.metrics.get("accuracy", 0.0)))

    assert best_v1.data.dvc_files[0].dvc_hash != best_v2.data.dvc_files[0].dvc_hash
    assert best_v1.data.dvc_files[0].path != best_v2.data.dvc_files[0].path
