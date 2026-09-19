# VCM (Version Control Models) - MVP Specification

**Project:** Model DNA Version Control Platform 
**Version:** 1.0.0-MVP 
**Status:** Ready for Agent Development 
**Target Launch:** 4 weeks 

---

## 1. MVP SCOPE (TIGHT - NO FEATURE CREEP)

### [x] IN SCOPE

#### 1.1 Core Feature: Model Metadata Capture
- **What:** When user trains and saves a model, automatically capture:
 - Git commit hash (current HEAD)
 - DVC tracked files & their hashes
 - Training metrics (from JSON file or dictionary)
 - Timestamp & user info
 - Hyperparameters (if provided)
 - Environment info (Python version, key libraries)

#### 1.2 Storage Layer
- **What:** 
 - Store metadata as `.vcm.json` files (attached to models)
 - Index metadata in SQLite database for querying
 - Keep it portable: JSON serializable, no custom binary formats

#### 1.3 CLI Commands (MVP Set)
```
vcm init # Initialize in project
vcm train <args> # Wrap training + auto-capture
vcm models [filters] # List all tracked models
vcm lineage <model.pkl> # Show full lineage
vcm compare <model1> <model2> # Compare two models
vcm info <model.pkl> # Show model metadata
vcm export <model.pkl> # Export metadata
```

#### 1.4 Integration (Minimal, Proven)
- **Git:** Get current commit via GitPython
- **DVC:** Query dvc.api for tracked file versions
- **Metrics:** Read from JSON files (user provides path)

### [FAIL] OUT OF SCOPE (Phase 2+)

- Model serving/deployment
- Web UI (CLI only for MVP)
- MLflow integration
- Docker registry tracking
- Auto-rollback/reproducibility
- Real-time monitoring/logging
- Weights & Biases sync
- Model search/analytics
- Collaborative features
- Cloud storage (local only for MVP)

---

## 2. ARCHITECTURE DECISIONS

### 2.1 Why SQLite + JSON?
- **SQLite:** Lightweight, zero setup, file-based (portable), queryable
- **JSON:** Human-readable, versionable, doesn't lock in binary formats
- **Tradeoff:** NOT for enterprise (10,000+ models); upgrade to PostgreSQL later

### 2.2 File Structure
```
my_ml_project/
├── .vcmconfig.yaml # VCM config
├── .vcm/ # VCM metadata directory
│ └── vcm.db # SQLite index
├── models/
│ ├── model_v1.pkl
│ ├── model_v1.pkl.vcm.json # Metadata attached to model
│ ├── model_v2.pkl
│ └── model_v2.pkl.vcm.json
├── data/ # DVC tracked
├── train.py
└── .git/
```

### 2.3 Metadata Schema (JSON Format)
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

### 2.4 Database Schema (SQLite)
```sql
-- Models table
CREATE TABLE models (
 id INTEGER PRIMARY KEY,
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
 metadata_json TEXT -- Full metadata as JSON
);

-- Index for fast queries
CREATE INDEX idx_model_name ON models(model_name);
CREATE INDEX idx_accuracy ON models(accuracy DESC);
CREATE INDEX idx_git_commit ON models(git_commit);
CREATE INDEX idx_dataset_hash ON models(dataset_hash);
```

---

## 3. DATA FLOW & INTERACTION PATTERNS

### 3.1 Training Flow (vcm train)
```
User calls: vcm train --model-name "classifier_v2" --dataset "data/train_v2.1" --script train.py --metrics metrics.json

VCM:
 1. Capture Git state: git_commit = current HEAD
 2. Capture DVC state: dvc_files = get_dvc_tracked_files()
 3. Capture environment: python_version, libraries
 4. Run user's train.py
 5. Wait for model file output
 6. Read metrics from metrics.json
 7. Create metadata JSON
 8. Save as model_name.pkl.vcm.json
 9. Insert into SQLite
 10. Print: [x] Model tracked successfully
```

### 3.2 Query Flow (vcm models)
```
User calls: vcm models --dataset "data/train_v2.1" --best --limit 5

VCM:
 1. Query SQLite WHERE dataset_hash = "..." ORDER BY accuracy DESC LIMIT 5
 2. Fetch matching model metadata
 3. Display formatted table
```

### 3.3 Lineage Flow (vcm lineage)
```
User calls: vcm lineage models/emotion_classifier_v2.pkl

VCM:
 1. Find emotion_classifier_v2.pkl.vcm.json
 2. Read metadata from JSON
 3. Display formatted lineage tree
```

---

## 4. TECHNOLOGY STACK

| Layer | Tech | Why |
|-------|------|-----|
| **CLI** | Python (Click) | Fast, lightweight, excellent docs |
| **Core** | Python 3.9+ | User's ML environment |
| **Git Integration** | GitPython | Standard, reliable |
| **DVC Integration** | dvc.api | Official, maintained |
| **Database** | SQLite3 | Zero setup, file-based |
| **Testing** | pytest | Industry standard |
| **Packaging** | setuptools/pip | Standard Python |
| **Config** | PyYAML | Human-readable |

---

## 5. SUCCESS CRITERIA (MVP Definition of Done)

### [x] Functional Requirements
- [ ] `vcm init` works without errors
- [ ] `vcm train` captures all metadata correctly
- [ ] `vcm models` returns results in <100ms for <100 models
- [ ] `vcm lineage` displays correct Git + DVC info
- [ ] `vcm compare` shows diffs between two models
- [ ] All 6 commands work end-to-end with test data

### [x] Data Integrity
- [ ] Model metadata is immutable (write-once)
- [ ] No data loss on Git/DVC version changes
- [ ] Metadata survives model file deletion
- [ ] Database corruption recovery plan exists

### [x] Testing
- [ ] >80% code coverage
- [ ] All edge cases covered (see test spec)
- [ ] E2E test on real project scenario

### [x] Documentation
- [ ] README with quick start
- [ ] CLI help text for all commands
- [ ] Example workflow documented

### [x] Production-Readiness
- [ ] Error messages are actionable
- [ ] Graceful degradation (works even if DVC not installed)
- [ ] Version compatibility checked (Python 3.9+)
- [ ] No breaking changes planned for 6 months

---

## 6. CONSTRAINTS & ASSUMPTIONS

### Constraints
- **Team size:** Solo developer (you) + AI agent
- **Timeline:** 4 weeks
- **Infrastructure:** Laptop/workstation only (no cloud)
- **Users:** ML practitioners with Git + Python knowledge

### Assumptions
- Users have Git initialized in project
- Users have DVC installed (optional but recommended)
- Models saved as pickle files (can extend later)
- Metrics provided as JSON or dict (user responsibility to save)
- Training scripts are Python-based

---

## 7. HANDOFF TO AGENT

### What Agent Needs to Do
1. Implement according to this spec (no deviations)
2. Write tests FIRST (TDD)
3. Build incrementally (feature by feature)
4. Validate each step with provided test cases
5. Generate production-ready code (not prototype)

### What Agent Should NOT Do
- Add features not in scope
- Use complex frameworks (keep it simple)
- Optimize prematurely
- Skip error handling
- Ignore test coverage

### Agent Context Windows Strategy
- **Context 1:** Architecture review + core models
- **Context 2:** Git/DVC integration
- **Context 3:** CLI implementation
- **Context 4:** Database layer
- **Context 5:** Testing + validation

---

## 8. DEVELOPMENT PHASES (4 Weeks)

### Week 1: Foundation
- Setup project structure
- Implement core metadata model
- Git + DVC integration basic
- Test infrastructure

### Week 2: Core Commands
- Implement `vcm init`
- Implement `vcm train` wrapper
- Implement `vcm models` query
- Unit tests for all

### Week 3: Advanced Commands
- Implement `vcm lineage`
- Implement `vcm compare`
- Implement `vcm info`
- Integration tests

### Week 4: Polish & Testing
- E2E testing with real project
- Error handling review
- Documentation
- Performance validation

---

## END OF SPECIFICATION

**Next Step:** Follow TEST_CASES.md to validate implementation at each step.
