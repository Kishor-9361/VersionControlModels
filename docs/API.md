# VCM Python API Reference

Comprehensive guide to programmatically integrating **VCM (Version Control Models)** into your Python machine learning pipelines, training notebooks, and deployment scripts.

---

## 1. Model Tracking (`vcm.trainer`)

### `ModelTracker`
The primary interface for instrumenting ML training pipelines.

```python
from vcm.trainer import ModelTracker

tracker = ModelTracker()
```

#### Method: `log_model(...)`
Manually logs a trained model artifact, extracts Model DNA, attaches sidecar JSON, and indexes into SQLite.

```python
metadata = tracker.log_model(
    model_path="models/random_forest_v1.pkl",
    model_name="random_forest_v1",
    metrics={"accuracy": 0.954, "f1_score": 0.948, "latency_ms": 1.2},
    hyperparameters={"n_estimators": 100, "max_depth": 5, "random_state": 42},
    dataset_path="data/train.csv",
    reasoning="Ensemble trees with depth cap to improve test generalization.",
)
```

**Parameters:**
- `model_path` (*str*): File path to saved model artifact (`.pkl`, `.onnx`, `.pt`, etc.).
- `model_name` (*str*): Unique model identifier.
- `metrics` (*Dict[str, float]*): Dictionary of evaluation metrics.
- `hyperparameters` (*Optional[Dict[str, Any]]*): Training parameters.
- `dataset_path` (*Optional[str]*): Path to training dataset file or folder.
- `reasoning` (*Optional[str]*): Developer rationale for creating this model version.

**Returns:** `MetadataModel` instance.

#### Context Manager: `track(...)`
Context manager that captures training execution duration, code state, and environment automatically.

```python
from sklearn.ensemble import RandomForestClassifier
import joblib

with tracker.track(
    model_name="iris_rf_v2",
    model_path="models/iris_rf_v2.pkl",
    hyperparameters={"n_estimators": 50, "max_depth": 4},
    dataset_path="data/iris.csv",
    reasoning="Reduced tree count for edge deployment.",
) as session:
    clf = RandomForestClassifier(n_estimators=50, max_depth=4)
    clf.fit(X_train, y_train)
    joblib.dump(clf, "models/iris_rf_v2.pkl")
    
    score = clf.score(X_test, y_test)
    session.set_metrics({"accuracy": score})
```

---

## 2. Session Tracking (`vcm.models.session`)

### `SessionTracker`
Groups multiple iterative training runs into a unified experiment session with automatic terminal capture.

```python
from vcm.models.session import SessionTracker

# Context manager usage
with SessionTracker(session_name="hyperopt_phase1", user="alice") as session:
    session.annotate("Testing learning rates between 0.001 and 0.1", category="hypothesis")
    
    # Train iteration 1
    # Train iteration 2
    
    session.annotate("LR=0.01 yielded highest validation score", category="conclusion")
```

#### Key Methods:
- `start() -> None`: Starts session and initiates terminal logging.
- `end() -> None`: Finalizes session duration, masks secrets in terminal logs, and persists to DB.
- `annotate(note: str, category: str = "general", model_id: Optional[str] = None) -> None`: Appends timestamped note.
- `log_model(...) -> MetadataModel`: Logs a model directly within session scope.
- `export(format: str = "html", output_path: Optional[str] = None) -> str`: Exports interactive HTML or JSON summary.

### `SessionComparator`
Compares two experimental sessions side-by-side.

```python
from vcm.models.session import SessionComparator

comparator = SessionComparator()
comparison = comparator.compare_sessions("session_01", "session_02")

print(f"Accuracy Delta: {comparison.accuracy_delta:+.2%}")
print(f"Winning Session: {comparison.winner}")
print(f"Recommendation: {comparison.recommendation}")
```

---

## 3. Model Evolution & Progression (`vcm.models.timeline`)

### `TimelineStore`
Builds sequential progression timelines, tracks accuracy trajectories, detects regressions, and diagnoses root causes.

```python
from vcm.db.database import Database
from vcm.models.timeline import TimelineStore

db = Database()
store = TimelineStore(db)

# 1. Retrieve timeline
timeline = store.get_model_timeline(session_id="exp_01")
print(f"Models in progression: {timeline.model_count}")
print(f"Net gain: {timeline.net_accuracy_gain:+.2%}")
print(f"Best performer: {timeline.best_model['model_id']}")

# 2. Detect performance regressions (>1% accuracy drop)
regressions = store.detect_regressions(threshold=0.01, timeline=timeline)
for reg in regressions:
    print(f"Regression detected at {reg['model_id']}!")
    print(f"Accuracy drop: {reg['accuracy_delta']:.2%}")
    print(f"Root Cause: {reg.get('root_cause')}")

# 3. Detect temporal gaps (>24 hours between iterations)
gaps = store.detect_timeline_gaps(threshold_hours=24.0, timeline=timeline)
```

---

## 4. Visual Formatters (`vcm.utils.timeline_formatters`)

Generate presentation-ready visual reports across multiple formats.

```python
from vcm.utils.timeline_formatters import (
    format_timeline_table,
    format_timeline_html,
    format_timeline_json,
    format_timeline_csv,
    format_timeline_ascii,
    generate_analysis_report,
)

# Render colorized terminal table
table_str = format_timeline_table(timeline, show_reasoning=True, highlight_best=True)
print(table_str)

# Generate standalone interactive HTML report with embedded SVG sparkline
html_content = format_timeline_html(timeline, title="Model Progression Report")
with open("timeline.html", "w") as f:
    f.write(html_content)

# ASCII trajectory chart for CLI
print(format_timeline_ascii(timeline))
```

---

## 5. Relational Database Interface (`vcm.db.database`)

### `Database`
Direct programmatic access to the indexed SQLite catalog (`.vcm/vcm.db`).

```python
from vcm.db.database import Database

db = Database(".vcm/vcm.db")
db.init()

# Query models
all_models = db.get_all_models()
top_model = db.get_best_model(metric="accuracy")
filtered = db.query_by_accuracy_range(min_acc=0.90, max_acc=0.99)
by_dataset = db.query_by_dataset(dataset_hash="abc123dvc")

# Evolution queries
evolution_chain = db.get_model_timeline(session_id="exp_01")
db.add_model_reasoning("model_v3", "Tuned depth parameter based on CV fold 2.")
```

---

## 6. Production Operations (`vcm.utils.helpers`)

### Model Deployment & Auditing
```python
from vcm.utils.helpers import deploy_model, vcm_audit

# Deploy model artifact to production
deploy_model("models/iris_rf_v2.pkl", environment="production")

# Retrieve production deployment audit trail
audit_record = vcm_audit(environment="production")
print(f"Active Production Model: {audit_record['model_name']}")
print(f"Deployed By: {audit_record['trained_by']}")
print(f"Commit SHA: {audit_record['git_commit']}")
```

### Deterministic Model Reproduction
```python
from vcm.utils.helpers import vcm_reproduce

# Rebuild and verify parity against saved metadata
model_obj, metrics = vcm_reproduce("models/iris_rf_v2.pkl")
print("Reproduced model accuracy:", metrics["accuracy"])
```
