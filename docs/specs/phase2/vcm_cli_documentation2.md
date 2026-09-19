# VCM CLI - Complete Command Reference

**Version:** 1.0.0 
**Format:** Official documentation for end users and developers 
**Last Updated:** 2024-01-15 

---

## QUICK START

```bash
# Installation
pip install vcm-ml

# Initialize in your ML project
cd my_ml_project
vcm init

# Train and track a model
vcm train --model-name "classifier_v1" \
 --dataset "data/train.csv" \
 --script train.py \
 --metrics metrics.json

# See all models
vcm models --best

# View model details
vcm lineage classifier_v1.pkl

# Compare two models
vcm compare classifier_v1.pkl classifier_v2.pkl
```

---

## COMMAND STRUCTURE

```
vcm <global-options> <command> <command-options>

Global options:
 --verbose, -v Enable verbose output
 --debug Enable debug logging
 --config PATH Use custom config file
 --version Show VCM version
 --help Show help
```

---

## INITIALIZATION COMMANDS

### `vcm init`

**Purpose:** Initialize VCM in your ML project

**Syntax:**
```bash
vcm init [OPTIONS]
```

**Options:**
```
--git-check : Verify Git repo exists (default: true)
--dvc-init : Auto-initialize DVC (default: false)
--config-file : Path to config template (default: .vcmconfig.yaml)
--force : Reinitialize if already initialized
```

**Examples:**

```bash
# Basic initialization
$ vcm init
[x] VCM initialized
 - Created .vcm/ directory
 - Created .vcm/vcm.db (SQLite database)
 - Created .vcmconfig.yaml (configuration)
 
# Initialize and setup DVC
$ vcm init --dvc-init
[x] VCM and DVC initialized
 - DVC ready for tracking data/models

# Reinitialize (overwrite existing config)
$ vcm init --force
[WARNING] Reinitializing VCM...
[x] Reset complete

# Verbose output
$ vcm init --verbose
[DEBUG] Checking Git repository...
[DEBUG] Found .git directory
[DEBUG] Creating .vcm/ directory...
[DEBUG] Initializing SQLite database...
```

**Output Files:**
- `.vcm/vcm.db` - SQLite database
- `.vcmconfig.yaml` - Configuration
- `.vcm/.gitignore` - VCM metadata exclusions

---

## TRAINING COMMANDS

### `vcm train`

**Purpose:** Train a model with automatic metadata capture

**Syntax:**
```bash
vcm train [OPTIONS]
```

**Required Options:**
```
--model-name MODEL_NAME : Name of the model (e.g., "classifier_v1")
--script SCRIPT_PATH : Path to training script (e.g., "train.py")
--metrics METRICS_FILE : Path to metrics JSON output (e.g., "metrics.json")
```

**Optional Options:**
```
--dataset DATASET_PATH : Primary dataset being used (for documentation)
--params KEY=VALUE ... : Hyperparameters (e.g., lr=0.001 epochs=50)
--description TEXT : Human-readable description
--tags TAG1 TAG2 ... : Tags for organization (e.g., "baseline" "v1")
--output MODEL_PATH : Where to save model (default: models/[name].pkl)
--skip-git-check : Train even with uncommitted changes (risky!)
--skip-dvc-check : Ignore DVC files
--validate : Validate metadata before saving
```

**Examples:**

```bash
# Basic training
$ vcm train --model-name "classifier_v1" \
 --script train.py \
 --metrics metrics.json

Running train.py...
[train.py output]
Model trained. Accuracy: 0.942

[x] Model tracked successfully
 Model: classifier_v1
 Accuracy: 0.942
 Git commit: f5a9d3e
 Timestamp: 2024-01-15T10:45:32Z

# With full context
$ vcm train --model-name "classifier_v2" \
 --script train.py \
 --metrics metrics.json \
 --dataset "data/iris_train_v2.1.csv" \
 --params lr=0.001 epochs=50 batch_size=32 random_seed=42 \
 --description "Improved model with feature scaling" \
 --tags "production" "v2" "feature-engineering" \
 --output "models/classifier_v2.pkl"

Running train.py...
[training output]

[x] Model tracked
 Name: classifier_v2
 Description: Improved model with feature scaling
 Hyperparameters:
 • lr: 0.001
 • epochs: 50
 • batch_size: 32
 • random_seed: 42
 Tags: production, v2, feature-engineering
 Accuracy: 0.948
 Improvement: +0.6% vs v1

# With validation
$ vcm train --model-name "classifier_v3" \
 --script train.py \
 --metrics metrics.json \
 --validate

Validating metadata...
[x] Git repo clean: yes
[x] Dataset tracked: yes
[x] Metrics valid: yes
[x] All validations passed

Running training...
[output]

[x] Model saved and indexed

# Verbose mode (see all captured metadata)
$ vcm train --model-name "classifier_v4" \
 --script train.py \
 --metrics metrics.json \
 --verbose

[DEBUG] Capturing Git state...
[DEBUG] Commit: f5a9d3e
[DEBUG] Branch: main
[DEBUG] Remote: origin
[DEBUG] Capturing DVC files...
[DEBUG] data/train.csv (hash: xyz789)
[DEBUG] Capturing environment...
[DEBUG] Python: 3.9.1
[DEBUG] scikit-learn: 1.2.0
[DEBUG] pandas: 2.0.0
[DEBUG] Running training script...
[DEBUG] Capturing metrics from metrics.json...
[DEBUG] Creating metadata object...
[DEBUG] Saving to models/classifier_v4.pkl.vcm.json...
[DEBUG] Inserting into database...
[DEBUG] Session tracking: enabled
[x] Complete
```

**Common Issues & Solutions:**

```bash
# Error: Model file not created
$ vcm train --model-name "v1" --script bad_train.py --metrics metrics.json
[FAIL] Error: Model file not found at models/v1.pkl
 Solution: 
 1. Check that your train.py saves model to models/v1.pkl
 2. Run train.py manually to verify it works
 3. Use --output to specify exact path

# Error: Git repo not clean
$ vcm train --model-name "v1" --script train.py --metrics metrics.json
[WARNING] Warning: Git repository has uncommitted changes
 Recommendation: Commit changes first for clean lineage
 
 To override: vcm train ... --skip-git-check

# Error: Metrics file not found
$ vcm train --model-name "v1" --script train.py --metrics nonexistent.json
[FAIL] Error: Metrics file not found: nonexistent.json
 Solution: Ensure your training script writes metrics.json
 
 Verify by running:
 python train.py
 ls -la metrics.json
```

---

## QUERY COMMANDS

### `vcm models`

**Purpose:** List and filter tracked models

**Syntax:**
```bash
vcm models [OPTIONS]
```

**Options:**
```
--best : Show only top model (by accuracy)
--limit N : Show top N models (default: 10)
--dataset DATASET : Filter by dataset
--accuracy RANGE : Filter by accuracy (e.g., 0.9-0.95)
--since DATE : Models trained since date (e.g., "1 week ago")
--tag TAG : Filter by tag
--sort FIELD : Sort by field (accuracy, timestamp, f1_score)
--format FORMAT : Output format (table, json, csv)
--export FILE : Save to file instead of printing
```

**Examples:**

```bash
# Show all models (default)
$ vcm models
┌──────────────────┬──────────┬─────────────┬──────────────┐
│ Model Name │ Accuracy │ Dataset │ Git Commit │
├──────────────────┼──────────┼─────────────┼──────────────┤
│ classifier_v2 │ 94.8% │ iris_v2.csv │ f5a9d3e │
│ classifier_v4 │ 94.2% │ iris_v2.csv │ a7b2c4f │
│ classifier_v1 │ 94.2% │ iris_v1.csv │ f5a9d3e │
│ classifier_v3 │ 92.1% │ iris_v1.csv │ f5a9d3e │
│ classifier_v5 │ 91.8% │ iris_v1.csv │ abc123d │
└──────────────────┴──────────┴─────────────┴──────────────┘
Total: 5 models

# Show best model
$ vcm models --best
┌──────────────────┬──────────┬─────────────┬──────────────┐
│ Model Name │ Accuracy │ Dataset │ Git Commit │
├──────────────────┼──────────┼─────────────┼──────────────┤
│ classifier_v2 │ 94.8% │ iris_v2.csv │ f5a9d3e │
└──────────────────┴──────────┴─────────────┴──────────────┘
 Best overall: classifier_v2 (94.8% accuracy)

# Top 3 models
$ vcm models --best --limit 3
[Table with top 3]

# Filter by dataset
$ vcm models --dataset iris_v2.csv
[Models trained on iris_v2.csv only]

# Filter by accuracy range
$ vcm models --accuracy 0.93-0.95
[Models with 93-95% accuracy]

# Models from last week
$ vcm models --since "1 week ago"
[Recent models]

# By tag
$ vcm models --tag production
[Models tagged as production]

# JSON output (for automation)
$ vcm models --best --format json
{
 "model_name": "classifier_v2",
 "accuracy": 0.948,
 "dataset": "iris_v2.csv",
 "git_commit": "f5a9d3e",
 "timestamp": "2024-01-15T10:45:32Z"
}

# Export to CSV
$ vcm models --format csv --export models_export.csv
[x] Exported 5 models to models_export.csv
```

---

### `vcm lineage`

**Purpose:** Show complete model lineage and context

**Syntax:**
```bash
vcm lineage MODEL_FILE [OPTIONS]
```

**Options:**
```
--format FORMAT : Output format (tree, json, detailed)
--show-diffs : Show what changed from previous models
--follow-chain : Show previous/next models in sequence
```

**Examples:**

```bash
# Basic lineage
$ vcm lineage models/classifier_v2.pkl

 Model: classifier_v2.pkl
├── Accuracy: 0.948
├── Git Commit: f5a9d3e
│ ├── Branch: main
│ ├── URL: https://github.com/user/ml-project
│ └── Timestamp: 2024-01-15T10:45:32Z
├── Dataset Files:
│ ├── data/iris_train_v2.1.csv (hash: xyz789)
│ └── data/iris_test_v2.1.csv (hash: qwe456)
├── Hyperparameters:
│ ├── learning_rate: 0.001
│ ├── epochs: 50
│ └── batch_size: 32
├── Metrics:
│ ├── Accuracy: 0.948
│ ├── Precision: 0.931
│ ├── Recall: 0.942
│ └── F1 Score: 0.936
├── Environment:
│ ├── Python: 3.9.1
│ ├── scikit-learn: 1.2.0
│ └── pandas: 2.0.0
└── Trained by: alice (2024-01-15)

# Detailed format
$ vcm lineage models/classifier_v2.pkl --format detailed
[Full JSON dump of all metadata]

# Show model chain
$ vcm lineage models/classifier_v2.pkl --follow-chain
Previous: classifier_v1 (Acc: 0.942)
 └─ Current: classifier_v2 (Acc: 0.948) 
 └─ Next: classifier_v3 (Acc: 0.921)

# With differences
$ vcm lineage models/classifier_v2.pkl --show-diffs
Comparing classifier_v1 -> classifier_v2:
 Code changes:
 • Added feature scaling in preprocessing
 Data changes:
 • Dataset v1.0 -> v2.0 (more samples)
 Hyperparameter changes:
 • learning_rate: 0.01 -> 0.001
 Performance improvement:
 • Accuracy: +0.6%
```

---

### `vcm compare`

**Purpose:** Compare two or more models side-by-side

**Syntax:**
```bash
vcm compare MODEL1 MODEL2 [MODEL3 ...] [OPTIONS]
```

**Options:**
```
--metric METRIC : Focus on specific metric (accuracy, f1, etc.)
--show-improvement : Highlight improvements
--show-degradation : Highlight degradations
--format FORMAT : Output format (table, json, detailed)
```

**Examples:**

```bash
# Compare two models
$ vcm compare classifier_v1.pkl classifier_v2.pkl

Comparison: classifier_v1 vs classifier_v2
┌──────────────────┬──────────────┬──────────────┬─────────┐
│ Metric │ v1 │ v2 │ Change │
├──────────────────┼──────────────┼──────────────┼─────────┤
│ Accuracy │ 94.2% │ 94.8% │ +0.6% ⬆ │
│ Precision │ 92.1% │ 93.1% │ +1.0% ⬆ │
│ Recall │ 94.2% │ 94.2% │ 0.0% │
│ F1 Score │ 93.1% │ 93.6% │ +0.5% ⬆ │
├──────────────────┼──────────────┼──────────────┼─────────┤
│ Git Commit │ f5a9d3e │ a7b2c4f │ Different
│ Dataset │ iris_v1.csv │ iris_v2.csv │ Different
│ Learning Rate │ 0.01 │ 0.001 │ 10x lower
│ Epochs │ 30 │ 50 │ +20 epochs
├──────────────────┼──────────────┼──────────────┼─────────┤
│ Training Time │ 12s │ 18s │ +50% │
└──────────────────┴──────────────┴──────────────┴─────────┘

 Summary:
 [x] v2 is better
 • Higher accuracy (+0.6%)
 • Better precision (+1.0%)
 • Same recall
 • Slower training (+50%)

 Recommendation:
 Use v2 for production
 (Better metrics outweigh longer training time)

# Compare three models
$ vcm compare classifier_v1.pkl classifier_v2.pkl classifier_v3.pkl

[Table with all three models]

# Focus on accuracy
$ vcm compare classifier_v1.pkl classifier_v2.pkl --metric accuracy

Accuracy Comparison:
 classifier_v1: 94.2%
 classifier_v2: 94.8% [BEST]
 
 Improvement: +0.6%

# Show why v2 is better
$ vcm compare classifier_v1.pkl classifier_v2.pkl --show-improvement

Key Improvements in v2:
 • Better dataset (v1.0 -> v2.0):
 - More samples (80 -> 100)
 - Better preprocessing
 
 • Better hyperparameters:
 - Lower learning rate (0.01 -> 0.001)
 → Better convergence
 - More epochs (30 -> 50)
 → Full training
 
 • Result:
 - Accuracy +0.6%
 - Precision +1.0%
```

---

### `vcm info`

**Purpose:** Display detailed metadata for a single model

**Syntax:**
```bash
vcm info MODEL_FILE [OPTIONS]
```

**Options:**
```
--format FORMAT : Output format (formatted, json, yaml)
--sections SECTIONS : Show only certain sections (code, data, metrics, etc.)
```

**Examples:**

```bash
# Show all info
$ vcm info models/classifier_v2.pkl

Model: classifier_v2.pkl
═══════════════════════════════════════════════════════════
Hash: sha256:abc123def456...

 TRAINING INFO
 Trained: 2024-01-15 10:45:32 UTC
 Duration: 18 seconds
 User: alice
 Hostname: ml-workstation-1

 HYPERPARAMETERS
 n_estimators: 10
 max_depth: 5
 random_state: 42
 learning_rate: 0.001

 METRICS
 accuracy: 0.948
 precision: 0.931
 recall: 0.942
 f1_score: 0.936

 DATA
 Dataset 1: data/iris_train_v2.1.csv
 └─ Hash: md5:xyz789...
 └─ Size: 2.9 KB
 Dataset 2: data/iris_test_v2.1.csv
 └─ Hash: md5:qwe456...
 └─ Size: 0.7 KB

 CODE
 Commit: f5a9d3e
 Branch: main
 URL: https://github.com/user/ml-project
 Clean: Yes (no uncommitted changes)

 ENVIRONMENT
 Python: 3.9.1
 scikit-learn: 1.2.0
 pandas: 2.0.0
 numpy: 1.23.0

# JSON format (for parsing)
$ vcm info models/classifier_v2.pkl --format json
{
 "model_name": "classifier_v2",
 "metrics": {"accuracy": 0.948},
 ...
}

# Only certain sections
$ vcm info models/classifier_v2.pkl --sections metrics,hyperparameters
 METRICS
 accuracy: 0.948
 precision: 0.931
 ...

 HYPERPARAMETERS
 n_estimators: 10
 ...
```

---

## ADVANCED COMMANDS

### `vcm export`

**Purpose:** Export model metadata to file

**Syntax:**
```bash
vcm export MODEL_FILE [OPTIONS]
```

**Options:**
```
--output FILE : Output file path (default: model_name_metadata.json)
--format FORMAT : Format (json, yaml, csv, html)
--include-log : Include terminal log (if available)
--pretty : Pretty-print (default: true)
```

**Examples:**

```bash
# Export to JSON
$ vcm export models/classifier_v2.pkl
[x] Exported to models/classifier_v2_metadata.json

# Custom output
$ vcm export models/classifier_v2.pkl --output my_model_info.json

# YAML format
$ vcm export models/classifier_v2.pkl --format yaml --output model.yaml

# HTML report
$ vcm export models/classifier_v2.pkl --format html --output model_report.html
[x] Exported to model_report.html
 (Open in browser for rich visualization)

# With terminal log
$ vcm export models/classifier_v2.pkl --include-log
[x] Exported including terminal session log
```

---

## SESSION COMMANDS (Phase 2)

### `vcm session start`

**Purpose:** Begin tracking a development session

**Syntax:**
```bash
vcm session start [SESSION_NAME] [OPTIONS]
```

**Examples:**

```bash
$ vcm session start "Tuesday morning experiments"
[x] Session started: sess_abc123
 Name: Tuesday morning experiments
 Start: 2024-01-15 09:00:00
 User: alice
 Terminal logging: enabled
 
Use 'vcm session end' when finished

# Auto-name by timestamp
$ vcm session start
[x] Session started: sess_2024_01_15_09_00
```

---

### `vcm session end`

**Purpose:** End session and save tracking data

**Syntax:**
```bash
vcm session end [OPTIONS]
```

**Examples:**

```bash
$ vcm session end
[x] Session ended
 Duration: 2h 45m
 Models trained: 5
 Commits: 3
 Best model: classifier_v3 (acc: 93.1%)
 Terminal log: 1,240 lines
 Session saved: sess_abc123
```

---

### `vcm session info`

**Purpose:** Show session details

**Syntax:**
```bash
vcm session info SESSION_NAME [OPTIONS]
```

**Examples:**

```bash
$ vcm session info "Tuesday morning experiments"

Session: Tuesday morning experiments
═════════════════════════════════════════
ID: sess_abc123
User: alice
Duration: 2h 45m (09:00 - 11:45)

 Models Trained: 5
 1. classifier_v1 (Acc: 91.2%) ├─ 09:15
 2. classifier_v2 (Acc: 92.8%) ├─ 09:45
 3. classifier_v3 (Acc: 93.1%) ├─ 10:12 [BEST]
 4. classifier_v4 (Acc: 91.5%) ├─ 10:45
 5. classifier_v5 (Acc: 92.1%) └─ 11:15

 Annotations: 2
 • 09:30: "Trying different random seeds"
 • 10:15: "Implemented feature scaling"

 Git Commits: 3
 • abc123: "Add feature engineering"
 • def456: "Update preprocessing"
 • ghi789: "Tune hyperparameters"

 Terminal Log: 1,240 lines captured
 Secrets masked: yes
 Encryption: enabled
```

---

### `vcm session logs`

**Purpose:** View terminal output from session

**Syntax:**
```bash
vcm session logs SESSION_NAME [OPTIONS]
```

**Examples:**

```bash
$ vcm session logs "Tuesday morning experiments"

═════════════════════════════════════════════════════════════
Session: Tuesday morning experiments
Start: 2024-01-15 09:00:00 | End: 2024-01-15 11:45:00
User: alice | Branch: main
─────────────────────────────────────────────────────────────
09:15:30 | python train.py --lr 0.001
09:15:45 | Epoch 1/50: loss=0.456, val_acc=0.85
09:16:12 | Epoch 10/50: loss=0.234, val_acc=0.91
09:16:45 | Model saved: models/classifier_v1.pkl
09:16:50 | Accuracy: 0.912

09:30:15 | User note: "Trying different random seeds"
09:30:16 | python train.py --lr 0.001 --seed 123
...
11:45:00 | Session ended
─────────────────────────────────────────────────────────────
Total: 5 models | Best: classifier_v3 (93.1%)
```

---

### `vcm session models`

**Purpose:** List all models trained in a session

**Syntax:**
```bash
vcm session models SESSION_NAME [OPTIONS]
```

**Examples:**

```bash
$ vcm session models "Tuesday morning experiments"

Models trained in: Tuesday morning experiments
┌────┬──────────────────┬──────────┬──────────┬──────────┐
│ # │ Model Name │ Accuracy │ Time │ Position │
├────┼──────────────────┼──────────┼──────────┼──────────┤
│ 1 │ classifier_v1 │ 91.2% │ 09:15 │ first │
│ 2 │ classifier_v2 │ 92.8% │ 09:45 │ │
│ 3 │ classifier_v3 │ 93.1% │ 10:12 │ [BEST] │
│ 4 │ classifier_v4 │ 91.5% │ 10:45 │ │
│ 5 │ classifier_v5 │ 92.1% │ 11:15 │ last │
└────┴──────────────────┴──────────┴──────────┴──────────┘
```

---

## UTILITY COMMANDS

### `vcm config`

**Purpose:** Manage configuration

**Syntax:**
```bash
vcm config [COMMAND] [OPTIONS]
```

**Commands:**
```
show : Display current config
set KEY VALUE : Update configuration
reset : Reset to defaults
```

**Examples:**

```bash
# Show config
$ vcm config show

Current Configuration
═══════════════════════════════════════════════════════
database_path: .vcm/vcm.db

integrations:
 git: enabled
 dvc: enabled
 mlflow: disabled

session_logging:
 enabled: true
 capture_terminal: true
 mask_secrets: true

# Update config
$ vcm config set session_logging.enabled false
[x] Updated: session_logging.enabled = false

# Reset
$ vcm config reset
[WARNING] This will reset all settings to defaults. Continue? [y/N]
y
[x] Configuration reset to defaults
```

---

### `vcm version`

**Purpose:** Show VCM version

**Syntax:**
```bash
vcm version [OPTIONS]
```

**Examples:**

```bash
$ vcm version
VCM version 1.0.0

$ vcm --version
1.0.0

$ vcm version --verbose
VCM Version: 1.0.0
Release: 2024-01-15
License: MIT
Home: https://github.com/user/vcm
```

---

### `vcm help`

**Purpose:** Show help

**Syntax:**
```bash
vcm help [COMMAND]
```

**Examples:**

```bash
$ vcm help
VCM - Version Control for ML Models
Usage: vcm <command> [options]

Commands:
 init Initialize VCM
 train Train and track model
 models List models
 lineage Show model lineage
 compare Compare models
 info Show model info
 export Export metadata
 session Manage sessions
 config Manage config
 help Show this help

$ vcm help train
Show detailed help for 'train' command
[Full command reference]
```

---

## PRACTICAL WORKFLOWS

### Workflow 1: Training Multiple Models

```bash
# Start session
vcm session start "Model comparison day"

# Train baseline
vcm train --model-name "baseline" \
 --script train.py \
 --metrics metrics.json \
 --params lr=0.01 epochs=30

# Experiment 1: Lower learning rate
vcm session annotate "Testing lower learning rate"
vcm train --model-name "lr_tuned" \
 --script train.py \
 --metrics metrics.json \
 --params lr=0.001 epochs=30

# Experiment 2: More epochs
vcm session annotate "Testing more epochs"
vcm train --model-name "epochs_tuned" \
 --script train.py \
 --metrics metrics.json \
 --params lr=0.001 epochs=50

# End session
vcm session end

# Review results
vcm models --best --limit 3
vcm session info "Model comparison day"
```

---

### Workflow 2: Debugging Model Regression

```bash
# Problem: New model performs worse

# Find good model
vcm models --accuracy 0.9-1.0 --limit 1
# → Found: classifier_v2 (94.8%)

# Find bad model
vcm models --sort timestamp | head -1
# → Latest: classifier_v5 (91.8%)

# Compare
vcm compare classifier_v2.pkl classifier_v5.pkl --show-degradation

# Investigate
vcm lineage classifier_v5.pkl --show-diffs

# Solution: Revert changes
git revert <commit_hash>
vcm train --model-name "classifier_v6" ...
```

---

### Workflow 3: Production Deployment

```bash
# Find best model
best_model=$(vcm models --best --format json | jq -r '.model_name')
echo "Deploying: $best_model"

# Export full report
vcm export models/$best_model.pkl --format html --output deployment_report.html

# Verify reproducibility
vcm reproduce models/$best_model.pkl --verify

# Tag for production
vcm models --tag production $best_model

# Archive session
vcm session export "final testing session" --format html
```

---

## COMMON TASKS

### How do I find the best model?
```bash
vcm models --best
```

### How do I compare models?
```bash
vcm compare model_v1.pkl model_v2.pkl
```

### How do I see what changed between models?
```bash
vcm lineage model_v2.pkl --show-diffs --follow-chain
```

### How do I view all my training history?
```bash
vcm session list
vcm session info "session_name"
```

### How do I export metadata for reporting?
```bash
vcm export model.pkl --format html --output report.html
```

### How do I troubleshoot poor performance?
```bash
# Find when it started
vcm models --sort timestamp | head -10

# Compare with good model
vcm compare good_model.pkl bad_model.pkl

# See what changed
vcm lineage bad_model.pkl --show-diffs
```

---

## ERROR MESSAGES & SOLUTIONS

| Error | Cause | Solution |
|-------|-------|----------|
| `Git repository not found` | Not in git project | `git init` first |
| `Model file not created` | Train script doesn't save model | Fix training script |
| `Metrics file not found` | Train script doesn't output metrics | Add metrics.json output |
| `Database corrupted` | Database file damaged | `vcm repair` or `rm .vcm/vcm.db` |
| `Uncommitted changes` | Git working directory dirty | `git add . && git commit` or use `--skip-git-check` |

---

## END OF CLI DOCUMENTATION

**All commands documented with examples and use cases**
