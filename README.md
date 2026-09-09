# VCM (Version Control Models)

**Model DNA Version Control Platform**  
*Enterprise-grade, lightweight, and zero-configuration version control for machine learning models.*

[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-65%20passed%20%7C%2091%25%20coverage-brightgreen.svg)](vcm/tests/)
[![Code Style](https://img.shields.io/badge/code%20style-flake8%20%7C%20mypy-black.svg)](https://github.com/psf/black)

---

## Executive Overview

In traditional software engineering, **Git** manages source code. In modern data science, **DVC** tracks datasets. However, trained machine learning models exist at the intersection of code, data, hyperparameters, environment dependencies, and evaluation metrics.

Without dedicated model version control, identifying which commit generated which model binary, on what dataset snapshot, using which hyperparameters, and under which environment dependencies remains fragmented and prone to audit failure.

**VCM (Version Control Models)** solves this challenge by automatically binding your code, data, training parameters, evaluation metrics, and system environment into an immutable, tamper-evident record termed **Model DNA**.

```text
  +-------------------+       +--------------------+
  | Git Source Commit |       | DVC Dataset Hashes |
  +---------+---------+       +---------+----------+
            |                           |
            +-------------+-------------+
                          |
                          v
               +----------------------+
               |    VCM Model DNA     |
               | (Code + Data + Env + |
               |   Params + Metrics)  |
               +----------+-----------+
                          |
            +-------------+-------------+
            |                           |
            v                           v
  +-------------------+       +--------------------+
  |   Model Artifact  |       | Portable Sidecar   |
  |  (e.g., .pkl)     | <---> | (<model>.vcm.json) |
  +-------------------+       +---------+----------+
                                        |
                                        v
                              +--------------------+
                              | Local SQLite Index |
                              |  (.vcm/vcm.db)     |
                              +--------------------+
```

---

## Core Capabilities

- **Automatic Model DNA Capture**: Tracks exact Git commit SHA, branch, remote repository URL, DVC dataset content hashes, hyperparameters, duration, user context, and system environment without boilerplate.
- **Dual-Layer Persistence (Zero Lock-In)**: Every model file (`.pkl`, `.onnx`, `.pt`, `.joblib`) has an attached `.vcm.json` sidecar that travels with the binary across S3, GCS, or Git LFS. A local SQLite database (`.vcm/vcm.db`) indexes all runs for sub-millisecond queries.
- **Complete Lineage Provenance**: View a comprehensive lineage tree linking any model binary back to its exact code commit, dataset files, hyperparameters, and author.
- **Side-by-Side Model Diffing**: Compare any two models with automatic delta computation across evaluation metrics, hyperparameters, dataset changes, and code revisions.
- **Self-Healing Architecture (`vcm repair`)**: The SQLite database functions as an ephemeral query acceleration index. If deleted or corrupted, `vcm repair` rebuilds the complete index from disk in seconds.
- **Flexible CLI & Multi-Param Parsing**: Supports repeated flags (`--params lr=0.01 --params max_iter=300`), compound space-separated strings (`--params lr=0.01 max_iter=300`), and comma-separated lists.

---

## Quick Start

### 1. Installation

Install in editable mode for local development:

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
pip install -e .
```

Verify installation:

```bash
vcm --version
vcm --help
```

### 2. Initialize in Your Project

Initialize VCM in your machine learning repository:

```bash
vcm init
```

This creates:
- `.vcmconfig.yaml`: Project configuration file.
- `.vcm/vcm.db`: Local SQLite query index.
- `models/`: Default output directory for tracked model artifacts.

### 3. Track a Training Run

Run your existing training script through VCM:

```bash
vcm train --model-name "iris_classifier_v1" \
          --dataset "data/iris.csv" \
          --script "train.py" \
          --metrics "metrics.json" \
          --model-file "models/iris_classifier_v1.pkl" \
          --params learning_rate=0.01 max_iter=300
```

Output:
```text
Running training script: train.py ...
[Script output]

Model tracked successfully.
  Model:      iris_classifier_v1
  Accuracy:   96.7%
  Git commit: 427af932ee5868fb54e21cad0646ff9f4c589761
  Dataset:    data/iris.csv
  Metadata:   models/iris_classifier_v1.pkl.vcm.json
```

---

## Command-Line Interface (CLI)

### Query & Filter Models (`vcm models`)

List all tracked models in reverse chronological order:

```bash
vcm models
```

```text
╭────────────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name         │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├────────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3         │ 100.0%     │ 100.0%     │ data/iris_v2.csv │ 55d5b5e6     │ 2026-09-09 13:37 │
├────────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_rf_v2         │ 98.2%      │ 98.1%      │ data/iris_v1.csv │ 55d5b5e6     │ 2026-09-09 13:35 │
├────────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_classifier_v1 │ 96.7%      │ 96.5%      │ data/iris_v1.csv │ 427af932     │ 2026-09-09 13:30 │
╰────────────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 3 models found
```

Filter by dataset, select top models, or export results:

```bash
# Filter models trained on a specific dataset
vcm models --dataset "data/iris_v1.csv"

# Display only the best performing model
vcm models --best

# Export model catalog to CSV
vcm models --export models_catalog.csv
```

### Inspect Model Lineage (`vcm lineage`)

Inspect the complete lineage tree connecting a model binary to its code commit, dataset files, hyperparameters, and environment context:

```bash
vcm lineage models/iris_rf_v2.pkl
```

```text
Model: iris_rf_v2 (models/iris_rf_v2.pkl)
├── Accuracy: 0.9820 (98.2%) | F1 Score: 0.9810
├── Git Commit: 55d5b5e6e72a5959108662acf4006d2a426c2d41
│   ├── Branch: main
│   ├── Remote: origin
│   └── URL: https://github.com/org/ml-repo.git
├── Dataset Files:
│   ├── data/iris_v1.csv (hash: 84f2c9e782e4f012..., size: 614 B)
├── Hyperparameters:
│   ├── n_estimators: 100
│   ├── max_depth: 4
└── Trained by: kishorveeraragavan on workstation-01 (2026-09-09T13:35:14+00:00)
```

### Side-by-Side Model Comparison (`vcm compare`)

Compare two model artifacts side-by-side with automatic metric delta computation:

```bash
vcm compare models/iris_classifier_v1.pkl models/iris_rf_v2.pkl
```

```text
Comparison: iris_classifier_v1 vs iris_rf_v2
╭──────────────────┬──────────────────────┬────────────────────┬──────────────────╮
│ Field / Metric   │ iris_classifier_v1   │ iris_rf_v2         │ Delta / Change   │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ Accuracy         │ 96.7%                │ 98.2%              │ +1.5%            │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ F1_score         │ 96.5%                │ 98.1%              │ +1.6%            │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ Precision        │ 0.9650               │ 0.9810             │ +0.0160          │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ Recall           │ 0.9650               │ 0.9810             │ +0.0160          │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ Dataset          │ data/iris_v1.csv     │ data/iris_v1.csv   │ Same             │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ Git Commit       │ 427af932             │ 55d5b5e6           │ Different        │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ learning_rate    │ 0.01                 │ N/A                │ Changed          │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ max_depth        │ N/A                  │ 4                  │ Changed          │
├──────────────────┼──────────────────────┼────────────────────┼──────────────────┤
│ n_estimators     │ N/A                  │ 100                │ Changed          │
╰──────────────────┴──────────────────────┴────────────────────┴──────────────────╯

Model 'iris_rf_v2' outperforms 'iris_classifier_v1':
   - 1.5% higher accuracy
```

### Model Inspection & Export (`vcm info` & `vcm export`)

```bash
# View formatted summary
vcm info models/iris_rf_v2.pkl

# View or export raw JSON metadata
vcm info models/iris_rf_v2.pkl --json
vcm export models/iris_rf_v2.pkl --output metadata_export.json
```

### Self-Healing Index Reconstruction (`vcm repair`)

If `.vcm/vcm.db` is accidentally removed or corrupted, run `vcm repair` to reconstruct the SQLite database from existing `.vcm.json` sidecar files:

```bash
rm .vcm/vcm.db
vcm repair
```

```text
Database repaired: Re-indexed 3 models.
```

---

## Python SDK Integration

VCM can be integrated directly into training scripts via the Python API:

### Method 1: Context Manager

```python
from vcm.trainer import ModelTracker
import joblib

tracker = ModelTracker()

with tracker.track(
    model_name="random_forest_v1",
    model_path="models/rf_model.pkl",
    hyperparameters={"n_estimators": 100, "max_depth": 5},
    dataset_path="data/train.csv",
) as session:
    # 1. Train model
    clf.fit(X_train, y_train)
    
    # 2. Evaluate
    acc = accuracy_score(y_test, clf.predict(X_test))
    
    # 3. Persist model binary
    joblib.dump(clf, "models/rf_model.pkl")
    
    # 4. Attach metrics to session
    session.set_metrics({"accuracy": acc, "f1_score": 0.94})
```

### Method 2: Direct Logging

```python
from vcm.trainer import ModelTracker

tracker = ModelTracker()

metadata = tracker.log_model(
    model_path="models/classifier.pkl",
    model_name="classifier_prod_v1",
    metrics={"accuracy": 0.952, "loss": 0.048},
    hyperparameters={"batch_size": 64, "lr": 0.001},
    dataset_path="data/dataset.csv",
)
```

---

## Model DNA Sidecar Specification

Each `.vcm.json` metadata sidecar follows this immutable JSON structure:

```json
{
  "schema_version": "1.0.0",
  "model_name": "iris_rf_v2",
  "model_file": "models/iris_rf_v2.pkl",
  "model_hash": "sha256:31f721cc48842a26a2428365962721c86000159368ebb0f656eb87bb69d58143",
  "created_at": "2026-09-09T13:35:14.316716+00:00",
  "code": {
    "git_commit": "55d5b5e6e72a5959108662acf4006d2a426c2d41",
    "git_branch": "main",
    "git_remote": "origin",
    "git_url": "https://github.com/org/ml-repo.git",
    "is_dirty": false
  },
  "data": {
    "dvc_files": [
      {
        "path": "data/iris_v1.csv",
        "dvc_hash": "84f2c9e782e4f012a91f58b0931215b2",
        "size_bytes": 614
      }
    ]
  },
  "training": {
    "timestamp": "2026-09-09T13:35:14.316666+00:00",
    "duration_seconds": 1.42,
    "user": "kishorveeraragavan",
    "hostname": "workstation-01"
  },
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 4
  },
  "metrics": {
    "accuracy": 0.982,
    "f1_score": 0.981
  },
  "environment": {
    "python_version": "3.14.7",
    "libraries": {
      "scikit-learn": "1.6.1",
      "pandas": "2.2.3",
      "numpy": "2.2.3"
    }
  }
}
```

---

## Test Suite & Verification

VCM includes a test suite covering unit, integration, CLI, error handling, performance benchmarks, and real ML lifecycle verification:

```bash
# Run pytest with full coverage report
pytest vcm/tests/ -v --cov=vcm

# Run static type checking
mypy vcm/ --python-version 3.12

# Run linter
flake8 vcm/ --max-line-length=140
```

### Test Coverage Summary

```text
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
vcm/cli/commands.py                        291     74    75%
vcm/config.py                               49      2    96%
vcm/db/database.py                         180     32    82%
vcm/integrations/dvc_client.py             109     19    83%
vcm/integrations/git_client.py              86     17    80%
vcm/models/metadata.py                     131      2    98%
vcm/trainer.py                             129     24    81%
vcm/utils/metrics_loader.py                 68      5    93%
...
------------------------------------------------------------
TOTAL                                     2087    182    91%
65 passed in 6.05s
```

---

## Contributing

Contributions are welcome. Please ensure your contributions satisfy all quality checks:

1. Fork the repository and create a feature branch (`git checkout -b feature/model-provenance`).
2. Implement your changes with corresponding test coverage under `vcm/tests/`.
3. Verify test passing and 90%+ code coverage (`pytest vcm/tests/ -v --cov=vcm`).
4. Ensure static analysis and formatting compliance (`mypy vcm/` and `flake8 vcm/`).
5. Submit a Pull Request.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
