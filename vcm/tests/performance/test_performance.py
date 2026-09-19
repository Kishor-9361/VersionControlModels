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


def test_perf_3_query_by_accuracy_range_performance(tmp_path):
    """PERF-3: Query by accuracy range with 1000 models is < 100ms."""
    db_path = str(tmp_path / "perf_range.db")
    db = Database(db_path)
    db.init()

    with db.get_connection() as conn:
        for i in range(1000):
            meta = MetadataModel(
                model_name=f"perf_model_{i}",
                model_hash=f"sha256:range_{i:04d}",
                metrics={"accuracy": 0.5 + (i / 2000.0), "f1_score": 0.5 + (i / 2500.0)},
            )
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

    start_time = time.time()
    results = db.query_by_accuracy_range(min_acc=0.7, max_acc=0.9)
    elapsed = time.time() - start_time

    assert len(results) > 0
    assert elapsed < 0.100  # < 100ms target


def test_perf_4_session_lifecycle_overhead(tmp_path):
    """PERF-4: SessionTracker lifecycle (start, annotate, log, end) overhead is < 200ms."""
    from vcm.models.session import SessionTracker

    db_path = str(tmp_path / ".vcm" / "vcm.db")
    tracker = SessionTracker(session_name="perf_session", user="perf_user", db_path=db_path, repo_path=str(tmp_path))

    start_time = time.time()
    tracker.start(auto_capture_terminal=False)
    for i in range(5):
        tracker.annotate(f"Milestone {i}", tags=["perf", "test"])
        meta = MetadataModel(model_name=f"session_model_{i}", model_hash=f"sha_{i}")
        tracker.log_model(meta, f"session_model_{i}", {"accuracy": 0.90 + (i * 0.01)})
    summary = tracker.end()
    elapsed = time.time() - start_time

    assert summary.models_count == 5
    assert elapsed < 0.200  # < 200ms target


def test_perf_5_terminal_logging_overhead(tmp_path):
    """PERF-5: TerminalLogger with secret masking overhead for 1,000 lines is < 500ms."""
    from vcm.utils.terminal_logger import TerminalLogger

    log_path = str(tmp_path / "perf_term.log")
    tlogger = TerminalLogger(log_path)

    start_time = time.time()
    for i in range(1000):
        tlogger.log_line(f"Step {i}: trained with api_key=sk-secret{i} on localhost")
    elapsed = time.time() - start_time

    assert elapsed < 0.500  # < 500ms target


def test_perf_6_session_comparison_performance(tmp_path):
    """PERF-6: Session comparison across complex sessions is < 50ms."""
    from vcm.models.session import SessionComparator, SessionTracker

    db_path = str(tmp_path / ".vcm" / "vcm.db")
    t1 = SessionTracker(session_name="s1", user="alice", db_path=db_path, repo_path=str(tmp_path))
    s1 = t1.start(auto_capture_terminal=False)
    m1 = MetadataModel(model_name="m1", model_hash="h1", metrics={"accuracy": 0.85})
    t1.log_model(m1, "m1", {"accuracy": 0.85})
    t1.end()

    t2 = SessionTracker(session_name="s2", user="alice", db_path=db_path, repo_path=str(tmp_path))
    s2 = t2.start(auto_capture_terminal=False)
    m2 = MetadataModel(model_name="m2", model_hash="h2", metrics={"accuracy": 0.95})
    t2.log_model(m2, "m2", {"accuracy": 0.95})
    t2.end()

    comparator = SessionComparator(db_path=db_path)
    start_time = time.time()
    diff = comparator.compare_sessions(s1, s2)
    elapsed = time.time() - start_time

    assert abs(round(diff.accuracy_delta, 2)) == 0.10
    assert elapsed < 0.050  # < 50ms target


def test_perf_7_dataset_query_performance(tmp_path):
    """PERF-7: Query by dataset hash across 1000 models is < 100ms."""
    db_path = str(tmp_path / "perf_ds.db")
    db = Database(db_path)
    db.init()

    with db.get_connection() as conn:
        for i in range(1000):
            ds_hash = "sha256:target_dataset" if i % 10 == 0 else f"sha256:other_{i}"
            meta = MetadataModel(
                model_name=f"perf_model_{i}",
                model_hash=f"sha256:perf_{i:04d}",
                metrics={"accuracy": 0.88},
            )
            conn.execute(
                """
                INSERT INTO models (
                    model_name, model_file, model_hash, dataset_hash, accuracy, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    meta.model_name,
                    meta.model_file,
                    meta.model_hash,
                    ds_hash,
                    meta.metrics["accuracy"],
                    meta.to_json(),
                ),
            )
        conn.commit()

    start_time = time.time()
    matches = db.query_by_dataset("sha256:target_dataset")
    elapsed = time.time() - start_time

    assert len(matches) == 100
    assert elapsed < 0.100  # < 100ms target
