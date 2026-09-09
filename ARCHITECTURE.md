# VCM Architecture Design & Specifications

## 1. System Overview

VCM (Version Control Models) implements a two-tier storage and metadata architecture designed for machine learning reproducibility and model DNA tracking.

```
+-------------------------------------------------------------+
|                         CLI Layer                           |
|  init | train | models | lineage | compare | info | export  |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                      Core & Tracker                         |
|   - ModelTracker (Wrapper & Context Manager)                |
|   - EnvironmentCapture (Runtime & Packages)                 |
|   - GitClient (Commits, Branches, Remotes)                  |
|   - DVCClient (.dvc files, dvc.lock, MD5/SHA hashes)        |
|   - MetricsLoader (JSON & Parameter Parsing)                |
+-------------------------------------------------------------+
               |                               |
               v                               v
+-----------------------------+ +-----------------------------+
|   Immutable File Storage    | |     SQLite Storage Layer    |
|   <model_file>.vcm.json     | |     .vcm/vcm.db             |
|   (Attached sidecar JSON)   | |     (Fast queryable index)  |
+-----------------------------+ +-----------------------------+
```

---

## 2. Storage Strategy: SQLite + JSON

1. **Immutable Sidecar JSON (`.vcm.json`)**:
   - Each model file has a companion `.vcm.json` (e.g. `models/model_v1.pkl.vcm.json`).
   - Self-contained, portable across systems, versionable in Git/DVC, and independent of centralized databases.
2. **Local SQLite Index (`.vcm/vcm.db`)**:
   - Provides sub-millisecond query performance across thousands of models.
   - Configured with WAL (Write-Ahead Logging) mode and busy timeouts for seamless concurrent access.
3. **Self-Healing & Auto-Recovery**:
   - The SQLite index is completely reconstructible from `.vcm.json` files on disk via `vcm repair`.

---

## 3. Database Schema

```sql
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_file TEXT NOT NULL,
    model_hash TEXT UNIQUE,
    accuracy REAL,
    f1_score REAL,
    git_commit TEXT,
    git_branch TEXT,
    dataset_hash TEXT,
    training_timestamp DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_name ON models(model_name);
CREATE INDEX IF NOT EXISTS idx_accuracy ON models(accuracy DESC);
CREATE INDEX IF NOT EXISTS idx_git_commit ON models(git_commit);
CREATE INDEX IF NOT EXISTS idx_dataset_hash ON models(dataset_hash);
```

---

## 4. Metadata Schema

```json
{
  "model_name": "emotion_classifier_v2",
  "model_hash": "sha256:abc123...",
  "model_file": "models/emotion_classifier_v2.pkl",
  "code": {
    "git_commit": "abc123def456",
    "git_branch": "main",
    "git_remote": "origin",
    "git_url": "https://github.com/user/repo"
  },
  "data": {
    "dvc_files": [
      {
        "path": "data/train.csv",
        "dvc_hash": "xyz789...",
        "size_bytes": 1024000,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  },
  "training": {
    "timestamp": "2024-01-15T10:45:32Z",
    "duration_seconds": 3600,
    "user": "alice",
    "hostname": "ml-workstation-1"
  },
  "hyperparameters": {
    "learning_rate": 0.001,
    "epochs": 50,
    "batch_size": 32,
    "random_seed": 42
  },
  "metrics": {
    "accuracy": 0.942,
    "precision": 0.921,
    "recall": 0.935,
    "f1_score": 0.928
  },
  "environment": {
    "python_version": "3.9.1",
    "libraries": {
      "torch": "2.0.1",
      "scikit-learn": "1.2.0",
      "pandas": "2.0.0"
    }
  },
  "metadata_version": "1.0",
  "created_at": "2024-01-15T10:45:32Z"
}
```
