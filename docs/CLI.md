# VCM CLI Reference

```
Usage: vcm [OPTIONS] COMMAND [ARGS]...

  VCM (Version Control Models) - Model DNA Version Control Platform.

Commands:
  init     Initialize VCM in current project.
  train    Wrap model training and automatically capture code, data, metrics, and environment.
  models   List and filter tracked models.
  lineage  Show complete lineage tree for a model.
  compare  Compare two models side-by-side.
  info     Show detailed model metadata.
  export   Export model metadata to JSON file or stdout.
  repair   Rebuild SQLite database from existing .vcm.json files on disk.
```

---

## Command Details

### `vcm init`
Initialize VCM configuration and SQLite database in the current project directory.
- `--db-path <path>`: Custom path for SQLite database (default: `.vcm/vcm.db`).
- `--models-dir <path>`: Default directory for saved models (default: `models`).

### `vcm train`
Execute training script and capture Model DNA.
- `--model-name <name>`: **[Required]** Unique name for the model.
- `--script <path>`: **[Required]** Python training script path.
- `--dataset <path>`: Path to training dataset file or folder.
- `--metrics <path>`: Path to metrics JSON file produced by training script.
- `--params <key=val>`: Hyperparameter key=value pair (can be passed multiple times).
- `--model-file <path>`: Explicit model output path if outside default directory.
- `--output-dir <path>`: Directory where model artifact is saved.

### `vcm models`
Query and filter tracked models.
- `--dataset <filter>`: Filter models trained on specific dataset file or hash.
- `--best`: Show only highest performing model (by default: accuracy).
- `--limit <n>`: Limit number of results.
- `--sort-by <metric>`: Metric to sort by (default: `accuracy`).
- `--format <table|json|csv>`: Output formatting.
- `--export <file>`: Export query output to CSV or JSON file.

### `vcm lineage <model_ref>`
Display visual ASCII/Unicode lineage tree for a model.
- `<model_ref>`: Model name (e.g. `classifier_v1`) or path to model file (`models/classifier_v1.pkl`).

### `vcm compare <model1> <model2>`
Generate side-by-side comparison matrix with delta computation and improvement highlights.

### `vcm info <model_ref>`
Display full metadata for a model.
- `--json`: Print raw JSON format.

### `vcm export <model_ref>`
Export model metadata to standard JSON format.
- `--output <path>`: File path to save exported JSON.

### `vcm repair`
Scans project workspace for all `.vcm.json` files and reconstructs the SQLite index database.
