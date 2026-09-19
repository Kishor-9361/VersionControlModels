# VCM Complete CLI Testing Playbook

This document is a step-by-step interactive testing guide designed to test **every single VCM command and subcommand** in sequence using real machine learning workflows.

---

## Testing Environment Setup

All commands below can be executed directly inside the included demo ML project (`ml_project_demo/`):

```bash
# 1. Activate the VCM virtual environment
source venv/bin/activate

# 2. Navigate to the demo project
cd ml_project_demo
```

---

## 1. System Information & Help Commands

### 1.1 Check CLI Version
```bash
vcm --version
vcm version
vcm version --verbose
```
- **Expected:** Prints VCM version (`v1.0.0`), release metadata, and system environment info.

### 1.2 View CLI Help
```bash
vcm --help
```
- **Expected:** Displays all registered root commands (`init`, `train`, `models`, `info`, `compare`, `lineage`, `export`, `repair`, `session`, `timeline`, `timeline-reason`, `analysis`, `reproduce`, `deploy`, `audit`, `config`, `version`).

---

## 2. Workspace Configuration Commands (`vcm config`)

### 2.1 View Current Configuration
```bash
vcm config show
```
- **Expected:** Displays YAML configuration settings including database path, models directory, and default metrics.

### 2.2 Update Configuration Setting
```bash
vcm config set models_dir models
vcm config show
# Reset configuration
vcm config reset
```
- **Expected:** Confirms configuration key updated successfully.

---

## 3. Project Initialization (`vcm init`)

### 3.1 Initialize VCM in Project
```bash
vcm init
```
- **Expected:** Creates `.vcm/`, initializes local SQLite database `.vcm/vcm.db`, and creates `models/` directory.

### 3.2 Inspect Workspace Status (`vcm status`)
```bash
vcm status
```
- **Expected:** Displays full workspace status (database, git commit/branch/cleanliness, active session, model catalog, integrations, and untracked model artifacts).

---

## 4. Training & Model DNA Tracking (`vcm train`)

Train 3 real scikit-learn models on Iris data with hyperparameters, metrics, and developer reasoning:

### 4.1 Train Model 1 (Logistic Regression)
```bash
vcm train --model-name iris_logistic_v1 \
          --dataset data/iris_v1.csv \
          --script train_model1.py \
          --metrics metrics_v1.json \
          --model-file models/iris_logistic_v1.pkl \
          --params C=0.1 \
          --params solver=lbfgs \
          --reasoning "Baseline Logistic Regression on Iris v1"
```
- **Expected:** Script executes, logs metrics (`accuracy: 1.0`), creates `models/iris_logistic_v1.pkl.vcm.json` sidecar, and indexes in SQLite.

### 4.2 Train Model 2 (Random Forest)
```bash
vcm train --model-name iris_rf_v2 \
          --dataset data/iris_v1.csv \
          --script train_model2.py \
          --metrics metrics_v2.json \
          --model-file models/iris_rf_v2.pkl \
          --params n_estimators=100 max_depth=4 \
          --reasoning "Random Forest with 100 trees for non-linear boundaries"
```
- **Expected:** Tracks model with hyperparameters and reasoning.

### 4.3 Train Model 3 (Gradient Boosting on Dataset v2)
```bash
vcm train --model-name iris_gb_v3 \
          --dataset data/iris_v2.csv \
          --script train_model3.py \
          --metrics metrics_v3.json \
          --model-file models/iris_gb_v3.pkl \
          --params n_estimators=150 learning_rate=0.05 \
          --reasoning "Gradient Boosting on scaled dataset v2"
```
- **Expected:** Tracks 3rd model linked to dataset v2.

---

## 5. Model Catalog & Query Commands (`vcm models`)

### 5.1 List All Tracked Models
```bash
vcm models
```
- **Expected:** Clean tabular list of all 3 models with name, accuracy, dataset, git commit, and creation timestamp.

### 5.2 Filter by Top Performer (`--best`)
```bash
vcm models --best
```
- **Expected:** Shows single top-performing model.

### 5.3 Filter by Dataset
```bash
vcm models --dataset data/iris_v1.csv
```
- **Expected:** Returns only models trained on `data/iris_v1.csv` (models 1 and 2).

### 5.4 Limit and Sort Results
```bash
vcm models --limit 2 --sort-by accuracy
```

### 5.5 Export Query Output (JSON & CSV)
```bash
vcm models --format json
vcm models --format csv --export models_export.csv
cat models_export.csv
```
- **Expected:** Dumps models in JSON format, and exports a clean CSV file.

---

## 6. Model Inspection & Comparison Commands

### 6.1 Inspect Model Metadata (`vcm info`)
```bash
vcm info models/iris_rf_v2.pkl
vcm info models/iris_rf_v2.pkl --json
```
- **Expected:** Formatted Model DNA summary (commit SHA, metrics, hyperparameters, python version, libraries) and raw JSON export.

### 6.2 Compare Two Models Side-by-Side (`vcm compare`)
```bash
vcm compare models/iris_logistic_v1.pkl models/iris_rf_v2.pkl
```
- **Expected:** Side-by-side comparison matrix showing metric deltas, hyperparameter changes, and dataset verification.

### 6.3 Visualize Model Lineage Tree (`vcm lineage`)
```bash
vcm lineage models/iris_rf_v2.pkl
```
- **Expected:** ASCII tree showing model ancestor chain, Git commit, branch, dataset hash, and training metadata.

---

## 7. Metadata Export & Self-Healing Repair

### 7.1 Export Metadata (`vcm export`)
```bash
vcm export models/iris_rf_v2.pkl --output rf_v2_export.json
cat rf_v2_export.json
```
- **Expected:** Exports full JSON payload to external file.

### 7.2 Test Self-Healing Recovery (`vcm repair`)
```bash
# Intentionally delete the SQLite index
rm -f .vcm/vcm.db

# Reconstruct the database from sidecar files
vcm repair

# Verify all models are restored
vcm models
```
- **Expected:** Output: `Database repaired: Re-indexed 3 models.` All models remain queryable.

---

## 8. Session Tracking Commands (`vcm session` - ALL Subcommands)

### 8.1 Start a Session (`vcm session start`)
```bash
vcm session start "interactive_tuning"
```
- **Expected:** `Session started: sess_...` Terminal logging begins.

### 8.2 Add Annotations (`vcm session annotate`)
```bash
vcm session annotate "Hypothesis: Increasing estimators improves stability"
vcm session annotate "Observation: Loss converged after 50 iterations" --model iris_rf_v2
```
- **Expected:** Records timestamped developer notes attached to session.

### 8.3 View Terminal Activity Logs (`vcm session logs`)
```bash
vcm session logs interactive_tuning
vcm session logs interactive_tuning --format json
```
- **Expected:** Shows captured terminal activity with automatic secret masking.

### 8.4 View Active Session Info (`vcm session info`)
```bash
vcm session info interactive_tuning
```
- **Expected:** Displays session status, duration, start time, and annotations.

### 8.5 List Sessions (`vcm session list`)
```bash
vcm session list
```
- **Expected:** Tabular summary showing active session.

### 8.6 Conclude Session (`vcm session end`)
```bash
vcm session end
```
- **Expected:** Session duration finalized, terminal logs saved, session status marked completed.

### 8.7 List Completed Sessions
```bash
vcm session list
```

### 8.8 Inspect Session Models (`vcm session models`)
```bash
vcm session models interactive_tuning
```

### 8.9 Create a Retrospective Session (`vcm session create-retrospective`)
```bash
vcm session create-retrospective --name historical_session
vcm session list
```
- **Expected:** Reconstructs a session grouping historical models trained before the session.

### 8.10 Compare Two Sessions (`vcm session compare`)
```bash
vcm session compare interactive_tuning historical_session
```
- **Expected:** Side-by-side comparison of session durations, model counts, and accuracy deltas.

### 8.11 Explain Improvement (`vcm session explain-improvement`)
```bash
vcm session explain-improvement historical_session iris_logistic_v1 iris_rf_v2
```
- **Expected:** Analyzes parameter and code differences explaining performance differences.

### 8.12 Export Session Reports (`vcm session export`)
```bash
# Export interactive HTML report
vcm session export historical_session --format html --output session_report.html

# Export structured JSON
vcm session export historical_session --format json --output session_report.json
```
- **Expected:** Generates standalone `session_report.html` and `session_report.json`.

---

## 9. Model Evolution Timeline Commands (`vcm timeline` - ALL Subcommands)

### 9.1 Display Progression Timeline in Terminal Table
```bash
vcm timeline --show-reasoning --highlight-best
```
- **Expected:** Chronological table displaying all model versions, accuracy deltas (`+0.00%`), best model highlighted, and developer reasoning notes.

### 9.2 View Timeline in Different Formats
```bash
# ASCII graph representation
vcm timeline --format ascii

# JSON export
vcm timeline --format json

# CSV export
vcm timeline --format csv --output timeline_export.csv

# Standalone Interactive HTML Visualizer (with SVG sparkline)
vcm timeline --format html --output timeline_report.html
```
- **Expected:** Renders ASCII chart in console and creates `timeline_report.html` (open in browser to view rich SVG graph and cards).

### 9.3 Filter Timeline
```bash
vcm timeline --accuracy-range 0.95-1.0 --show-changes
vcm timeline show
```

### 9.4 Analyze Trajectory & Regressions (`vcm timeline analyze`)
```bash
vcm timeline analyze
vcm timeline analyze --output timeline_analysis.txt
cat timeline_analysis.txt
```
- **Expected:** Analyzes trajectory, flags any accuracy drops, detects temporal gaps, and outputs recommendations.

### 9.5 Add / Update Developer Reasoning (`vcm timeline reason` & `vcm timeline-reason`)
```bash
# Using subcommand (with --force if already annotated)
vcm timeline reason iris_rf_v2 "Confirmed 100% precision on validation set" --force

# Using standalone command to view
vcm timeline-reason iris_rf_v2 --show

# Using standalone command to force-update
vcm timeline-reason iris_rf_v2 "Production candidate approved by ML team" --force
vcm timeline-reason iris_rf_v2 --show
```
- **Expected:** Displays and updates reasoning annotations for the model.

---

## 10. Deep Lineage Analysis (`vcm analysis`)

```bash
# Generate full lineage report
vcm analysis --report full_lineage

# Compare two models through analysis command
vcm analysis --compare iris_logistic_v1 iris_rf_v2

# Redirect analysis report to file
vcm analysis --report full_lineage > full_lineage_report.txt
cat full_lineage_report.txt
```
- **Expected:** Generates comprehensive dataset-to-model hierarchy with production deployment readiness recommendations.

---

## 11. Production Operations (Deploy & Audit)

### 11.1 Deploy Model (`vcm deploy`)
```bash
# Deploy to staging
vcm deploy models/iris_rf_v2.pkl --environment staging

# Deploy to production
vcm deploy models/iris_rf_v2.pkl --environment production
```
- **Expected:** `Model iris_rf_v2 deployed to production successfully.`

### 11.2 Inspect Audit Trail (`vcm audit`)
```bash
vcm audit --environment staging
vcm audit --environment production
```
- **Expected:** Shows tamper-evident audit record with model name, commit SHA, deployer username, and timestamp.

---

## 12. Deterministic Model Reproduction (`vcm reproduce`)

```bash
vcm reproduce models/iris_logistic_v1.pkl
```
- **Expected:**
  - Verifies Git repository and code state.
  - Verifies training dataset availability.
  - Re-executes training with recorded hyperparameters.
  - Computes prediction parity: `100.0% match` (zero metric drift).

---

## 13. MLflow Experiment Tracking Integration (`vcm mlflow`)

### 13.1 Inspect Integration Status (`vcm mlflow status`)
```bash
vcm mlflow status
```
- **Expected:** Displays current tracking URI (`file:./mlruns`), default experiment name, and Python SDK status.

### 13.2 Enable MLflow Integration (`vcm mlflow enable`)
```bash
vcm mlflow enable
vcm mlflow status
```
- **Expected:** Configuration updated to enable automatic logging to MLflow.

### 13.3 Sync Single Model to MLflow (`vcm mlflow sync <model_name>`)
```bash
vcm mlflow sync iris_logistic_v1
```
- **Expected:** Syncs hyperparameters, metrics, and Model DNA tags to target MLflow experiment.

### 13.4 Sync All Workspace Models to MLflow (`vcm mlflow sync --all`)
```bash
vcm mlflow sync --all
```
- **Expected:** Bulk synchronizes all models tracked in the database to MLflow runs.

### 13.5 Disable MLflow Integration (`vcm mlflow disable`)
```bash
vcm mlflow disable
vcm mlflow status
```
- **Expected:** MLflow tracking disabled in configuration.

---

## Summary Checklist of Tested Commands

| # | Command | Subcommands / Key Flags Tested | Verified |
| :---: | :--- | :--- | :---: |
| 1 | `vcm --version` / `vcm version` | `--verbose` | [x] |
| 2 | `vcm --help` | Root command listing | [x] |
| 3 | `vcm config` | `show`, `set`, `reset` | [x] |
| 4 | `vcm init` | Workspace setup (`.vcm/vcm.db`) | [x] |
| 5 | `vcm status` | Workspace status, Git state, active session, catalog, untracked artifacts | [x] |
| 6 | `vcm train` | `--params`, `--dataset`, `--metrics`, `--reasoning` | [x] |
| 7 | `vcm models` | `--best`, `--dataset`, `--limit`, `--sort-by`, `--format`, `--export` | [x] |
| 8 | `vcm info` | Default summary, `--json` | [x] |
| 9 | `vcm compare` | Side-by-side metric & hyperparameter diffing | [x] |
| 10 | `vcm lineage` | Visual ASCII lineage tree | [x] |
| 11 | `vcm export` | `--output <file.json>` | [x] |
| 12 | `vcm repair` | SQLite database index reconstruction from disk sidecars | [x] |
| 13 | `vcm session` | `start`, `annotate`, `logs`, `info`, `list`, `end`, `models`, `compare`, `explain-improvement`, `create-retrospective`, `export` | [x] |
| 14 | `vcm timeline` | `--show-reasoning`, `--highlight-best`, `--format table/ascii/html/csv/json`, `analyze`, `reason`, `show` | [x] |
| 15 | `vcm timeline-reason` | Standalone command, `--show`, `--force` | [x] |
| 16 | `vcm analysis` | `--report full_lineage`, `--output` | [x] |
| 17 | `vcm deploy` | `--environment staging/production` | [x] |
| 18 | `vcm audit` | `--environment staging/production` audit trail | [x] |
| 19 | `vcm reproduce` | Deterministic rebuild & prediction parity verification | [x] |
| 20 | `vcm mlflow` | `status`, `enable`, `sync <model>`, `sync --all`, `disable` | [x] |
