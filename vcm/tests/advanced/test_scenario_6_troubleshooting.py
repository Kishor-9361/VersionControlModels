"""Scenario 6: Developer Troubleshooting (Root Cause Analysis)."""

from vcm.db.database import Database


def test_scenario_6_developer_troubleshooting(trained_iris_models):
    """Verify VCM helps developer find root cause of model degradation."""
    db = Database(".vcm/vcm.db")

    # Step 1: Find previously good model
    good_models = db.query_by_accuracy_range(min=0.90, max=1.0)
    assert len(good_models) > 0, "Should find previously good models"

    model_v2 = db.get_model_by_name("iris_classifier_v2")
    model_v3 = db.get_model_by_name("iris_classifier_v3")
    assert model_v2 is not None, "Model v2 should exist"
    assert model_v3 is not None, "Model v3 should exist"

    # Step 2: Detailed comparison
    comparison = {
        "metrics_delta": {
            "accuracy": model_v3["metrics"]["accuracy"] - model_v2["metrics"]["accuracy"],
            "precision": model_v3["metrics"]["precision"] - model_v2["metrics"]["precision"],
        },
        "data_changed": model_v2["data"]["dvc_files"][0]["dvc_hash"] != model_v3["data"]["dvc_files"][0]["dvc_hash"],
        "code_changed": model_v2["code"]["git_commit"] != model_v3["code"]["git_commit"],
        "params_changed": model_v2["hyperparameters"] != model_v3["hyperparameters"],
    }

    # Step 3: Root cause analysis
    if comparison["data_changed"] and not comparison["code_changed"]:
        root_cause = "DATA"
    elif comparison["code_changed"] and not comparison["data_changed"]:
        root_cause = "CODE"
    elif comparison["params_changed"]:
        root_cause = "HYPERPARAMETERS"
    else:
        root_cause = "UNKNOWN"

    assert root_cause != "UNKNOWN", "Should identify root cause"
    assert root_cause == "HYPERPARAMETERS"
