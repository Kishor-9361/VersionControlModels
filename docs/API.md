# VCM Python API Reference

## Module: `vcm.models.metadata`

### `MetadataModel`
Immutable data class representing full Model DNA.

```python
from vcm.models.metadata import MetadataModel, CodeInfo, DataInfo, TrainingInfo, EnvironmentInfo

model = MetadataModel(
    model_name="classifier_v1",
    model_hash="sha256:abc123456...",
    model_file="models/classifier_v1.pkl",
    metrics={"accuracy": 0.942, "f1_score": 0.928},
    hyperparameters={"learning_rate": 0.001, "epochs": 50},
)
```

#### Methods
- `to_dict() -> Dict[str, Any]`
- `to_json(indent: int = 2) -> str`
- `MetadataModel.from_dict(d: Dict[str, Any]) -> MetadataModel`
- `MetadataModel.from_json(json_str: str) -> MetadataModel`

---

## Module: `vcm.trainer`

### `ModelTracker`
Wrapper class for automated tracking during model training.

```python
from vcm.trainer import ModelTracker

tracker = ModelTracker()
```

#### Context Manager
```python
with tracker.track(
    model_name="classifier_v2",
    model_path="models/classifier_v2.pkl",
    hyperparameters={"lr": 0.001},
) as session:
    # Run training
    session.set_metrics({"accuracy": 0.952})
```

#### Manual Logging
```python
meta = tracker.log_model(
    model_path="models/classifier_v2.pkl",
    model_name="classifier_v2",
    metrics={"accuracy": 0.952},
    hyperparameters={"lr": 0.001},
    dataset_path="data/train.csv",
)
```

---

## Module: `vcm.db.database`

### `Database`
SQLite interface for indexing and querying metadata records.

```python
from vcm.db.database import Database

db = Database(".vcm/vcm.db")
db.init()

# Queries
all_models = db.get_all_models()
best_model = db.get_best_model(metric="accuracy")
models_on_dataset = db.query_by_dataset(dataset_hash="abc123hash")
```
