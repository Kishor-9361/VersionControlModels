# VCM (Version Control Models)

**Model DNA Version Control Platform**  
*Enterprise-grade, lightweight, and zero-configuration version control for machine learning models.*

[![Release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/Kishor-9361/VersionControlModels/releases)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/architecture-zero--lockin-orange.svg)](#architecture--data-flow)
[![Code Style](https://img.shields.io/badge/code%20style-flake8%20%7C%20mypy-black.svg)](https://github.com/psf/black)

---

## Executive Overview

In software engineering, **Git** tracks source code. In data engineering, **DVC** tracks datasets. However, machine learning models exist at the intersection of code, data, hyperparameters, runtime dependencies, and evaluation metrics.

Without a dedicated model version control system, identifying which Git commit produced a specific model binary, on which dataset version, with which hyperparameters, and under which environment dependencies is fragmented and difficult to audit.

**VCM (Version Control Models)** establishes complete traceability and reproducibility by automatically packaging your code state, dataset hashes, training parameters, evaluation metrics, and system environment into an immutable, tamper-evident record termed **Model DNA**.

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
  |   Model Binary    |       | Portable Sidecar   |
  | (.pkl, .pt, .onnx)| <---> | (<model>.vcm.json) |
  +-------------------+       +---------+----------+
                                        |
                                        v
                              +--------------------+
                              | Local SQLite Index |
                              |  (.vcm/vcm.db)     |
                              +--------------------+
```

---

## Key Features

- **Automatic Model DNA Capture**: Automatically extracts the exact Git commit SHA, branch, remote repository URL, DVC/content dataset hashes, hyperparameters, training duration, and runtime dependencies with zero boilerplate.
- **Dual-Layer Persistence (Zero Lock-In)**: Every model file (`.pkl`, `.onnx`, `.pt`, `.joblib`) has an attached `<model>.vcm.json` sidecar that travels with the binary across local storage, S3, GCS, or Git LFS. An optimized local SQLite database (`.vcm/vcm.db`) indexes all records for sub-millisecond queries.
- **Complete Lineage Provenance**: Visualize the exact provenance tree connecting a trained model binary back to its source code, dataset revisions, hyperparameters, and environment context.
- **Side-by-Side Model Diffing**: Compare any two models with automatic delta computation across evaluation metrics, hyperparameter adjustments, dataset shifts, and code revisions.
- **Self-Healing Architecture (`vcm repair`)**: The local SQLite database operates as an ephemeral query acceleration index. If deleted, corrupted, or moved across machines, `vcm repair` reconstructs the entire index from disk sidecars in seconds.
- **Flexible CLI & Multi-Parameter Parsing**: Accepts hyperparameters passed as repeated flags (`--params lr=0.01 --params max_depth=5`), space-separated pairs (`--params lr=0.01 max_depth=5`), or quoted comma-separated strings.
- **Framework Agnostic**: Works out-of-the-box with PyTorch, TensorFlow, Scikit-learn, XGBoost, LightGBM, Hugging Face, ONNX, and custom ML pipelines.

---

## Installation

### Prerequisites
- Python 3.9 or higher
- Git (optional, for code versioning)
- DVC (optional, for dataset hash tracking)

### Install via pip

Clone and install VCM locally:

```bash
git clone https://github.com/Kishor-9361/VersionControlModels.git
cd VersionControlModels

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install VCM in editable mode
pip install -e .
```

Verify that the CLI is accessible:

```bash
vcm --version
vcm --help
```

---

## Quick Start Workflow

### 1. Initialize VCM in Your Project

Navigate to your ML project directory and run:

```bash
vcm init
```

This initializes:
- `.vcmconfig.yaml`: Project configuration settings.
- `.vcm/vcm.db`: Local SQLite metadata index.
- `models/`: Default directory for trained model artifacts.

### 2. Track a Training Run

Run your existing training script through `vcm train`. VCM executes the script and automatically captures the code commit, data hashes, metrics, and environment:

```bash
vcm train --model-name "my_model_v1" \
          --dataset "data/train.csv" \
          --script "train.py" \
          --metrics "metrics.json" \
          --model-file "models/my_model_v1.pkl" \
          --params learning_rate=0.01 batch_size=32 epochs=50
```

Output:
```text
Running training script: train.py ...
[Script output]

Model tracked successfully.
  Model:      my_model_v1
  Accuracy:   94.2%
  Git commit: a8f41b92c0192e8fa4d9b62ef05d15c7e39a018b
  Dataset:    data/train.csv
  Metadata:   models/my_model_v1.pkl.vcm.json
```

---

## CLI Command Reference

| Command | Description | Example |
| :--- | :--- | :--- |
| `vcm init` | Initialize VCM configuration and database in the current project | `vcm init` |
| `vcm train` | Execute a training script and record Model DNA | `vcm train --model-name m1 --script train.py` |
| `vcm models` | List, query, and filter tracked models | `vcm models --best` |
| `vcm lineage` | Render provenance tree for a model artifact | `vcm lineage models/model.pkl` |
| `vcm compare` | Diff two models side-by-side with metric deltas | `vcm compare models/m1.pkl models/m2.pkl` |
| `vcm info` | Display detailed metadata and environment configuration | `vcm info models/model.pkl` |
| `vcm export` | Export model metadata to standalone JSON file or stdout | `vcm export models/model.pkl -o meta.json` |
| `vcm repair` | Rebuild SQLite database from `.vcm.json` sidecar files | `vcm repair` |

---

## CLI Usage Examples

### Listing & Filtering Models (`vcm models`)

Display all tracked models in a structured table:

```bash
vcm models
```

```text
╭────────────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name         │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├────────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ my_model_v2        │ 96.5%      │ 96.2%      │ data/train.csv   │ 55d5b5e6     │ 2026-09-09 15:30 │
├────────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ my_model_v1        │ 94.2%      │ 93.8%      │ data/train.csv   │ a8f41b92     │ 2026-09-09 14:15 │
├────────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ baseline_model_v0  │ 89.1%      │ 88.5%      │ data/train.csv   │ 427af932     │ 2026-09-09 11:00 │
╰────────────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 3 models found
```

Filter by dataset, select top performers, or export:

```bash
# Filter models by dataset file or hash
vcm models --dataset "data/train.csv"

# Show only the top performing model
vcm models --best

# Export model catalog to CSV or JSON
vcm models --export models_export.csv
vcm models --format json --export models_export.json
```

### Lineage Provenance Tree (`vcm lineage`)

Inspect the complete lineage tree connecting a model binary to its code commit, dataset files, hyperparameters, and environment:

```bash
vcm lineage models/my_model_v2.pkl
```

```text
Model: my_model_v2 (models/my_model_v2.pkl)
├── Accuracy: 0.9650 (96.5%) | F1 Score: 0.9620
├── Git Commit: 55d5b5e6e72a5959108662acf4006d2a426c2d41
│   ├── Branch: main
│   ├── Remote: origin
│   └── URL: https://github.com/Kishor-9361/VersionControlModels.git
├── Dataset Files:
│   ├── data/train.csv (hash: 84f2c9e782e4f012..., size: 14.2 MB)
├── Hyperparameters:
│   ├── learning_rate: 0.005
│   ├── batch_size: 64
│   ├── epochs: 100
└── Trained by: ml-engineer on prod-cluster-01 (2026-09-09T15:30:00+00:00)
```

### Side-by-Side Model Comparison (`vcm compare`)

Compare two model artifacts side-by-side with metric delta computation and parameter diffs:

```bash
vcm compare models/my_model_v1.pkl models/my_model_v2.pkl
```

```text
Comparison: my_model_v1 vs my_model_v2
╭──────────────────┬──────────────────┬──────────────────┬──────────────────╮
│ Field / Metric   │ my_model_v1      │ my_model_v2      │ Delta / Change   │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Accuracy         │ 94.2%            │ 96.5%            │ +2.3%            │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ F1_score         │ 93.8%            │ 96.2%            │ +2.4%            │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Precision        │ 0.9400           │ 0.9640           │ +0.0240          │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Recall           │ 0.9360           │ 0.9600           │ +0.0240          │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Dataset          │ data/train.csv   │ data/train.csv   │ Same             │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Git Commit       │ a8f41b92         │ 55d5b5e6         │ Different        │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ learning_rate    │ 0.01             │ 0.005            │ Changed          │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ batch_size       │ 32               │ 64               │ Changed          │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ epochs           │ 50               │ 100              │ Changed          │
╰──────────────────┴──────────────────┴──────────────────┴──────────────────╯

Model 'my_model_v2' outperforms 'my_model_v1':
   - 2.3% higher accuracy
```

### Model Inspection & Export (`vcm info` & `vcm export`)

```bash
# View human-readable model summary
vcm info models/my_model_v2.pkl

# View or export raw JSON metadata
vcm info models/my_model_v2.pkl --json
vcm export models/my_model_v2.pkl --output metadata_export.json
```

### Ephemeral Recovery (`vcm repair`)

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

VCM can also be used directly within Python scripts and Jupyter notebooks:

### Context Manager Mode

```python
from vcm.trainer import ModelTracker
import joblib

tracker = ModelTracker()

with tracker.track(
    model_name="my_model_v3",
    model_path="models/my_model_v3.pkl",
    hyperparameters={"learning_rate": 0.001, "batch_size": 128},
    dataset_path="data/train.csv",
) as session:
    # 1. Train model
    model.fit(X_train, y_train)
    
    # 2. Evaluate
    acc = accuracy_score(y_test, model.predict(X_test))
    
    # 3. Save model binary
    joblib.dump(model, "models/my_model_v3.pkl")
    
    # 4. Attach evaluation metrics
    session.set_metrics({"accuracy": acc, "f1_score": 0.958})
```

### Direct Logging Mode

```python
from vcm.trainer import ModelTracker

tracker = ModelTracker()

metadata = tracker.log_model(
    model_path="models/my_model_prod.pkl",
    model_name="my_model_prod_v1",
    metrics={"accuracy": 0.952, "loss": 0.048},
    hyperparameters={"batch_size": 64, "learning_rate": 0.001},
    dataset_path="data/train.csv",
)
```

---

## Model DNA Sidecar Specification

Each model artifact has a corresponding `.vcm.json` sidecar file adhering to this specification:

```json
{
  "schema_version": "1.0.0",
  "model_name": "my_model_v2",
  "model_file": "models/my_model_v2.pkl",
  "model_hash": "sha256:31f721cc48842a26a2428365962721c86000159368ebb0f656eb87bb69d58143",
  "created_at": "2026-09-09T15:30:00.000000+00:00",
  "code": {
    "git_commit": "55d5b5e6e72a5959108662acf4006d2a426c2d41",
    "git_branch": "main",
    "git_remote": "origin",
    "git_url": "https://github.com/Kishor-9361/VersionControlModels.git",
    "is_dirty": false
  },
  "data": {
    "dvc_files": [
      {
        "path": "data/train.csv",
        "dvc_hash": "84f2c9e782e4f012a91f58b0931215b2",
        "size_bytes": 14200000
      }
    ]
  },
  "training": {
    "timestamp": "2026-09-09T15:30:00.000000+00:00",
    "duration_seconds": 12.45,
    "user": "ml-engineer",
    "hostname": "prod-cluster-01"
  },
  "hyperparameters": {
    "learning_rate": 0.005,
    "batch_size": 64,
    "epochs": 100
  },
  "metrics": {
    "accuracy": 0.965,
    "f1_score": 0.962
  },
  "environment": {
    "python_version": "3.12.0",
    "libraries": {
      "scikit-learn": "1.5.0",
      "pandas": "2.2.0",
      "numpy": "1.26.0"
    }
  }
}
```

---

## Development & Testing

To run the automated test suite locally:

```bash
# Run pytest
pytest vcm/tests/ -v

# Run static type checking
mypy vcm/

# Run linter
flake8 vcm/ --max-line-length=140
```

---

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository on GitHub.
2. Create a feature branch (`git checkout -b feature/new-capability`).
3. Implement your changes with corresponding test coverage.
4. Ensure all tests and linters pass (`pytest`, `mypy`, `flake8`).
5. Open a Pull Request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
