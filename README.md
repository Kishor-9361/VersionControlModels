# VCM (Version Control Models)

**Model DNA Version Control Platform**  
*Version:* `1.0.0-MVP`

VCM is a lightweight, zero-configuration version control system for machine learning models. It connects your code (Git), your data (DVC), your training metrics, hyperparameters, and environment dependencies into an immutable **Model DNA** record.

---

## Key Features

- 🧬 **Automatic Metadata Capture:** Captures Git commit hash, DVC dataset hashes, training duration, user context, Python environment, hyperparameters, and evaluation metrics without boilerplate.
- ⚡ **Zero Setup & Ultra-Fast:** Dual persistence with human-readable `.vcm.json` sidecar files attached to model artifacts and indexed in local SQLite (`.vcm/vcm.db`).
- 🌲 **Model Lineage:** Inspect the complete lineage tree connecting trained models back to their exact source code commits, datasets, and hyperparameters.
- ⚖️ **Model Comparison:** Compare two model versions side-by-side with automatic metric delta highlighting.
- 🛡️ **Zero Lock-In & Self-Healing:** JSON-serializable, portable metadata. If the SQLite database is ever deleted or corrupted, `vcm repair` rebuilds the complete index from `.vcm.json` files.

---

## Quick Start

### 1. Installation

```bash
pip install -e .
```

### 2. Initialize in your ML Project

```bash
vcm init
```

This creates:
- `.vcmconfig.yaml`
- `.vcm/vcm.db`
- `models/` directory

### 3. Track Training

```bash
vcm train --model-name "emotion_classifier_v1" \
          --dataset "data/train.csv" \
          --script train.py \
          --metrics metrics.json \
          --params lr=0.001 epochs=50 batch_size=32
```

Output:
```
Running training script: train.py ...
[Script output]
✅ Model tracked successfully
   Model: emotion_classifier_v1
   Accuracy: 94.2%
   Git commit: abc123def456
   Dataset: data/train.csv
   Metadata: models/emotion_classifier_v1.pkl.vcm.json
```

### 4. Query & Filter Models

```bash
# List all models
vcm models

# Filter by dataset
vcm models --dataset "data/train.csv"

# Show highest accuracy model
vcm models --best
```

### 5. Inspect Lineage

```bash
vcm lineage models/emotion_classifier_v1.pkl
```

### 6. Compare Two Models

```bash
vcm compare models/emotion_classifier_v1.pkl models/emotion_classifier_v2.pkl
```

### 7. Export Metadata

```bash
vcm export models/emotion_classifier_v1.pkl --output metadata.json
```

---

## Python API Usage

You can also use VCM directly within your Python scripts:

### Mode 1: Context Manager

```python
from vcm.trainer import ModelTracker

tracker = ModelTracker()

with tracker.track(
    model_name="classifier_v1",
    model_path="models/classifier.pkl",
    hyperparameters={"lr": 0.001, "epochs": 50},
) as session:
    # Train your model
    model = train_model()
    metrics = evaluate_model(model)
    model.save("models/classifier.pkl")
    session.set_metrics(metrics)
```

### Mode 2: Manual Logging

```python
from vcm.trainer import ModelTracker

tracker = ModelTracker()
tracker.log_model(
    model_path="models/classifier.pkl",
    model_name="classifier_v1",
    metrics={"accuracy": 0.942, "f1_score": 0.928},
    hyperparameters={"batch_size": 32},
    dataset_path="data/train.csv",
)
```

---

## Architecture Overview

```
project/
├── .vcmconfig.yaml          # VCM configuration
├── .vcm/
│   └── vcm.db              # SQLite index
├── models/
│   ├── model_v1.pkl
│   ├── model_v1.pkl.vcm.json  # Attached immutable metadata
│   ├── model_v2.pkl
│   └── model_v2.pkl.vcm.json
├── data/                    # DVC tracked datasets
├── train.py                 # Training script
└── .git/                    # Git repository
```

---

## Testing & Quality

Run the test suite with pytest:

```bash
pytest vcm/tests/ -v --cov=vcm
```

Run static type checking and linting:

```bash
mypy vcm/
flake8 vcm/ --max-line-length=140
```
