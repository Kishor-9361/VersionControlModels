"""Unit tests for Model Evolution dataclasses (EvolutionEntry, ModelTimeline, ModelDifference)."""

from datetime import datetime, timezone
import pytest

from vcm.models.evolution import (
    Annotation,
    EvolutionEntry,
    ModelDifference,
    ModelTimeline,
)


def test_evolution_entry_creation():
    """Verify EvolutionEntry fields and automatic improvement calculation."""
    now = datetime.now(timezone.utc)
    entry1 = EvolutionEntry(
        position=1,
        model_name="v1",
        model_id=101,
        timestamp=now,
        accuracy=0.91,
        metrics={"f1": 0.90},
        reasoning="Initial baseline",
    )

    assert entry1.position == 1
    assert entry1.model_name == "v1"
    assert entry1.model_id == 101
    assert entry1.accuracy == 0.91
    assert entry1.metrics["f1"] == 0.90
    assert entry1.reasoning == "Initial baseline"
    assert entry1.accuracy_improvement is None

    # Entry 2 with previous model accuracy
    entry2 = EvolutionEntry(
        position=2,
        model_name="v2",
        model_id=102,
        timestamp=now,
        accuracy=0.925,
        previous_model="v1",
        previous_model_accuracy=0.91,
    )

    assert entry2.position == 2
    assert entry2.previous_model == "v1"
    assert entry2.previous_model_accuracy == 0.91
    assert entry2.accuracy_improvement == pytest.approx(0.015)


def test_model_difference_dataclass():
    """Verify ModelDifference serialization and from_dict hydration."""
    diff = ModelDifference(
        code_changed=True,
        code_files=["train.py"],
        git_commits=["abc1234"],
        data_changed=True,
        data_files=["data.csv"],
        data_hashes_changed={"data.csv": ("hash1", "hash2")},
        hyperparams_changed={"lr": (0.01, 0.001)},
        environment_changed=False,
    )

    d = diff.to_dict()
    assert d["code_changed"] is True
    assert d["code_files"] == ["train.py"]
    assert d["hyperparams_changed"]["lr"] == (0.01, 0.001)

    hydrated = ModelDifference.from_dict(d)
    assert hydrated.code_changed is True
    assert hydrated.git_commits == ["abc1234"]
    assert hydrated.data_hashes_changed["data.csv"] == ("hash1", "hash2")


def test_annotation_dataclass():
    """Verify Annotation dataclass."""
    now = datetime.now()
    ann = Annotation(timestamp=now, text="Experiment notes", added_by="alice")
    assert ann.text == "Experiment notes"
    assert ann.added_by == "alice"
    d = ann.to_dict()
    assert d["text"] == "Experiment notes"
    assert d["added_by"] == "alice"


def test_model_timeline_statistics():
    """Verify ModelTimeline calculation of best, worst, improvement, and serialization."""
    t1 = datetime(2026, 1, 1, 10, 0, 0)
    t2 = datetime(2026, 1, 1, 11, 0, 0)
    t3 = datetime(2026, 1, 1, 12, 0, 0)

    entries = [
        EvolutionEntry(position=1, model_name="v1", model_id=1, timestamp=t1, accuracy=0.91),
        EvolutionEntry(
            position=2, model_name="v2", model_id=2, timestamp=t2,
            accuracy=0.92, previous_model_accuracy=0.91
        ),
        EvolutionEntry(
            position=3, model_name="v3", model_id=3, timestamp=t3,
            accuracy=0.93, previous_model_accuracy=0.92
        ),
    ]

    timeline = ModelTimeline(
        entries=entries,
        total_models=3,
        best_model="v3",
        worst_model="v1",
        best_accuracy=0.93,
        worst_accuracy=0.91,
        accuracy_improvement=0.02,
        date_range=(t1, t3),
        session_ids={"session_1"},
    )

    assert timeline.total_models == 3
    assert timeline.best_model == "v3"
    assert timeline.worst_model == "v1"
    assert timeline.accuracy_improvement == pytest.approx(0.02)
    assert "session_1" in timeline.session_ids

    d = timeline.to_dict()
    assert len(d["entries"]) == 3
    assert d["best_model"] == "v3"
    assert d["accuracy_improvement"] == pytest.approx(0.02)
