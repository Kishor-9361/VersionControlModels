# VCM Model Evolution Timeline - Agent Implementation Guide

**Feature:** Model Progression Tracking with Change Annotations 
**Implementation Duration:** 3-4 days (Phase 2.1) 
**Priority:** High - Critical workflow tracking feature 
**Status:** Ready for Agent Development 

---

## OBJECTIVE

Add capability to track and visualize model evolution through development cycle, capture reasoning for why each model was trained, and analyze progression patterns.

**Problem Solved:**
```
Before: "Which model was trained first? Why did I train model v4 if v3 was better?"
After: vcm timeline --show-reasoning
 (Shows complete progression with annotations and reasoning)
```

---

## REFERENCE DOCUMENTS

### Primary Specification
- **vcm_model_evolution_timeline_spec.md** - Complete feature specification (read FIRST)

### Supporting Documentation
- vcm_phase2_agent_guide.md - General agent guidelines
- vcm_cli_documentation.md - CLI patterns and conventions
- vcm_testing_strategy.md - Testing approach
- vcm_advanced_testing.md - Scenario testing patterns

---

## DAY-BY-DAY IMPLEMENTATION PLAN

### DAY 1: Data Model & Database Layer

**Reading:** vcm_model_evolution_timeline_spec.md sections 2, 3, 5

**Task 1.1: Create Data Models** (1-2 hours)

**File:** `vcm/models/evolution.py` (NEW)

Create these dataclasses (frozen, immutable):

```python
@dataclass(frozen=True)
class ModelDifference:
 """What changed between two consecutive models"""
 code_changed: bool
 code_files: List[str]
 git_commits: List[str]
 
 data_changed: bool
 data_files: List[str]
 data_hashes_changed: Dict[str, Tuple[str, str]] # {path: (old_hash, new_hash)}
 
 hyperparams_changed: Dict[str, Tuple[Any, Any]] # {param: (old_val, new_val)}
 
 environment_changed: bool

@dataclass(frozen=True)
class Annotation:
 """User note about a model in timeline"""
 timestamp: datetime
 text: str
 added_by: str

@dataclass(frozen=True)
class EvolutionEntry:
 """One step in model progression"""
 position: int # 1st, 2nd, 3rd, etc.
 model_name: str
 model_id: int
 timestamp: datetime
 accuracy: float
 metrics: Dict[str, float]
 
 # Reasoning/context
 reasoning: Optional[str] = None # Why we trained this model
 reasoning_added_by: Optional[str] = None
 reasoning_timestamp: Optional[datetime] = None
 
 # Relationships
 previous_model: Optional[str] = None
 next_model: Optional[str] = None
 previous_model_accuracy: Optional[float] = None
 accuracy_improvement: Optional[float] = None
 
 # Changes from previous
 changes: Optional[ModelDifference] = None
 
 # Context
 session_id: Optional[str] = None
 git_commit: str = ""
 
 def __post_init__(self):
 # Calculate accuracy improvement
 if self.previous_model_accuracy:
 delta = self.accuracy - self.previous_model_accuracy
 object.__setattr__(self, 'accuracy_improvement', delta)

@dataclass(frozen=True)
class ModelTimeline:
 """Complete evolution progression"""
 entries: List[EvolutionEntry]
 total_models: int
 best_model: str
 worst_model: str
 best_accuracy: float
 worst_accuracy: float
 accuracy_improvement: float # best - first
 date_range: Tuple[datetime, datetime]
 session_ids: Set[str]
 
 def to_dict(self) -> Dict:
 """Convert to dictionary"""
 return {
 'entries': [e.__dict__ for e in self.entries],
 'total_models': self.total_models,
 'best_model': self.best_model,
 'accuracy_improvement': self.accuracy_improvement,
 }
```

**Verification:**
```bash
pytest vcm/tests/unit/test_evolution_models.py -v
# Expected: Model initialization, serialization tests pass
```

**Task 1.2: Database Schema Update** (1-2 hours)

**File:** `vcm/db/database.py` (UPDATE)

Add to `Database.init()`:

```python
def init(self):
 # ... existing code ...
 
 # Create evolution tracking table
 cursor.execute("""
 CREATE TABLE IF NOT EXISTS model_evolution (
 id INTEGER PRIMARY KEY,
 model_id INTEGER NOT NULL UNIQUE,
 position_in_timeline INTEGER NOT NULL,
 
 reasoning TEXT,
 reasoning_added_by TEXT,
 reasoning_timestamp DATETIME,
 
 previous_model_id INTEGER,
 next_model_id INTEGER,
 
 session_id TEXT,
 git_commit TEXT,
 
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 
 FOREIGN KEY(model_id) REFERENCES models(id),
 FOREIGN KEY(previous_model_id) REFERENCES models(id),
 FOREIGN KEY(next_model_id) REFERENCES models(id),
 FOREIGN KEY(session_id) REFERENCES sessions(session_id),
 
 UNIQUE(position_in_timeline)
 )
 """)
 
 cursor.execute("""
 CREATE INDEX IF NOT EXISTS idx_evolution_position 
 ON model_evolution(position_in_timeline)
 """)
 
 cursor.execute("""
 CREATE INDEX IF NOT EXISTS idx_evolution_session 
 ON model_evolution(session_id)
 """)
```

Add methods to `Database` class:

```python
def create_evolution_entry(
 self,
 model_id: int,
 position: int,
 previous_model_id: Optional[int] = None,
 next_model_id: Optional[int] = None,
 session_id: Optional[str] = None,
 git_commit: str = ""
) -> int:
 """Create evolution tracking entry for model"""
 cursor = self.conn.cursor()
 cursor.execute("""
 INSERT OR REPLACE INTO model_evolution 
 (model_id, position_in_timeline, previous_model_id, next_model_id, session_id, git_commit)
 VALUES (?, ?, ?, ?, ?, ?)
 """, (model_id, position, previous_model_id, next_model_id, session_id, git_commit))
 self.conn.commit()
 return cursor.lastrowid

def add_reasoning(
 self,
 model_id: int,
 reasoning: str,
 user: str = "",
 force: bool = False
) -> bool:
 """Add reasoning for why model was trained"""
 cursor = self.conn.cursor()
 
 # Check if already exists
 cursor.execute(
 "SELECT reasoning FROM model_evolution WHERE model_id = ?",
 (model_id,)
 )
 existing = cursor.fetchone()
 
 if existing and existing[0] and not force:
 raise ValueError(f"Reasoning already exists. Use force=True to override.")
 
 cursor.execute("""
 UPDATE model_evolution
 SET reasoning = ?, reasoning_added_by = ?, reasoning_timestamp = ?
 WHERE model_id = ?
 """, (reasoning, user, datetime.now(), model_id))
 
 self.conn.commit()
 return True

def get_evolution_entry(self, model_id: int) -> Optional[Dict]:
 """Get evolution entry for model"""
 cursor = self.conn.cursor()
 cursor.execute(
 "SELECT * FROM model_evolution WHERE model_id = ?",
 (model_id,)
 )
 return cursor.fetchone()

def auto_detect_timeline(self, session_id: Optional[str] = None) -> ModelTimeline:
 """Auto-detect model progression from training timestamps"""
 # Query all models, order by training timestamp
 # Auto-assign positions
 # Link previous/next
 # Calculate improvements
 pass
```

**Verification:**
```bash
pytest vcm/tests/unit/test_database_evolution.py -v
# Expected: Table creation, CRUD operations pass
```

---

### DAY 2: Core Timeline Logic

**Reading:** vcm_model_evolution_timeline_spec.md sections 5, 6

**Task 2.1: Timeline Queries** (2 hours)

**File:** `vcm/models/timeline.py` (NEW)

```python
class TimelineStore:
 """Query and manage model evolution timelines"""
 
 def __init__(self, db: Database):
 self.db = db
 
 def get_model_timeline(
 self,
 session_id: Optional[str] = None,
 since: Optional[datetime] = None,
 until: Optional[datetime] = None,
 accuracy_range: Optional[Tuple[float, float]] = None
 ) -> ModelTimeline:
 """Get chronologically ordered model progression"""
 query = """
 SELECT 
 me.position_in_timeline,
 m.id,
 m.model_name,
 m.training_timestamp,
 m.accuracy,
 m.metadata_json,
 me.reasoning,
 me.reasoning_added_by,
 me.reasoning_timestamp,
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
 
 if accuracy_range:
 query += " AND m.accuracy BETWEEN ? AND ?"
 params.extend(accuracy_range)
 
 query += " ORDER BY me.position_in_timeline ASC"
 
 results = self.db.query(query, params)
 
 # Build evolution entries
 entries = []
 for i, row in enumerate(results):
 # Calculate improvement from previous
 prev_accuracy = entries[-1].accuracy if entries else None
 improvement = None
 if prev_accuracy:
 improvement = row[4] - prev_accuracy
 
 entry = EvolutionEntry(
 position=row[0],
 model_id=row[1],
 model_name=row[2],
 timestamp=row[3],
 accuracy=row[4],
 metrics=json.loads(row[5]).get('metrics', {}),
 reasoning=row[6],
 reasoning_added_by=row[7],
 reasoning_timestamp=row[8],
 previous_model=entries[-1].model_name if entries else None,
 previous_model_accuracy=prev_accuracy,
 accuracy_improvement=improvement,
 session_id=row[11],
 git_commit=json.loads(row[5]).get('code', {}).get('git_commit', '')
 )
 entries.append(entry)
 
 # Calculate statistics
 accuracies = [e.accuracy for e in entries]
 
 return ModelTimeline(
 entries=entries,
 total_models=len(entries),
 best_model=entries[accuracies.index(max(accuracies))].model_name if entries else None,
 worst_model=entries[accuracies.index(min(accuracies))].model_name if entries else None,
 best_accuracy=max(accuracies) if accuracies else 0,
 worst_accuracy=min(accuracies) if accuracies else 0,
 accuracy_improvement=(max(accuracies) - min(accuracies)) if len(accuracies) > 1 else 0,
 date_range=(entries[0].timestamp, entries[-1].timestamp) if entries else (None, None),
 session_ids=set(e.session_id for e in entries if e.session_id)
 )
 
 def detect_regressions(self, timeline: ModelTimeline) -> List[Dict]:
 """Identify accuracy regressions in progression"""
 regressions = []
 
 for i, entry in enumerate(timeline.entries):
 if i > 0:
 prev_entry = timeline.entries[i-1]
 if entry.accuracy < prev_entry.accuracy:
 regressions.append({
 'model': entry.model_name,
 'accuracy': entry.accuracy,
 'previous_accuracy': prev_entry.accuracy,
 'delta': entry.accuracy - prev_entry.accuracy,
 'severity': 'high' if abs(entry.accuracy_improvement) > 0.02 else 'low'
 })
 
 return regressions
 
 def detect_timeline_gaps(self, timeline: ModelTimeline) -> List[str]:
 """Find anomalies: missing reasoning, regressions, etc."""
 issues = []
 
 for entry in timeline.entries:
 # Missing reasoning
 if not entry.reasoning:
 issues.append(f"No reasoning for {entry.model_name}")
 
 # Regressions
 regressions = self.detect_regressions(timeline)
 for reg in regressions:
 issues.append(f"Regression at {reg['model']}: {reg['delta']:+.2%}")
 
 return issues
```

**Task 2.2: Timeline Detection & Linking** (1-2 hours)

Add to `TimelineStore`:

```python
def auto_detect_and_link_timeline(self, session_id: Optional[str] = None):
 """
 Automatically detect model progression from timestamps
 and link as evolution chain
 """
 # Get all models sorted by timestamp
 query = """
 SELECT id, model_name, training_timestamp, accuracy
 FROM models
 WHERE session_id = ? OR ? IS NULL
 ORDER BY training_timestamp ASC
 """
 
 models = self.db.query(query, (session_id, session_id))
 
 # Assign positions and link
 for position, (model_id, model_name, timestamp, accuracy) in enumerate(models, 1):
 prev_model_id = models[position - 2][0] if position > 1 else None
 next_model_id = models[position][0] if position < len(models) else None
 
 self.db.create_evolution_entry(
 model_id=model_id,
 position=position,
 previous_model_id=prev_model_id,
 next_model_id=next_model_id,
 session_id=session_id
 )
```

**Verification:**
```bash
pytest vcm/tests/unit/test_timeline_logic.py -v
# Expected: Timeline queries, detection, regression finding pass
```

---

### DAY 3: CLI Commands & Formatters

**Reading:** vcm_model_evolution_timeline_spec.md sections 4, 6

**Task 3.1: CLI Commands** (2 hours)

**File:** `vcm/cli/timeline_commands.py` (NEW)

```python
import click
from vcm.db.database import Database
from vcm.models.timeline import TimelineStore, ModelTimeline
from vcm.utils.formatters import format_timeline_table, format_timeline_html

@click.group()
def timeline():
 """Model evolution timeline commands"""
 pass

@timeline.command()
@click.option('--session', default=None, help='Filter by session name')
@click.option('--since', default=None, help='Models trained since (e.g., "1 week ago")')
@click.option('--until', default=None, help='Models trained until')
@click.option('--format', type=click.Choice(['table', 'json', 'html', 'csv']), default='table')
@click.option('--output', default=None, help='Export to file')
@click.option('--show-reasoning', is_flag=True, help='Include reasoning annotations')
@click.option('--show-changes', is_flag=True, help='Show what changed between models')
@click.option('--highlight-best', is_flag=True, help='Highlight best model')
@click.option('--accuracy-range', default=None, help='Filter by accuracy range (e.g., 0.9-0.95)')
def show(session, since, until, format, output, show_reasoning, show_changes, highlight_best, accuracy_range):
 """Show model evolution timeline"""
 db = Database()
 store = TimelineStore(db)
 
 # Parse date filters
 since_dt = parse_date_filter(since) if since else None
 until_dt = parse_date_filter(until) if until else None
 acc_range = parse_accuracy_range(accuracy_range) if accuracy_range else None
 
 # Get timeline
 timeline = store.get_model_timeline(
 session_id=session,
 since=since_dt,
 until=until_dt,
 accuracy_range=acc_range
 )
 
 # Format output
 if format == 'table':
 output_text = format_timeline_table(
 timeline,
 show_reasoning=show_reasoning,
 show_changes=show_changes,
 highlight_best=highlight_best
 )
 elif format == 'html':
 output_text = format_timeline_html(timeline, show_reasoning=show_reasoning)
 elif format == 'json':
 output_text = json.dumps(timeline.to_dict(), indent=2, default=str)
 elif format == 'csv':
 output_text = format_timeline_csv(timeline)
 
 if output:
 with open(output, 'w') as f:
 f.write(output_text)
 click.echo(f"[x] Timeline exported to {output}")
 else:
 click.echo(output_text)


@timeline.command()
@click.argument('model_name')
@click.argument('reasoning')
@click.option('--force', is_flag=True, help='Override existing reasoning')
def reason(model_name, reasoning, force):
 """Add or update reasoning for a model"""
 db = Database()
 
 model = db.get_model_by_name(model_name)
 if not model:
 click.echo(f"[FAIL] Model not found: {model_name}")
 return
 
 db.add_reasoning(
 model_id=model.id,
 reasoning=reasoning,
 user=get_current_user(),
 force=force
 )
 
 click.echo(f"[x] Added reasoning to {model_name}")


@timeline.command()
@click.option('--session', default=None)
@click.option('--output', default=None)
def analyze(session, output):
 """Analyze model evolution trajectory"""
 db = Database()
 store = TimelineStore(db)
 
 timeline = store.get_model_timeline(session_id=session)
 
 # Generate analysis report
 report = generate_analysis_report(timeline, store)
 
 if output:
 with open(output, 'w') as f:
 f.write(report)
 click.echo(f"[x] Analysis exported to {output}")
 else:
 click.echo(report)


# Register with main CLI
@click.group()
def cli():
 pass

cli.add_command(timeline)
```

**Task 3.2: Formatters** (1-2 hours)

**File:** `vcm/utils/timeline_formatters.py` (NEW)

```python
def format_timeline_table(timeline: ModelTimeline, show_reasoning: bool = True, 
 show_changes: bool = True, highlight_best: bool = True) -> str:
 """Format timeline as ASCII table"""
 output = []
 output.append("Model Evolution Timeline")
 output.append("=" * 80)
 output.append("")
 
 for entry in timeline.entries:
 # Model line
 badge = ""
 if highlight_best and entry.model_name == timeline.best_model:
 badge = " [BEST]"
 
 if entry.accuracy_improvement:
 if entry.accuracy_improvement > 0:
 change = f" (+{entry.accuracy_improvement:.1%} ⬆)"
 else:
 change = f" ({entry.accuracy_improvement:.1%} ⬇) [WARNING]"
 else:
 change = " (baseline)"
 
 output.append(f"Position {entry.position} │ {entry.model_name}{badge}")
 output.append(f"Accuracy │ {entry.accuracy:.1%}{change}")
 output.append(f"Date │ {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
 
 if show_reasoning and entry.reasoning:
 output.append(f"Why this? │ {entry.reasoning}")
 
 output.append("")
 
 # Summary
 output.append("=" * 80)
 output.append("Summary")
 output.append("=" * 80)
 output.append(f"Total models: {timeline.total_models}")
 output.append(f"Best model: {timeline.best_model} ({timeline.best_accuracy:.1%})")
 output.append(f"Overall improvement: {timeline.accuracy_improvement:+.1%}")
 
 regressions = len([e for e in timeline.entries if e.accuracy_improvement and e.accuracy_improvement < 0])
 if regressions:
 output.append(f"Regressions: {regressions}")
 
 return "\n".join(output)


def format_timeline_html(timeline: ModelTimeline, show_reasoning: bool = True) -> str:
 """Format timeline as HTML report"""
 html = """
 <!DOCTYPE html>
 <html>
 <head>
 <title>Model Evolution Timeline</title>
 <style>
 body { font-family: Arial; margin: 20px; }
 .timeline { max-width: 900px; }
 .model-card {
 border: 1px solid #ddd;
 padding: 15px;
 margin: 10px 0;
 border-radius: 5px;
 background: #f9f9f9;
 }
 .model-card.best { background: #e8f5e9; border-color: #4caf50; }
 .model-card.regression { background: #ffebee; border-color: #f44336; }
 .accuracy { font-size: 20px; font-weight: bold; color: #2196f3; }
 .improvement { color: #4caf50; }
 .regression { color: #f44336; }
 .reasoning { font-style: italic; color: #666; margin-top: 10px; }
 </style>
 </head>
 <body>
 <h1>Model Evolution Timeline</h1>
 <div class="timeline">
 """
 
 for entry in timeline.entries:
 is_best = entry.model_name == timeline.best_model
 is_regression = entry.accuracy_improvement and entry.accuracy_improvement < 0
 
 card_class = "model-card"
 if is_best:
 card_class += " best"
 elif is_regression:
 card_class += " regression"
 
 html += f'<div class="{card_class}">'
 html += f'<h3>{entry.model_name}'
 
 if is_best:
 html += ' [BEST]'
 elif is_regression:
 html += ' [WARNING] REGRESSION'
 
 html += '</h3>'
 html += f'<p class="accuracy">{entry.accuracy:.1%}</p>'
 html += f'<p>{entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</p>'
 
 if entry.accuracy_improvement:
 cls = "improvement" if entry.accuracy_improvement > 0 else "regression"
 html += f'<p class="{cls}">Change: {entry.accuracy_improvement:+.1%}</p>'
 
 if show_reasoning and entry.reasoning:
 html += f'<p class="reasoning">Why: {entry.reasoning}</p>'
 
 html += '</div>'
 
 html += """
 </div>
 </body>
 </html>
 """
 
 return html
```

**Verification:**
```bash
pytest vcm/tests/cli/test_timeline_commands.py -v
# Expected: All CLI commands work, output formatting correct
```

---

### DAY 4: Testing & Integration

**Reading:** vcm_model_evolution_timeline_spec.md section 7

**Task 4.1: Unit Tests** (1 hour)

**File:** `vcm/tests/unit/test_evolution_timeline.py`

```python
def test_evolution_entry_creation():
 """Create evolution entry with all fields"""
 entry = EvolutionEntry(
 position=1,
 model_name="v1",
 model_id=1,
 timestamp=datetime.now(),
 accuracy=0.91,
 metrics={"f1": 0.90}
 )
 
 assert entry.position == 1
 assert entry.model_name == "v1"

def test_timeline_accuracy_calculation():
 """Calculate improvement from first to last model"""
 entries = [
 EvolutionEntry(position=1, model_name="v1", model_id=1, timestamp=datetime.now(), accuracy=0.91),
 EvolutionEntry(position=2, model_name="v2", model_id=2, timestamp=datetime.now(), accuracy=0.92),
 EvolutionEntry(position=3, model_name="v3", model_id=3, timestamp=datetime.now(), accuracy=0.93),
 ]
 
 timeline = ModelTimeline(
 entries=entries,
 total_models=3,
 best_model="v3",
 worst_model="v1",
 best_accuracy=0.93,
 worst_accuracy=0.91,
 accuracy_improvement=0.02,
 date_range=(entries[0].timestamp, entries[-1].timestamp),
 session_ids=set()
 )
 
 assert timeline.accuracy_improvement == pytest.approx(0.02)
 assert timeline.best_model == "v3"

def test_regression_detection():
 """Detect accuracy regression"""
 store = TimelineStore(db)
 timeline = create_timeline_with_accuracies([0.91, 0.93, 0.90])
 
 regressions = store.detect_regressions(timeline)
 
 assert len(regressions) == 1
 assert regressions[0]['model'] == 'v3'

def test_missing_reasoning_detection():
 """Detect models without reasoning"""
 store = TimelineStore(db)
 timeline = create_timeline(with_reasoning=[True, False, True])
 
 issues = store.detect_timeline_gaps(timeline)
 
 assert any("reasoning" in issue.lower() for issue in issues)
```

**Task 4.2: Integration Tests** (1.5 hours)

**File:** `vcm/tests/integration/test_timeline_integration.py`

```python
def test_full_timeline_workflow():
 """End-to-end timeline tracking"""
 # Create 3 models
 create_model("v1", accuracy=0.91)
 create_model("v2", accuracy=0.92)
 create_model("v3", accuracy=0.93)
 
 # Auto-detect timeline
 store = TimelineStore(db)
 store.auto_detect_and_link_timeline()
 
 # Add reasoning
 db.add_reasoning(model_id=2, reasoning="Lower learning rate")
 db.add_reasoning(model_id=3, reasoning="Feature engineering")
 
 # Get timeline
 timeline = store.get_model_timeline()
 
 # Verify
 assert len(timeline.entries) == 3
 assert timeline.entries[0].model_name == "v1"
 assert timeline.entries[1].reasoning == "Lower learning rate"
 assert timeline.entries[2].reasoning == "Feature engineering"

def test_timeline_cli_command():
 """vcm timeline command works"""
 result = run_command(['timeline', '--show-reasoning', '--format', 'table'])
 
 assert "Model Evolution Timeline" in result
 assert "Lower learning rate" in result

def test_timeline_html_export():
 """Timeline exports as HTML"""
 run_command(['timeline', '--format', 'html', '--output', 'timeline.html'])
 
 with open('timeline.html') as f:
 content = f.read()
 assert "<html>" in content
 assert "accuracy" in content.lower()
```

**Task 4.3: Advanced Scenario Test** (1.5 hours)

**File:** `vcm/tests/advanced/test_scenario_9_model_evolution.py`

```python
def test_scenario_9_model_evolution_complete_workflow():
 """Real workflow: Full model progression tracking"""
 project = setup_iris_project()
 os.chdir(project)
 
 # Train sequence of models
 models_to_train = [
 ("v1", None), # Baseline
 ("v2", "Testing lower learning rate"),
 ("v3", "Feature engineering with scaling"),
 ("v4", "Ensemble approach (FAILED)"),
 ("v5", "Back to feature engineering"),
 ]
 
 for model_name, reasoning in models_to_train:
 os.system(f"vcm train --model-name {model_name} --script train.py --metrics metrics.json")
 if reasoning:
 os.system(f"vcm timeline-reason {model_name} '{reasoning}'")
 
 # Get timeline
 timeline_output = os.popen("vcm timeline --show-reasoning").read()
 
 # Verify complete progression
 assert "v1" in timeline_output
 assert "v5" in timeline_output
 assert "Testing lower learning rate" in timeline_output
 assert "Feature engineering" in timeline_output
 assert "FAILED" in timeline_output
 
 # Get timeline object
 db = Database()
 store = TimelineStore(db)
 timeline = store.get_model_timeline()
 
 # Verify structure
 assert len(timeline.entries) == 5
 assert timeline.entries[0].model_name == "v1"
 assert timeline.entries[4].model_name == "v5"
 
 # Verify reasoning captured
 assert timeline.entries[1].reasoning == "Testing lower learning rate"
 
 # Verify regression detected
 issues = store.detect_timeline_gaps(timeline)
 
 print("[x] Scenario 9: Model evolution complete workflow - PASSED")
```

**Verification:**
```bash
pytest vcm/tests/unit/test_evolution_timeline.py -v --cov
pytest vcm/tests/integration/test_timeline_integration.py -v
pytest vcm/tests/advanced/test_scenario_9_model_evolution.py -v
# Expected: All tests passing, >90% coverage
```

---

## [x] COMPLETION CHECKLIST

### Day 1
- [ ] Data models created (EvolutionEntry, ModelTimeline, etc.)
- [ ] Database schema updated with model_evolution table
- [ ] Indexes created
- [ ] CRUD operations implemented
- [ ] Unit tests for models & DB passing

### Day 2
- [ ] Timeline queries implemented (get_model_timeline, detect_regressions, etc.)
- [ ] Auto-detection of model sequences
- [ ] Gap detection logic
- [ ] Unit tests for timeline logic passing

### Day 3
- [ ] CLI commands implemented (timeline, reason, analyze)
- [ ] Formatters for table, HTML, JSON, CSV
- [ ] Output styling and visualization
- [ ] CLI tests passing

### Day 4
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Advanced scenario test passing
- [ ] Code coverage >90% for timeline module
- [ ] Type checking: 0 errors (mypy)
- [ ] Linting: 0 violations (flake8)

---

## EXPECTED OUTCOMES

### After Completion

**Code:**
- 1 new data model file (evolution.py)
- 1 new timeline logic file (timeline.py)
- 1 new CLI commands file (timeline_commands.py)
- 1 new formatters file (timeline_formatters.py)
- Updates to database.py
- Updates to main CLI

**Tests:**
- 15+ new unit tests
- 5+ new integration tests
- 1 new advanced scenario
- Total coverage: >90% for timeline module

**Features:**
- Model progression tracking
- Reasoning annotations
- Timeline visualization (table, HTML, JSON, CSV)
- Regression detection
- Timeline analysis & recommendations

**Quality:**
- 100% of tests passing
- 0 type errors
- 0 linting violations
- Performance: <100ms for timeline queries on 100+ models

---

## QUICK VALIDATION AFTER COMPLETION

```bash
# Run all timeline tests
pytest vcm/tests/*/test_*timeline*.py -v --cov=vcm.models.evolution

# Run timeline CLI commands
vcm timeline --show-reasoning
vcm timeline-reason classifier_v2 "Testing approach"
vcm timeline analyze

# Verify real scenario
pytest vcm/tests/advanced/test_scenario_9_model_evolution.py -v -s

# Type checking
mypy vcm/models/evolution.py vcm/models/timeline.py --strict

# Linting
flake8 vcm/cli/timeline_commands.py vcm/utils/timeline_formatters.py
```

---

## REFERENCE COMMANDS

```bash
# Show timeline
vcm timeline

# Show with reasoning
vcm timeline --show-reasoning

# Show for specific session
vcm timeline --session "Tuesday morning"

# Add reasoning
vcm timeline-reason classifier_v2 "Testing lower learning rate"

# Analyze progression
vcm timeline analyze

# Export to HTML
vcm timeline --format html --output timeline.html
```

---

**Ready for implementation! Follow day-by-day and validate at checkpoints.** 
