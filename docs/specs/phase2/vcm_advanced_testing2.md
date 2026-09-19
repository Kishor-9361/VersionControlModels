# VCM Advanced Testing - Real ML Project Scenarios

**Purpose:** Validate VCM works correctly in real-world ML workflows 
**Format:** Complete end-to-end test scenarios with expected outputs 
**Scope:** Post-MVP validation in production-like environment 

---

## TEST PROJECT SETUP

### Real Dataset: Iris Classification (Small, Reproducible)

```python
# tests/fixtures/real_project/prepare_data.py
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['target'] = iris.target

# Create data versions
train, test = train_test_split(df, test_size=0.2, random_state=42)
train.to_csv('data/iris_train_v1.0.csv', index=False)
test.to_csv('data/iris_test_v1.0.csv', index=False)

# Version 2: with feature scaling
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
train_scaled = train.copy()
train_scaled.iloc[:, :-1] = scaler.fit_transform(train.iloc[:, :-1])
train_scaled.to_csv('data/iris_train_v2.0.csv', index=False)

print("Data prepared: v1.0 (raw), v2.0 (scaled)")
```

### Real Training Scripts

```python
# training_scripts/train_model_v1.py
import json
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Load data
train = pd.read_csv('data/iris_train_v1.0.csv')
test = pd.read_csv('data/iris_test_v1.0.csv')

X_train, y_train = train.iloc[:, :-1], train.iloc[:, -1]
X_test, y_test = test.iloc[:, :-1], test.iloc[:, -1]

# Train model
model = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=5)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
metrics = {
 'accuracy': float(accuracy_score(y_test, y_pred)),
 'precision': float(precision_score(y_test, y_pred, average='weighted')),
 'recall': float(recall_score(y_test, y_pred, average='weighted')),
 'f1_score': float(f1_score(y_test, y_pred, average='weighted'))
}

# Save outputs
pickle.dump(model, open('models/iris_classifier_v1.pkl', 'wb'))
with open('metrics.json', 'w') as f:
 json.dump(metrics, f)

print(f"Model trained. Accuracy: {metrics['accuracy']:.4f}")
```

---

## SCENARIO 1: Single Model Training with Data Versioning

### Workflow
```bash
cd real_project
git init
git add .
git commit -m "Initial project setup"

# Initialize DVC and VCM
dvc init
vcm init

# Add data to DVC
dvc add data/iris_train_v1.0.csv
dvc add data/iris_test_v1.0.csv
git add data/*.dvc .gitignore
git commit -m "Add training data v1.0"

# Train model with VCM
vcm train \
 --model-name "iris_classifier_v1" \
 --dataset "data/iris_train_v1.0.csv" \
 --script training_scripts/train_model_v1.py \
 --metrics metrics.json \
 --params n_estimators=10 max_depth=5 random_state=42
```

### Expected VCM Capture

```json
{
 "model_name": "iris_classifier_v1",
 "model_file": "models/iris_classifier_v1.pkl",
 "model_hash": "sha256:abc123...",
 
 "code": {
 "git_commit": "f5a9d3e...",
 "git_branch": "main",
 "git_url": "file:///path/to/real_project",
 "files_changed": ["training_scripts/train_model_v1.py"],
 "uncommitted_changes": false
 },
 
 "data": {
 "dvc_files": [
 {
 "path": "data/iris_train_v1.0.csv",
 "dvc_hash": "md5:xyz789...",
 "size_bytes": 2945
 },
 {
 "path": "data/iris_test_v1.0.csv",
 "dvc_hash": "md5:qwe456...",
 "size_bytes": 738
 }
 ]
 },
 
 "metrics": {
 "accuracy": 1.0,
 "precision": 1.0,
 "recall": 1.0,
 "f1_score": 1.0
 },
 
 "hyperparameters": {
 "n_estimators": 10,
 "max_depth": 5,
 "random_state": 42
 },
 
 "environment": {
 "python_version": "3.9.1",
 "libraries": {
 "scikit-learn": "1.2.0",
 "pandas": "2.0.0"
 }
 },
 
 "training": {
 "timestamp": "2024-01-15T14:23:45Z",
 "duration_seconds": 12,
 "user": "alice",
 "hostname": "ml-workstation-1"
 }
}
```

### Test Assertions

```python
def test_scenario_1_single_model_training():
 """Verify all metadata captured for single model"""
 metadata = load_model_metadata('models/iris_classifier_v1.pkl.vcm.json')
 
 # Code tracking
 assert metadata['code']['git_commit'] is not None, "Git commit missing"
 assert len(metadata['code']['git_commit']) == 40, "Invalid git commit hash"
 assert metadata['code']['git_branch'] == 'main', "Wrong branch"
 assert not metadata['code']['uncommitted_changes'], "Should be clean"
 
 # Data tracking
 assert len(metadata['data']['dvc_files']) == 2, "Missing DVC files"
 assert any('iris_train_v1.0.csv' in f['path'] for f in metadata['data']['dvc_files'])
 assert all('dvc_hash' in f for f in metadata['data']['dvc_files']), "Missing DVC hashes"
 
 # Metrics
 assert metadata['metrics']['accuracy'] == 1.0, "Wrong accuracy"
 assert all(m in metadata['metrics'] for m in ['accuracy', 'precision', 'recall', 'f1_score'])
 
 # Hyperparameters
 assert metadata['hyperparameters']['n_estimators'] == 10
 assert metadata['hyperparameters']['max_depth'] == 5
 
 # Environment
 assert 'scikit-learn' in metadata['environment']['libraries']
 assert metadata['environment']['python_version'].startswith('3.')
 
 # Training info
 assert metadata['training']['duration_seconds'] < 60, "Training too slow"
 assert metadata['training']['user'] is not None
 
 print("[x] Scenario 1: Single model training - PASSED")
```

---

## SCENARIO 2: Multiple Models, Same Dataset

### Workflow
```bash
# Train model v2 with different hyperparameters
vcm train \
 --model-name "iris_classifier_v2" \
 --dataset "data/iris_train_v1.0.csv" \
 --script training_scripts/train_model_v1.py \
 --metrics metrics.json \
 --params n_estimators=20 max_depth=10 random_state=42

# Train model v3 with even different params
vcm train \
 --model-name "iris_classifier_v3" \
 --dataset "data/iris_train_v1.0.csv" \
 --script training_scripts/train_model_v1.py \
 --metrics metrics.json \
 --params n_estimators=50 max_depth=15 random_state=42
```

### Test: Query All Models on Same Dataset

```python
def test_scenario_2_multiple_models_same_dataset():
 """Verify VCM can find and compare multiple models on same dataset"""
 
 # Query database
 models = db.query_by_dataset('data/iris_train_v1.0.csv')
 
 assert len(models) >= 3, "Should find at least 3 models"
 
 # Verify each model has same dataset but different hyperparams
 for model in models:
 assert 'iris_train_v1.0.csv' in str(model['data']['dvc_files'])
 
 # Find best model
 best = max(models, key=lambda m: m['metrics'].get('accuracy', 0))
 print(f"[x] Best model on dataset v1.0: {best['model_name']} ({best['metrics']['accuracy']:.2%})")
 
 # Verify hyperparameters differ
 hparams = [m['hyperparameters']['n_estimators'] for m in models]
 assert len(set(hparams)) > 1, "Hyperparameters should differ"
 
 print("[x] Scenario 2: Multiple models on same dataset - PASSED")
```

---

## SCENARIO 3: Data Version Update

### Workflow
```bash
# Train v4 with SCALED data (v2.0)
vcm train \
 --model-name "iris_classifier_v4" \
 --dataset "data/iris_train_v2.0.csv" \
 --script training_scripts/train_model_v1.py \
 --metrics metrics.json \
 --params n_estimators=10 max_depth=5 random_state=42

# Now we have:
# - Models v1-v3: trained on iris_train_v1.0.csv
# - Model v4: trained on iris_train_v2.0.csv (scaled)
```

### Test: Compare Across Data Versions

```python
def test_scenario_3_data_version_impact():
 """Verify impact of data version on model performance"""
 
 # Models on v1.0
 v1_models = db.query_by_dataset_version('data/iris_train_v1.0.csv')
 best_v1 = max(v1_models, key=lambda m: m['metrics']['accuracy'])
 
 # Model on v2.0
 v2_models = db.query_by_dataset_version('data/iris_train_v2.0.csv')
 best_v2 = max(v2_models, key=lambda m: m['metrics']['accuracy'])
 
 print(f"\n Data Version Impact Analysis:")
 print(f"Data v1.0 (raw): Best accuracy = {best_v1['metrics']['accuracy']:.4f} ({best_v1['model_name']})")
 print(f"Data v2.0 (scaled): Best accuracy = {best_v2['metrics']['accuracy']:.4f} ({best_v2['model_name']})")
 print(f"Impact: {(best_v2['metrics']['accuracy'] - best_v1['metrics']['accuracy']) / best_v1['metrics']['accuracy'] * 100:+.2f}%")
 
 # Verify metadata shows different datasets
 assert best_v1['data']['dvc_files'][0]['dvc_hash'] != best_v2['data']['dvc_files'][0]['dvc_hash']
 
 print("[x] Scenario 3: Data version impact - PASSED")
```

---

## SCENARIO 4: Code Changes Impact

### Workflow
```bash
# Update training script: new preprocessing
# (Modify training_scripts/train_model_v1.py)
git add training_scripts/train_model_v1.py
git commit -m "Add feature scaling in training pipeline"

# Train new model with updated code
vcm train \
 --model-name "iris_classifier_v5" \
 --dataset "data/iris_train_v1.0.csv" \
 --script training_scripts/train_model_v1.py \
 --metrics metrics.json \
 --params n_estimators=10 max_depth=5 random_state=42
```

### Test: Track Code Changes

```python
def test_scenario_4_code_changes_impact():
 """Verify VCM tracks which code version trained each model"""
 
 v1_model = db.get_model_by_name('iris_classifier_v1')
 v5_model = db.get_model_by_name('iris_classifier_v5')
 
 # Different commits
 assert v1_model['code']['git_commit'] != v5_model['code']['git_commit']
 
 # Can see what changed
 diff = get_git_diff(v1_model['code']['git_commit'], v5_model['code']['git_commit'])
 assert 'training_scripts/train_model_v1.py' in diff['files_changed']
 
 print(f"\n Code Evolution:")
 print(f"Model v1: Commit {v1_model['code']['git_commit'][:8]} (original)")
 print(f"Model v5: Commit {v5_model['code']['git_commit'][:8]} (with preprocessing)")
 print(f"Code diff: {diff}")
 
 print("[x] Scenario 4: Code changes tracking - PASSED")
```

---

## SCENARIO 5: Full Lineage Query (The Power of VCM)

### Workflow
```bash
# After all above training, user wants: "Show me all models and their lineage"
vcm analysis --report full_lineage
```

### Expected Output
```
VCM Full Lineage Report
========================

Dataset: data/iris_train_v1.0.csv (raw, 80 samples)
 └─ Model: iris_classifier_v1 (Acc: 100.0%) | Code: f5a9d3e | Params: n_est=10, depth=5
 └─ Model: iris_classifier_v2 (Acc: 98.5%) | Code: f5a9d3e | Params: n_est=20, depth=10
 └─ Model: iris_classifier_v3 (Acc: 99.2%) | Code: f5a9d3e | Params: n_est=50, depth=15
 └─ Model: iris_classifier_v5 (Acc: 100.0%)| Code: a7b2c4f | Params: n_est=10, depth=5 [NEW CODE]

Dataset: data/iris_train_v2.0.csv (scaled, 80 samples)
 └─ Model: iris_classifier_v4 (Acc: 99.8%) | Code: f5a9d3e | Params: n_est=10, depth=5

Analysis:
 Best Overall: iris_classifier_v1 (100.0% accuracy)
 Data Impact: Scaling reduced accuracy by 0.2% (v4 vs v1)
 Code Impact: New preprocessing in v5 maintains accuracy with different data version
 Recommendation: Use iris_classifier_v1 for production (raw data, n_est=10)
```

### Test: Comprehensive Analysis Query

```python
def test_scenario_5_full_lineage_analysis():
 """Verify VCM can generate comprehensive lineage reports"""
 
 report = vcm_cli(['analysis', '--report', 'full_lineage'])
 
 # Parse report
 assert 'Dataset: data/iris_train_v1.0.csv' in report
 assert 'Dataset: data/iris_train_v2.0.csv' in report
 assert 'Model: iris_classifier_v1' in report
 assert 'Best Overall: iris_classifier_v1' in report
 
 # Verify accuracy of insights
 best_model = 'iris_classifier_v1'
 assert best_model in report
 
 # Check recommendations
 assert 'Recommendation:' in report
 
 print(f"\n{report}")
 print("[x] Scenario 5: Full lineage analysis - PASSED")
```

---

## SCENARIO 6: Developer Troubleshooting (Real Use Case)

### Problem Statement
```
Developer Alice: "My model used to have 95% accuracy, now it's 92%. 
What changed? Was it the data or my code?"
```

### VCM Solution
```bash
# Find the old good model
vcm models --best --accuracy-range 0.94 0.96

# Output: iris_classifier_v2 (94.2%)

# Get full context
vcm lineage iris_classifier_v2.pkl

# Compare with current model
vcm compare iris_classifier_v2.pkl iris_classifier_v3.pkl

# Detailed analysis
vcm analysis --compare v2 v3 --show-impact
```

### Test: Troubleshooting Workflow

```python
def test_scenario_6_developer_troubleshooting():
 """Verify VCM helps developer find root cause of model degradation"""
 
 # Step 1: Find previously good model
 good_models = db.query_by_accuracy_range(min=0.94, max=0.96)
 assert len(good_models) > 0, "Should find previously good models"
 
 model_v2 = good_models[0]
 model_v3 = db.get_model_by_name('iris_classifier_v3')
 
 # Step 2: Detailed comparison
 comparison = {
 'metrics_delta': {
 'accuracy': model_v3['metrics']['accuracy'] - model_v2['metrics']['accuracy'],
 'precision': model_v3['metrics']['precision'] - model_v2['metrics']['precision']
 },
 'data_changed': model_v2['data']['dvc_files'][0]['dvc_hash'] != model_v3['data']['dvc_files'][0]['dvc_hash'],
 'code_changed': model_v2['code']['git_commit'] != model_v3['code']['git_commit'],
 'params_changed': model_v2['hyperparameters'] != model_v3['hyperparameters']
 }
 
 # Step 3: Root cause analysis
 if comparison['data_changed'] and not comparison['code_changed']:
 root_cause = "DATA"
 elif comparison['code_changed'] and not comparison['data_changed']:
 root_cause = "CODE"
 elif comparison['params_changed']:
 root_cause = "HYPERPARAMETERS"
 else:
 root_cause = "UNKNOWN"
 
 print(f"\n Troubleshooting Analysis:")
 print(f"Accuracy delta: {comparison['metrics_delta']['accuracy']:+.2%}")
 print(f"Data changed: {comparison['data_changed']}")
 print(f"Code changed: {comparison['code_changed']}")
 print(f"Params changed: {comparison['params_changed']}")
 print(f"Root cause: {root_cause}")
 
 assert root_cause != "UNKNOWN", "Should identify root cause"
 print("[x] Scenario 6: Developer troubleshooting - PASSED")
```

---

## SCENARIO 7: Model Reproducibility

### Workflow
```bash
# 2 weeks later, DevOps asks: "Can you rebuild model v2 exactly?"
vcm reproduce iris_classifier_v2.pkl

# VCM should:
# 1. Checkout git commit from metadata
# 2. Pull exact DVC dataset version
# 3. Use exact same hyperparameters
# 4. Run training script
# 5. Verify output matches original
```

### Test: Perfect Reproducibility

```python
def test_scenario_7_reproducibility():
 """Verify models can be reproduced exactly"""
 
 original_model = load_pickle('models/iris_classifier_v2.pkl')
 original_metrics = load_json('models/iris_classifier_v2.pkl.vcm.json')['metrics']
 
 # Reproduce
 reproduced_model, reproduced_metrics = vcm_reproduce('iris_classifier_v2.pkl')
 
 # Verify
 from sklearn.metrics import accuracy_score
 assert accuracy_score(
 original_model.predict(X_test),
 reproduced_model.predict(X_test)
 ) == 1.0, "Reproduced model should be identical"
 
 for metric in original_metrics:
 assert abs(
 original_metrics[metric] - reproduced_metrics[metric]
 ) < 1e-6, f"Metric {metric} doesn't match"
 
 print("[x] Scenario 7: Perfect reproducibility - PASSED")
```

---

## SCENARIO 8: Production Audit Trail

### Workflow
```bash
# DevOps needs: "Which model is running in production? When was it trained?"
vcm audit --environment production

# Output should show:
# - Model in production
# - Training date
# - Who trained it
# - Performance metrics
# - Git commit
# - Data version
```

### Test: Audit Trail

```python
def test_scenario_8_production_audit():
 """Verify audit trail for production deployment"""
 
 # Mark model as production
 vcm deploy iris_classifier_v1.pkl --environment production
 
 # Later, audit
 audit_log = vcm_audit(environment='production')
 
 assert audit_log['model_name'] == 'iris_classifier_v1'
 assert 'deployment_timestamp' in audit_log
 assert 'trained_by' in audit_log
 assert 'git_commit' in audit_log
 
 print(f"\n Production Audit Trail:")
 print(f"Model: {audit_log['model_name']}")
 print(f"Deployed: {audit_log['deployment_timestamp']}")
 print(f"Trained by: {audit_log['trained_by']}")
 print(f"Code: {audit_log['git_commit']}")
 print("[x] Scenario 8: Production audit trail - PASSED")
```

---

## COMPREHENSIVE TEST SUITE EXECUTION

```bash
# Run all real project tests
pytest tests/advanced_scenarios/ -v --tb=short

# Expected output:
# test_scenario_1_single_model_training PASSED [10%]
# test_scenario_2_multiple_models_same_dataset PASSED [20%]
# test_scenario_3_data_version_impact PASSED [30%]
# test_scenario_4_code_changes_impact PASSED [40%]
# test_scenario_5_full_lineage_analysis PASSED [50%]
# test_scenario_6_developer_troubleshooting PASSED [60%]
# test_scenario_7_reproducibility PASSED [70%]
# test_scenario_8_production_audit_trail PASSED [80%]

# ====== 8 passed in 45.23s ======
# [x] All real-world scenarios validated
```

---

## VALIDATION CHECKLIST

- [ ] Scenario 1: Single model captures all metadata
- [ ] Scenario 2: Query returns multiple models correctly
- [ ] Scenario 3: Data version differences tracked
- [ ] Scenario 4: Code changes tracked
- [ ] Scenario 5: Lineage analysis complete and accurate
- [ ] Scenario 6: Root cause analysis works
- [ ] Scenario 7: Models reproducible to machine precision
- [ ] Scenario 8: Audit trail complete

---

## END OF ADVANCED TESTING

**Run with:** `pytest tests/advanced_scenarios/ -v`
