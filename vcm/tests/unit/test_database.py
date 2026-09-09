"""Unit tests for Database layer (UT-4.1 to UT-4.6)."""

import os
import concurrent.futures
import pytest
from datetime import datetime

from vcm.models.metadata import (
    MetadataModel,
    CodeInfo,
    DataInfo,
    DVCFileInfo,
    TrainingInfo,
    EnvironmentInfo,
)
from vcm.db.database import Database, DatabaseError


def _make_metadata(
    name: str,
    acc: float,
    f1: float = 0.9,
    dataset_hash: str = "hash1",
    model_hash: str = "sha256:1",
    model_file: str = "models/model.pkl",
) -> MetadataModel:
    return MetadataModel(
        model_name=name,
        model_hash=model_hash,
        model_file=model_file,
        code=CodeInfo(git_commit="abc1234", git_branch="main"),
        data=DataInfo(dvc_files=[DVCFileInfo(path="data/train.csv", dvc_hash=dataset_hash)]),
        training=TrainingInfo(timestamp=datetime.now().isoformat(), user="tester"),
        hyperparameters={"lr": 0.01},
        metrics={"accuracy": acc, "f1_score": f1},
        environment=EnvironmentInfo(python_version="3.9.1"),
    )


def test_ut_4_1_database_initialize(tmp_path):
    """UT-4.1: Database.init() creates schema correctly and is idempotent."""
    db_path = str(tmp_path / ".vcm" / "vcm.db")
    db = Database(db_path=db_path)

    # First init
    db.init()
    assert os.path.exists(db_path)

    # Re-initialization should be idempotent without error
    db.init()
    assert os.path.exists(db_path)


def test_ut_4_2_database_insert_model(tmp_path):
    """UT-4.2: Database.insert_model(metadata) stores model record."""
    db_path = str(tmp_path / "vcm.db")
    db = Database(db_path=db_path)
    db.init()

    meta = _make_metadata("classifier_v1", acc=0.94, model_hash="sha256:abc1")
    model_id = db.insert_model(meta)
    assert isinstance(model_id, int)
    assert model_id > 0

    all_models = db.get_all_models()
    assert len(all_models) == 1
    stored = all_models[0]
    assert stored.model_name == "classifier_v1"
    assert stored.metrics["accuracy"] == 0.94
    assert stored.code.git_commit == "abc1234"


def test_ut_4_3_database_query_by_accuracy(tmp_path):
    """UT-4.3: Database.query_by_accuracy(min=0.9) returns matching models."""
    db = Database(str(tmp_path / "vcm.db"))
    db.init()

    db.insert_model(_make_metadata("m1", acc=0.85, model_hash="sha256:1"))
    db.insert_model(_make_metadata("m2", acc=0.92, model_hash="sha256:2"))
    db.insert_model(_make_metadata("m3", acc=0.95, model_hash="sha256:3"))

    matching = db.query_by_accuracy(min_acc=0.90)
    assert len(matching) == 2
    # Should be sorted DESC
    assert matching[0].metrics["accuracy"] == 0.95
    assert matching[1].metrics["accuracy"] == 0.92


def test_ut_4_4_database_query_by_dataset_hash(tmp_path):
    """UT-4.4: Database.query_by_dataset(dataset_hash="xyz") returns models."""
    db = Database(str(tmp_path / "vcm.db"))
    db.init()

    db.insert_model(_make_metadata("m1", acc=0.85, dataset_hash="xyz", model_hash="sha256:1"))
    db.insert_model(_make_metadata("m2", acc=0.92, dataset_hash="abc", model_hash="sha256:2"))
    db.insert_model(_make_metadata("m3", acc=0.95, dataset_hash="xyz", model_hash="sha256:3"))

    matching = db.query_by_dataset(dataset_hash="xyz")
    assert len(matching) == 2
    assert {m.model_name for m in matching} == {"m1", "m3"}


def test_ut_4_5_database_update_model(tmp_path):
    """UT-4.5: Database.update_model(id, metadata) updates record."""
    db = Database(str(tmp_path / "vcm.db"))
    db.init()

    meta = _make_metadata("m1", acc=0.85, model_hash="sha256:1")
    model_id = db.insert_model(meta)

    updated_meta = _make_metadata("m1_updated", acc=0.89, model_hash="sha256:1_mod")
    success = db.update_model(model_id, updated_meta)
    assert success is True

    retrieved = db.get_model_by_id(model_id)
    assert retrieved is not None
    assert retrieved.model_name == "m1_updated"
    assert retrieved.metrics["accuracy"] == 0.89

    # Update nonexistent
    assert db.update_model(9999, updated_meta) is False


def test_ut_4_6_database_concurrent_access(tmp_path):
    """UT-4.6: Database handles concurrent reads/writes with WAL mode."""
    db_path = str(tmp_path / "vcm_concurrent.db")
    db = Database(db_path)
    db.init()

    def insert_worker(i: int):
        local_db = Database(db_path)
        meta = _make_metadata(f"model_{i}", acc=0.80 + (i * 0.01), model_hash=f"sha256:worker_{i}")
        return local_db.insert_model(meta)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(insert_worker, i) for i in range(5)]
        results = [f.result() for f in futures]

    assert len(results) == 5
    all_models = db.get_all_models()
    assert len(all_models) == 5


def test_database_additional_queries_and_recovery(tmp_path):
    """Test lookup helpers, best model query, corruption check, and rebuild."""
    db = Database(str(tmp_path / "vcm.db"))
    db.init()

    m1 = _make_metadata("m1", acc=0.85, model_hash="sha256:1", model_file="models/m1.pkl")
    m2 = _make_metadata("m2", acc=0.95, model_hash="sha256:2", model_file="models/m2.pkl")
    db.insert_model(m1)
    db.insert_model(m2)

    assert db.get_model_by_name("m2") is not None
    assert db.get_model_by_name("nonexistent") is None

    assert db.get_model_by_file("models/m1.pkl") is not None
    assert db.get_model_by_hash("sha256:2") is not None

    best = db.get_best_model(metric="accuracy")
    assert best is not None
    assert best.model_name == "m2"

    # Test rebuild
    rebuilt_count = db.rebuild_from_metadata([m1, m2])
    assert rebuilt_count == 2
    assert len(db.get_all_models()) == 2

    # Test delete_model
    assert db.get_model_by_id(1) is not None
    assert db.get_model_by_id(9999) is None
    deleted = db.delete_model(1)
    assert deleted is True
    assert db.delete_model(9999) is False

    # Test get_best_model edge cases
    empty_db = Database(str(tmp_path / "empty.db"))
    empty_db.init()
    assert empty_db.get_best_model() is None

    # Duplicate model_hash error
    with pytest.raises(DatabaseError, match="already exists"):
        db.insert_model(m2)

    # Test is_corrupted
    assert not db.is_corrupted()
    non_existent = Database(str(tmp_path / "does_not_exist.db"))
    assert not non_existent.is_corrupted()

    # Create corrupted file
    corrupt_path = str(tmp_path / "corrupt.db")
    with open(corrupt_path, "w") as f:
        f.write("corrupted data content not sqlite")
    corrupt_db = Database(corrupt_path)
    assert corrupt_db.is_corrupted()
