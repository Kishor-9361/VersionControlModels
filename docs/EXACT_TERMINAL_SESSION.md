# Exact VCM Terminal Session Transcript

**User:** Kishor Veeraragavan  
**Host:** `fedora`  
**Working Directory:** `~/Desktop/VersionControl/ml_project_demo`  
**Environment:** Python 3.14.7 Virtual Environment (`venv`)  
**Package Version:** VCM 1.0.0 (Release: 2026-09-16)  
**Repository:** [https://github.com/Kishor-9361/VersionControlModels](https://github.com/Kishor-9361/VersionControlModels)

---

## Complete Verbatim Terminal Session Log

```console
kishorveeraragavan@fedora:~/Desktop/VersionControl$ source venv/bin/activate
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl$ cd ml_project_demo/
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm --version
vcm, version 1.0.0
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm version
VCM version 1.0.0
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm version --verbose
VCM Version: 1.0.0
Release: 2024-01-15
License: MIT
Home: https://github.com/user/vcm
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm --version
vcm, version 1.0.0
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm version
VCM version 1.0.0
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm version --verbose
VCM Version: 1.0.0
Release: 2026-09-16
License: MIT
Author: Kishor Veeraragavan
Home: https://github.com/Kishor-9361/VersionControlModels
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm --help
Usage: vcm [OPTIONS] COMMAND [ARGS]...

  VCM (Version Control Models) - Model DNA Version Control Platform.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  analysis         Analyze model lineages, code evolutions, and...
  audit            Inspect model deployment audit trail for an environment.
  compare          Compare two models side-by-side.
  config           Manage VCM configuration settings.
  deploy           Deploy a model and log its audit trail.
  export           Export model metadata to JSON file or stdout.
  info             Show detailed model metadata.
  init             Initialize VCM in current project.
  lineage          Show complete lineage tree for a model.
  models           List and filter tracked models.
  repair           Rebuild SQLite database from existing .vcm.json files...
  reproduce        Rebuild and reproduce a trained model from its metadata.
  session          Manage development and training sessions.
  timeline         Display model evolution timeline and progression...
  timeline-reason  Add or view reasoning for why a model version was...
  train            Wrap model training and automatically capture code,...
  version          Show VCM version.
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm config show

Current Configuration
══════════════════════════════════════════════════
database_path: .vcm/vcm.db
models_dir:    models

integrations:
  git: enabled
  dvc: enabled
  mlflow: disabled

session_logging:
  enabled: true
  capture_terminal: true
  mask_secrets: true

(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm config set models_dir models
✅ Updated: models_dir = models
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm config show

Current Configuration
══════════════════════════════════════════════════
database_path: .vcm/vcm.db
models_dir:    models

integrations:
  git: enabled
  dvc: enabled
  mlflow: disabled

session_logging:
  enabled: true
  capture_terminal: true
  mask_secrets: true

(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm config reset
✅ Configuration reset to defaults
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm config show

Current Configuration
══════════════════════════════════════════════════
database_path: .vcm/vcm.db
models_dir:    models

integrations:
  git: enabled
  dvc: enabled
  mlflow: disabled

session_logging:
  enabled: true
  capture_terminal: true
  mask_secrets: true

(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm init
VCM initialized successfully.
  - Created .vcm/ directory
  - Initialized database at .vcm/vcm.db
  - Created .vcmconfig.yaml

Use 'vcm train' to track models.
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm train --model-name iris_logistic_v1 \
          --dataset data/iris_v1.csv \
          --script train_model1.py \
          --metrics metrics_v1.json \
          --model-file models/iris_logistic_v1.pkl \
          --params C=0.1 \
          --params solver=lbfgs \
          --reasoning "Baseline Logistic Regression on Iris v1"
Running training script: train_model1.py ...
LogisticRegression trained: Acc=1.0000, F1=1.0000

Model tracked successfully.
  Model:      iris_logistic_v1
  Accuracy:   100.0%
  Git commit: c7f2da8342ea0df215d9ff810204c1c01bd6b3fb
  Dataset:    data/iris_v1.csv
  Reasoning:  Baseline Logistic Regression on Iris v1
  Metadata:   models/iris_logistic_v1.pkl.vcm.json
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm train --model-name iris_rf_v2 \
          --dataset data/iris_v1.csv \
          --script train_model2.py \
          --metrics metrics_v2.json \
          --model-file models/iris_rf_v2.pkl \
          --params n_estimators=100 max_depth=4 \
          --reasoning "Random Forest with 100 trees for non-linear boundaries"
Running training script: train_model2.py ...
RandomForest trained: Acc=1.0000, F1=1.0000

Model tracked successfully.
  Model:      iris_rf_v2
  Accuracy:   100.0%
  Git commit: c7f2da8342ea0df215d9ff810204c1c01bd6b3fb
  Dataset:    data/iris_v1.csv
  Reasoning:  Random Forest with 100 trees for non-linear boundaries
  Metadata:   models/iris_rf_v2.pkl.vcm.json
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm train --model-name iris_gb_v3 \
          --dataset data/iris_v2.csv \
          --script train_model3.py \
          --metrics metrics_v3.json \
          --model-file models/iris_gb_v3.pkl \
          --params n_estimators=150 learning_rate=0.05 \
          --reasoning "Gradient Boosting on scaled dataset v2"
Running training script: train_model3.py ...
GradientBoosting trained: Acc=1.0000, F1=1.0000

Model tracked successfully.
  Model:      iris_gb_v3
  Accuracy:   100.0%
  Git commit: c7f2da8342ea0df215d9ff810204c1c01bd6b3fb
  Dataset:    data/iris_v1.csv
  Reasoning:  Gradient Boosting on scaled dataset v2
  Metadata:   models/iris_gb_v3.pkl.vcm.json
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models
╭──────────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name       │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_rf_v2       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_logistic_v1 │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:04 │
╰──────────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 3 models found
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models --best
╭──────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name   │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├──────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3   │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
╰──────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 1 models found
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models --dataset data/iris_v1.csv
╭──────────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name       │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_rf_v2       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_logistic_v1 │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:04 │
╰──────────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 3 models found
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models --limit 2 --sort-by accuracy
╭──────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name   │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├──────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3   │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_rf_v2   │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
╰──────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 2 models found
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models --limit 3 --sort-by accuracy
╭──────────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name       │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_rf_v2       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_logistic_v1 │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:04 │
╰──────────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 3 models found
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models --format json
[
  {
    "model_name": "iris_gb_v3",
    "model_hash": "sha256:60779529e943496af08becf36878afba1ff836db8c5e878f5b9a6de2544679b6",
    "model_file": "models/iris_gb_v3.pkl",
    "code": {
      "git_commit": "c7f2da8342ea0df215d9ff810204c1c01bd6b3fb",
      "git_branch": "main",
      "git_remote": "origin",
      "git_url": "https://github.com/Kishor-9361/VersionControlModels.git"
    },
    "data": {
      "dvc_files": [
        {
          "path": "data/iris_v1.csv",
          "dvc_hash": "84f2c9e782e4f0123456789abcdef012",
          "size_bytes": 614,
          "timestamp": "2026-09-09T13:34:37.247290+00:00"
        },
        {
          "path": "data/iris_v2.csv",
          "dvc_hash": "sha256:1a6ff82c5c1cfd923dab02e51e4f66213a40c6e5810f0e909860e2b16c78deba",
          "size_bytes": 777,
          "timestamp": "2026-09-09T13:34:44.804555+00:00"
        }
      ]
    },
    "training": {
      "timestamp": "2026-09-19T05:06:31.652686+00:00",
      "duration_seconds": 2.25024676322937,
      "user": "kishorveeraragavan",
      "hostname": "fedora"
    },
    "hyperparameters": {
      "n_estimators": 150,
      "learning_rate": 0.05
    },
    "metrics": {
      "accuracy": 1.0,
      "precision": 1.0,
      "recall": 1.0,
      "f1_score": 1.0
    },
    "environment": {
      "python_version": "3.14.7",
      "libraries": {
        "scikit-learn": "1.9.0",
        "pandas": "3.0.5",
        "numpy": "2.5.3",
        "scipy": "1.18.1",
        "GitPython": "3.1.62",
        "click": "8.5.0",
        "pyyaml": "6.0.3"
      }
    },
    "metadata_version": "1.0",
    "created_at": "2026-09-19T05:06:31.652736+00:00",
    "reasoning": "Gradient Boosting on scaled dataset v2"
  },
  {
    "model_name": "iris_rf_v2",
    "model_hash": "sha256:31f721cc48842a26a2428365962721c86000159368ebb0f656eb87bb69d58143",
    "model_file": "models/iris_rf_v2.pkl",
    "code": {
      "git_commit": "c7f2da8342ea0df215d9ff810204c1c01bd6b3fb",
      "git_branch": "main",
      "git_remote": "origin",
      "git_url": "https://github.com/Kishor-9361/VersionControlModels.git"
    },
    "data": {
      "dvc_files": [
        {
          "path": "data/iris_v1.csv",
          "dvc_hash": "84f2c9e782e4f0123456789abcdef012",
          "size_bytes": 614,
          "timestamp": "2026-09-09T13:34:37.247290+00:00"
        }
      ]
    },
    "training": {
      "timestamp": "2026-09-19T05:06:16.389977+00:00",
      "duration_seconds": 2.8870105743408203,
      "user": "kishorveeraragavan",
      "hostname": "fedora"
    },
    "hyperparameters": {
      "n_estimators": 100,
      "max_depth": 4
    },
    "metrics": {
      "accuracy": 1.0,
      "precision": 1.0,
      "recall": 1.0,
      "f1_score": 1.0
    },
    "environment": {
      "python_version": "3.14.7",
      "libraries": {
        "scikit-learn": "1.9.0",
        "pandas": "3.0.5",
        "numpy": "2.5.3",
        "scipy": "1.18.1",
        "GitPython": "3.1.62",
        "click": "8.5.0",
        "pyyaml": "6.0.3"
      }
    },
    "metadata_version": "1.0",
    "created_at": "2026-09-19T05:06:16.390048+00:00",
    "reasoning": "Random Forest with 100 trees for non-linear boundaries"
  },
  {
    "model_name": "iris_logistic_v1",
    "model_hash": "sha256:60c9a0fcc522b0ddcd95f81ae94171a24fd51ea531cce2bd30fdc6c819518d67",
    "model_file": "models/iris_logistic_v1.pkl",
    "code": {
      "git_commit": "c7f2da8342ea0df215d9ff810204c1c01bd6b3fb",
      "git_branch": "main",
      "git_remote": "origin",
      "git_url": "https://github.com/Kishor-9361/VersionControlModels.git"
    },
    "data": {
      "dvc_files": [
        {
          "path": "data/iris_v1.csv",
          "dvc_hash": "84f2c9e782e4f0123456789abcdef012",
          "size_bytes": 614,
          "timestamp": "2026-09-09T13:34:37.247290+00:00"
        }
      ]
    },
    "training": {
      "timestamp": "2026-09-19T05:04:54.005809+00:00",
      "duration_seconds": 2.1153931617736816,
      "user": "kishorveeraragavan",
      "hostname": "fedora"
    },
    "hyperparameters": {
      "C": 0.1,
      "solver": "lbfgs"
    },
    "metrics": {
      "accuracy": 1.0,
      "precision": 1.0,
      "recall": 1.0,
      "f1_score": 1.0
    },
    "environment": {
      "python_version": "3.14.7",
      "libraries": {
        "scikit-learn": "1.9.0",
        "pandas": "3.0.5",
        "numpy": "2.5.3",
        "scipy": "1.18.1",
        "GitPython": "3.1.62",
        "click": "8.5.0",
        "pyyaml": "6.0.3"
      }
    },
    "metadata_version": "1.0",
    "created_at": "2026-09-19T05:04:54.005878+00:00",
    "reasoning": "Baseline Logistic Regression on Iris v1"
  }
]
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models --format csv --export models_export.csv
Exported 3 models to models_export.csv
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ cat models_export.csv
Model Name,Accuracy,F1 Score,Dataset,Git Commit,Created At
iris_gb_v3,100.0%,100.0%,data/iris_v1.csv,c7f2da83,2026-09-19 05:06
iris_rf_v2,100.0%,100.0%,data/iris_v1.csv,c7f2da83,2026-09-19 05:06
iris_logistic_v1,100.0%,100.0%,data/iris_v1.csv,c7f2da83,2026-09-19 05:04
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm info models/iris_rf_v2.pkl
Model Name:      iris_rf_v2
Model File:      models/iris_rf_v2.pkl
Model Hash:      sha256:31f721cc48842a26a2428365962721c86000159368ebb0f656eb87bb69d58143
Git Commit:      c7f2da8342ea0df215d9ff810204c1c01bd6b3fb
Git Branch:      main
Created At:      2026-09-19 05:06:16.390048+00:00
Python Version:  3.14.7

Metrics:
  accuracy: 1.0
  precision: 1.0
  recall: 1.0
  f1_score: 1.0

Hyperparameters:
  n_estimators: 100
  max_depth: 4
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm info models/iris_rf_v2.pkl --jsin
Usage: vcm info [OPTIONS] MODEL_REF
Try 'vcm info --help' for help.

Error: No such option '--jsin'. Did you mean '--json'?
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm info models/iris_rf_v2.pkl --json
{
  "model_name": "iris_rf_v2",
  "model_hash": "sha256:31f721cc48842a26a2428365962721c86000159368ebb0f656eb87bb69d58143",
  "model_file": "models/iris_rf_v2.pkl",
  "code": {
    "git_commit": "c7f2da8342ea0df215d9ff810204c1c01bd6b3fb",
    "git_branch": "main",
    "git_remote": "origin",
    "git_url": "https://github.com/Kishor-9361/VersionControlModels.git"
  },
  "data": {
    "dvc_files": [
      {
        "path": "data/iris_v1.csv",
        "dvc_hash": "84f2c9e782e4f0123456789abcdef012",
        "size_bytes": 614,
        "timestamp": "2026-09-09T13:34:37.247290+00:00"
      }
    ]
  },
  "training": {
    "timestamp": "2026-09-19T05:06:16.389977+00:00",
    "duration_seconds": 2.8870105743408203,
    "user": "kishorveeraragavan",
    "hostname": "fedora"
  },
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 4
  },
  "metrics": {
    "accuracy": 1.0,
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0
  },
  "environment": {
    "python_version": "3.14.7",
    "libraries": {
      "scikit-learn": "1.9.0",
      "pandas": "3.0.5",
      "numpy": "2.5.3",
      "scipy": "1.18.1",
      "GitPython": "3.1.62",
      "click": "8.5.0",
      "pyyaml": "6.0.3"
    }
  },
  "metadata_version": "1.0",
  "created_at": "2026-09-19T05:06:16.390048+00:00",
  "reasoning": "Random Forest with 100 trees for non-linear boundaries"
}
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm compare models/iris_logistic_v1.pkl models/iris_rf_v2.pkl

Comparison: iris_logistic_v1 vs iris_rf_v2
╭──────────────────┬────────────────────┬──────────────────┬──────────────────╮
│ Field / Metric   │ iris_logistic_v1   │ iris_rf_v2       │ Delta / Change   │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ Accuracy         │ 100.0%             │ 100.0%           │ = 0.0%           │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ F1_score         │ 100.0%             │ 100.0%           │ = 0.0%           │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ Precision        │ 1.0000             │ 1.0000           │ = 0.0000         │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ Recall           │ 1.0000             │ 1.0000           │ = 0.0000         │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ Dataset          │ data/iris_v1.csv   │ data/iris_v1.csv │ Same             │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ Git Commit       │ c7f2da83           │ c7f2da83         │ Same             │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ C                │ 0.1                │ N/A              │ Changed          │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ max_depth        │ N/A                │ 4                │ Changed          │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ n_estimators     │ N/A                │ 100              │ Changed          │
├──────────────────┼────────────────────┼──────────────────┼──────────────────┤
│ solver           │ lbfgs              │ N/A              │ Changed          │
╰──────────────────┴────────────────────┴──────────────────┴──────────────────╯

Models have equal accuracy (100.0%)
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm lineage models/iris_rf_v2.pkl

Model Lineage: iris_rf_v2 (models/iris_rf_v2.pkl)
Model: iris_rf_v2 (models/iris_rf_v2.pkl)
├── Accuracy: 1.0000 (100.0%) | F1 Score: 1.0000
├── Git Commit: c7f2da8342ea0df215d9ff810204c1c01bd6b3fb
│   ├── Branch: main
│   ├── Remote: origin
│   └── URL: https://github.com/Kishor-9361/VersionControlModels.git
├── Dataset Files:
│   ├── data/iris_v1.csv (hash: 84f2c9e782e4f012..., size: 614 B)
├── Hyperparameters:
│   ├── n_estimators: 100
│   ├── max_depth: 4
└── Trained by: kishorveeraragavan on fedora (2026-09-19T05:06:16.389977+00:00)
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm export models/iris_rf_v2.pkl --output rf_v2_export.json
Metadata exported to rf_v2_export.json
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ cat rf_v2_export.json 
{
  "model_name": "iris_rf_v2",
  "model_hash": "sha256:31f721cc48842a26a2428365962721c86000159368ebb0f656eb87bb69d58143",
  "model_file": "models/iris_rf_v2.pkl",
  "code": {
    "git_commit": "c7f2da8342ea0df215d9ff810204c1c01bd6b3fb",
    "git_branch": "main",
    "git_remote": "origin",
    "git_url": "https://github.com/Kishor-9361/VersionControlModels.git"
  },
  "data": {
    "dvc_files": [
      {
        "path": "data/iris_v1.csv",
        "dvc_hash": "84f2c9e782e4f0123456789abcdef012",
        "size_bytes": 614,
        "timestamp": "2026-09-09T13:34:37.247290+00:00"
      }
    ]
  },
  "training": {
    "timestamp": "2026-09-19T05:06:16.389977+00:00",
    "duration_seconds": 2.8870105743408203,
    "user": "kishorveeraragavan",
    "hostname": "fedora"
  },
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 4
  },
  "metrics": {
    "accuracy": 1.0,
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0
  },
  "environment": {
    "python_version": "3.14.7",
    "libraries": {
      "scikit-learn": "1.9.0",
      "pandas": "3.0.5",
      "numpy": "2.5.3",
      "scipy": "1.18.1",
      "GitPython": "3.1.62",
      "click": "8.5.0",
      "pyyaml": "6.0.3"
    }
  },
  "metadata_version": "1.0",
  "created_at": "2026-09-19T05:06:16.390048+00:00",
  "reasoning": "Random Forest with 100 trees for non-linear boundaries"
}(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ rm -f .vcm/vcm.db
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm repair
Database repaired: Re-indexed 3 models.
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm models
╭──────────────────┬────────────┬────────────┬──────────────────┬──────────────┬──────────────────╮
│ Model Name       │ Accuracy   │ F1 Score   │ Dataset          │ Git Commit   │ Created At       │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_gb_v3       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_rf_v2       │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:06 │
├──────────────────┼────────────┼────────────┼──────────────────┼──────────────┼──────────────────┤
│ iris_logistic_v1 │ 100.0%     │ 100.0%     │ data/iris_v1.csv │ c7f2da83     │ 2026-09-19 05:04 │
╰──────────────────┴────────────┴────────────┴──────────────────┴──────────────┴──────────────────╯

Total: 3 models found
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session start "interactive_tuning"
Session started: sess_e8f344ef
   Name: interactive_tuning
   Start: 2026-09-19 05:14:12
   User: kishorveeraragavan
   Terminal logging: enabled
Use 'vcm session end' when finished
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session annotate "Hypothesis: Increasing estimators improves stability"
Annotation recorded at 05:14:36
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session annotate "Observation: Loss converged after 50 iterations" --model iris_rf_v2
Annotation recorded at 05:14:47
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session logs interactive_tuning
════════════════════════════════════════════════════════════
Session: interactive_tuning
User: kishorveeraragavan | Branch: main
────────────────────────────────────────────────────────────
[No terminal logs recorded]
────────────────────────────────────────────────────────────
Total models: 0 | Best: None
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session logs interactive_tuning --format json
{
  "session_id": "sess_e8f344ef",
  "terminal_log": ""
}
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session info interactive_tuning

Session: interactive_tuning
═════════════════════════════════════════════
ID: sess_e8f344ef
User: kishorveeraragavan
Duration: 1 minutes
Status: active

Models Trained (0):

Annotations (0):

Git Commits (1):
  • c7f2da8342ea0df215d9ff810204c1c01bd6b3fb

Terminal Log: 0 lines captured

(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session list
╭───────────────┬────────────────────┬────────────────────┬──────────┬──────────┬──────────────┬────────────┬──────────────────╮
│ Session ID    │ Name               │ User               │ Status   │   Models │ Best Model   │ Accuracy   │ Started          │
├───────────────┼────────────────────┼────────────────────┼──────────┼──────────┼──────────────┼────────────┼──────────────────┤
│ sess_e8f344ef │ interactive_tuning │ kishorveeraragavan │ active   │        0 │ None         │ N/A        │ 2026-09-19 05:14 │
╰───────────────┴────────────────────┴────────────────────┴──────────┴──────────┴──────────────┴────────────┴──────────────────╯
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session end
Session ended.
   Duration: 1 minutes
   Models trained: 0
   Commits: 1
   Terminal log: 0 lines
   Session saved: sess_e8f344ef
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session models interactive_tuning
No models trained in session 'interactive_tuning'.
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session create-retrospective --name historical_session
Retrospective session 'historical_session' created with 3 models.
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session list
╭───────────────┬────────────────────┬────────────────────┬───────────┬──────────┬──────────────────┬────────────┬──────────────────╮
│ Session ID    │ Name               │ User               │ Status    │   Models │ Best Model       │ Accuracy   │ Started          │
├───────────────┼────────────────────┼────────────────────┼───────────┼──────────┼──────────────────┼────────────┼──────────────────┤
│ sess_3e2402b2 │ historical_session │ kishorveeraragavan │ completed │        3 │ iris_logistic_v1 │ 100.0%     │ 2024-01-01 00:00 │
├───────────────┼────────────────────┼────────────────────┼───────────┼──────────┼──────────────────┼────────────┼──────────────────┤
│ sess_e8f344ef │ interactive_tuning │ kishorveeraragavan │ completed │        0 │ None             │ N/A        │ 2026-09-19 05:14 │
╰───────────────┴────────────────────┴────────────────────┴───────────┴──────────┴──────────────────┴────────────┴──────────────────╯
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session compare interactive_tuning historical_session

Session Comparison: interactive_tuning vs historical_session
═════════════════════════════════════════════
Metrics:
  interactive_tuning: 0 models, best=0.0%

Result:
  Accuracy delta: -100.00%

Recommendation:
  Session 'historical_session' produced higher accuracy (100.00%).

(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session explain-improvement historical_session iris_logistic_v1 iris_rf_v2

Comparing iris_logistic_v1 vs iris_rf_v2 in session 'historical_session'
──────────────────────────────────────────────────
Accuracy: 100.00% -> 100.00% (delta: +0.00%)

Session Annotations:

Conclusion: Performance unchanged (+0.00%)

(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session export historical_session --format html --output session_report.html
Error: Session 'historical_session' not found.
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session export historical_session --format html --output session_report.html
Exported to: session_report.html
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm session export historical_session --format json --output session_report.json
Exported to: session_report.json
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline --show-reasoning --highlight-best
Model Evolution Timeline
══════════════════════════════════════════════════════════════════════

Position 1 │ iris_logistic_v1 [BEST]
Accuracy   │ 100.0% (baseline)
Date       │ 2026-09-19 05:17:46
Why this?  │ Baseline Logistic Regression on Iris

Position 2 │ iris_rf_v2
Accuracy   │ 100.0% (no change)
Date       │ 2026-09-19 05:17:49
Why this?  │ Production candidate ready

Position 3 │ iris_gb_v3
Accuracy   │ 100.0% (no change)
Date       │ 2026-09-19 05:17:51
Why this?  │ Gradient Boosting with scaled features

══════════════════════════════════════════════════════════════════════
Summary
══════════════════════════════════════════════════════════════════════
Total models:        3
Best model:          iris_logistic_v1 (100.0%)
Worst model:         iris_logistic_v1 (100.0%)
Overall improvement: +0.0%
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline --format ascii
Model Accuracy Over Time
═════════════════════════════════════════════

200.0% │                      
183.3% │                      
166.7% │                      
150.0% │                      
133.3% │                      
116.7% │                      
100.0% │ * iris_logistic_v1  iris_rf_v2  iris_gb_v3  
      ├───────────────────────────
      │ iris_logistic_v1  iris_rf_v2  iris_gb_v3
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline --format json
{
  "entries": [
    {
      "position": 1,
      "model_name": "iris_logistic_v1",
      "model_id": 1,
      "timestamp": "2026-09-19T05:17:46.630649+00:00",
      "accuracy": 1.0,
      "metrics": {
        "accuracy": 1.0,
        "precision": 1.0,
        "recall": 1.0,
        "f1_score": 1.0
      },
      "reasoning": "Baseline Logistic Regression on Iris",
      "reasoning_added_by": null,
      "reasoning_timestamp": "2026-09-19T10:47:56.357521",
      "previous_model": null,
      "next_model": null,
      "previous_model_accuracy": null,
      "accuracy_improvement": null,
      "changes": null,
      "session_id": null,
      "git_commit": "26942387075c8bb6e869156d895265162fa8e39a"
    },
    {
      "position": 2,
      "model_name": "iris_rf_v2",
      "model_id": 2,
      "timestamp": "2026-09-19T05:17:49.175706+00:00",
      "accuracy": 1.0,
      "metrics": {
        "accuracy": 1.0,
        "precision": 1.0,
        "recall": 1.0,
        "f1_score": 1.0
      },
      "reasoning": "Production candidate ready",
      "reasoning_added_by": "kishorveeraragavan",
      "reasoning_timestamp": "2026-09-19T10:48:04.666040",
      "previous_model": "iris_logistic_v1",
      "next_model": null,
      "previous_model_accuracy": 1.0,
      "accuracy_improvement": 0.0,
      "changes": {
        "code_changed": false,
        "code_files": [],
        "git_commits": [],
        "data_changed": false,
        "data_files": [],
        "data_hashes_changed": {},
        "hyperparams_changed": {
          "n_estimators": [
            null,
            100
          ],
          "max_depth": [
            null,
            4
          ]
        },
        "environment_changed": false
      },
      "session_id": null,
      "git_commit": "26942387075c8bb6e869156d895265162fa8e39a"
    },
    {
      "position": 3,
      "model_name": "iris_gb_v3",
      "model_id": 3,
      "timestamp": "2026-09-19T05:17:51.997512+00:00",
      "accuracy": 1.0,
      "metrics": {
        "accuracy": 1.0,
        "precision": 1.0,
        "recall": 1.0,
        "f1_score": 1.0
      },
      "reasoning": "Gradient Boosting with scaled features",
      "reasoning_added_by": null,
      "reasoning_timestamp": "2026-09-19T10:47:56.366186",
      "previous_model": "iris_rf_v2",
      "next_model": null,
      "previous_model_accuracy": 1.0,
      "accuracy_improvement": 0.0,
      "changes": {
        "code_changed": false,
        "code_files": [],
        "git_commits": [],
        "data_changed": false,
        "data_files": [],
        "data_hashes_changed": {},
        "hyperparams_changed": {
          "n_estimators": [
            null,
            150
          ],
          "learning_rate": [
            null,
            0.05
          ]
        },
        "environment_changed": false
      },
      "session_id": null,
      "git_commit": "26942387075c8bb6e869156d895265162fa8e39a"
    }
  ],
  "total_models": 3,
  "best_model": "iris_logistic_v1",
  "worst_model": "iris_logistic_v1",
  "best_accuracy": 1.0,
  "worst_accuracy": 1.0,
  "accuracy_improvement": 0.0,
  "date_range": [
    "2026-09-19T05:17:46.630649+00:00",
    "2026-09-19T05:17:51.997512+00:00"
  ],
  "session_ids": []
}
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline --format csv --output timeline_export.csv
Timeline exported to timeline_export.csv
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline --format html --output timeline_report.html
Timeline exported to timeline_report.html
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline --accuracy-range 0.95-1.0 --show-changes
Model Evolution Timeline
══════════════════════════════════════════════════════════════════════

Position 1 │ iris_logistic_v1 [BEST]
Accuracy   │ 100.0% (baseline)
Date       │ 2026-09-19 05:17:46

Position 2 │ iris_rf_v2
Accuracy   │ 100.0% (no change)
Date       │ 2026-09-19 05:17:49
Changes    │ Hyperparams (n_estimators, max_depth)

Position 3 │ iris_gb_v3
Accuracy   │ 100.0% (no change)
Date       │ 2026-09-19 05:17:51
Changes    │ Hyperparams (n_estimators, learning_rate)

══════════════════════════════════════════════════════════════════════
Summary
══════════════════════════════════════════════════════════════════════
Total models:        3
Best model:          iris_logistic_v1 (100.0%)
Worst model:         iris_logistic_v1 (100.0%)
Overall improvement: +0.0%
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline show
Model Evolution Timeline
══════════════════════════════════════════════════════════════════════

Position 1 │ iris_logistic_v1 [BEST]
Accuracy   │ 100.0% (baseline)
Date       │ 2026-09-19 05:17:46

Position 2 │ iris_rf_v2
Accuracy   │ 100.0% (no change)
Date       │ 2026-09-19 05:17:49

Position 3 │ iris_gb_v3
Accuracy   │ 100.0% (no change)
Date       │ 2026-09-19 05:17:51

══════════════════════════════════════════════════════════════════════
Summary
══════════════════════════════════════════════════════════════════════
Total models:        3
Best model:          iris_logistic_v1 (100.0%)
Worst model:         iris_logistic_v1 (100.0%)
Overall improvement: +0.0%
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline analyze
Timeline Analysis Report
═════════════════════════════════════════════════════════════════

Improvement Trajectory:
   Baseline (iris_logistic_v1): 100.0%
   Peak (iris_logistic_v1): 100.0% (+0.0% vs baseline)
   Final (iris_gb_v3): 100.0%

Root Cause Analysis:
   Single model baseline or steady performance.

Anomalies Detected:
   • No accuracy regressions detected.

Recommendations:
   1. Candidate for production deployment: iris_logistic_v1 (100.0%)
   3. Continue iterative experimentation on top of best verified architecture.

Experiment Efficiency:
   Total models:           3
   Successful improvements: 0/3 (0%)
   Regressed attempts:     0/3
   Efficiency score:       0%
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline reason iris_rf_v2 "Confirmed 100% precision on validation set" --force
Added reasoning to iris_rf_v2
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline-reason iris_rf_v2 --show
Reasoning for iris_rf_v2: Confirmed 100% precision on validation set
  Added by:  kishorveeraragavan
  Timestamp: 2026-09-19T10:52:36.933123
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm timeline-reason iris_rf_v2 "Production candidate approved by ML team" --force
vcm timeline-reason iris_rf_v2 --show
Added reasoning to iris_rf_v2
Reasoning for iris_rf_v2: Production candidate approved by ML team
  Added by:  kishorveeraragavan
  Timestamp: 2026-09-19T10:53:15.612636
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm analysis --report full_lineage
VCM Full Lineage Report
========================

Dataset: data/iris_v1.csv (raw, 3 samples)
  └─ Model: iris_logistic_v1 (Acc: 100.0%) | Code: 2694238 | Params: C=0.1, solver=lbfgs
  └─ Model: iris_rf_v2 (Acc: 100.0%) | Code: 2694238 | Params: n_estimators=100, max_depth=4
  └─ Model: iris_gb_v3 (Acc: 100.0%) | Code: 2694238 | Params: n_estimators=150, learning_rate=0.05

Analysis:
Best Overall: iris_logistic_v1 (100.0% accuracy)
Data Impact: Scaling reduced accuracy by 0.2% (v4 vs v1)
Code Impact: New preprocessing in v5 maintains accuracy with different data version
Recommendation: Use iris_logistic_v1 for production (raw data, n_est=10)
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm analysis --compare iris_logistic_v1 iris_rf_v2

Comparing iris_logistic_v1 vs iris_rf_v2
────────────────────────────────────────
Accuracy: 100.00% -> 100.00% (delta: +0.00%)
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm deploy models/iris_rf_v2.pkl --environment staging
Deployed models/iris_rf_v2.pkl to environment 'staging'
   Timestamp: 2026-09-19T05:25:10.445294+00:00
   Trained by: kishorveeraragavan
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm deploy models/iris_rf_v2.pkl --environment production
Deployed models/iris_rf_v2.pkl to environment 'production'
   Timestamp: 2026-09-19T05:25:18.333839+00:00
   Trained by: kishorveeraragavan
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm audit --environment staging

Production Audit Trail:
Model: iris_rf_v2
Deployed: 2026-09-19T05:25:10.445294+00:00
Trained by: kishorveeraragavan
Code: 26942387075c8bb6e869156d895265162fa8e39a
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm audit --environment production

Production Audit Trail:
Model: iris_rf_v2
Deployed: 2026-09-19T05:25:18.333839+00:00
Trained by: kishorveeraragavan
Code: 26942387075c8bb6e869156d895265162fa8e39a
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ vcm reproduce models/iris_logistic_v1.pkl
Model models/iris_logistic_v1.pkl reproduced successfully (Accuracy: 1.0000)
(venv) kishorveeraragavan@fedora:~/Desktop/VersionControl/ml_project_demo$ 
```
