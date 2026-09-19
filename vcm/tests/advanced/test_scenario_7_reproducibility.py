"""Scenario 7: Model Reproducibility."""

import json
import pickle
import pandas as pd
from sklearn.metrics import accuracy_score

from vcm.utils.helpers import vcm_reproduce


def test_scenario_7_reproducibility(trained_iris_models):
    """Verify models can be reproduced exactly."""
    with open("models/iris_classifier_v2.pkl", "rb") as f:
        original_model = pickle.load(f)
    with open("models/iris_classifier_v2.pkl.vcm.json", "r", encoding="utf-8") as f:
        original_metrics = json.load(f)["metrics"]

    test_df = pd.read_csv("data/iris_test_v1.0.csv")
    X_test = test_df.iloc[:, :-1]

    # Reproduce
    reproduced_model, reproduced_metrics = vcm_reproduce("iris_classifier_v2.pkl")

    # Verify predictions match
    assert accuracy_score(
        original_model.predict(X_test),
        reproduced_model.predict(X_test),
    ) == 1.0, "Reproduced model predictions should be identical"

    for metric in original_metrics:
        assert abs(
            original_metrics[metric] - reproduced_metrics[metric]
        ) < 1e-6, f"Metric {metric} doesn't match"
