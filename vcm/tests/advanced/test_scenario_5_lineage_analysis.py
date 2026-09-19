"""Scenario 5: Full Lineage Query."""

from vcm.utils.helpers import vcm_cli


def test_scenario_5_full_lineage_analysis(trained_iris_models):
    """Verify VCM can generate comprehensive lineage reports."""
    report = vcm_cli(["analysis", "--report", "full_lineage"])

    # Parse report
    assert "Dataset: data/iris_train_v1.0.csv" in report
    assert "Dataset: data/iris_train_v2.0.csv" in report
    assert "Model: iris_classifier_v1" in report
    assert "Best Overall: iris_classifier_v1" in report

    # Verify accuracy of insights
    best_model = "iris_classifier_v1"
    assert best_model in report

    # Check recommendations
    assert "Recommendation:" in report
