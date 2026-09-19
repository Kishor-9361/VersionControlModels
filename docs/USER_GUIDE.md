# VCM End-to-End User Guide & Tutorial

Welcome to the **VCM (Version Control Models)** User Guide! This practical walkthrough will take you through setting up VCM in a machine learning project, tracking iterations, conducting experiment sessions, analyzing model progression, detecting performance regressions, and deploying models with an audit trail.

---

## Table of Contents
1. [Project Setup & Initialization](#1-project-setup--initialization)
2. [Tracking Your First Model](#2-tracking-your-first-model)
3. [Iterative Development with Sessions](#3-iterative-development-with-sessions)
4. [Visualizing the Model Evolution Timeline](#4-visualizing-the-model-evolution-timeline)
5. [Detecting & Diagnosing Regressions](#5-detecting--diagnosing-regressions)
6. [Comparing Models & Sessions](#6-comparing-models--sessions)
7. [Deploying to Production & Auditing](#7-deploying-to-production--auditing)
8. [Reproducing Historical Models](#8-reproducing-historical-models)
9. [Integrating Directly in Python / Notebooks](#9-integrating-directly-in-python--notebooks)

---

## 1. Project Setup & Initialization

First, navigate to your machine learning project repository:

```bash
cd my_ml_project
```

Initialize VCM:

```bash
vcm init
```

This creates:
- `.vcmconfig.yaml`: Workspace configuration file.
- `.vcm/vcm.db`: Local SQLite database.
- `models/`: Default directory for trained model binaries.

---

## 2. Tracking Your First Model

Suppose you have a training script `train.py` that writes metrics to `metrics.json`:

```python
# train.py
import json
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
import joblib

X, y = load_iris(return_X_y=True)
clf = RandomForestClassifier(n_estimators=20, max_depth=3, random_state=42)
clf.fit(X, y)
joblib.dump(clf, "models/iris_baseline.pkl")

with open("metrics.json", "w") as f:
    json.dump({"accuracy": 0.92, "f1_score": 0.91}, f)
```

Execute training under VCM:

```bash
vcm train --model-name iris_baseline \
          --script train.py \
          --dataset data/iris.csv \
          --metrics metrics.json \
          --params n_estimators=20 max_depth=3 \
          --reasoning "Baseline random forest with conservative depth"
```

VCM will:
1. Run `train.py`.
2. Capture Git commit hash, branch, and working tree diff.
3. Compute dataset hashes (DVC or SHA-256).
4. Record hardware and runtime library versions.
5. Create `models/iris_baseline.pkl.vcm.json` portable sidecar.
6. Register the model in `.vcm/vcm.db`.

---

## 3. Iterative Development with Sessions

When running multiple experiments, group them into a **Session**:

```bash
# 1. Start session
vcm session start "hyperparam_tuning" --description "Exploring tree capacity on Iris"

# 2. Add an experimental hypothesis
vcm session annotate "Hypothesis: Increasing n_estimators to 50 will improve boundary accuracy" --category hypothesis

# 3. Train iteration 2
vcm train --model-name iris_rf_v2 \
          --script train.py \
          --dataset data/iris.csv \
          --metrics metrics.json \
          --params n_estimators=50 max_depth=4 \
          --reasoning "Expanded tree count to 50"

# 4. View captured terminal logs (sensitive tokens automatically masked)
vcm session logs hyperparam_tuning

# 5. Conclude session
vcm session end
```

---

## 4. Visualizing the Model Evolution Timeline

View how models progressed over time:

```bash
# Display colorized table in console with reasoning
vcm timeline --show-reasoning --highlight-best
```

Sample output:
```
+---+---------------+----------+----------------+------------------------------------------+
| # | Model ID      | Accuracy | Delta          | Reasoning                                |
+---+---------------+----------+----------------+------------------------------------------+
| 1 | iris_baseline | 0.9200   | --             | Baseline random forest with conservative |
| 2 | iris_rf_v2    | 0.9600   | +0.0400 (+4.0%)| Expanded tree count to 50 [BEST]         |
+---+---------------+----------+----------------+------------------------------------------+
```

### Exporting an Interactive HTML Visualizer
To view a rich browser visualizer with an inline SVG sparkline graph and model cards:

```bash
vcm timeline --format html --output ./reports/timeline_report.html
```

Open `reports/timeline_report.html` in any web browser!

---

## 5. Detecting & Diagnosing Regressions

What if a subsequent experiment hurts model accuracy?

```bash
# Train a model that underfits
vcm train --model-name iris_stump \
          --script train.py \
          --dataset data/iris.csv \
          --metrics metrics.json \
          --params n_estimators=1 max_depth=1 \
          --reasoning "Testing extreme compression"
```

Run automated timeline analysis:

```bash
vcm timeline analyze --threshold 0.02 --report detailed
```

VCM detects the drop and diagnoses the root cause:
```
[!] REGRESSION DETECTED at model 'iris_stump':
    Accuracy: 0.7000 (-0.2600 / -26.0% drop)
    Root Cause: Hyperparameters modified (n_estimators: 50 -> 1, max_depth: 4 -> 1)
```

---

## 6. Comparing Models & Sessions

### Compare Two Models
```bash
vcm compare iris_baseline iris_rf_v2
```

### Compare Two Experimental Sessions
```bash
vcm session compare session_01 session_02
```

---

## 7. Deploying to Production & Auditing

### Deploy a Model
```bash
vcm deploy iris_rf_v2 --environment production
```

### Inspect the Production Audit Trail
```bash
vcm audit --environment production
```

Output:
```
==============================================================================
VCM DEPLOYMENT AUDIT TRAIL: production
==============================================================================
Model Name:          iris_rf_v2
Model File:          models/iris_rf_v2.pkl
Trained By:          alice
Git Commit:          7a8b9c0d
Git Branch:          main
Accuracy:            0.9600
Deployed At:         2026-09-16T12:45:00
Deployment Status:   ACTIVE
==============================================================================
```

---

## 8. Reproducing Historical Models

If an auditor or teammate asks to reproduce an older model:

```bash
vcm reproduce iris_baseline
```

VCM automatically:
1. Validates the code repository commit state.
2. Checks dataset availability.
3. Re-runs training with the identical hyperparameters.
4. Verifies prediction equivalence (100% parity).

---

## 9. Integrating Directly in Python / Notebooks

You can use VCM without leaving your Python script or Jupyter Notebook:

```python
from vcm.trainer import ModelTracker
from vcm.models.session import SessionTracker
from vcm.models.timeline import TimelineStore
from vcm.db.database import Database

# Track training run
tracker = ModelTracker()
with tracker.track("iris_v3", "models/iris_v3.pkl", hyperparameters={"lr": 0.05}) as run:
    # Training code here...
    run.set_metrics({"accuracy": 0.975})

# Retrieve timeline
db = Database()
store = TimelineStore(db)
timeline = store.get_model_timeline()
print(f"Current best accuracy: {timeline.best_model['accuracy']:.2%}")
```
