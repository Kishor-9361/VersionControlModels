"""Fixtures for advanced real-world machine learning project testing."""

import os
import subprocess
import pytest
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from vcm.cli.main import cli
from click.testing import CliRunner


@pytest.fixture
def iris_project(tmp_path):
    """Create a complete, realistic ML project with Git, DVC metadata, and Iris data."""
    orig_cwd = os.getcwd()
    project_dir = tmp_path / "real_iris_project"
    project_dir.mkdir()
    os.chdir(project_dir)

    # 1. Initialize Git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "alice@example.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "alice"], check=True, capture_output=True)

    # 2. Prepare Iris datasets
    os.makedirs("data", exist_ok=True)
    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df["target"] = iris.target

    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    train_v1_path = "data/iris_train_v1.0.csv"
    test_v1_path = "data/iris_test_v1.0.csv"
    train_df.to_csv(train_v1_path, index=False)
    test_df.to_csv(test_v1_path, index=False)

    # Data version 2.0 (scaled)
    scaler = StandardScaler()
    train_scaled = train_df.copy()
    train_scaled.iloc[:, :-1] = scaler.fit_transform(train_df.iloc[:, :-1])
    train_v2_path = "data/iris_train_v2.0.csv"
    train_scaled.to_csv(train_v2_path, index=False)

    # 3. Simulate DVC tracking metadata (.dvc files)
    with open("data/iris_train_v1.0.csv.dvc", "w") as f:
        f.write(f"""outs:
- md5: 9a7b8c1234567890abcdef1234567890
  size: {os.path.getsize(train_v1_path)}
  path: iris_train_v1.0.csv
""")

    with open("data/iris_test_v1.0.csv.dvc", "w") as f:
        f.write(f"""outs:
- md5: 1234567890abcdef1234567890abcdef
  size: {os.path.getsize(test_v1_path)}
  path: iris_test_v1.0.csv
""")

    with open("data/iris_train_v2.0.csv.dvc", "w") as f:
        f.write(f"""outs:
- md5: 567890abcdef1234567890abcdef1234
  size: {os.path.getsize(train_v2_path)}
  path: iris_train_v2.0.csv
""")

    # 4. Training script
    os.makedirs("training_scripts", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    script_content = """import argparse
import json
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', default='data/iris_train_v1.0.csv')
parser.add_argument('--test-data', default='data/iris_test_v1.0.csv')
parser.add_argument('--output', default='models/iris_classifier_v1.pkl')
parser.add_argument('--metrics-out', default='metrics.json')
parser.add_argument('--n-estimators', type=int, default=10)
parser.add_argument('--max-depth', type=int, default=5)
parser.add_argument('--random-state', type=int, default=42)
args, _ = parser.parse_known_args()

train = pd.read_csv(args.dataset)
test = pd.read_csv(args.test_data)

X_train, y_train = train.iloc[:, :-1], train.iloc[:, -1]
X_test, y_test = test.iloc[:, :-1], test.iloc[:, -1]

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

print(f"Model trained. Accuracy: {metrics['accuracy']:.4f}")
"""
    with open("training_scripts/train_model_v1.py", "w") as f:
        f.write(script_content)

    # 5. Commit initial repository state
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial Iris project setup"], check=True, capture_output=True)

    # 6. Initialize VCM
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    yield project_dir

    os.chdir(orig_cwd)


@pytest.fixture
def trained_iris_models(iris_project):
    """Fixture that trains models v1 through v5 in the iris_project."""
    runner = CliRunner()

    # Model 1
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

    # Model 2
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

    # Model 3
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

    # Model 4 (trained on scaled data v2.0)
    with open("training_scripts/train_model_v4.py", "w") as f:
        with open("training_scripts/train_model_v1.py", "r") as src:
            f.write(src.read().replace("iris_classifier_v1.pkl", "iris_classifier_v4.pkl"))
    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v4",
        "--dataset", "data/iris_train_v2.0.csv",
        "--script", "training_scripts/train_model_v4.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=10",
        "--params", "max_depth=5",
        "--params", "random_state=42",
    ])

    # Model 5 (new code commit with feature scaling)
    with open("training_scripts/train_model_v5.py", "w") as f:
        with open("training_scripts/train_model_v1.py", "r") as src:
            code = src.read().replace("iris_classifier_v1.pkl", "iris_classifier_v5.pkl")
            scaling_code = """
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
"""
            needle = "X_test, y_test = test.iloc[:, :-1], test.iloc[:, -1]"
            code = code.replace(needle, needle + scaling_code)
            f.write(code)
    subprocess.run(["git", "add", "training_scripts/train_model_v5.py"], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add feature scaling in training pipeline"], check=True, capture_output=True)
    runner.invoke(cli, [
        "train",
        "--model-name", "iris_classifier_v5",
        "--dataset", "data/iris_train_v1.0.csv",
        "--script", "training_scripts/train_model_v5.py",
        "--metrics", "metrics.json",
        "--params", "n_estimators=10",
        "--params", "max_depth=5",
        "--params", "random_state=42",
    ])

    return iris_project
