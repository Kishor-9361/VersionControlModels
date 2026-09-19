# VCM Feature: Model Evolution Timeline

**Feature Name:** Model Progression Tracking with Change Annotations 
**Status:** New Enhancement (Phase 2.1) 
**Priority:** High - Solves critical workflow tracking gap 
**Estimated Implementation:** 3-4 days 

---

## 1. PROBLEM STATEMENT

### Current State (What's Missing)
When training multiple models during a session/project, developers lose track of:
- **Sequence:** Which model was trained first? In what order?
- **Rationale:** Why did we move from model A to model B?
- **Changes:** What actually changed between consecutive attempts?
- **Context:** Was it data, code, hyperparameters, or all three?

### User Pain Point (Real Scenario)
```
Developer Alice trains 5 models across 2 weeks:
- classifier_v1 (91.2%)
- classifier_v2 (92.8%)
- classifier_v3 (93.1%) ← Best
- classifier_v4 (91.5%) ← Regression!
- classifier_v5 (92.1%)

Later she asks:
"Why did I create v4? It was worse than v3.
Why did I go back to v5?
What was I thinking?"

Current VCM: "Model info shows metrics and git commit"
NEEDED: "Timeline showing progression + reasoning"
```

### Why This Matters
- **Research Reproducibility:** Understand the thought process
- **Decision Tracking:** Justify model selection
- **Prevent Regressions:** See when/why performance dropped
- **Knowledge Transfer:** Explain to team members the evolution
- **Audit Trail:** Compliance requirement for ML pipelines

---

## 2. SOLUTION ARCHITECTURE

### Feature: `vcm timeline` Command

```bash
# Show full model progression
vcm timeline

# Show for specific session
vcm timeline --session "Tuesday morning"

# Show for date range
vcm timeline --since "2 weeks ago"

# Export as visualization
vcm timeline --format html --output timeline.html

# With detailed reasoning
vcm timeline --show-reasoning
```

### Data Model: Model Evolution Entry

```python
@dataclass
class EvolutionEntry:
 """Represents one step in model evolution"""
 position: int # 1st, 2nd, 3rd model in sequence
 model_name: str
 timestamp: datetime
 accuracy: float
 metrics: Dict[str, float]
 
 # Why we moved to this model
 reasoning: Optional[str] # Optional note: "Testing lower learning rate"
 
 # What changed from previous model
 changes: Optional[ModelDifference]
 
 # Previous model reference
 previous_model: Optional[str]
 next_model: Optional[str]
 
 # Session context
 session_id: Optional[str]
 git_commit: str
```

### Timeline Query Result

```python
@dataclass
class ModelTimeline:
 """Complete evolution timeline"""
 entries: List[EvolutionEntry] # Ordered by training timestamp
 total_models: int
 best_model: str
 worst_model: str
 accuracy_improvement: float # Best - first
 accuracy_delta_over_time: List[float]
 session_ids: List[str] # Sessions involved
 date_range: Tuple[datetime, datetime]
```

---

## 3. DATABASE SCHEMA UPDATE

### New Table: `model_evolution`

```sql
CREATE TABLE model_evolution (
 id INTEGER PRIMARY KEY,
 model_id INTEGER NOT NULL,
 position_in_timeline INTEGER, -- 1, 2, 3, etc.
 reasoning TEXT, -- Optional: Why we moved to this model
 reasoning_timestamp DATETIME, -- When reasoning was added
 reasoning_added_by TEXT, -- Who added the note
 previous_model_id INTEGER, -- FK to previous model
 next_model_id INTEGER, -- FK to next model
 session_id TEXT, -- Which session (if any)
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 
 FOREIGN KEY(model_id) REFERENCES models(id),
 FOREIGN KEY(previous_model_id) REFERENCES models(id),
 FOREIGN KEY(next_model_id) REFERENCES models(id),
 FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_timeline_position ON model_evolution(position_in_timeline);
CREATE INDEX idx_timeline_session ON model_evolution(session_id);
```

### Metadata Schema Update

```json
{
 "model_name": "classifier_v3",
 "metrics": {"accuracy": 0.93},
 
 // NEW: Timeline context
 "evolution": {
 "position_in_timeline": 3,
 "position_in_session": 3,
 "reasoning": "Feature engineering improved accuracy",
 "previous_model": "classifier_v2",
 "next_model": "classifier_v4",
 "accuracy_improvement_from_previous": 0.002,
 "changes_summary": "Code +1 file, Hyperparameters: lr 0.001->0.0005, Data unchanged"
 }
}
```

---

## 4. FEATURE SPECIFICATIONS

### 4.1 Core Command: `vcm timeline`

**Syntax:**
```bash
vcm timeline [OPTIONS]
```

**Options:**
```
--session NAME # Show models only from this session
--since DATE # Show models trained since date (e.g., "1 week ago")
--until DATE # Show models trained until date
--show-reasoning # Include why each model was trained
--show-changes # Include what changed between models
--format FORMAT # output (table, json, html, csv)
--output FILE # Export to file
--highlight-best # Highlight best performer
--highlight-worst # Highlight worst performer
--accuracy-range MIN-MAX # Filter by accuracy range
```

**Output Example (table format):**
```
Model Evolution Timeline
═════════════════════════════════════════════════════════════════

Position │ Model │ Accuracy │ Improvement │ When 
──────────┼────────────────────┼──────────┼─────────────┼────────────
 1 │ classifier_v1 │ 91.2% │ baseline │ Jan 15 09:15
 2 │ classifier_v2 │ 92.8% │ +1.6% ⬆ │ Jan 15 09:45
 │ │ │ │
 │ Why v2? │ Changed hyperparameters (lr: 0.01 → 0.001)
 │ │ │ │
 3 │ classifier_v3 │ 93.1% │ +0.3% ⬆ │ Jan 15 10:12
 │ BEST │ │ │
 │ │ │ │
 │ Why v3? │ Feature engineering: Added scaling + normalization
 │ │ │ │
 4 │ classifier_v4 │ 91.5% │ -1.6% ⬇ │ Jan 15 10:45
 [WARNING] REGRESSION
 │ │ │ │
 │ Why v4? │ Testing different ensemble approach
 │ Note: │ Failed - reverted back to v3
 │ │ │ │
 5 │ classifier_v5 │ 92.1% │ -1.0% ⬇ │ Jan 15 11:15
 │ │ │ │
 │ Why v5? │ Hyperparameter tuning continued
 │ │ │ │

Summary
═══════════════════════════════════════════════════════════════
Total models: 5
Best model: classifier_v3 (93.1%)
Worst model: classifier_v1 (91.2%)
Overall improvement: +1.9%
Regressions: 1 (v4)
Best session: Tuesday morning (3 models)
Date range: 2026-01-15 09:15 - 11:15 (2h)
```

### 4.2 Add Reasoning Retroactively

**Command:**
```bash
vcm timeline-reason <MODEL_NAME> "<REASON>"
```

**Examples:**
```bash
# Add reason to existing model
vcm timeline-reason classifier_v4 "Testing ensemble approach for robustness check"

# Update existing reason
vcm timeline-reason classifier_v2 "Lower learning rate improved convergence" --force

# View reasoning
vcm timeline-reason classifier_v3 --show
```

**Interaction Pattern:**
```bash
# During training (optional annotation)
vcm train --model-name v2 --script train.py --reasoning "Trying lower learning rate"

# Or after training
vcm timeline-reason v2 "Trying lower learning rate"

# Later, add more context
vcm timeline-reason v2 "Trying lower learning rate - resulted in better convergence" --force
```

### 4.3 Timeline Analysis

**Command:**
```bash
vcm timeline analyze [OPTIONS]
```

**Generates:**
```
Timeline Analysis Report
═══════════════════════════════════════════════════════════════

 Improvement Trajectory:
 Steady improvement (v1→v3): +1.9%
 Regression (v4): -1.6%
 Recovery (v5): Partial recovery

 Root Cause Analysis:
 Best improvement (v2→v3): Feature engineering (+0.3%)
 Key insight: Preprocessing (scaling) more impactful than hyperparameters

[WARNING] Anomalies Detected:
 1. v4 regression: Ensemble approach unsuccessful
 2. v5: Incomplete recovery

 Recommendations:
 1. Use v3 for production (best accuracy 93.1%)
 2. Don't retry ensemble approach (v4 showed no benefit)
 3. Continue with v3 baseline + gradual feature engineering

 Experiment Efficiency:
 Total models: 5
 Successful improvements: 3/5 (60%)
 Wasted experiments: 1/5 (20%) - v4 regression
 Efficiency score: 60%
```

### 4.4 Visualization

**Command:**
```bash
vcm timeline --format html --output timeline.html --show-reasoning
```

**HTML Output Includes:**
- Timeline graph (accuracy vs model sequence)
- Model cards showing metrics, changes, and reasoning
- Improvement/regression indicators
- Session grouping visualization
- Interactive model comparison
- Export options (PNG, SVG)

**ASCII Visualization:**
```
Model Accuracy Over Time
════════════════════════════════════════

94% │ v3
 │ ╱╲
93% │ ╱╱ ╲╲
 │ ╱╱ ╲╲ v5
92% │ ╱╱╱ ╲╲
 │ ╱╱ ╲╲
91% │ v1 ───╱╱ v2 ╲ v4 [WARNING]
 │
 ├─────┬──────┬──────┬──────┬──────┬─────
 │ v1 │ v2 │ v3 │ v4 │ v5 │ time
 
Annotations below each model showing why moved to next
```

---

## 5. DATABASE QUERIES

### Query 1: Get Model Timeline (Ordered)

```python
def get_model_timeline(
 session_id: Optional[str] = None,
 since: Optional[datetime] = None,
 until: Optional[datetime] = None
) -> ModelTimeline:
 """
 Get chronologically ordered model progression
 """
 query = """
 SELECT 
 me.position_in_timeline,
 m.model_name,
 m.training_timestamp,
 m.accuracy,
 m.metadata_json,
 me.reasoning,
 me.previous_model_id,
 me.next_model_id,
 me.session_id
 FROM model_evolution me
 JOIN models m ON me.model_id = m.id
 WHERE 1=1
 """
 
 params = []
 
 if session_id:
 query += " AND me.session_id = ?"
 params.append(session_id)
 
 if since:
 query += " AND m.training_timestamp >= ?"
 params.append(since)
 
 if until:
 query += " AND m.training_timestamp <= ?"
 params.append(until)
 
 query += " ORDER BY me.position_in_timeline ASC"
 
 return ModelTimeline(...)
```

### Query 2: Add Reasoning

```python
def add_model_reasoning(model_name: str, reasoning: str, force: bool = False):
 """
 Add or update reasoning for model
 """
 model = db.get_model_by_name(model_name)
 evolution = db.query_evolution_entry(model_id=model.id)
 
 if evolution.reasoning and not force:
 raise ValueError(f"Reasoning already exists: {evolution.reasoning}")
 
 db.update_evolution_reasoning(
 model_id=model.id,
 reasoning=reasoning,
 timestamp=datetime.now(),
 user=get_current_user()
 )
```

### Query 3: Auto-detect Timeline Gaps

```python
def detect_timeline_issues() -> List[str]:
 """
 Identify anomalies in model progression
 """
 timeline = get_model_timeline()
 issues = []
 
 for i, entry in enumerate(timeline.entries):
 # Detect regressions
 if i > 0 and entry.accuracy < timeline.entries[i-1].accuracy:
 improvement = entry.accuracy - timeline.entries[i-1].accuracy
 issues.append(f"Regression at {entry.model_name}: {improvement:.2%}")
 
 # Detect missing reasoning
 if not entry.reasoning:
 issues.append(f"No reasoning for {entry.model_name}")
 
 return issues
```

---

## 6. CLI IMPLEMENTATION

### File: `vcm/cli/timeline_commands.py` (NEW)

```python
import click
from vcm.db.database import Database
from vcm.models.timeline import ModelTimeline, EvolutionEntry
from vcm.utils.formatters import format_timeline_table, format_timeline_html

@click.command()
@click.option('--session', default=None, help='Filter by session')
@click.option('--since', default=None, help='Models trained since (e.g., "1 week ago")')
@click.option('--until', default=None, help='Models trained until')
@click.option('--format', type=click.Choice(['table', 'json', 'html', 'csv']), default='table')
@click.option('--output', default=None, help='Export to file')
@click.option('--show-reasoning', is_flag=True, help='Show why each model was trained')
@click.option('--show-changes', is_flag=True, help='Show what changed between models')
@click.option('--highlight-best', is_flag=True, help='Highlight best model')
def timeline(session, since, until, format, output, show_reasoning, show_changes, highlight_best):
 """Show model evolution timeline"""
 db = Database()
 timeline = db.get_model_timeline(session_id=session, since=since, until=until)
 
 if format == 'table':
 output_text = format_timeline_table(
 timeline,
 show_reasoning=show_reasoning,
 show_changes=show_changes,
 highlight_best=highlight_best
 )
 elif format == 'html':
 output_text = format_timeline_html(timeline)
 elif format == 'json':
 output_text = timeline.to_json()
 
 if output:
 with open(output, 'w') as f:
 f.write(output_text)
 click.echo(f"[x] Timeline exported to {output}")
 else:
 click.echo(output_text)


@click.command()
@click.argument('model_name')
@click.argument('reasoning')
@click.option('--force', is_flag=True, help='Override existing reasoning')
def timeline_reason(model_name, reasoning, force):
 """Add reasoning for why a model was trained"""
 db = Database()
 db.add_model_reasoning(model_name, reasoning, force=force)
 click.echo(f"[x] Added reasoning to {model_name}")


@click.command()
@click.option('--session', default=None)
@click.option('--output', default=None)
def timeline_analyze(session, output):
 """Analyze model evolution trajectory"""
 db = Database()
 timeline = db.get_model_timeline(session_id=session)
 analysis = analyze_timeline(timeline)
 
 output_text = format_analysis_report(analysis)
 
 if output:
 with open(output, 'w') as f:
 f.write(output_text)
 else:
 click.echo(output_text)
```

---

## 7. TEST CASES

### Unit Tests: `vcm/tests/unit/test_timeline.py`

```python
def test_timeline_query_ordering():
 """Models returned in chronological order"""
 # Create 3 models with known timestamps
 models = create_ordered_models(3)
 timeline = db.get_model_timeline()
 
 assert timeline.entries[0].model_name == models[0].name
 assert timeline.entries[1].model_name == models[1].name
 assert timeline.entries[2].model_name == models[2].name

def test_timeline_accuracy_improvement():
 """Calculate improvement from first to last model"""
 timeline = create_timeline_with_metrics([0.91, 0.92, 0.93])
 
 assert timeline.accuracy_improvement == pytest.approx(0.02) # 93% - 91%
 assert timeline.best_model == "v3"
 assert timeline.worst_model == "v1"

def test_add_reasoning_to_model():
 """Reasoning can be added to model"""
 db.add_model_reasoning("v2", "Testing lower learning rate")
 entry = db.get_evolution_entry("v2")
 
 assert entry.reasoning == "Testing lower learning rate"

def test_timeline_with_session_filter():
 """Timeline filters by session"""
 session1_models = create_models(3, session="session1")
 session2_models = create_models(2, session="session2")
 
 timeline = db.get_model_timeline(session_id="session1")
 
 assert len(timeline.entries) == 3
 assert all(e.session_id == "session1" for e in timeline.entries)

def test_detect_regression():
 """Detect accuracy regression"""
 timeline = create_timeline_with_metrics([0.91, 0.93, 0.90]) # v3 regression
 issues = detect_timeline_issues(timeline)
 
 assert any("regression" in issue.lower() for issue in issues)

def test_missing_reasoning_detection():
 """Detect models without reasoning"""
 model = create_model("v2", reasoning=None)
 issues = detect_timeline_issues()
 
 assert any("reasoning" in issue.lower() for issue in issues)
```

### Integration Tests: `vcm/tests/integration/test_timeline_integration.py`

```python
def test_full_timeline_workflow():
 """End-to-end timeline tracking workflow"""
 # Train first model
 vcm_train("v1", "train.py", "data.csv")
 
 # Train second model with reasoning
 vcm_train("v2", "train.py", "data.csv", 
 reasoning="Lower learning rate")
 
 # Train third model
 vcm_train("v3", "train.py", "data.csv",
 reasoning="Feature engineering")
 
 # Get timeline
 timeline = db.get_model_timeline()
 
 # Verify ordering
 assert timeline.entries[0].model_name == "v1"
 assert timeline.entries[1].model_name == "v2"
 assert timeline.entries[2].model_name == "v3"
 
 # Verify reasoning captured
 assert timeline.entries[1].reasoning == "Lower learning rate"
 assert timeline.entries[2].reasoning == "Feature engineering"

def test_timeline_cli_output():
 """CLI timeline command produces correct output"""
 result = run_cli(['timeline', '--show-reasoning', '--format', 'table'])
 
 assert "Model Evolution Timeline" in result
 assert "v1" in result
 assert "Lower learning rate" in result

def test_timeline_html_export():
 """Timeline exported as interactive HTML"""
 export_file = "timeline.html"
 run_cli(['timeline', '--format', 'html', '--output', export_file])
 
 assert os.path.exists(export_file)
 with open(export_file) as f:
 content = f.read()
 assert "<html>" in content
 assert "accuracy" in content.lower()
```

### Advanced Scenario Tests: `vcm/tests/advanced/test_scenario_9_model_evolution.py`

```python
def test_scenario_9_model_evolution_tracking():
 """Real workflow: Track model progression from start to finish"""
 # Setup: Create iris project
 project = setup_iris_project()
 os.chdir(project)
 
 # Step 1: Train baseline model
 os.system("vcm train --model-name v1 --script train.py --metrics metrics.json")
 
 # Step 2: Improve with lower LR
 os.system("vcm train --model-name v2 --script train.py --metrics metrics.json")
 os.system("vcm timeline-reason v2 'Testing lower learning rate'")
 
 # Step 3: Add feature engineering
 os.system("vcm train --model-name v3 --script train.py --metrics metrics.json")
 os.system("vcm timeline-reason v3 'Added feature scaling and normalization'")
 
 # Step 4: Failed experiment
 os.system("vcm train --model-name v4 --script train.py --metrics metrics.json")
 os.system("vcm timeline-reason v4 'Testing ensemble (FAILED - reverted)'")
 
 # Step 5: Recovery
 os.system("vcm train --model-name v5 --script train.py --metrics metrics.json")
 os.system("vcm timeline-reason v5 'Back to feature engineering with tuning'")
 
 # Verify: Get timeline
 timeline_output = os.popen("vcm timeline --show-reasoning").read()
 
 # Assertions
 assert "Model Evolution Timeline" in timeline_output
 assert "v1" in timeline_output
 assert "v2" in timeline_output
 assert "v3" in timeline_output
 assert "Testing lower learning rate" in timeline_output
 assert "Feature scaling" in timeline_output
 assert "FAILED" in timeline_output
 
 # Verify database entries
 timeline = db.get_model_timeline()
 assert len(timeline.entries) == 5
 assert timeline.best_model == "v3"
 assert timeline.accuracy_improvement > 0
 
 # Verify regression detection
 issues = detect_timeline_issues(timeline)
 assert any("v4" in issue for issue in issues)
 
 print("[x] Scenario 9: Model evolution tracking - PASSED")
```

---

## 8. IMPLEMENTATION ROADMAP

### Phase 2.1 (3-4 days)

**Day 1:** Data Model & Database
- [ ] Create `evolution.py` with `EvolutionEntry`, `ModelTimeline`, `ModelDifference`
- [ ] Update database schema (add `model_evolution` table)
- [ ] Add database queries (`get_model_timeline`, `add_reasoning`, etc.)

**Day 2:** Core Functionality
- [ ] Implement timeline detection logic
- [ ] Auto-link consecutive models
- [ ] Calculate improvements/regressions

**Day 3:** CLI Commands
- [ ] Implement `vcm timeline` command
- [ ] Implement `vcm timeline-reason` command
- [ ] Implement `vcm timeline analyze` command
- [ ] Add formatters for table/HTML/JSON

**Day 4:** Testing & Integration
- [ ] Unit tests (5+ test cases)
- [ ] Integration tests (3+ workflows)
- [ ] Advanced scenario test
- [ ] Performance testing

### Success Criteria
- 10+ tests passing
- >90% code coverage for timeline module
- All CLI commands working
- HTML export generating valid output
- Real iris scenario working end-to-end

---

## 9. IMPACT & BENEFITS

### What Gets Solved
[x] **Lost Context:** Know the full evolution of models 
[x] **Decision Rationale:** Understand why each model was created 
[x] **Regression Analysis:** Identify when/why performance dropped 
[x] **Research Reproducibility:** Justify model selection 
[x] **Team Knowledge:** Share experiment progression 
[x] **Audit Trail:** Complete history for compliance 

### New Use Cases Enabled
1. **Research Papers:** "We improved accuracy from 91% to 93% through feature engineering"
2. **Model Governance:** Track decision history for production deployments
3. **Team Communication:** "Here's why we chose this model over others"
4. **Experiment Management:** Dashboard showing experiment evolution
5. **ML Ops:** Automatic documentation of model selection process

---

## 10. EXAMPLE OUTPUTS

### Terminal Output

```
$ vcm timeline --show-reasoning

Model Evolution Timeline
═══════════════════════════════════════════════════════════════════

Position 1 │ classifier_v1
Accuracy │ 91.2%
Date │ 2026-01-15 09:15:00
Reasoning │ (none - baseline model)
Session │ Tuesday morning

Position 2 │ classifier_v2 (+1.6% improvement)
Accuracy │ 92.8%
Date │ 2026-01-15 09:45:00
Reasoning │ Testing lower learning rate (0.01 → 0.001)
Changes │ Code: unchanged, Data: unchanged, Hyperparams: learning_rate changed
Session │ Tuesday morning

Position 3 │ classifier_v3 [BEST] (+0.3% improvement)
Accuracy │ 93.1%
Date │ 2026-01-15 10:12:00
Reasoning │ Feature engineering: Added StandardScaler + feature normalization
Changes │ Code: +preprocessing.py, Data: unchanged, Hyperparams: unchanged
Session │ Tuesday morning

Position 4 │ classifier_v4 (-1.6% regression) [WARNING]
Accuracy │ 91.5%
Date │ 2026-01-15 10:45:00
Reasoning │ Testing ensemble approach for robustness
Changes │ Code: new ensemble.py, Data: unchanged, Hyperparams: weights=[0.5,0.3,0.2]
Session │ Tuesday morning
Note │ Failed - reverted to v3 approach

Position 5 │ classifier_v5 (-1.0% vs best, +0.9% vs baseline)
Accuracy │ 92.1%
Date │ 2026-01-15 11:15:00
Reasoning │ Continued hyperparameter tuning based on v3 foundation
Changes │ Code: unchanged, Data: unchanged, Hyperparams: batch_size 32→64, epochs 50→100
Session │ Tuesday morning

═══════════════════════════════════════════════════════════════════
Summary:
 Total Models: 5
 Best Model: classifier_v3 (93.1%)
 Overall Improvement: +1.9% (from v1 to v3)
 Regressions: 1 (v4)
 Success Rate: 60% (3/5 improved)
 Session Duration: 2 hours
```

### HTML Export

```html
<div class="model-timeline">
 <h1>Model Evolution Timeline</h1>
 
 <div class="timeline-graph">
 <!-- SVG graph showing accuracy over time -->
 </div>
 
 <div class="model-cards">
 <div class="card model-v1">
 <h3>classifier_v1</h3>
 <p class="accuracy">91.2%</p>
 <p class="date">Jan 15, 09:15</p>
 <p class="reasoning">Baseline model</p>
 </div>
 
 <div class="card model-v2 improvement">
 <h3>classifier_v2 <span class="badge">+1.6%</span></h3>
 <p class="accuracy">92.8%</p>
 <p class="date">Jan 15, 09:45</p>
 <p class="reasoning">Testing lower learning rate</p>
 <div class="changes">
 <strong>Changes:</strong>
 <ul>
 <li>Learning rate: 0.01 → 0.001</li>
 </ul>
 </div>
 </div>
 
 <div class="card model-v3 best">
 <h3>classifier_v3 [BEST] <span class="badge">+0.3%</span></h3>
 <p class="accuracy">93.1%</p>
 <p class="date">Jan 15, 10:12</p>
 <p class="reasoning">Feature engineering: Added StandardScaler</p>
 </div>
 
 <div class="card model-v4 regression">
 <h3>classifier_v4 <span class="badge regression">-1.6%</span></h3>
 <p class="accuracy">91.5% [WARNING]</p>
 <p class="date">Jan 15, 10:45</p>
 <p class="reasoning">Testing ensemble (FAILED)</p>
 </div>
 
 <div class="card model-v5">
 <h3>classifier_v5 <span class="badge">-1.0%</span></h3>
 <p class="accuracy">92.1%</p>
 <p class="date">Jan 15, 11:15</p>
 <p class="reasoning">Hyperparameter tuning</p>
 </div>
 </div>
 
 <div class="analysis">
 <h2>Analysis</h2>
 <ul>
 <li>[x] Steady improvement v1→v3 (+1.9%)</li>
 <li>[WARNING] Regression with v4 (-1.6%)</li>
 <li> Total efficiency: 60%</li>
 </ul>
 </div>
</div>
```

---

## 11. BACKWARD COMPATIBILITY

[x] All changes are backward compatible:
- Existing models continue to work
- Evolution table is optional (populated on demand)
- Reasoning is optional
- No breaking changes to CLI

---

## 12. END OF SPECIFICATION

**This feature adds critical tracking capability to VCM:**
- Captures model progression
- Stores decision rationale
- Enables analysis and insights
- Solves "lost context" problem

**Ready for agent implementation with these specifications.**
