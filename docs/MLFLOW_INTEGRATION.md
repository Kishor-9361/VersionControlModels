# VCM & MLflow Integration Guide

**VCM (Version Control Models)** seamlessly connects with **MLflow** to provide full bidirectional synchronization between immutable Model DNA (Git commit SHA, DVC dataset content hashes, hyperparameters, environment) and MLflow's experiment tracking & model registry UI.

---

## 1. Architecture Overview

```
+-------------------------------------------------------------+
|                      Machine Learning Run                   |
|                   (vcm train --model-name ...)              |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     VCM Model DNA Capture                   |
|       Code Commit + DVC Dataset Hash + Params + Metrics     |
+---------------+-----------------------------+---------------+
                |                             |
                v                             v
+-------------------------------+ +---------------------------+
|    Portable VCM Sidecars      | |    MLflow Client Sync     |
|     (<model>.vcm.json)        | |  (Native SDK or Offline)  |
+---------------+---------------+ +-------------+-------------+
                |                               |
                v                               v
+-------------------------------+ +---------------------------+
|     Local SQLite Index        | |       MLflow Server       |
|        (.vcm/vcm.db)          | |    (http://localhost:5000)|
+-------------------------------+ +---------------------------+
```

### Dual-Mode Support
- **Native Python SDK Mode**: If the `mlflow` library is installed (`pip install mlflow`), VCM connects directly to any remote or local tracking server (AWS SageMaker, Databricks, local `http://localhost:5000`) and logs metrics, parameters, tags, and model artifacts via the native MLflow Client.
- **Zero-Dependency Offline File Store Mode**: If `mlflow` is not installed, VCM logs runs into standard MLflow directory structure (`./mlruns/<experiment_id>/<run_id>/`) with `meta.yaml`, `params/`, `metrics/`, and `tags/`. You can view these runs immediately at any time by launching `mlflow ui`.

---

## 2. Quick Setup

### Step 1: Install MLflow (Optional for remote tracking)
```bash
pip install mlflow
```

### Step 2: Configure MLflow in VCM
```bash
# Enable MLflow integration
vcm mlflow enable

# Set tracking server URI (remote server or local directory)
vcm config set mlflow_tracking_uri "http://localhost:5000"
# or for local runs:
vcm config set mlflow_tracking_uri "file:./mlruns"

# Set target experiment name
vcm config set mlflow_experiment_name "iris_classification"
```

### Step 3: Inspect Connection Status
```bash
vcm mlflow status
```
**Example Output:**
```
MLflow Integration Status
══════════════════════════════════════════════════
Status:          enabled
Tracking URI:    http://localhost:5000
Experiment:      iris_classification
Python SDK:      installed (native SDK active)
```

---

## 3. CLI Commands

### Sync a Specific Model to MLflow
```bash
vcm mlflow sync iris_rf_v2
```
**Output:**
```
Model 'iris_rf_v2' synced to MLflow successfully.
   Run ID:      7b04e6c989874a95a4980bb29ff4bf26
   Mode:        native_sdk
   Destination: http://localhost:5000
   Experiment:  iris_classification
```

### Sync All Models in Workspace
```bash
vcm mlflow sync --all
```
**Output:**
```
Synced 3 model(s) to MLflow:
  • iris_logistic_v1 -> run_id: 48e9df64789d4432 (native_sdk)
  • iris_rf_v2 -> run_id: 7b04e6c989874a95 (native_sdk)
  • iris_gb_v3 -> run_id: 11ac92837bc94120 (native_sdk)
Target: http://localhost:5000 [Experiment: iris_classification]
```

### Disable MLflow Integration
```bash
vcm mlflow disable
```

---

## 4. Metadata Mapping (VCM to MLflow)

Every synced model run in MLflow includes rich tags linking back to VCM:

| VCM Model DNA Attribute | MLflow Property | Purpose |
| :--- | :--- | :--- |
| `model_name` | `mlflow.runName` | Human-readable run name |
| `model_hash` | Tag `vcm.model_hash` | Cryptographic SHA-256 hash of model binary |
| `code.git_commit` | Tag `vcm.git_commit` | Exact Git commit SHA used during training |
| `code.git_branch` | Tag `vcm.branch` | Active Git branch |
| `data.dvc_files.path` | Tag `vcm.dataset_path` | DVC-tracked dataset path |
| `data.dvc_files.dvc_hash`| Tag `vcm.dataset_hash` | Exact content hash of training dataset |
| `reasoning` | Tag `vcm.reasoning` | Developer reasoning note explaining why version was trained |
| `hyperparameters` | MLflow Parameters | Tunable parameters (`n_estimators`, `max_depth`, `learning_rate`) |
| `metrics` | MLflow Metrics | Evaluation metrics (`accuracy`, `precision`, `recall`, `f1_score`) |
| Model Sidecar (`<model>.vcm.json`) | Artifact | Immutable JSON sidecar attached directly to run artifacts |

---

## 5. Python API Usage

You can also use the MLflow client directly in your Python code and Jupyter notebooks:

```python
from vcm.integrations.mlflow_client import MLflowClient
from vcm.cli.commands import _find_metadata

# Initialize client with custom tracking URI
client = MLflowClient(
    tracking_uri="http://localhost:5000",
    experiment_name="production_models",
)

# Sync a model
meta = _find_metadata("iris_rf_v2")
if meta:
    result = client.sync_model(meta)
    print(f"Synced run {result['run_id']} to {result['tracking_uri']}")
```
