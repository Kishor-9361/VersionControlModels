# VCM Agent Execution Guide - Phase 2 & Advanced Testing

**Status:** Phase 1 Complete → Starting Phase 2 
**Objective:** Add session tracking + advanced testing validation 
**Timeline:** 2 weeks (Weeks 5-6) 
**Approach:** TDD-first, incremental, validated at checkpoints 

---

## CRITICAL CONTEXT

### What's Complete (Phase 1)
[x] Metadata model (frozen dataclass) 
[x] Git & DVC integrations 
[x] SQLite database with querying 
[x] CLI commands (init, train, models, lineage, compare, info, export) 
[x] 60+ unit tests passing 
[x] 85%+ code coverage 

### What We're Adding (Phase 2)
 **Session Tracking** (The missing feature):
 - Auto-capture terminal output
 - Group models by session
 - User annotations
 - Secret masking
 - Session comparison
 - HTML export reports

 **Advanced Scenario Testing** (Real ML project):
 - 8 real-world scenarios
 - Iris classification dataset
 - Production workflows
 - Troubleshooting patterns
 - Reproducibility validation

---

## DOCUMENT REFERENCE

### Your Reference Documents (Use These!)

1. **vcm_session_tracking_spec.md**
 - What session tracking is
 - Architecture decisions
 - Database schema updates
 - Implementation approach

2. **vcm_advanced_testing.md**
 - Real ML project scenarios
 - Test implementation
 - Expected outputs
 - Validation criteria

3. **vcm_cli_documentation.md**
 - Complete CLI reference
 - Examples for every command
 - Session commands
 - Real workflows

4. **vcm_testing_strategy.md**
 - Complete test pyramid
 - Week 5-6 schedule
 - Quality gates
 - Validation checklist

---

## PHASE 2: WEEK 1 (Session Tracking Core)

### Day 1-2: Session Model & Database

**Task:** Implement SessionTracker class and database schema

**Files to Create/Modify:**
```
vcm/models/session.py # NEW - Session dataclasses
vcm/db/database.py # UPDATE - Add session tables
vcm/tests/unit/test_session.py # NEW - Unit tests
```

**Implementation Checklist:**
```python
# SessionTracker class needed:
class SessionTracker:
 def __init__(self, session_name: str)
 def start(self) -> str # Returns session_id
 def end(self) -> None
 def log_model(self, model_meta: dict) -> None
 def annotate(self, text: str) -> None
 def get_terminal_log(self) -> str
 def get_models(self) -> List[Dict]
 def get_annotations(self) -> List[Annotation]
 def get_commits(self) -> List[str]
 def get_duration(self) -> timedelta
 def export_json(self) -> str
 def export_html(self) -> str

# Database tables needed:
CREATE TABLE sessions (...)
CREATE TABLE session_annotations (...)
CREATE TABLE session_models (...)
```

**Validation:**
```bash
pytest tests/unit/test_session.py -v --cov=vcm.models.session
# Expected: 12/12 passing, >95% coverage
```

**Reference:** `vcm_session_tracking_spec.md` → "Session Structure" & "Unit Tests for Session"

---

### Day 3: Terminal Logging with Privacy

**Task:** Implement terminal capture with secret masking

**Files to Create:**
```
vcm/utils/terminal_logger.py # NEW - Capture & mask
vcm/tests/unit/test_terminal.py # NEW - Masking tests
```

**Requirements:**
```python
class TerminalLogger:
 def start_capture(self) -> None
 def stop_capture(self) -> str
 def mask_secrets(self, text: str) -> str # Mask API keys, passwords
 def get_log(self) -> str

# Privacy patterns to mask:
- ".*password.*"
- ".*API_KEY.*"
- ".*SECRET.*"
- ".*token.*"
- ".*github_token.*"
```

**Test Scenarios:**
- Capture print() output
- Capture subprocess output
- Mask API_KEY and passwords
- Exclude verbose operations
- Encrypt at rest

**Reference:** `vcm_session_tracking_spec.md` → "Terminal Output Logging (With Privacy)"

---

### Day 4: Session-Model Linkage

**Task:** Link models to sessions in metadata

**Files to Modify:**
```
vcm/models/metadata.py # UPDATE - Add session field
vcm/trainer.py # UPDATE - Auto-session detection
```

**Changes Needed:**
```python
# Add to MetadataModel:
session: Optional[SessionInfo] # Session context
session_position: Optional[int] # Position in session (1st, 2nd, 3rd model)
previous_model: Optional[str] # Name of previous model in session
next_model: Optional[str] # Name of next model in session

# In trainer.py:
def log_model(...):
 # Detect if session is active
 active_session = SessionTracker.get_active_session()
 if active_session:
 metadata.session = SessionInfo(...)
 # Link models
 metadata.previous_model = active_session.last_model_name
```

**Validation:**
```bash
pytest tests/integration/test_session_model_integration.py -v
# Expected: 6/6 passing
```

**Reference:** `vcm_session_tracking_spec.md` → "Integration With Model Metadata"

---

### Day 5: Session CLI Commands

**Task:** Implement session CLI commands

**Files to Create/Modify:**
```
vcm/cli/session_commands.py # NEW - All session CLI
vcm/tests/cli/test_session_cli.py # NEW - CLI tests
```

**Commands to Implement:**
```bash
vcm session start <name> # Start session
vcm session end # End session
vcm session list # List all sessions
vcm session info <name> # Show session details
vcm session logs <name> # View terminal logs
vcm session models <name> # List models in session
vcm session annotate <text> # Add note
vcm session compare <s1> <s2> # Compare sessions
vcm session export <name> # Export as JSON/HTML
```

**Implementation Pattern:**
```python
@click.command()
@click.argument('session_name')
def session_info(session_name):
 """Show session details"""
 session = SessionStore.get_session(session_name)
 click.echo(format_session_output(session))
```

**Validation:**
```bash
pytest tests/cli/test_session_cli.py -v
# Expected: All session CLI tests passing
```

**Reference:** `vcm_cli_documentation.md` → "SESSION COMMANDS"

---

### Day 6-7: Integration & E2E

**Task:** Full session workflow end-to-end

**Workflow Test:**
```bash
# Start session
vcm session start "Tuesday morning"

# Train models (auto-join session)
vcm train --model-name v1 --script train.py --metrics metrics.json
vcm session annotate "Improved data preprocessing"
vcm train --model-name v2 --script train.py --metrics metrics.json

# End session
vcm session end

# Review
vcm session info "Tuesday morning"
vcm session models "Tuesday morning"
vcm session logs "Tuesday morning"
vcm session export "Tuesday morning" --format html
```

**Validation:**
```bash
pytest tests/integration/test_session_*.py -v
pytest tests/unit/test_session*.py -v
# Expected: All passing
```

---

## PHASE 2: WEEK 2 (Advanced Scenarios & Testing)

### Day 1-2: Iris Dataset Setup

**Task:** Create real ML project fixtures

**Files to Create:**
```
tests/fixtures/iris_project/ # NEW - Real project dir
 ├── data/
 │ ├── iris_train_v1.0.csv
 │ ├── iris_train_v2.0.csv (scaled)
 │ └── iris_test_v1.0.csv
 ├── training_scripts/
 │ ├── train_model_v1.py
 │ └── train_model_v2.py (improved)
 ├── .gitignore
 ├── .vcmconfig.yaml
 └── conftest.py
```

**Implementation:**
```python
# tests/fixtures/conftest.py
@pytest.fixture
def iris_project(tmp_path):
 """Create real iris classification project"""
 # Setup git repo
 # Create datasets (raw + scaled)
 # Create training scripts
 # Initialize VCM
 return project_dir

# Fixture provides:
# - Real git repo
# - Real DVC setup
# - Real training scripts
# - Real data files
```

**Validation:**
```bash
# Run fixture
pytest tests/advanced/ --setup-only
# Verify all files created correctly
```

---

### Day 3-5: Advanced Scenario Tests

**Task:** Implement all 8 real-world scenarios

**Files to Create:**
```
tests/advanced/
├── test_scenario_1_single_training.py
├── test_scenario_2_multiple_models.py
├── test_scenario_3_data_version_impact.py
├── test_scenario_4_code_changes.py
├── test_scenario_5_lineage_analysis.py
├── test_scenario_6_troubleshooting.py
├── test_scenario_7_reproducibility.py
└── test_scenario_8_audit_trail.py
```

**Each Scenario:**
1. Real ML workflow (train models)
2. VCM captures everything
3. Query/analyze results
4. Verify accuracy of insights

**Example (Scenario 1):**
```python
def test_scenario_1_single_model_training(iris_project):
 """Verify all metadata captured for single model"""
 os.chdir(iris_project)
 
 # Train model
 os.system("vcm train --model-name iris_v1 "
 "--dataset data/iris_train_v1.0.csv "
 "--script train.py --metrics metrics.json")
 
 # Verify metadata
 metadata = load_metadata('models/iris_v1.pkl.vcm.json')
 assert metadata['metrics']['accuracy'] > 0.9
 assert metadata['code']['git_commit'] is not None
 assert len(metadata['data']['dvc_files']) > 0
```

**Validation:**
```bash
pytest tests/advanced/ -v -s
# Expected: 8/8 scenarios passing
# Expected: Real models trained with correct metadata
```

**Reference:** `vcm_advanced_testing.md` → All 8 scenarios

---

### Day 6: Performance & Reproducibility

**Task:** Validate performance and reproducibility

**Tests to Add:**
```python
# Performance: Queries <200ms for 100 models
# Metadata capture: <2.5s overhead
# Reproducibility: Identical models after rebuild

def test_query_performance():
 # Create 100 models
 # Query: vcm models --best
 # Assert: <200ms

def test_reproducibility():
 # Train model v1
 # Reproduce it
 # Assert: Byte-for-byte identical
```

**Validation:**
```bash
pytest tests/performance/ -v
# Expected: All benchmarks passing
```

---

### Day 7: Full Test Suite & Quality Check

**Task:** Run everything, validate quality gates

**Commands:**
```bash
# Full test suite
pytest tests/ -v \
 --cov=vcm \
 --cov-report=html \
 --cov-report=term-missing \
 --tb=short

# Code quality
mypy vcm/ --strict
flake8 vcm/ --max-line-length=100
black vcm/ --check
bandit -r vcm/

# Generate report
# pytest-html report
```

**Quality Gates Check:**
```
[x] Tests passing: 120+/120+
[x] Coverage: >85%
[x] Type checking: 0 errors
[x] Linting: 0 violations
[x] Security: No HIGH severity
[x] Performance: All targets met
[x] Documentation: Complete
```

---

## DAILY CHECKLIST TEMPLATE

### Each Day, Follow This Pattern:

```
 Goal: [What you're implementing today]

 Tasks:
 [ ] Read relevant spec section
 [ ] Design (if needed)
 [ ] Write tests FIRST
 [ ] Implement code to pass tests
 [ ] Run pytest
 [ ] Verify coverage >90%
 [ ] Commit to git
 [ ] Move to next task

[x] Validation:
 pytest [module] -v --cov=[module]
 # Expected: All passing, >90% coverage

 Deliverable:
 [Files created/modified]
 [Test count: X/X passing]
 [Coverage: X%]
```

---

## WEEKLY CHECKLIST

### Week 1 (Session Tracking)
```
Monday-Tuesday:
 [ ] SessionTracker class with lifecycle
 [ ] Database schema for sessions
 [ ] 12 unit tests passing

Wednesday:
 [ ] Terminal logging with masking
 [ ] Privacy validation

Thursday:
 [ ] Session-model linkage in metadata
 [ ] Integration tests passing

Friday-Saturday:
 [ ] Session CLI commands
 [ ] Full workflow E2E

Sunday:
 [ ] Review + commit
 [ ] Document any issues
 [ ] Plan week 2
```

### Week 2 (Advanced Testing)
```
Monday:
 [ ] Iris project fixtures
 [ ] Real datasets created

Tuesday-Thursday:
 [ ] 8 advanced scenarios implemented
 [ ] All 8 tests passing

Friday:
 [ ] Performance testing
 [ ] Reproducibility validation

Saturday-Sunday:
 [ ] Full test suite
 [ ] Quality gates validation
 [ ] Production readiness check
```

---

## TOKEN EFFICIENCY STRATEGY

### How to Handle Large Codebase

**In Each Context Window:**

1. **Load once:** Specification document
2. **Focus on:** ONE module only
3. **Output:** Complete, tested module
4. **Don't:** Discuss unrelated code
5. **Clear:** Before next context

**Context 1 (Phase 2.1):**
- Load: `vcm_session_tracking_spec.md`
- Write: SessionTracker + DB schema + tests
- Output: vcm/models/session.py (complete)

**Context 2 (Phase 2.2):**
- Load: Session CLI tests spec
- Write: All session CLI commands
- Output: vcm/cli/session_commands.py (complete)

**Context 3 (Phase 2.3):**
- Load: `vcm_advanced_testing.md`
- Write: All 8 scenario tests
- Output: tests/advanced/ (complete)

**Context 4 (Phase 2.4):**
- Load: `vcm_testing_strategy.md`
- Write: Full validation + reports
- Output: Test results + quality report

---

## SUCCESS CRITERIA

### Phase 2 Complete When:

```
[x] Session Tracking:
 - SessionTracker class works
 - Terminal logging with masking
 - Models linked to sessions
 - CLI commands implemented
 - 12+ unit tests passing
 - 6+ integration tests passing

[x] Advanced Testing:
 - 8 real-world scenarios tested
 - Iris project runs end-to-end
 - All metadata captured correctly
 - Performance validated
 - Reproducibility proven

[x] Quality:
 - 120+ total tests passing
 - >85% code coverage
 - 0 type errors
 - 0 linting violations
 - Full documentation

[x] Production Ready:
 - No TODOs in code
 - All error cases handled
 - Real projects validated
 - Comprehensive documentation
```

---

## WHAT TO DO WHEN STUCK

### If Tests Fail:
1. Read the error message carefully
2. Check specification (this should clarify)
3. Look at test case to understand expected behavior
4. Implement to match spec

### If Something Seems Missing:
1. Check `vcm_session_tracking_spec.md`
2. Check `vcm_testing_strategy.md`
3. Follow reference documents exactly

### If Confused About Architecture:
1. Check `vcm_mvp_specification.md` (still valid)
2. See database schema
3. Follow existing patterns from Phase 1

---

## FINAL CHECKLIST BEFORE COMPLETION

- [ ] Phase 2 unit tests: 12/12 passing
- [ ] Integration tests: 6/6 passing
- [ ] Advanced scenarios: 8/8 passing
- [ ] Performance tests: Benchmarks met
- [ ] CLI tests: All commands working
- [ ] Code coverage: >85%
- [ ] Type checking: 0 errors
- [ ] Linting: 0 violations
- [ ] Documentation: Complete
- [ ] No TODOs in code
- [ ] All error cases handled
- [ ] Real project validated
- [ ] Production ready

---

## FINAL OUTPUT

When complete, you should have:

```
vcm/
├── models/
│ ├── metadata.py (Phase 1)
│ ├── session.py (Phase 2) 
│ └── __init__.py
├── db/
│ ├── database.py (Phase 1 + Phase 2 updates)
│ └── __init__.py
├── cli/
│ ├── commands.py (Phase 1)
│ ├── session_commands.py (Phase 2) 
│ └── __init__.py
├── integrations/
│ ├── git_client.py
│ ├── dvc_client.py
│ └── __init__.py
├── utils/
│ ├── terminal_logger.py (Phase 2) 
│ ├── environment.py
│ ├── metrics_loader.py
│ └── __init__.py
├── trainer.py (Phase 1 + updates)
├── config.py
└── __init__.py

tests/
├── unit/
│ ├── test_metadata.py
│ ├── test_session.py (Phase 2) 
│ ├── test_terminal.py (Phase 2) 
│ ├── test_database.py
│ ├── test_git_client.py
│ ├── test_dvc_client.py
│ └── ...
├── integration/
│ ├── test_session_model_integration.py (Phase 2) 
│ ├── test_session_cli.py (Phase 2) 
│ ├── test_cli_complete.py
│ └── ...
├── advanced/
│ ├── test_scenario_1_single_training.py 
│ ├── test_scenario_2_multiple_models.py 
│ ├── test_scenario_3_data_version_impact.py 
│ ├── test_scenario_4_code_changes.py 
│ ├── test_scenario_5_lineage_analysis.py 
│ ├── test_scenario_6_troubleshooting.py 
│ ├── test_scenario_7_reproducibility.py 
│ └── test_scenario_8_audit_trail.py 
├── performance/
│ ├── test_query_performance.py (Phase 2) 
│ └── test_metadata_overhead.py (Phase 2) 
└── fixtures/
 └── iris_project/ (Phase 2) 

[x] 130+ tests
[x] >85% coverage
[x] Phase 1 + Phase 2 complete
[x] Production ready
```

---

## YOU'RE READY!

This is your complete guide for Phase 2 and advanced testing.

**Start with:** Day 1-2 of Week 1 → SessionTracker class

**Questions?** Check reference documents

**Good luck!** 
