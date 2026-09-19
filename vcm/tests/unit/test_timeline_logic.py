"""Unit tests for TimelineStore queries, regression detection, and issue analysis."""

from datetime import datetime, timedelta
from typing import Optional
import pytest

from vcm.db.database import Database
from vcm.models.evolution import EvolutionEntry, ModelTimeline
from vcm.models.metadata import MetadataModel, TrainingInfo
from vcm.models.session import SessionInfo
from vcm.models.timeline import TimelineStore, detect_timeline_issues


@pytest.fixture
def db(tmp_path):
    """Provide initialized Database in temporary directory."""
    db_file = str(tmp_path / "timeline_test.db")
    database = Database(db_file)
    database.init()
    return database


def make_metadata(
    name: str,
    accuracy: float,
    timestamp: Optional[datetime] = None,
    session: Optional[str] = None,
    reasoning: Optional[str] = None,
) -> MetadataModel:
    """Helper to build MetadataModel with controlled timestamp and session."""
    session_obj = SessionInfo(session_id=session, session_name=session) if session else None
    t_obj = TrainingInfo(timestamp=timestamp.isoformat()) if timestamp else TrainingInfo()
    return MetadataModel(
        model_name=name,
        model_hash=f"hash_{name}_{accuracy}_{timestamp or datetime.now()}",
        model_file=f"models/{name}.pkl",
        training=t_obj,
        metrics={"accuracy": accuracy},
        session=session_obj,
        reasoning=reasoning,
        created_at=timestamp or datetime.now(),
    )


def test_timeline_query_ordering(db):
    """Verify models are returned in strict chronological timeline order."""
    t0 = datetime(2026, 1, 1, 10, 0, 0)
    db.insert_model(make_metadata("m1", 0.90, timestamp=t0))
    db.insert_model(make_metadata("m2", 0.92, timestamp=t0 + timedelta(hours=1)))
    db.insert_model(make_metadata("m3", 0.94, timestamp=t0 + timedelta(hours=2)))

    timeline = db.get_model_timeline()
    assert len(timeline.entries) == 3
    assert timeline.entries[0].model_name == "m1"
    assert timeline.entries[1].model_name == "m2"
    assert timeline.entries[2].model_name == "m3"


def test_timeline_accuracy_improvement(db):
    """Calculate improvement from first to last model and identify best/worst models."""
    t0 = datetime.now()
    db.insert_model(make_metadata("v1", 0.91, timestamp=t0))
    db.insert_model(make_metadata("v2", 0.92, timestamp=t0 + timedelta(minutes=10)))
    db.insert_model(make_metadata("v3", 0.93, timestamp=t0 + timedelta(minutes=20)))

    timeline = db.get_model_timeline()
    assert timeline.accuracy_improvement == pytest.approx(0.02)
    assert timeline.best_model == "v3"
    assert timeline.worst_model == "v1"
    assert timeline.best_accuracy == pytest.approx(0.93)
    assert timeline.worst_accuracy == pytest.approx(0.91)


def test_add_reasoning_to_model(db):
    """Verify reasoning can be attached and retrieved from evolution entry."""
    db.insert_model(make_metadata("v2", 0.92))
    db.add_model_reasoning("v2", "Testing lower learning rate")
    entry = db.get_evolution_entry("v2")

    assert entry is not None
    assert entry.reasoning == "Testing lower learning rate"


def test_timeline_with_session_filter(db):
    """Verify timeline filters records by session ID."""
    t0 = datetime.now()
    # 3 models in session1
    db.insert_model(make_metadata("s1_m1", 0.85, timestamp=t0, session="session1"))
    db.insert_model(make_metadata("s1_m2", 0.88, timestamp=t0 + timedelta(minutes=5), session="session1"))
    db.insert_model(make_metadata("s1_m3", 0.90, timestamp=t0 + timedelta(minutes=10), session="session1"))

    # 2 models in session2
    db.insert_model(make_metadata("s2_m1", 0.91, timestamp=t0 + timedelta(minutes=15), session="session2"))
    db.insert_model(make_metadata("s2_m2", 0.92, timestamp=t0 + timedelta(minutes=20), session="session2"))

    timeline = db.get_model_timeline(session_id="session1")
    assert len(timeline.entries) == 3
    assert all(e.session_id == "session1" for e in timeline.entries)
    assert [e.model_name for e in timeline.entries] == ["s1_m1", "s1_m2", "s1_m3"]


def test_detect_regression():
    """Verify regression detection flags drop in accuracy."""
    t0 = datetime.now()
    entries = [
        EvolutionEntry(position=1, model_name="v1", model_id=1, timestamp=t0, accuracy=0.91),
        EvolutionEntry(
            position=2, model_name="v2", model_id=2, timestamp=t0,
            accuracy=0.93, previous_model_accuracy=0.91
        ),
        EvolutionEntry(
            position=3, model_name="v3", model_id=3, timestamp=t0,
            accuracy=0.90, previous_model_accuracy=0.93
        ),
    ]
    timeline = ModelTimeline(
        entries=entries,
        total_models=3,
        best_model="v2",
        worst_model="v3",
        best_accuracy=0.93,
        worst_accuracy=0.90,
        accuracy_improvement=-0.01,
        date_range=(t0, t0),
    )

    issues = detect_timeline_issues(timeline)
    assert any("regression" in issue.lower() for issue in issues)


def test_missing_reasoning_detection(db):
    """Verify detection of models without reasoning annotations."""
    db.insert_model(make_metadata("v1", 0.90, reasoning="Baseline"))
    db.insert_model(make_metadata("v2", 0.92, reasoning=None))

    issues = detect_timeline_issues(db=db)
    assert any("reasoning" in issue.lower() for issue in issues)
    assert any("v2" in issue for issue in issues)


def test_accuracy_range_filtering(db):
    """Verify accuracy_range filter limits models returned in timeline."""
    t0 = datetime.now()
    db.insert_model(make_metadata("low", 0.70, timestamp=t0))
    db.insert_model(make_metadata("mid", 0.85, timestamp=t0 + timedelta(minutes=5)))
    db.insert_model(make_metadata("high", 0.95, timestamp=t0 + timedelta(minutes=10)))

    timeline = db.get_model_timeline(accuracy_range=(0.80, 0.90))
    assert len(timeline.entries) == 1
    assert timeline.entries[0].model_name == "mid"


def test_empty_timeline(db):
    """Verify empty database returns empty timeline object."""
    timeline = db.get_model_timeline()
    assert timeline.total_models == 0
    assert timeline.entries == []
    assert timeline.best_model is None
    assert timeline.worst_model is None
    assert timeline.accuracy_improvement == 0.0


def test_auto_detect_and_link_timeline(db):
    """Verify auto_detect_and_link_timeline links models when table was reset."""
    t0 = datetime(2026, 1, 1, 12, 0, 0)
    db.insert_model(make_metadata("m1", 0.90, timestamp=t0))
    db.insert_model(make_metadata("m2", 0.92, timestamp=t0 + timedelta(hours=1)))
    db.insert_model(make_metadata("m3", 0.94, timestamp=t0 + timedelta(hours=2)))

    # Clear model_evolution table manually
    with db.get_connection() as conn:
        conn.execute("DELETE FROM model_evolution")
        conn.commit()

    store = TimelineStore(db)
    store.auto_detect_and_link_timeline()

    timeline = store.get_model_timeline()
    assert len(timeline.entries) == 3
    assert timeline.entries[0].position == 1
    assert timeline.entries[1].position == 2
    assert timeline.entries[2].position == 3


def test_since_and_until_filters(db):
    """Verify filtering by since and until datetime thresholds."""
    t1 = datetime(2026, 1, 10)
    t2 = datetime(2026, 1, 20)
    t3 = datetime(2026, 1, 30)

    db.insert_model(make_metadata("early", 0.80, timestamp=t1))
    db.insert_model(make_metadata("target", 0.85, timestamp=t2))
    db.insert_model(make_metadata("late", 0.90, timestamp=t3))

    # Test since
    tl_since = db.get_model_timeline(since=datetime(2026, 1, 15))
    assert len(tl_since.entries) == 2
    assert [e.model_name for e in tl_since.entries] == ["target", "late"]

    # Test until
    tl_until = db.get_model_timeline(until=datetime(2026, 1, 25))
    assert len(tl_until.entries) == 2
    assert [e.model_name for e in tl_until.entries] == ["early", "target"]
