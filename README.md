# VCM (Version Control Models)

**Model DNA Version Control Platform**  
*Enterprise-grade, lightweight, and zero-configuration version control for machine learning models.*

[![Release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/Kishor-9361/VersionControlModels/releases)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-166%20passed%20%28100%25%29-brightgreen.svg)](#test-suite--quality-gates)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)](#test-suite--quality-gates)
[![Typing](https://img.shields.io/badge/typing-mypy%20strict%20%280%20errors%29-blue.svg)](#test-suite--quality-gates)
[![Code Style](https://img.shields.io/badge/code%20style-flake8%20clean-black.svg)](https://github.com/psf/black)

---

## Overview

In traditional software development, **Git** tracks source code. In data engineering, **DVC** tracks datasets. However, machine learning models exist at the intersection of source code, data versions, training hyperparameters, runtime environments, and evaluation metrics.

Without a unified model version control system, answering critical questions is tedious and error-prone:
- *Which exact Git commit and training script generated this model binary?*
- *Which dataset revision was used to train it?*
- *Why did accuracy drop by 4% between model version 2 and version 3?*
- *Can this production model be deterministically reproduced with 100% parity?*

**VCM (Version Control Models)** solves this by automatically capturing the complete **Model DNA** for every training run, linking Git commits, dataset hashes, hyperparameters, environment dependencies, and developer reasoning into an immutable, verifiable record.

```
       +--------------------+       +--------------------+
       |  Git Source State  |       | DVC Dataset Hashes |
       +---------+----------+       +---------+----------+
                 |                            |
                 +--------------+-------------+
                                |
                                v
                     +--------------------+
                     |   VCM Model DNA    |
                     | Code + Data + Env  |
                     |  Params + Metrics  |
                     | + Reasoning Notes  |
                     +----------+---------+
                                |
                 +--------------+-------------+
                 |                            |
                 v                            v
       +--------------------+       +--------------------+
       |    Model Binary    | <---> |  Portable Sidecar  |
       | (.pkl, .pt, .onnx) |       | (<model>.vcm.json) |
       +--------------------+       +---------+----------+
                                              |
                                              v
                                    +--------------------+
                                    | Local SQLite Index |
                                    |   (.vcm/vcm.db)    |
                                    +--------------------+
```

---

## Key Features

- **Automated Model DNA Capture**: Zero-boilerplate capture of Git commit SHA, branch name, DVC dataset content hashes, hyperparameters, system hardware, and Python package versions.
- **Dual-Layer Persistence (Zero Vendor Lock-In)**:
  - **Portable JSON Sidecars (`<model>.vcm.json`)**: Accompanies model binaries across cloud buckets (S3, GCS), local drives, or Git LFS.
  - **Local SQLite Index (`.vcm/vcm.db`)**: High-speed indexed cache delivering sub-5ms queries across thousands of models.
- **Model Evolution Timeline & Progression Tracking**:
  - Trajectory tracking linking sequential model versions with delta accuracy calculations.
  - Developer reasoning capture (`--reasoning`) documenting *why* each version was trained.
  - Visual formatters: Console Tables, Interactive HTML visualizer with inline SVG sparklines, JSON, CSV, and ASCII graphs.
- **Automated Regression Detection**:
  - Automatically flags accuracy drops exceeding configurable thresholds.
  - Performs automated root-cause diagnosis across hyperparameters, code changes, and dataset modifications.
- **Interactive Development Sessions**:
  - Group iterative training runs into sessions with transparent terminal stdout/stderr capture.
  - Built-in regex privacy filter replacing API keys, bearer tokens, and secrets with `***MASKED***`.
- **Deterministic Model Reproduction**: Re-executes training from metadata, verifying 100% prediction parity and zero metric drift.
- **Production Deployment & Audit Trail**: Deploy model artifacts to staging/production and query tamper-evident audit logs.
- **Self-Healing Architecture (`vcm repair`)**: Rebuilds the entire SQLite database index directly from sidecar files on disk in seconds.

---

## Installation

### Prerequisites
- Python 3.9 or higher
- Git (recommended, for code commit tracking)
- DVC (optional, for dataset content hash tracking)

### Quick Install
```bash
git clone https://github.com/Kishor-9361/VersionControlModels.git
cd VersionControlModels

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install VCM in editable mode
pip install -e .
```

Verify installation:
```bash
vcm --version
vcm --help
```

---

## Quick Start (5-Minute Walkthrough)

### 1. Initialize VCM in Your Project
```bash
vcm init
```

### 2. Track Model Training
Execute your existing training script through VCM to automatically capture Model DNA:
```bash
vcm train --model-name iris_v1 \
          --script train.py \
          --dataset data/train.csv \
          --metrics metrics.json \
          --params n_estimators=50 max_depth=4 \
          --reasoning "Baseline Random Forest on cleaned iris dataset"
```

### 3. Manage Iterations with Sessions
```bash
# Start tracking a session
vcm session start "hyperopt_run" --description "Tuning tree depth and count"

# Train next iteration
vcm train --model-name iris_v2 \
          --script train.py \
          --dataset data/train.csv \
          --metrics metrics.json \
          --params n_estimators=100 max_depth=6 \
          --reasoning "Increased capacity to capture non-linear class boundaries"

# End session
vcm session end
```

### 4. View Model Evolution Timeline
```bash
# View progression in terminal
vcm timeline --show-reasoning --highlight-best

# Export standalone interactive HTML report with embedded SVG sparkline
vcm timeline --format html --output ./timeline_report.html
```

### 5. Detect Performance Regressions
```bash
vcm timeline analyze --threshold 0.02 --report detailed
```

### 6. Compare Any Two Models Side-by-Side
```bash
vcm compare iris_v1 iris_v2
```

---

## CLI Command Reference

| Command | Description |
| :--- | :--- |
| `vcm init` | Initialize VCM workspace configuration and SQLite database index. |
| `vcm status` | Show overall workspace status: Git branch/commit, active session, catalog, and untracked artifacts. |
| `vcm train` | Wrap model training and capture code, data, metrics, and environment. |
| `vcm models` | List, query, and filter tracked models by metric, dataset, or best performer. |
| `vcm info` | Display complete Model DNA metadata for a specified model. |
| `vcm compare` | Side-by-side comparative diff of two models across metrics, params, and code. |
| `vcm lineage` | Render ASCII visual lineage tree connecting model to Git, DVC, and predecessor models. |
| `vcm export` | Export model metadata to external JSON or stdout. |
| `vcm repair` | Rebuild SQLite database index from disk `.vcm.json` sidecar files. |
| `vcm session` | Manage development sessions (`start`, `end`, `list`, `info`, `logs`, `annotate`, `compare`, `export`). |
| `vcm timeline` | Display model evolution timeline in Table, HTML, JSON, CSV, or ASCII format. |
| `vcm timeline analyze`| Detect regressions, development gaps, and identify root causes. |
| `vcm timeline reason` | Add or update developer reasoning notes for a model version. |
| `vcm timeline-reason` | Standalone reasoning annotation command with `--force` and `--show`. |
| `vcm analysis` | Comprehensive lineage analysis and production readiness recommendations. |
| `vcm reproduce` | Deterministically rebuild and verify a model from its Model DNA metadata. |
| `vcm deploy` | Deploy a model to `staging` or `production` and record audit log. |
| `vcm audit` | Retrieve deployment audit trail for a target environment. |
| `vcm mlflow` | Manage MLflow experiment tracking integration (`enable`, `disable`, `sync`, `experiments`, `runs`). |
| `vcm config` | Inspect or update VCM workspace configuration (`show`, `set`, `reset`). |
| `vcm version` | Display VCM software release and runtime details. |

> For comprehensive documentation with all options and arguments, see **[docs/CLI.md](docs/CLI.md)**.

---

## Python API Reference

VCM can be integrated directly into your Python scripts, pipelines, and Jupyter notebooks:

```python
from vcm.trainer import ModelTracker
from vcm.models.session import SessionTracker
from vcm.models.timeline import TimelineStore
from vcm.db.database import Database

# 1. Track a training session
with SessionTracker(session_name="hyperopt_exp", user="alice") as session:
    session.annotate("Testing higher learning rate and tree depth")
    
    tracker = ModelTracker()
    tracker.log_model(
        model_path="models/iris_v2.pkl",
        model_name="iris_v2",
        metrics={"accuracy": 0.98},
        hyperparameters={"n_estimators": 50, "max_depth": 5},
        reasoning="Ensemble depth increased for higher recall",
    )

# 2. Inspect progression timeline & regressions
db = Database()
store = TimelineStore(db)
timeline = store.get_model_timeline()
regressions = store.detect_regressions(threshold=0.01)
```

> For the full Python API specification, see **[docs/API.md](docs/API.md)**.

---

## Documentation Directory

The repository includes a complete documentation library:

- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)**: End-to-end practical walkthrough and tutorials.
- **[docs/CLI.md](docs/CLI.md)**: Full command-line reference with all arguments and examples.
- **[docs/API.md](docs/API.md)**: Complete Python class and method reference.
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design, database schemas, and data flow models.
- **[docs/specs/README.md](docs/specs/README.md)**: Archive of Phase 1, Phase 2, and Phase 3 specifications and test strategies.

---

## Test Suite & Quality Gates

VCM enforces strict enterprise engineering standards:

```bash
# Run all 164 tests with coverage
pytest vcm/tests/ --cov=vcm --cov-report=term-missing

# Strict static type check
mypy vcm/ --strict

# PEP8 style and line length check
flake8 vcm/ --max-line-length=120
```

### Quality Scorecard
- **Test Suite**: **166 / 166 tests passing** (100%)
- **Test Coverage**: **91% overall coverage** (Timeline & MLflow models: 93%–100%)
- **Static Typing**: **0 errors** across all 76 source files (`mypy --strict`)
- **Linting**: **0 violations** (`flake8 --max-line-length=120`)
- **Query Performance**: **< 4 ms** for 1,000 models on local SQLite

---

## Project Structure

```
VersionControl/
├── docs/                                  # Complete documentation suite
│   ├── CLI.md                             # Complete CLI command reference
│   ├── API.md                             # Python API documentation
│   ├── ARCHITECTURE.md                    # Architecture & schema design
│   ├── USER_GUIDE.md                      # Step-by-step user tutorial
│   ├── MLFLOW_INTEGRATION.md              # MLflow integration & tracking guide
│   ├── CLI_TESTING_GUIDE.md               # End-to-end CLI command verification guide
│   ├── TERMINAL_COMMAND_EXECUTION_REPORT.md # Technical command execution report & analysis
│   ├── EXACT_TERMINAL_SESSION.md          # Complete verbatim terminal execution transcript
│   ├── EXACT_TERMINAL_SESSION_CORRECTED.md # Validated & corrected terminal session transcript
│   ├── TERMINAL_SESSION_ANALYSIS_REPORT.md # Comprehensive 14-point terminal session audit
│   ├── TERMINAL_SESSION_SUMMARY.md        # Executive summary of terminal inconsistencies & resolutions
│   ├── 00_COMPLETE_DELIVERABLES_INDEX.md  # Master deliverable and documentation index
│   └── specs/                             # Specifications (Phase 1, 2, 3)
├── vcm/                                   # Core VCM package
│   ├── cli/                               # CLI command groups (click)
│   ├── db/                                # SQLite database storage & migrations
│   ├── integrations/                      # Git, DVC & MLflow connectors
│   ├── models/                            # Domain models (Metadata, Session, Evolution)
│   ├── utils/                             # Visual formatters, terminal logger, helpers
│   └── tests/                             # 164 test cases (unit, cli, integration, advanced)
├── examples/                              # Runnable training examples and scripts
│   └── train_sample.py                    # Sample training script capturing Model DNA
├── ml_project_demo/                       # Isolated demo ML project & end-to-end command verification
├── pyproject.toml                         # Packaging, dependencies & tool configs
├── setup.py                               # Setup script
├── .gitignore                             # Git ignore configuration
├── LICENSE                                # MIT License
└── README.md                              # Main project documentation
```

---

## Author

**Kishor Veeraragavan**
- GitHub: [@Kishor-9361](https://github.com/Kishor-9361)
- Repository: [VersionControlModels](https://github.com/Kishor-9361/VersionControlModels)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
