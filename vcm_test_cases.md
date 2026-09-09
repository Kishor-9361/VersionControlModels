# VCM MVP - Comprehensive Test Cases

**Purpose:** TDD validation framework for MVP development  
**Format:** Organized by module/feature  
**Execution:** Run before each commit  

---

## TEST EXECUTION STRATEGY

### Test Pyramid
```
E2E Tests (Real project)          [10% - 5 tests]
Integration Tests (Module pairs)  [20% - 15 tests]
Unit Tests (Individual functions) [70% - 35 tests]
```

### Test Phases
1. **Unit Tests:** Run after each function implementation
2. **Integration Tests:** Run after module completion
3. **E2E Tests:** Run at end of week (cumulative)

---

## PART 1: UNIT TESTS

### Module 1: Metadata Model (`vcm.models.metadata`)

#### UT-1.1: MetadataModel - Initialization
```python
Test: MetadataModel can be created with required fields
Input: 
  - model_name="classifier_v1"
  - model_hash="sha256:abc123"
  - metrics={"accuracy": 0.94}
Expected:
  - Object created without errors
  - model_name == "classifier_v1"
  - metadata_version == "1.0"
  - created_at is set to current time
```

#### UT-1.2: MetadataModel - JSON Serialization
```python
Test: MetadataModel can serialize to JSON
Input: MetadataModel with all fields
Expected:
  - json.dumps(metadata.to_dict()) succeeds
  - JSON is valid and readable
  - No circular references
  - All datetime objects converted to ISO format
```

#### UT-1.3: MetadataModel - JSON Deserialization
```python
Test: MetadataModel can deserialize from JSON
Input: Valid JSON metadata string
Expected:
  - MetadataModel.from_json(json_str) succeeds
  - All fields restored correctly
  - Datetime strings converted back to datetime objects
```

#### UT-1.4: MetadataModel - Field Validation
```python
Test: MetadataModel rejects invalid data
Input variations:
  - model_name = None (should fail)
  - accuracy = "not_a_number" (should fail)
  - git_commit = "" (empty string, should fail)
  - metrics = {} (empty dict, should be allowed)
Expected:
  - Appropriate ValidationError raised
  - Error message is descriptive
```

#### UT-1.5: MetadataModel - Immutability
```python
Test: Metadata object is immutable after creation
Input: Created MetadataModel
Actions:
  - Try to modify: metadata.accuracy = 0.50
Expected:
  - AttributeError or FrozenDataclass behavior
  - Original value unchanged
```

---

### Module 2: Git Integration (`vcm.integrations.git_client`)

#### UT-2.1: GitClient - Get Current Commit
```python
Test: GitClient.get_current_commit() returns valid commit hash
Setup: Use test repo with known commit
Expected:
  - Returns 40-character hex string
  - Matches git rev-parse HEAD
  - No errors raised
```

#### UT-2.2: GitClient - Get Current Branch
```python
Test: GitClient.get_current_branch() returns branch name
Setup: Test repo checked out to specific branch
Expected:
  - Returns branch name correctly
  - Handles "detached HEAD" state gracefully
  - Returns appropriate error message
```

#### UT-2.3: GitClient - Get Remote URL
```python
Test: GitClient.get_remote_url() returns valid URL
Setup: Test repo with origin remote
Expected:
  - Returns https or git URL
  - Handles missing remote (optional field)
  - No credentials exposed in URL
```

#### UT-2.4: GitClient - Detect Uncommitted Changes
```python
Test: GitClient.has_uncommitted_changes() detects staged/unstaged changes
Setup: Test repo with various file states
Expected:
  - Returns True when changes exist
  - Returns False when clean
  - Ignores .vcm/ directory
  - Ignores .gitignore'd files
```

#### UT-2.5: GitClient - Error Handling
```python
Test: GitClient handles errors gracefully
Input: Non-git directory
Expected:
  - Raises GitNotInitializedError (custom exception)
  - Error message: "Git repository not found in current or parent directories"
  - Graceful degradation (training continues, git_commit = None)
```

---

### Module 3: DVC Integration (`vcm.integrations.dvc_client`)

#### UT-3.1: DVCClient - Get Tracked Files
```python
Test: DVCClient.get_tracked_files() returns all DVC-tracked files
Setup: Test repo with dvc.yaml and *.dvc files
Expected:
  - Returns list of tracked file paths
  - Each entry has: path, hash, size
  - Returns empty list if DVC not initialized
  - No errors on DVC not installed
```

#### UT-3.2: DVCClient - Get File Hash
```python
Test: DVCClient.get_file_hash(filepath) returns DVC hash
Input: Path to DVC-tracked file
Expected:
  - Returns MD5 or equivalent DVC hash
  - Consistent across multiple calls
  - Different hash if file modified
```

#### UT-3.3: DVCClient - Detect DVC Initialization
```python
Test: DVCClient.is_initialized() correctly detects DVC setup
Input variations:
  - Project with dvc.yaml → True
  - Project without DVC → False
  - Project with .dvc/ directory → True
Expected:
  - Returns boolean correctly
  - No errors raised
```

#### UT-3.4: DVCClient - Handle Missing DVC
```python
Test: DVCClient gracefully handles when DVC not installed
Expected:
  - DVCNotInstalledWarning logged
  - dvc_files = [] (empty list)
  - Training continues normally
  - No exception raised
```

---

### Module 4: Database Layer (`vcm.db.database`)

#### UT-4.1: Database - Initialize
```python
Test: Database.init() creates schema correctly
Expected:
  - .vcm/vcm.db file created
  - All tables created: models, metadata_json
  - Indexes created for fast queries
  - No errors on re-initialization (idempotent)
```

#### UT-4.2: Database - Insert Model
```python
Test: Database.insert_model(metadata) stores model record
Input: Valid MetadataModel
Expected:
  - Record inserted successfully
  - ID auto-incremented
  - Timestamp auto-set
  - metadata_json stored completely
```

#### UT-4.3: Database - Query by Accuracy
```python
Test: Database.query_by_accuracy(min=0.9) returns matching models
Setup: Database with 3 models: accuracy [0.85, 0.92, 0.95]
Expected:
  - Returns 2 models (0.92, 0.95)
  - Sorted by accuracy DESC
  - No errors
```

#### UT-4.4: Database - Query by Dataset Hash
```python
Test: Database.query_by_dataset(dataset_hash="xyz") returns models
Setup: Multiple models with different datasets
Expected:
  - Returns only models trained on that dataset
  - Correct count and data
```

#### UT-4.5: Database - Update Model Metadata
```python
Test: Database.update_model(id, metadata) updates record
Expected:
  - Record updated successfully
  - Only specified fields changed
  - Other fields unchanged
  - Update timestamp recorded
```

#### UT-4.6: Database - Concurrent Access
```python
Test: Database handles concurrent reads/writes
Setup: Simulate 5 simultaneous insert operations
Expected:
  - All inserts succeed
  - No data corruption
  - No deadlocks
  - SQLite WAL mode handles concurrency
```

---

### Module 5: Metrics Loader (`vcm.utils.metrics_loader`)

#### UT-5.1: Load Metrics from JSON File
```python
Test: MetricsLoader.from_json_file(path) reads metrics
Input: metrics.json with {"accuracy": 0.94, "f1": 0.92}
Expected:
  - Returns dict with correct values
  - Types preserved (float, int, string)
```

#### UT-5.2: Load Metrics from Python Dict
```python
Test: MetricsLoader.from_dict(dict) accepts runtime metrics
Input: {"accuracy": 0.94, "precision": 0.91}
Expected:
  - Returns copy of dict
  - No side effects
```

#### UT-5.3: Load Metrics - File Not Found
```python
Test: MetricsLoader handles missing file
Input: Non-existent path
Expected:
  - Returns empty dict {}
  - Warning logged: "metrics file not found"
  - Training continues with empty metrics
```

#### UT-5.4: Load Metrics - Invalid JSON
```python
Test: MetricsLoader handles malformed JSON
Input: Invalid JSON file
Expected:
  - JSONDecodeError caught
  - Warning logged
  - Returns empty dict
  - Training continues
```

---

### Module 6: Environment Capture (`vcm.utils.environment`)

#### UT-6.1: Get Python Version
```python
Test: EnvironmentCapture.get_python_version() returns version
Expected:
  - Returns version string like "3.9.1"
  - Matches sys.version_info
```

#### UT-6.2: Get Installed Libraries
```python
Test: EnvironmentCapture.get_libraries() returns package versions
Expected:
  - Returns dict with {package: version}
  - Only critical packages (torch, sklearn, pandas, etc.)
  - Handles missing packages gracefully
```

#### UT-6.3: Get System Info
```python
Test: EnvironmentCapture.get_system_info() returns hostname, OS
Expected:
  - hostname is valid
  - os is recognized (Linux, Darwin, Windows)
  - timestamp is current
```

---

## PART 2: INTEGRATION TESTS

### Integration Test 1: Git + Metadata
```python
Test: Git info is correctly captured in metadata
Setup: 
  1. Initialize test git repo
  2. Commit a change
  3. Create metadata with git_client
Expected:
  - metadata.code.git_commit matches HEAD
  - metadata.code.git_branch is correct
  - metadata.code.git_url is correct
```

### Integration Test 2: DVC + Metadata
```python
Test: DVC file hashes are correctly captured
Setup:
  1. Initialize test DVC repo
  2. Add file to DVC (dvc add data.csv)
  3. Create metadata with dvc_client
Expected:
  - metadata.data.dvc_files has correct entries
  - Each file has path, hash, size
  - Handles mix of DVC and non-DVC files
```

### Integration Test 3: Database + Metadata
```python
Test: Metadata is stored and retrieved from database
Setup:
  1. Create metadata object
  2. Insert into database
  3. Query from database
Expected:
  - Retrieved metadata matches original
  - All fields preserved
  - JSON serialization/deserialization works
```

### Integration Test 4: File System + Database
```python
Test: .vcm.json files are created and indexed
Setup:
  1. Create metadata
  2. Save to model.pkl.vcm.json
  3. Insert into database
  4. Query database
Expected:
  - File created in correct location
  - File is readable JSON
  - Database points to correct file
  - File and DB stay in sync
```

### Integration Test 5: All Components Together
```python
Test: Git + DVC + DB + Metrics + Env work together
Setup: Real test project scenario
  1. Initialize test project with Git, DVC
  2. Run training (mock train.py)
  3. Capture all metadata components
  4. Save to file and DB
Expected:
  - All components captured correctly
  - No data loss or corruption
  - Query results accurate
  - Performance acceptable (<500ms)
```

---

## PART 3: CLI TESTS

### CLI Test 1: `vcm init`
```python
Test: vcm init initializes project correctly
Commands:
  mkdir test_project && cd test_project
  git init
  vcm init
Expected:
  - .vcmconfig.yaml created
  - .vcm/ directory created
  - .vcm/vcm.db initialized
  - Message: "✅ VCM initialized successfully"
```

### CLI Test 2: `vcm train` - Basic
```python
Test: vcm train captures metadata
Commands:
  vcm train --model-name "test_v1" \
            --dataset "data/test.csv" \
            --script test_train.py \
            --metrics metrics.json
Expected:
  - Script executes successfully
  - Model file detected
  - Metadata captured (Git, DVC, metrics, env)
  - test_v1.pkl.vcm.json created
  - Database entry inserted
  - Output: "✅ Model tracked successfully"
```

### CLI Test 3: `vcm train` - With Hyperparameters
```python
Test: vcm train accepts hyperparameters
Commands:
  vcm train --model-name "test_v2" \
            --dataset "data/test.csv" \
            --script test_train.py \
            --metrics metrics.json \
            --params lr=0.001 epochs=50 batch_size=32
Expected:
  - Hyperparameters captured in metadata
  - Values in metadata.hyperparameters match input
  - JSON format correct
```

### CLI Test 4: `vcm models` - List All
```python
Test: vcm models lists all tracked models
Setup: Database with 3 models
Command:
  vcm models
Expected:
  - Table format output
  - Shows: Name, Accuracy, Dataset, Git Commit, Timestamp
  - All 3 models listed
  - Sorted by timestamp (newest first)
```

### CLI Test 5: `vcm models` - Filter by Dataset
```python
Test: vcm models filters by dataset
Setup: 3 models on 2 different datasets
Command:
  vcm models --dataset "data/train_v2.1"
Expected:
  - Only models trained on that dataset shown
  - Count correct
  - Filter applied correctly
```

### CLI Test 6: `vcm models` - Best Model
```python
Test: vcm models --best shows highest accuracy
Setup: Models with accuracies [0.85, 0.92, 0.88]
Command:
  vcm models --best
Expected:
  - Returns model with 0.92 accuracy
  - Shows full metadata
```

### CLI Test 7: `vcm lineage`
```python
Test: vcm lineage displays model lineage
Command:
  vcm lineage models/test_v1.pkl
Expected:
  - Formatted output showing:
    * Model name and file
    * Git commit and branch
    * DVC files and hashes
    * Training timestamp and user
    * Metrics
    * Hyperparameters
  - All info correct
```

### CLI Test 8: `vcm compare`
```python
Test: vcm compare shows differences between two models
Command:
  vcm compare models/test_v1.pkl models/test_v2.pkl
Expected:
  - Side-by-side comparison
  - Shows differences in:
    * Metrics
    * Hyperparameters
    * Dataset
    * Code (git commit)
  - Highlights improvements/regressions
```

### CLI Test 9: `vcm info`
```python
Test: vcm info shows model metadata
Command:
  vcm info models/test_v1.pkl
Expected:
  - Displays full metadata JSON or formatted
  - All fields visible
  - Readable format
```

### CLI Test 10: `vcm export`
```python
Test: vcm export exports metadata to file
Command:
  vcm export models/test_v1.pkl --output model_metadata.json
Expected:
  - JSON file created
  - Content matches database record
  - File is valid JSON
```

---

## PART 4: ERROR HANDLING TESTS

### EH-1: Git Not Initialized
```python
Test: Graceful handling when Git not initialized
Setup: Non-git directory
Command: vcm train ...
Expected:
  - Warning: "Git repository not found"
  - Training continues
  - metadata.code.git_commit = None
  - No training failure
```

### EH-2: DVC Not Installed
```python
Test: Graceful handling when DVC not installed
Expected:
  - Warning: "DVC not installed"
  - Training continues
  - metadata.data.dvc_files = []
  - No training failure
```

### EH-3: Model File Not Found
```python
Test: Error when training script doesn't produce model
Command: vcm train --script bad_script.py ...
Expected:
  - Clear error: "Model file not created by training script"
  - Suggestion: "Expected model at [path]"
  - No partial database entry
```

### EH-4: Corrupted Database
```python
Test: Recover from corrupted .vcm/vcm.db
Setup: Manually corrupt database file
Command: vcm models
Expected:
  - Error caught gracefully
  - Option to rebuild: "vcm repair"
  - Message: "Database corrupted. Run: vcm repair"
```

### EH-5: Duplicate Model Name
```python
Test: Handle duplicate model names
Setup: Attempt to train two models with same name on same date
Expected:
  - Automatic versioning: model_v1, model_v1_001, etc.
  - Or error with guidance: "Model already exists. Use --force to overwrite"
  - Decision: AUTO-VERSION (don't force overwrite)
```

---

## PART 5: END-TO-END TESTS

### E2E-1: Real Project Scenario
```python
Test: Complete ML workflow with VCM
Scenario:
  1. Initialize empty project
  2. Setup Git repo
  3. Create mock training data
  4. Train model v1 with DVC data
  5. Train model v2 with improved hyperparams
  6. Train model v3 with new dataset
  7. Compare all three models
  8. Query for best model
  9. Export results

Expected:
  - All commands succeed
  - All models tracked correctly
  - Queries return accurate results
  - Lineage chains are complete
  - No data loss
  - Performance: Total time < 5 seconds
```

### E2E-2: Reproduce Exact Scenario
```python
Test: Can retrieve all metadata from saved model
Scenario:
  1. Train model_v1
  2. Save to disk
  3. Delete .vcm/vcm.db
  4. Manually inspect model_v1.pkl.vcm.json
  5. Restore database: vcm restore
  6. Query for model_v1

Expected:
  - Metadata survives database loss
  - Can restore from .vcm.json files
  - All info recoverable
```

### E2E-3: Multiple Users Scenario
```python
Test: Track models from different users
Scenario:
  1. User alice trains model_alice_v1
  2. User bob trains model_bob_v1
  3. Query all models

Expected:
  - Both models tracked separately
  - User info captured correctly
  - No conflicts or overwrites
```

---

## PART 6: PERFORMANCE TESTS

### PERF-1: Database Query Performance
```python
Test: Query performance with increasing data
Scenarios:
  - 10 models: Query should take < 10ms
  - 100 models: Query should take < 50ms
  - 1000 models: Query should take < 200ms

Command: vcm models --best
Expected:
  - Results within time limits
  - Index usage optimized
```

### PERF-2: Metadata Capture Overhead
```python
Test: Time to capture metadata
Scenario: Training time 1 hour
Overhead for metadata capture should be < 5 seconds

Expected:
  - Git commit lookup: < 100ms
  - DVC hash lookup: < 2s
  - Metadata JSON creation: < 100ms
  - Database insert: < 100ms
  - Total overhead: < 2.5 seconds
```

---

## TEST EXECUTION CHECKLIST

Before each commit:

```
[ ] All unit tests pass: pytest vcm/tests/unit/ -v
[ ] All integration tests pass: pytest vcm/tests/integration/ -v
[ ] All CLI tests pass: pytest vcm/tests/cli/ -v
[ ] Error handling tested: pytest vcm/tests/errors/ -v
[ ] Code coverage >= 80%: pytest --cov=vcm
[ ] No new warnings: pytest -W error::Warning
[ ] Linting clean: flake8 vcm/ --max-line-length=100
[ ] Type checking: mypy vcm/ --strict
```

---

## TEST DATA & FIXTURES

### Fixture: Test Git Repo
```python
@pytest.fixture
def test_git_repo(tmp_path):
    """Create a temporary Git repo for testing"""
    repo = Repo.init(tmp_path)
    # Commit initial file
    (tmp_path / "README.md").write_text("Test project")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    return repo
```

### Fixture: Test DVC Repo
```python
@pytest.fixture
def test_dvc_repo(test_git_repo):
    """Initialize DVC in test Git repo"""
    repo = Repo.init(test_git_repo.working_dir)
    # Add dummy data file
    data_file = test_git_repo.working_dir / "data" / "test.csv"
    data_file.parent.mkdir(exist_ok=True)
    data_file.write_text("id,value\n1,100\n2,200")
    # dvc add file
    return test_git_repo
```

### Fixture: Test Metadata
```python
@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing"""
    return MetadataModel(
        model_name="test_model",
        model_hash="sha256:abc123",
        metrics={"accuracy": 0.94},
        git_commit="abc123def456",
        git_branch="main",
        dvc_files=[],
        training_timestamp=datetime.now()
    )
```

---

## END OF TEST CASES

**Next Step:** Start implementation with Week 1 unit tests. Run tests after each function.
