# VCM MVP - Agent Build Procedure

**Purpose:** Step-by-step guide for AI agent to build production-quality MVP  
**Duration:** 4 weeks (parallel execution possible)  
**Approach:** TDD-first, incremental, validated at each step  

---

## CRITICAL SUCCESS FACTORS FOR AGENT

### 1. Token Efficiency Strategy
**Problem:** Large codebase exceeds context windows  
**Solution:** Divide and conquer

**Phase-based context allocation:**
- **Phase 1:** Architecture + Core Models (30K tokens)
- **Phase 2:** Integrations (35K tokens)
- **Phase 3:** CLI (35K tokens)
- **Phase 4:** Testing + Polish (40K tokens)

**In each phase:**
- Focus on ONE module only
- Write and test complete module
- Generate complete source file
- Don't discuss unrelated code
- Clear context before next phase

### 2. Test-First Discipline
**Every module MUST follow:**
1. Write test cases (from test spec)
2. Write failing tests
3. Implement code to pass tests
4. Refactor for clarity
5. Run full test suite
6. Move to next module

### 3. Code Quality Standards
```
- No TODOs or FIXMEs
- All public functions documented
- Type hints on all functions
- Error handling comprehensive
- No commented-out code
```

---

## PHASE 1: FOUNDATION & CORE MODELS (Week 1)

### Objective
Establish solid architecture and core data models that everything else builds on.

### 1.1: Project Setup

**Task:** Initialize project structure

**Steps:**
```bash
mkdir vcm_project
cd vcm_project
git init
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install pytest pytest-cov GitPython pyyaml click

# Create directory structure
mkdir -p vcm/{models,integrations,db,utils,cli,tests/{unit,integration,cli,fixtures}}
mkdir -p docs examples
touch vcm/__init__.py
touch setup.py
touch README.md
touch .gitignore
```

**Validation:**
- [ ] Directory structure matches above
- [ ] venv activated
- [ ] All packages installed: `pip list | grep -E "pytest|GitPython|click|pyyaml"`
- [ ] Python version >= 3.9: `python --version`

---

### 1.2: Core Data Model - MetadataModel

**File:** `vcm/models/metadata.py`

**Agent Task:**
1. Read: `vcm_test_cases.md` → "PART 1: UNIT TESTS" → "Module 1: Metadata Model"
2. Write test file: `vcm/tests/unit/test_metadata.py` (all 5 tests from UT-1.1 to UT-1.5)
3. Write code to pass tests
4. Run: `pytest vcm/tests/unit/test_metadata.py -v`
5. Verify: All tests pass, coverage > 95%

**Required Implementation:**
```python
# vcm/models/metadata.py should contain:
- MetadataModel class (dataclass, frozen=True for immutability)
- Nested classes: CodeInfo, DataInfo, TrainingInfo, MetricsInfo, EnvironmentInfo
- Methods: to_dict(), to_json(), from_json()
- Validation: All required fields validated in __post_init__
- Type hints: Full typing module usage
```

**Example Structure (Reference Only):**
```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass(frozen=True)
class CodeInfo:
    git_commit: str
    git_branch: str
    git_url: Optional[str]

@dataclass(frozen=True)
class MetadataModel:
    model_name: str
    model_hash: str
    model_file: str
    metrics: Dict[str, float]
    code: CodeInfo
    # ... other nested objects
    
    def to_dict(self) -> Dict: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, json_str: str) -> 'MetadataModel': ...
```

**Deliverable:** 
- `vcm/models/metadata.py` (complete, tested, no TODOs)
- `vcm/tests/unit/test_metadata.py` (all 5 tests passing)
- Test report: `pytest vcm/tests/unit/test_metadata.py -v --tb=short`

**Checkpoint Validation:**
```bash
pytest vcm/tests/unit/test_metadata.py -v --cov=vcm.models.metadata --cov-report=term-missing
# Expected: 5/5 passed, coverage > 95%
```

---

### 1.3: Database Module - Initialization & Schema

**File:** `vcm/db/database.py`

**Agent Task:**
1. Read: Test spec → "PART 1" → "Module 4: Database Layer" (UT-4.1 to UT-4.6)
2. Write tests: `vcm/tests/unit/test_database.py`
3. Implement Database class
4. Run and pass all tests

**Required Implementation:**
```python
# vcm/db/database.py should provide:
class Database:
    def __init__(self, db_path: str = ".vcm/vcm.db")
    def init(self) -> None  # Create schema
    def insert_model(self, metadata: MetadataModel) -> int  # Returns ID
    def query_by_accuracy(self, min_acc: float = 0) -> List[MetadataModel]
    def query_by_dataset(self, dataset_hash: str) -> List[MetadataModel]
    def update_model(self, model_id: int, metadata: MetadataModel) -> bool
    def get_all_models(self) -> List[MetadataModel]
```

**Key Design Decisions:**
- Use SQLite3 (no ORM, pure SQL for control)
- Store metadata as JSON blob + indexed fields
- Tables: models (indexed fields), full schema in SCHEMA.md

**Checkpoint Validation:**
```bash
pytest vcm/tests/unit/test_database.py -v --cov=vcm.db --cov-report=term-missing
# Expected: 6/6 passed, coverage > 90%
```

---

### 1.4: Utilities - Environment & Metrics

**Files:** 
- `vcm/utils/environment.py`
- `vcm/utils/metrics_loader.py`

**Agent Task:**
1. Read: Test spec → "Module 5 & 6"
2. Write: `vcm/tests/unit/test_environment.py` and `test_metrics_loader.py`
3. Implement both modules
4. All tests pass

**Required Implementation:**
```python
# vcm/utils/environment.py
class EnvironmentCapture:
    @staticmethod
    def get_python_version() -> str
    @staticmethod
    def get_libraries() -> Dict[str, str]
    @staticmethod
    def get_system_info() -> Dict[str, str]
    @staticmethod
    def capture_all() -> Dict

# vcm/utils/metrics_loader.py
class MetricsLoader:
    @staticmethod
    def from_json_file(path: str) -> Dict[str, float]
    @staticmethod
    def from_dict(d: Dict) -> Dict[str, float]
```

**Checkpoint Validation:**
```bash
pytest vcm/tests/unit/test_environment.py vcm/tests/unit/test_metrics_loader.py -v --cov=vcm.utils
# Expected: All tests passing, coverage > 85%
```

---

### 1.5: Configuration & Project Init

**File:** `vcm/config.py`

**Agent Task:**
1. Design config structure (YAML-based)
2. Write loader/validator
3. Handle missing/invalid configs gracefully

**Required Implementation:**
```python
class VCMConfig:
    def __init__(self, config_path: str = ".vcmconfig.yaml")
    def load() -> VCMConfig
    def is_initialized() -> bool
    def get_enabled_integrations() -> List[str]
```

**Example `.vcmconfig.yaml`:**
```yaml
vcm:
  version: "1.0"
  database_path: ".vcm/vcm.db"
  
integrations:
  git:
    enabled: true
  dvc:
    enabled: true
  mlflow:
    enabled: false

auto_tracking:
  capture_environment: true
  capture_terminal: false
```

---

## PHASE 2: INTEGRATIONS (Week 1-2)

### Objective
Implement Git and DVC integrations to capture version information.

### 2.1: Git Integration

**File:** `vcm/integrations/git_client.py`

**Agent Task:**
1. Read: Test spec → "Module 2: Git Integration"
2. Write: `vcm/tests/unit/test_git_client.py`
3. Implement GitClient class
4. Handle all edge cases

**Required Implementation:**
```python
class GitClient:
    def __init__(self, repo_path: str = ".")
    def get_current_commit(self) -> str  # 40-char hash
    def get_current_branch(self) -> str
    def get_remote_url(self) -> Optional[str]
    def has_uncommitted_changes(self) -> bool
    
    # Custom exception
class GitNotInitializedError(Exception): pass
```

**Edge Cases to Handle:**
- Detached HEAD state
- No origin remote
- No commits yet (new repo)
- Submodules
- No .git directory

**Checkpoint Validation:**
```bash
pytest vcm/tests/unit/test_git_client.py -v --cov=vcm.integrations.git_client
# Expected: 5/5 tests passing
```

---

### 2.2: DVC Integration

**File:** `vcm/integrations/dvc_client.py`

**Agent Task:**
1. Read: Test spec → "Module 3: DVC Integration"
2. Write: `vcm/tests/unit/test_dvc_client.py`
3. Implement DVCClient
4. Graceful degradation when DVC not installed

**Required Implementation:**
```python
class DVCClient:
    def __init__(self, repo_path: str = ".")
    def is_initialized(self) -> bool
    def get_tracked_files(self) -> List[DVCFile]  # {path, hash, size}
    def get_file_hash(self, filepath: str) -> Optional[str]
    
class DVCFile:
    path: str
    hash: str
    size_bytes: int

class DVCNotInstalledWarning(Warning): pass
```

**Edge Cases:**
- DVC not installed
- Not a DVC project
- Corrupted .dvc files
- Remote storage not accessible

**Important:** If DVC not available, return empty list (no errors)

**Checkpoint Validation:**
```bash
pytest vcm/tests/unit/test_dvc_client.py -v --cov=vcm.integrations.dvc_client
# Expected: 4/4 tests passing
```

---

### 2.3: Integration Tests (Git + DVC + DB)

**File:** `vcm/tests/integration/test_git_dvc_db.py`

**Agent Task:**
1. Write integration tests (Part 2 of test spec)
2. Test all three components working together
3. Ensure no isolation issues

**Required Tests:**
- Test 1: Git info captured in metadata
- Test 2: DVC file hashes captured correctly
- Test 3: Database stores metadata accurately
- Test 4: File system + DB stay in sync
- Test 5: All components together

**Checkpoint Validation:**
```bash
pytest vcm/tests/integration/test_git_dvc_db.py -v
# Expected: 5/5 integration tests passing
```

---

## PHASE 3: CLI & TRAINING WRAPPER (Week 2-3)

### Objective
Build CLI commands and training wrapper to capture complete metadata during model training.

### 3.1: Model Tracker (Training Wrapper)

**File:** `vcm/trainer.py`

**Agent Task:**
1. Write `vcm/tests/unit/test_trainer.py`
2. Implement ModelTracker class
3. Support two usage modes: decorator and context manager

**Required Implementation:**
```python
class ModelTracker:
    def __init__(self, database: Database)
    
    # Mode 1: Decorator
    @ModelTracker.track(model_name="classifier_v1")
    def train_model(): ...
    
    # Mode 2: Context manager
    with ModelTracker().track(model_name="classifier_v1"):
        model = train()
        metrics = evaluate(model)
        model.save("model.pkl")
    
    # Mode 3: Manual
    tracker = ModelTracker()
    tracker.log_model(model_path, model_name, metrics)
```

**Flow:**
1. Capture Git commit
2. Capture DVC files
3. Capture environment
4. Run user code
5. Capture output model
6. Read metrics from file or dict
7. Create MetadataModel
8. Save .vcm.json file
9. Insert into database

**Checkpoint Validation:**
```bash
pytest vcm/tests/unit/test_trainer.py -v
# Expected: All tests passing
```

---

### 3.2: CLI Base Structure

**File:** `vcm/cli/main.py`

**Agent Task:**
1. Create CLI skeleton using Click library
2. Implement base command structure
3. Setup logging and error handling

**Required Implementation:**
```python
@click.group()
@click.version_option()
def cli():
    """VCM - Version Control Models"""
    pass

# Subcommands will be added in 3.3-3.8
@cli.command()
def init():
    """Initialize VCM in project"""
    pass
```

---

### 3.3: CLI Command - `vcm init`

**File:** `vcm/cli/commands.py` (add to this file)

**Agent Task:**
1. Write: `vcm/tests/cli/test_init.py` (from test spec CLI-1)
2. Implement `vcm init` command
3. Create .vcm/ directory
4. Initialize database
5. Create .vcmconfig.yaml

**Expected Behavior:**
```bash
$ cd my_project
$ vcm init
✅ VCM initialized successfully
   - Created .vcm/ directory
   - Initialized database
   - Created .vcmconfig.yaml
   
Use 'vcm train' to track models
```

**Checkpoint Validation:**
```bash
pytest vcm/tests/cli/test_init.py -v
# Expected: CLI test passing
```

---

### 3.4: CLI Command - `vcm train`

**File:** `vcm/cli/commands.py`

**Agent Task:**
1. Write: `vcm/tests/cli/test_train.py` (from test spec CLI-2, CLI-3)
2. Implement `vcm train` wrapper command
3. Support options: --model-name, --dataset, --script, --metrics, --params

**Expected Behavior:**
```bash
$ vcm train --model-name "classifier_v1" \
            --dataset "data/train.csv" \
            --script train.py \
            --metrics metrics.json \
            --params lr=0.001 epochs=50

Running training script: train.py ...
[Script output]
...training complete...

✅ Model tracked successfully
   Model: classifier_v1
   Accuracy: 0.942
   Git commit: abc123
   Dataset: data/train.csv
   Metadata: models/classifier_v1.pkl.vcm.json
```

**Implementation Strategy:**
1. Parse all CLI arguments
2. Create ModelTracker
3. Use context manager to wrap script execution
4. Capture output model file
5. Read metrics
6. Save metadata
7. Print summary

**Checkpoint Validation:**
```bash
pytest vcm/tests/cli/test_train.py -v
# Expected: Tests passing
```

---

### 3.5: CLI Command - `vcm models`

**File:** `vcm/cli/commands.py`

**Agent Task:**
1. Write: `vcm/tests/cli/test_models.py` (CLI-4, CLI-5, CLI-6)
2. Implement query and display logic
3. Support filters: --dataset, --best, --limit, --since

**Expected Behavior:**
```bash
$ vcm models --best --limit 3
┌─────────────────┬──────────┬─────────────┬──────────┐
│ Model Name      │ Accuracy │ Dataset     │ Git Commit
├─────────────────┼──────────┼─────────────┼──────────┤
│ classifier_v2   │ 94.2%    │ train_v2.1  │ abc123
│ classifier_v4   │ 94.0%    │ train_v2.1  │ def456
│ classifier_v1   │ 92.5%    │ train_v2.0  │ ghi789
└─────────────────┴──────────┴─────────────┴──────────┘

Total: 3 models found
```

**Implementation:**
- Query database with filters
- Format as table (use tabulate library)
- Support JSON output: --format json
- Support CSV export: --export file.csv

**Checkpoint Validation:**
```bash
pytest vcm/tests/cli/test_models.py -v
# Expected: All filter tests passing
```

---

### 3.6: CLI Command - `vcm lineage`

**File:** `vcm/cli/commands.py`

**Agent Task:**
1. Write: `vcm/tests/cli/test_lineage.py` (CLI-7)
2. Implement lineage display
3. Show formatted tree of model's full context

**Expected Behavior:**
```bash
$ vcm lineage models/classifier_v2.pkl

📦 Model: classifier_v2.pkl
├── 💾 Accuracy: 0.942
├── 🎯 Git Commit: abc123def456
│   ├── Branch: main
│   ├── URL: https://github.com/user/ml-project
│   └── Timestamp: 2024-01-15T10:45:00Z
├── 📊 Dataset Files:
│   ├── data/train_v2.1.csv (hash: xyz789...)
│   └── data/test_v2.1.csv (hash: qwe456...)
├── ⚙️ Hyperparameters:
│   ├── lr: 0.001
│   ├── epochs: 50
│   └── batch_size: 32
└── 👤 Trained by: alice (2024-01-15)
```

**Checkpoint Validation:**
```bash
pytest vcm/tests/cli/test_lineage.py -v
# Expected: Lineage display test passing
```

---

### 3.7: CLI Command - `vcm compare`

**File:** `vcm/cli/commands.py`

**Agent Task:**
1. Write: `vcm/tests/cli/test_compare.py` (CLI-8)
2. Implement model comparison

**Expected Behavior:**
```bash
$ vcm compare classifier_v1.pkl classifier_v2.pkl

Comparison: classifier_v1 vs classifier_v2
┌──────────────────┬──────────────┬──────────────┬─────────┐
│ Metric           │ v1           │ v2           │ Change  │
├──────────────────┼──────────────┼──────────────┼─────────┤
│ Accuracy         │ 91.5%        │ 94.2%        │ +2.7% ⬆ │
│ F1 Score         │ 90.2%        │ 92.8%        │ +2.6% ⬆ │
│ Dataset          │ train_v2.0   │ train_v2.1   │ Different
│ Git Commit       │ xyz123       │ abc456       │ Different
│ Learning Rate    │ 0.01         │ 0.001        │ 10x lower
│ Epochs           │ 30           │ 50           │ +20 epochs
└──────────────────┴──────────────┴──────────────┴─────────┘

📈 Model v2 is better:
   • 2.7% higher accuracy
   • Different dataset with more samples
   • Better hyperparameter tuning
```

**Checkpoint Validation:**
```bash
pytest vcm/tests/cli/test_compare.py -v
# Expected: Comparison test passing
```

---

### 3.8: CLI Command - `vcm info` & `vcm export`

**File:** `vcm/cli/commands.py`

**Agent Task:**
1. Write: `vcm/tests/cli/test_info.py` (CLI-9)
2. Write: `vcm/tests/cli/test_export.py` (CLI-10)
3. Implement both commands

**vcm info:** Display full JSON metadata formatted
**vcm export:** Save metadata to file

---

## PHASE 4: TESTING & POLISH (Week 3-4)

### 4.1: Error Handling Audit

**Task:** Implement all error cases from test spec Part 4

**Error Handling Tests:**
- EH-1: Git not initialized (graceful)
- EH-2: DVC not installed (graceful)
- EH-3: Model file not found (clear error)
- EH-4: Corrupted database (recovery)
- EH-5: Duplicate model name (auto-version)

**File:** `vcm/tests/error_handling/` (multiple test files)

**Checkpoint:** All error tests passing

---

### 4.2: End-to-End Testing

**Task:** Real project scenario testing

**File:** `vcm/tests/e2e/test_real_scenarios.py`

**Scenarios:**
1. Complete ML workflow (E2E-1)
2. Reproduce from saved metadata (E2E-2)
3. Multi-user scenario (E2E-3)

**Execution:**
```bash
pytest vcm/tests/e2e/ -v --tb=short
# Expected: All E2E tests passing
```

---

### 4.3: Performance Testing

**Task:** Validate performance requirements

**File:** `vcm/tests/performance/`

**Tests:**
- PERF-1: Database query < 200ms for 1000 models
- PERF-2: Metadata capture overhead < 2.5s

**Execution:**
```bash
pytest vcm/tests/performance/ -v
# Expected: All performance targets met
```

---

### 4.4: Code Quality & Coverage

**Task:** Comprehensive quality checks

**Checklist:**
```bash
# Run full test suite
pytest vcm/tests/ -v --cov=vcm --cov-report=html

# Expected output:
# ====== X passed in Y.XXs ======
# coverage: X%
# ✅ coverage > 80%

# Type checking
mypy vcm/ --strict
# Expected: No errors

# Linting
flake8 vcm/ --max-line-length=100
# Expected: No violations

# Security check
bandit -r vcm/
# Expected: No HIGH severity issues
```

---

### 4.5: Documentation

**Files to Create:**
- `README.md` - Quick start guide
- `ARCHITECTURE.md` - Design decisions
- `CONTRIBUTING.md` - Development guide
- `docs/CLI.md` - Command reference
- `docs/API.md` - Python API documentation

**Minimum Required:**
```markdown
# VCM - Version Control for ML Models

Quick Start:
1. pip install vcm-ml
2. cd your_ml_project
3. vcm init
4. vcm train --model-name v1 --dataset data/ --script train.py --metrics metrics.json
5. vcm models --best
```

---

## FINAL VALIDATION CHECKLIST

### Code Completeness
```
[ ] vcm/models/metadata.py - COMPLETE
[ ] vcm/models/__init__.py - COMPLETE
[ ] vcm/db/database.py - COMPLETE
[ ] vcm/db/__init__.py - COMPLETE
[ ] vcm/integrations/git_client.py - COMPLETE
[ ] vcm/integrations/dvc_client.py - COMPLETE
[ ] vcm/integrations/__init__.py - COMPLETE
[ ] vcm/utils/environment.py - COMPLETE
[ ] vcm/utils/metrics_loader.py - COMPLETE
[ ] vcm/utils/__init__.py - COMPLETE
[ ] vcm/trainer.py - COMPLETE
[ ] vcm/config.py - COMPLETE
[ ] vcm/cli/main.py - COMPLETE
[ ] vcm/cli/commands.py - COMPLETE
[ ] vcm/cli/__init__.py - COMPLETE
[ ] vcm/__init__.py - Package exports
[ ] setup.py - Installation config
```

### Test Completeness
```
[ ] Unit tests: 35+ tests, coverage > 80%
[ ] Integration tests: 5+ tests passing
[ ] CLI tests: 10+ commands tested
[ ] Error handling: 5+ error cases covered
[ ] E2E tests: 3+ real scenarios
[ ] Performance: All targets met
```

### Quality Gates
```
[ ] No TODOs or FIXMEs in code
[ ] All functions have type hints
[ ] All public functions documented
[ ] Linting score: 10/10
[ ] Type checking: 0 errors
[ ] Test coverage: >80%
[ ] All imports organized (isort)
```

### Documentation
```
[ ] README.md with quick start
[ ] ARCHITECTURE.md with design
[ ] CLI.md with all commands
[ ] Type hints on all functions
[ ] Docstrings on all classes/methods
```

---

## AGENT CONTEXT MANAGEMENT

### How to Handle Large Codebase (Token Limits)

**Strategy: Divide into contexts**

**Context Window 1: Architecture + Core**
- Load: Spec + Test Cases
- Write: metadata.py + database.py + tests
- Output: Complete modules
- Clear context

**Context Window 2: Integrations**
- Load: git_client tests
- Write: git_client.py + dvc_client.py + integration tests
- Output: Complete modules
- Clear context

**Context Window 3: CLI**
- Load: CLI tests
- Write: trainer.py + cli/commands.py + trainer tests
- Output: Complete modules
- Clear context

**Context Window 4: Final**
- Load: All created modules
- Write: Error handling + E2E tests + docs
- Quality checks
- Final validation

---

## QUICK REFERENCE: MODULE DEPENDENCIES

```
metadata.py (independent)
    ↓
database.py (depends on metadata.py)
    ↓
git_client.py (independent)
    ↓
dvc_client.py (independent)
    ↓
trainer.py (depends on metadata.py, database.py, git_client.py, dvc_client.py)
    ↓
cli/commands.py (depends on trainer.py, database.py)
```

**Build Order:** metadata.py → database.py → integrations → trainer.py → cli → tests

---

## EXECUTION SUMMARY FOR AGENT

**Your mission:**
1. Follow this procedure step by step
2. Complete one section per context window
3. Run all tests before moving forward
4. No shortcuts on testing
5. No features beyond spec
6. Deliver production-ready code

**Success = All tests passing + zero warnings + full documentation**

```bash
# Final validation command
python -m pytest vcm/ -v --cov=vcm --cov-report=html --tb=short && \
mypy vcm/ --strict && \
flake8 vcm/ --max-line-length=100
```

**Expected output:**
```
====== XXXX passed in XX.XXs ======
.mypy: ok
All OK (0 issues)
```

---

## END OF AGENT PROCEDURE

**Ready to start building?**

1. Print this document
2. Start with Phase 1.1: Project Setup
3. Follow each step sequentially
4. Validate at checkpoints
5. Move to next phase

Good luck! 🚀
