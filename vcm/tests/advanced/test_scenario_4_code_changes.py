"""Scenario 4: Code Changes Impact Tracking."""

import subprocess
from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.db.database import Database
from vcm.integrations.git_client import GitClient


def test_scenario_4_code_changes_impact(iris_project):
    """Verify VCM tracks which code version trained each model."""
    runner = CliRunner()

    # Train v1 with original code
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

    # Update training script: Add feature scaling preprocessing
    with open("training_scripts/train_model_v1.py", "w") as f:
        f.write("""import argparse
import json
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', default='data/iris_train_v1.0.csv')
parser.add_argument('--test-data', default='data/iris_test_v1.0.csv')
parser.add_argument('--output', default='models/iris_classifier_v5.pkl')
parser.add_argument('--metrics-out', default='metrics.json')
parser.add_argument('--n-estimators', type=int, default=10)
parser.add_argument('--max-depth', type=int, default=5)
parser.add_argument('--random-state', type=int, default=42)
args, _ = parser.parse_known_args()

train = pd.read_csv(args.dataset)
test = pd.read_csv(args.test_data)

X_train, y_train = train.iloc[:, :-1], train.iloc[:, -1]
X_test, y_test = test.iloc[:, :-1], test.iloc[:, -1]

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = RandomForestClassifier(
    n_estimators=args.n_estimators,
    max_depth=args.max_depth,
    random_state=args.random_state,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
metrics = {
    'accuracy': float(accuracy_score(y_test, y_pred)),
    'precision': float(precision_score(y_test, y_pred, average='weighted')),
    'recall': float(recall_score(y_test, y_pred, average='weighted')),
    'f1_score': float(f1_score(y_test, y_pred, average='weighted')),
}

with open(args.output, 'wb') as f:
    pickle.dump(model, f)

with open(args.metrics_out, 'w') as f:
    json.dump(metrics, f)
""")

    subprocess.run(["git", "add", "training_scripts/train_model_v1.py"], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add feature scaling in training pipeline"], check=True, capture_output=True)

    # Train v5 with new commit
    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v5",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v1.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=10",
        "--params", "max_depth=5",
        "--params", "random_state=42",
    ])

    db = Database(".vcm/vcm.db")
    v1_model = db.get_model_by_name("iris_classifier_v1")
    v5_model = db.get_model_by_name("iris_classifier_v5")

    assert v1_model is not None
    assert v5_model is not None

    # Different git commits
    assert v1_model.code.git_commit != v5_model.code.git_commit

    # Inspect git diff
    git = GitClient()
    diff = git.get_diff(v1_model.code.git_commit, v5_model.code.git_commit)
    assert any("train_model_v1.py" in f for f in diff.get("files_changed", []))
