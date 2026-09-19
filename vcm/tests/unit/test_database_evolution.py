"""Unit tests for Database model_evolution table, CRUD methods, and reasoning annotations."""

from typing import Optional
import pytest

from vcm.db.database import Database
from vcm.models.metadata import MetadataModel


@pytest.fixture
def test_db(tmp_path):
    """Provide a clean, initialized Database instance in temporary directory."""
    db_file = str(tmp_path / "test_vcm.db")
    db = Database(db_file)
    db.init()
    return db


def create_mock_metadata(name: str, accuracy: float, reasoning: Optional[str] = None) -> MetadataModel:
    """Helper to construct dummy MetadataModel."""
    return MetadataModel(
        model_name=name,
        model_hash=f"hash_{name}_{accuracy}",
        model_file=f"models/{name}.pkl",
        metrics={"accuracy": accuracy, "f1_score": accuracy - 0.01},
        reasoning=reasoning,
    )


def test_model_evolution_table_creation(test_db):
    """Verify model_evolution table exists with expected schema and indexes."""
    with test_db.get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(model_evolution)")
        cols = {row["name"] for row in cursor.fetchall()}
        assert "model_id" in cols
        assert "position_in_timeline" in cols
        assert "reasoning" in cols
        assert "reasoning_added_by" in cols
        assert "previous_model_id" in cols
        assert "next_model_id" in cols
        assert "session_id" in cols

        # Check indexes
        idx_cur = conn.execute("PRAGMA index_list(model_evolution)")
        idx_names = {row["name"] for row in idx_cur.fetchall()}
        assert any("position" in name for name in idx_names)


def test_insert_model_auto_registers_evolution(test_db):
    """Verify insert_model automatically creates evolution entries linking previous models."""
    m1 = create_mock_metadata("classifier_v1", 0.91)
    m2 = create_mock_metadata("classifier_v2", 0.925, reasoning="Decreased learning rate")
    m3 = create_mock_metadata("classifier_v3", 0.93)

    id1 = test_db.insert_model(m1)
    id2 = test_db.insert_model(m2)
    id3 = test_db.insert_model(m3)

    e1 = test_db.get_evolution_entry(id1)
    e2 = test_db.get_evolution_entry("classifier_v2")
    e3 = test_db.get_evolution_entry(id3)

    assert e1 is not None
    assert e1.position_in_timeline == 1
    assert e1.previous_model_id is None
    assert e1.next_model_id == id2

    assert e2 is not None
    assert e2.position_in_timeline == 2
    assert e2.previous_model_id == id1
    assert e2.next_model_id == id3
    assert e2.reasoning == "Decreased learning rate"

    assert e3 is not None
    assert e3.position_in_timeline == 3
    assert e3.previous_model_id == id2


def test_add_reasoning_and_force_override(test_db):
    """Verify adding reasoning to a model, checking existence, and force updating."""
    m = create_mock_metadata("v1", 0.90)
    test_db.insert_model(m)

    # Add reasoning
    test_db.add_model_reasoning("v1", "Initial baseline architecture", user="tester")
    entry = test_db.get_evolution_entry("v1")
    assert entry.reasoning == "Initial baseline architecture"
    assert entry.reasoning_added_by == "tester"

    # Attempt to overwrite without force should raise ValueError
    with pytest.raises(ValueError, match="Reasoning already exists"):
        test_db.add_model_reasoning("v1", "New reason without force", force=False)

    # Overwrite with force=True
    test_db.add_model_reasoning("v1", "Overridden reasoning notes", force=True)
    updated_entry = test_db.get_evolution_entry("v1")
    assert updated_entry.reasoning == "Overridden reasoning notes"


def test_add_reasoning_nonexistent_model(test_db):
    """Verify attempting to add reasoning to a non-existent model raises ValueError."""
    with pytest.raises(ValueError, match="Model not found"):
        test_db.add_model_reasoning("ghost_model", "Does not exist")


def test_raw_query_helper(test_db):
    """Verify test_db.query executes raw SQL and returns rows."""
    test_db.insert_model(create_mock_metadata("v1", 0.88))
    rows = test_db.query("SELECT model_name, accuracy FROM models WHERE model_name = ?", ("v1",))
    assert len(rows) == 1
    assert rows[0]["model_name"] == "v1"
    assert rows[0]["accuracy"] == pytest.approx(0.88)
