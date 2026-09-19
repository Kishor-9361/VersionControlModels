# VCM Phase 2 - Session Tracking & Activity Logging

**Status:** Previously discussed but NOT in MVP - Adding NOW for comprehensive testing 
**Purpose:** Auto-capture everything developer does during training session 
**Why Important:** Solves original pain point: "lost most data about what I did"

---

## THE MISSING FEATURE (Root Cause Analysis)

### What You Said Initially
> "developers may failed to log everything they need like model performance, terminal outputs what they did in a particular day or session kinda everything for a developer"

### What We Missed
 Terminal output logging 
 Session-based grouping 
 Developer activity timeline 
 Script execution logging 
 Git commit history during session 

### Impact
Without this, if developer trains 3 models in one day but forgets which was which, we can't track:
- What terminal commands were run
- What intermediate outputs were produced
- What experiment iterations happened
- Why specific decisions were made
- Entire session context

---

## SOLUTION: Session Tracking System

### Core Concept

```
Session = Atomic time window during which developer trains models

Session captures:
├── Terminal output (stdout, stderr)
├── All git commits in time window
├── All model training runs
├── All model metrics
├── Developer annotations ("trying new preprocessing")
├── Timestamps of key events
└── Session summary
```

### Session Structure

```python
@dataclass
class Session:
 session_id: str # UUID
 session_name: str # "Tuesday morning experiments"
 start_time: datetime
 end_time: datetime
 user: str # alice
 branch: str # main
 initial_commit: str # git commit at start
 final_commit: str # git commit at end
 
 # Activity capture
 terminal_log: str # All output
 models_trained: List[ModelInfo] # All models in session
 commits_made: List[str] # All git commits
 annotations: List[Annotation] # User notes
 
 # Summary
 total_duration: timedelta
 models_count: int
 best_model: str # Best accuracy in session
 best_accuracy: float

@dataclass
class Annotation:
 timestamp: datetime
 text: str # "Trying feature engineering"
 model_related: Optional[str] # "iris_classifier_v3"
```

---

## FEATURE: Auto Session Tracking

### Implementation Approach

#### Mode 1: Automatic Background Daemon
```bash
# Start background session tracker
vcm session start --name "Tuesday morning training"

# Developer does their work normally:
python train_model_v1.py
python train_model_v2.py
vcm train --model-name v3 ...

# Daemon captures everything:
# - Terminal I/O
# - Git changes
# - DVC changes
# - VCM commands

# End session
vcm session end

# Automatic session created with all context
```

#### Mode 2: Manual Session Context Manager
```python
from vcm import SessionTracker

with SessionTracker("morning experiments") as session:
 # Everything here is tracked
 
 # Train model 1
 model1 = train(X_train, y_train)
 session.log_model(model1, "v1", metrics)
 
 # Experiment with preprocessing
 session.annotate("Trying new feature scaling")
 
 # Train model 2
 model2 = train_with_scaling(X_train, y_train)
 session.log_model(model2, "v2", metrics)
 
# Session automatically saved with all context
```

#### Mode 3: Retrospective Session (After the fact)
```bash
# Developer realizes they should have tracked this
vcm session create-retrospective \
 --name "Last Friday training" \
 --start "2024-01-12T09:00:00" \
 --end "2024-01-12T17:00:00"
 
# VCM reconstructs from:
# - Git log in time range
# - Model files created in time range
# - DVC changes in time range
```

---

## TERMINAL OUTPUT LOGGING (With Privacy)

### Secure Logging (NO credential leakage)

```yaml
# .vcmconfig.yaml - Session logging config
session_logging:
 enabled: true
 capture_terminal: true
 
 # Privacy protection
 mask_patterns:
 - ".*password.*"
 - ".*API_KEY.*"
 - ".*SECRET.*"
 - ".*token.*"
 - ".*github_token.*"
 
 # Exclude patterns
 exclude_patterns:
 - ".*npm install.*" # Too verbose
 - ".*pip install.*" # Too verbose
 - ".*/bin/.*" # System paths
 
 encryption:
 enabled: true
 algorithm: "AES-256" # Encrypt at rest
 
 retention_days: 90 # Auto-delete old logs
```

### What Gets Logged

```
[x] Model training output:
 "Epoch 1/50: loss=0.234, acc=0.92"
 "Model saved to models/v1.pkl"

[x] Git operations:
 "git add data/train.csv"
 "git commit -m 'Add new features'"

[x] DVC operations:
 "dvc add models/v1.pkl"
 "dvc push"

[x] Python script output:
 "Data loaded: 1000 samples"
 "Feature engineering: 45 -> 52 features"

[FAIL] Sensitive data (MASKED):
 "export API_KEY=***MASKED***"
 "password: ***MASKED***"

[FAIL] Noise (EXCLUDED):
 "pip installing packages..." (too verbose)
```

---

## SESSION QUERIES & ANALYSIS

### Find Models from Session
```bash
# Show all models trained on Tuesday morning
vcm session list-models "Tuesday morning training"

# Output:
# Session: Tuesday morning training
# Duration: 2h 45m (09:00 - 11:45)
# User: alice
# Models trained: 5
# ├── iris_classifier_v1 (Acc: 91.2%) | 09:15
# ├── iris_classifier_v2 (Acc: 92.8%) | 09:45
# ├── iris_classifier_v3 (Acc: 93.1%) | 10:12 [BEST]
# ├── iris_classifier_v4 (Acc: 91.5%) | 10:45
# └── iris_classifier_v5 (Acc: 92.1%) | 11:15
# # Session notes:
# - 09:30: "Trying different random seeds"
# - 10:15: "Implemented feature scaling"
# - 11:00: "Back to basic approach"
```

### Session Terminal Log
```bash
# View what happened during session
vcm session logs "Tuesday morning training" --format text

# Output:
# ===== Session: Tuesday morning training =====
# Start: 2024-01-15 09:00:00
# User: alice on ml-workstation-1
# Branch: main
# ─────────────────────────────────────────────
# 09:15:30 | python train.py --lr 0.001
# 09:15:45 | Epoch 1/50: loss=0.456, val_acc=0.85
# 09:16:12 | Epoch 10/50: loss=0.234, val_acc=0.91
# 09:16:45 | Model saved: models/iris_classifier_v1.pkl
# 09:16:50 | Accuracy: 0.912
# ─────────────────────────────────────────────
# 09:30:15 | User note: "Trying different random seeds"
# 09:30:16 | python train.py --lr 0.001 --seed 123
# ...
# 11:45:00 | Session ended
# ─────────────────────────────────────────────
# Total models: 5 | Best accuracy: 0.931
```

### Developer Context Reconstruction
```bash
# Developer asks: "Why is v3 better than v1?"
vcm session explain-improvement "Tuesday morning training" v1 v3

# Output:
# Comparing iris_classifier_v1 vs iris_classifier_v3
# ──────────────────────────────────────────────────
# Time difference: 57 minutes
# Between v1 and v3 in session log:
# # 10:12:00 | Code changes committed:
# - Added feature scaling (preprocessing.py)
# - Updated hyperparameters
# # 10:15:30 | User annotation: "Implemented feature scaling"
# # Differences:
# • Code: preprocessing.py added StandardScaler
# • Hyperparameters: learning_rate 0.001 -> 0.0005
# • Data: No change (same dataset)
# # Conclusion: [x] Feature scaling + tuned hyperparameters
# Accuracy improvement: +1.9% (91.2% -> 93.1%)
```

---

## SESSION COMPARISON

### Compare Two Sessions
```bash
vcm session compare "Tuesday morning" "Wednesday morning"

# Output:
# Session Comparison: Tuesday vs Wednesday
# ═════════════════════════════════════════
# # Metrics:
# Tuesday: 5 models, best=93.1%, 2h 45m
# Wednesday: 3 models, best=92.8%, 1h 30m
# # Approach:
# Tuesday: Feature engineering focus
# Wednesday: Hyperparameter tuning focus
# # Result:
# Tuesday better by 0.3%
# Tuesday approach more fruitful
# # Recommendation:
# Continue Tuesday's feature engineering approach
```

---

## INTEGRATION WITH MODEL METADATA

### Extended Model Metadata with Session

```json
{
 "model_name": "iris_classifier_v3",
 "metrics": {"accuracy": 0.931},
 
 // NEW: Session context
 "session": {
 "session_id": "sess_abc123",
 "session_name": "Tuesday morning training",
 "session_start": "2024-01-15T09:00:00Z",
 "session_end": "2024-01-15T11:45:00Z",
 "position_in_session": 3,
 "previous_model_in_session": "iris_classifier_v2",
 "next_model_in_session": "iris_classifier_v4",
 "session_best_model": "iris_classifier_v3"
 },
 
 // NEW: Annotations in session
 "session_annotations": [
 {
 "timestamp": "2024-01-15T10:15:30Z",
 "text": "Implemented feature scaling"
 }
 ],
 
 // NEW: What changed since previous model in session
 "changes_from_previous": {
 "code": {
 "files_changed": ["preprocessing.py"],
 "git_commit_range": "abc123..def456"
 },
 "hyperparameters": {
 "learning_rate": "0.001 -> 0.0005",
 "batch_size": "unchanged"
 },
 "data": "unchanged"
 }
}
```

---

## TESTING SESSION TRACKING

### Unit Tests for Session

```python
# tests/unit/test_session.py

def test_session_creation():
 """Create session and track models"""
 session = SessionTracker("test_session")
 session.start()
 
 assert session.session_id is not None
 assert session.status == "active"
 assert session.start_time is not None

def test_session_terminal_logging():
 """Capture terminal output"""
 with SessionTracker("test") as session:
 print("Training model...")
 import subprocess
 subprocess.run(['echo', 'Model training complete'])
 
 logs = session.get_terminal_log()
 assert "Training model" in logs
 assert "Model training complete" in logs

def test_session_annotation():
 """Add human annotations"""
 with SessionTracker("test") as session:
 session.annotate("Trying new preprocessing")
 
 annotations = session.get_annotations()
 assert len(annotations) == 1
 assert "preprocessing" in annotations[0].text

def test_session_mask_secrets():
 """Verify secrets are masked"""
 with SessionTracker("test") as session:
 print("export API_KEY=secret123456")
 
 logs = session.get_terminal_log()
 assert "secret123456" not in logs
 assert "***MASKED***" in logs

def test_session_model_grouping():
 """All models in session are linked"""
 with SessionTracker("test") as session:
 session.log_model(model1, "v1", metrics1)
 session.log_model(model2, "v2", metrics2)
 
 models = session.get_models()
 assert len(models) == 2
 assert models[0].next_model == models[1]
 assert models[1].previous_model == models[0]

def test_session_git_tracking():
 """Capture git commits in session"""
 session = SessionTracker("test")
 session.start()
 
 # Make a commit
 os.system("git add . && git commit -m 'Test'")
 
 session.end()
 
 commits = session.get_commits()
 assert len(commits) >= 1
 assert "Test" in commits[0].message
```

### Integration Tests

```python
# tests/integration/test_session_integration.py

def test_session_model_linkage():
 """Verify models know their session context"""
 session = SessionTracker("integration_test")
 
 with session:
 model_v1 = train_model(data, "v1")
 session.log_model(model_v1, "v1", metrics)
 
 model_v2 = train_model(data, "v2") 
 session.log_model(model_v2, "v2", metrics)
 
 # Load model and check session
 loaded_metadata = load_metadata("models/model_v2.pkl.vcm.json")
 assert loaded_metadata['session']['session_name'] == "integration_test"
 assert loaded_metadata['session']['previous_model'] == "model_v1"

def test_session_retrospective():
 """Reconstruct session from git history"""
 # Create some commits
 for i in range(3):
 create_model(f"model_v{i}")
 os.system(f"git add . && git commit -m 'Model {i}'")
 
 # Retrospectively create session
 session = SessionTracker.create_retrospective(
 name="past_session",
 start=datetime(2024, 1, 15, 9, 0),
 end=datetime(2024, 1, 15, 12, 0)
 )
 
 # Should find all models
 models = session.get_models()
 assert len(models) == 3

def test_session_comparison():
 """Compare two sessions"""
 session1 = create_session_with_5_models()
 session2 = create_session_with_3_models()
 
 comparison = SessionComparator.compare(session1, session2)
 
 assert comparison['models_count']['s1'] == 5
 assert comparison['models_count']['s2'] == 3
 assert comparison['best_accuracy']['s1'] > comparison['best_accuracy']['s2']
```

---

## CLI COMMANDS FOR SESSIONS

### New Commands

```bash
vcm session start <name> # Start new session
vcm session end # End current session
vcm session list # List all sessions
vcm session info <session_name> # Show session details
vcm session logs <session_name> # View terminal logs
vcm session models <session_name> # List models in session
vcm session annotate <text> # Add note to session
vcm session compare <session1> <session2> # Compare sessions
vcm session create-retrospective # Build session from history
vcm session export <session_name> --format {json|html|csv}
```

### Example: Full Session Workflow

```bash
# Start session
$ vcm session start "Testing feature engineering"
[x] Session started: sess_abc123
 Session name: Testing feature engineering
 Start time: 2024-01-15 14:00:00
 Use 'vcm session end' when finished

# Do some work...
$ python train_v1.py
$ vcm train --model-name v1 --dataset data/ --script train_v1.py --metrics metrics.json

# Add annotation
$ vcm session annotate "Added polynomial features"
[x] Annotation recorded at 14:15:32

# Continue training...
$ python train_v2.py
$ vcm train --model-name v2 --dataset data/ --script train_v2.py --metrics metrics.json

# End session
$ vcm session end
[x] Session ended
 Duration: 45 minutes
 Models trained: 2
 Best model: v2 (accuracy: 94.2%)
 Terminal log saved
 Session complete: sess_abc123

# Later, review session
$ vcm session info "Testing feature engineering"
Session: Testing feature engineering
├── ID: sess_abc123
├── Duration: 45 minutes
├── User: alice
├── Models: 2 (best: v2, 94.2%)
├── Commits: 2
├── Annotations: 1
│ └── "Added polynomial features"
└── Terminal log: 245 lines captured

# View what happened
$ vcm session logs "Testing feature engineering"
[Full terminal output with timestamps]

# Export session report
$ vcm session export "Testing feature engineering" --format html
[x] Exported to: sessions/Testing_feature_engineering.html
 (Rich HTML report with all context)
```

---

## DATABASE SCHEMA UPDATE

### New Tables for Sessions

```sql
CREATE TABLE sessions (
 id INTEGER PRIMARY KEY,
 session_id TEXT UNIQUE NOT NULL,
 session_name TEXT NOT NULL,
 user TEXT NOT NULL,
 start_time DATETIME NOT NULL,
 end_time DATETIME,
 branch TEXT,
 initial_commit TEXT,
 final_commit TEXT,
 total_duration_seconds INTEGER,
 models_count INTEGER,
 best_model TEXT,
 best_accuracy REAL,
 terminal_log TEXT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE session_annotations (
 id INTEGER PRIMARY KEY,
 session_id TEXT NOT NULL,
 timestamp DATETIME NOT NULL,
 text TEXT NOT NULL,
 model_related TEXT,
 FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE TABLE session_models (
 id INTEGER PRIMARY KEY,
 session_id TEXT NOT NULL,
 model_id INTEGER NOT NULL,
 position_in_session INTEGER,
 FOREIGN KEY(session_id) REFERENCES sessions(session_id),
 FOREIGN KEY(model_id) REFERENCES models(id)
);
```

---

## WHY THIS MATTERS

### Before (Your Original Problem)
```
Developer trained 5 models in a day:
"Which one was best? What was different? What did I do?"
[FAIL] Lost information
[FAIL] Can't reproduce experiments
[FAIL] Can't find good models
[FAIL] Decision-making is fuzzy
```

### After (With Session Tracking)
```
Developer trained 5 models in a day:
"Show me my Tuesday session"
[x] See all models in sequence
[x] See what changed between each
[x] See terminal log of exactly what happened
[x] See annotations ("tried feature X")
[x] Compare to other sessions
[x] Full reproducibility
[x] Clear decision trail
```

---

## IMPLEMENTATION ROADMAP FOR AGENT

### Phase 2.1: Core Session Tracking (Week 1)
- [ ] SessionTracker class
- [ ] Database tables
- [ ] Terminal logging (non-sensitive)
- [ ] Basic session operations

### Phase 2.2: Advanced Features (Week 2)
- [ ] Secret masking
- [ ] Git integration
- [ ] Session comparison
- [ ] Retrospective sessions

### Phase 2.3: CLI Commands (Week 3)
- [ ] All session commands
- [ ] Report generation
- [ ] Export formats

### Phase 2.4: Testing & Integration (Week 4)
- [ ] Unit tests for sessions
- [ ] Integration tests
- [ ] E2E with real workflows

---

## END OF SESSION TRACKING SPEC

**This was the missing piece - now we have:**
[x] Model metadata capture (Phase 1 - DONE)
[x] Session-based tracking (Phase 2 - THIS DOCUMENT)
[x] Complete developer activity audit trail

**Together = Solves original pain point completely**
