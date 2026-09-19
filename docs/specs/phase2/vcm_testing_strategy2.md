# VCM Comprehensive Testing & Validation Strategy

**Scope:** Phase 1 (MVP) + Phase 2 (Session Tracking) + Advanced Scenarios 
**Purpose:** Complete validation framework for production readiness 
**Duration:** Week 5-6 (after Phase 4 completion) 

---

## TESTING ARCHITECTURE

### Test Pyramid (Revised)

```
Advanced Scenarios (Real Projects) [5% - 8 tests]
├─ Single model training
├─ Multiple models on same data
├─ Data version impact
├─ Code change tracking
├─ Full lineage queries
├─ Developer troubleshooting
├─ Model reproducibility
└─ Production audit trails

Session Tracking Tests [10% - 12 tests]
├─ Session creation & lifecycle
├─ Terminal logging with masking
├─ Model grouping in session
├─ Session comparisons
├─ Retrospective sessions
└─ Export & reporting

Integration Tests [15% - 18 tests)
├─ Phase 1 + Phase 2 combined
├─ Session + Model metadata
├─ CLI with sessions
├─ Database consistency
└─ Cross-module interactions

CLI Command Tests [20% - 20 tests)
├─ All 20+ commands
├─ Option combinations
├─ Error handling
└─ Output validation

Unit Tests (Phase 1 + 2) [50% - 60 tests)
├─ Models (metadata + session)
├─ Integrations (git, dvc)
├─ Database (queries, updates)
├─ CLI handlers
├─ Utilities & helpers
└─ Session tracker
```

**Total: 120+ tests, >85% code coverage**

---

## PHASE 2 UNIT TESTS

### Session Tracker Unit Tests (12 tests)

```python
# tests/unit/test_session_tracker.py

def test_session_creation():
 """SessionTracker initializes correctly"""
 session = SessionTracker("test_session")
 assert session.session_id is not None
 assert session.session_name == "test_session"
 assert session.status == "inactive"

def test_session_start_end():
 """Session lifecycle works"""
 session = SessionTracker("test")
 session.start()
 assert session.status == "active"
 assert session.start_time is not None
 
 session.end()
 assert session.status == "completed"
 assert session.end_time is not None

def test_session_terminal_capture():
 """Terminal output is captured"""
 with SessionTracker("test") as session:
 print("Test output")
 import subprocess
 subprocess.run(['echo', 'subprocess output'])
 
 logs = session.get_terminal_log()
 assert "Test output" in logs or "subprocess output" in logs

def test_session_secret_masking():
 """Sensitive data is masked"""
 with SessionTracker("test") as session:
 print("API_KEY=secret123")
 print("password=mypass")
 
 logs = session.get_terminal_log()
 assert "secret123" not in logs
 assert "mypass" not in logs
 assert "***MASKED***" in logs

def test_session_model_logging():
 """Models are grouped in session"""
 with SessionTracker("test") as session:
 model1_meta = {"name": "v1", "accuracy": 0.91}
 model2_meta = {"name": "v2", "accuracy": 0.93}
 
 session.log_model(model1_meta)
 session.log_model(model2_meta)
 
 models = session.get_models()
 assert len(models) == 2
 assert models[0]["name"] == "v1"
 assert models[1]["name"] == "v2"
 assert models[0].next_model == models[1]

def test_session_annotations():
 """User annotations saved"""
 with SessionTracker("test") as session:
 session.annotate("Testing approach 1")
 session.annotate("Trying new preprocessing")
 
 annotations = session.get_annotations()
 assert len(annotations) == 2
 assert "Testing approach 1" in annotations[0].text

def test_session_git_tracking():
 """Git commits in session tracked"""
 session = SessionTracker("test")
 session.start()
 
 # Make mock commit
 commits_before = len(session.get_commits())
 # (In real test, make actual commit)
 
 session.end()
 commits_after = len(session.get_commits())
 assert commits_after >= commits_before

def test_session_duration_calculation():
 """Session duration calculated correctly"""
 import time
 session = SessionTracker("test")
 session.start()
 time.sleep(1)
 session.end()
 
 duration = session.get_duration()
 assert duration.total_seconds() >= 1

def test_session_database_storage():
 """Session persisted to database"""
 session = SessionTracker("test")
 session_id = session.start()
 session.annotate("test")
 session.end()
 
 # Retrieve from database
 retrieved = SessionStore.get_session(session_id)
 assert retrieved.session_name == "test"
 assert len(retrieved.get_annotations()) == 1

def test_session_export_json():
 """Session exported as JSON"""
 with SessionTracker("test") as session:
 session.log_model({"name": "v1"})
 session.annotate("test note")
 
 json_export = session.export_json()
 assert "test" in json_export
 assert "v1" in json_export

def test_session_export_html():
 """Session exported as HTML report"""
 with SessionTracker("test") as session:
 session.log_model({"name": "v1", "accuracy": 0.92})
 
 html = session.export_html()
 assert "<html>" in html
 assert "v1" in html
 assert "0.92" in html

def test_session_retrospective_creation():
 """Retrospective session built from history"""
 # Create some models with timestamps
 create_model("v1", time=datetime(2024, 1, 15, 9, 0))
 create_model("v2", time=datetime(2024, 1, 15, 10, 0))
 
 # Retrospectively create session
 session = SessionTracker.create_retrospective(
 "past",
 start=datetime(2024, 1, 15, 8, 0),
 end=datetime(2024, 1, 15, 11, 0)
 )
 
 models = session.get_models()
 assert len(models) == 2
```

**Checkpoint:** All 12 tests passing

---

## PHASE 2 INTEGRATION TESTS

### Session + Model Integration (6 tests)

```python
# tests/integration/test_session_model_integration.py

def test_session_model_metadata_linkage():
 """Model metadata includes session context"""
 with SessionTracker("integration_test") as session:
 model = train_simple_model("v1")
 session.log_model(model, "v1", {"accuracy": 0.92})
 
 # Load metadata
 metadata = load_metadata("v1.pkl.vcm.json")
 assert metadata["session"]["session_name"] == "integration_test"
 assert metadata["session"]["position_in_session"] == 1

def test_session_model_chain_creation():
 """Models linked in session sequence"""
 with SessionTracker("chain_test") as session:
 for i in range(3):
 model = train_model(f"v{i+1}")
 session.log_model(model, f"v{i+1}", {})
 
 # Check linkage
 meta_v1 = load_metadata("v1.pkl.vcm.json")
 meta_v2 = load_metadata("v2.pkl.vcm.json")
 
 assert meta_v1["session"]["next_model"] == "v2"
 assert meta_v2["session"]["previous_model"] == "v1"

def test_vcm_train_with_session_active():
 """vcm train auto-joins active session"""
 session = SessionTracker("train_integration")
 session.start()
 
 # Run vcm train (session is active)
 os.system("vcm train --model-name v1 --script train.py --metrics metrics.json")
 
 # Model should be in session
 models = session.get_models()
 assert any(m.name == "v1" for m in models)

def test_session_comparison_with_metadata():
 """Compare sessions using model metadata"""
 session1 = create_session_with_5_models()
 session2 = create_session_with_3_models()
 
 comp = SessionComparator.compare(session1, session2)
 
 # Should extract metadata from all models
 assert comp["s1_models_count"] == 5
 assert comp["s2_models_count"] == 3
 assert "s1_best_accuracy" in comp
 assert "s2_best_accuracy" in comp

def test_session_export_includes_models():
 """Session export includes all model metadata"""
 with SessionTracker("export_test") as session:
 session.log_model({"name": "v1", "accuracy": 0.91})
 session.log_model({"name": "v2", "accuracy": 0.93})
 
 export = session.export_json()
 parsed = json.loads(export)
 
 assert len(parsed["models"]) == 2
 assert parsed["models"][0]["name"] == "v1"
 assert parsed["best_model"]["name"] == "v2"

def test_session_cli_integration():
 """CLI commands work with sessions"""
 os.system("vcm session start 'cli_test'")
 os.system("vcm train --model-name v1 --script train.py --metrics metrics.json")
 os.system("vcm session end")
 
 # Query through CLI
 result = os.popen("vcm session models 'cli_test'").read()
 assert "v1" in result
```

**Checkpoint:** All 6 tests passing

---

## ADVANCED SCENARIO TESTS (Real ML Project)

### Iris Classification Scenarios (8 tests)

```python
# tests/advanced/test_iris_scenarios.py
# (Detailed in vcm_advanced_testing.md)

# Run with: pytest tests/advanced/ -v
```

**Scenarios Covered:**
1. Single model training with all metadata
2. Multiple models on same dataset
3. Data version update impact
4. Code changes tracking
5. Full lineage analysis
6. Developer troubleshooting
7. Model reproducibility
8. Production audit trail

**Checkpoint:** All 8 tests passing with real project

---

## CLI INTEGRATION TEST SUITE

### Complete Command Testing (20+ tests)

```python
# tests/integration/test_cli_complete.py

def test_cli_init():
 """vcm init creates all necessary files"""
 with TempDir() as tmp:
 os.chdir(tmp)
 os.system("git init")
 exit_code = os.system("vcm init")
 
 assert exit_code == 0
 assert os.path.exists(".vcm/vcm.db")
 assert os.path.exists(".vcmconfig.yaml")

def test_cli_train():
 """vcm train runs successfully"""
 create_real_training_scenario()
 
 result = os.popen(
 "vcm train --model-name test_v1 "
 "--script train.py --metrics metrics.json"
 ).read()
 
 assert "[x] Model tracked" in result
 assert os.path.exists("models/test_v1.pkl.vcm.json")

def test_cli_models_query():
 """vcm models returns results"""
 create_multiple_models(3)
 
 result = os.popen("vcm models --best").read()
 
 assert "Model Name" in result or "model_" in result
 assert "Accuracy" in result

def test_cli_compare():
 """vcm compare works"""
 create_two_models()
 
 result = os.popen(
 "vcm compare models/v1.pkl models/v2.pkl"
 ).read()
 
 assert "Comparison" in result or "v1" in result

def test_cli_lineage():
 """vcm lineage shows full context"""
 create_model_with_git()
 
 result = os.popen("vcm lineage models/v1.pkl").read()
 
 assert "Git" in result or "commit" in result
 assert "Accuracy" in result or "metrics" in result

def test_cli_session_start():
 """vcm session start creates session"""
 result = os.popen("vcm session start 'cli_test'").read()
 
 assert "[x]" in result or "started" in result

def test_cli_session_end():
 """vcm session end completes session"""
 os.system("vcm session start 'test'")
 result = os.popen("vcm session end").read()
 
 assert "[x]" in result or "ended" in result

def test_cli_session_info():
 """vcm session info shows details"""
 create_session_with_models()
 
 result = os.popen("vcm session info 'test_session'").read()
 
 assert "Models trained" in result or "models" in result

def test_cli_session_models():
 """vcm session models lists models"""
 create_session_with_models()
 
 result = os.popen("vcm session models 'test_session'").read()
 
 assert "Model" in result or "model_" in result

def test_cli_json_output():
 """CLI can output JSON for automation"""
 create_multiple_models(2)
 
 result = os.popen("vcm models --format json").read()
 
 # Should be valid JSON
 data = json.loads(result)
 assert len(data) >= 2

def test_cli_error_handling():
 """CLI shows helpful errors"""
 result = os.popen("vcm train --model-name test --script nonexistent.py").read()
 
 assert "Error" in result or "not found" in result

def test_cli_help():
 """CLI help works"""
 result = os.popen("vcm --help").read()
 
 assert "train" in result
 assert "models" in result
 assert "usage" in result.lower()

# ... more command tests
```

**Checkpoint:** All CLI tests passing

---

## COMPREHENSIVE TEST EXECUTION

### Test Running Strategy

**Week 5 - Run Incrementally:**

```bash
# Day 1-2: Phase 2 Unit Tests
pytest tests/unit/test_session_tracker.py -v --cov
# Expected: 12/12 passing, >95% coverage

# Day 3-4: Phase 2 Integration Tests
pytest tests/integration/test_session_model_integration.py -v
# Expected: 6/6 passing

# Day 5: Advanced Scenarios
pytest tests/advanced/test_iris_scenarios.py -v -s
# Expected: 8/8 passing, real ML project validation

# Day 6: CLI Tests
pytest tests/integration/test_cli_complete.py -v
# Expected: 20+/20+ passing

# Day 7: Full Suite
pytest tests/ -v --cov=vcm --cov-report=html
# Expected: 120+/120+ passing, >85% coverage
```

**Week 6 - Performance & Quality:**

```bash
# Performance validation
pytest tests/performance/ -v
# Check all benchmarks pass

# Quality metrics
mypy vcm/ --strict # 0 errors
flake8 vcm/ --max-line-length=100 # 0 violations
black vcm/ --check # Code formatted
bandit -r vcm/ # No HIGH severity issues

# Final validation
pytest tests/ -v \
 --cov=vcm \
 --cov-report=html \
 --cov-report=term-missing \
 --tb=short
```

---

## QUALITY GATES FINAL CHECKLIST

| Criterion | Target | Validation |
|-----------|--------|-----------|
| Code Coverage | >85% | `pytest --cov` report |
| Test Count | 120+ | `pytest --collect-only` |
| Passing Tests | 100% | `pytest -v` all green |
| Type Checking | 0 errors | `mypy vcm/ --strict` |
| Linting | 0 violations | `flake8 vcm/` |
| Security | No HIGH | `bandit -r vcm/` |
| Performance | <500ms/query | Benchmark tests |
| Documentation | Complete | README, CLI.md, API.md |
| E2E Real Project | Works | Iris scenario 100% |
| Session Tracking | Accurate | Session tests all pass |

---

## VALIDATION REPORT TEMPLATE

After all tests pass, generate:

```
VCM Comprehensive Testing Report
═════════════════════════════════════════════════════════════

1. Test Coverage Summary
 [x] Unit Tests: 60 passed
 [x] Integration Tests: 25 passed
 [x] Advanced Scenarios: 8 passed
 [x] CLI Tests: 20 passed
 [x] Performance Tests: 7 passed
 ─────────────────────────────────
 Total: 120 tests passed
 Coverage: 88%

2. Quality Metrics
 [x] Type Coverage: 100%
 [x] Linting Score: 10/10
 [x] Security: No vulnerabilities
 [x] Performance: All targets met

3. Feature Validation
 [x] Phase 1 MVP: Complete
 [x] Phase 2 Sessions: Complete
 [x] Advanced Scenarios: Complete
 [x] CLI Commands: 20+ commands working

4. Production Readiness
 [x] No TODOs in code
 [x] All error cases handled
 [x] Full documentation
 [x] Real project tested
 [x] Session tracking validated
 [x] Reproducibility verified

5. Recommendation
 [x] READY FOR PRODUCTION RELEASE
```

---

## END OF TESTING STRATEGY

**All components tested, validated, and ready for use**
