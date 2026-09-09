import time
from vcm.db.database import Database
from vcm.models.metadata import MetadataModel
from vcm.trainer import ModelTracker


def test_perf_1_database_query_performance(tmp_path):
    """PERF-1: Database query performance with 1000 models is < 200ms."""
    db_path = str(tmp_path / "perf.db")
    db = Database(db_path)
    db.init()

    # Seed 1000 models
    with db.get_connection() as conn:
        for i in range(1000):
            meta = MetadataModel(
                model_name=f"perf_model_{i}",
                model_hash=f"sha256:perf_{i:04d}",
                metrics={"accuracy": 0.5 + (i / 2000.0), "f1_score": 0.5 + (i / 2500.0)},
            )
            # Fast batch insert
            conn.execute(
                """
                INSERT INTO models (
                    model_name, model_file, model_hash, accuracy, f1_score, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    meta.model_name,
                    meta.model_file,
                    meta.model_hash,
                    meta.metrics["accuracy"],
                    meta.metrics["f1_score"],
                    meta.to_json(),
                ),
            )
        conn.commit()

    # Time query
    start_time = time.time()
    best = db.get_best_model(metric="accuracy")
    elapsed = time.time() - start_time

    assert best is not None
    assert elapsed < 0.200  # < 200ms target


def test_perf_2_metadata_capture_overhead(tmp_path):
    """PERF-2: Metadata capture overhead is < 2.5 seconds."""
    db_path = str(tmp_path / ".vcm" / "vcm.db")
    db = Database(db_path)
    db.init()

    model_file = tmp_path / "perf_model.pkl"
    model_file.write_bytes(b"sample weights" * 1000)

    tracker = ModelTracker(db_path=db_path, repo_path=str(tmp_path))

    start_time = time.time()
    meta = tracker.log_model(
        model_path=str(model_file),
        model_name="perf_model",
        metrics={"accuracy": 0.94},
    )
    elapsed = time.time() - start_time

    assert meta is not None
    assert elapsed < 2.5  # < 2.5s target
