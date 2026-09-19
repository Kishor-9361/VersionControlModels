"""SQLite Database layer for VCM model metadata indexing and querying."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generator, List, Optional, Sequence, Tuple, Union

from vcm.models.metadata import MetadataModel
from vcm.models.session import Annotation, Session

if TYPE_CHECKING:
    from vcm.models.evolution import ModelTimeline


class DatabaseError(Exception):
    """Raised when database operations encounter an error."""
    pass


class EvolutionRecord(dict[str, Any]):
    """Evolution entry dictionary with attribute access support."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'EvolutionRecord' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class Database:
    """Manages SQLite storage, querying, and indexing for VCM."""

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT NOT NULL,
        model_file TEXT NOT NULL,
        model_hash TEXT UNIQUE,
        accuracy REAL,
        f1_score REAL,
        git_commit TEXT,
        git_branch TEXT,
        dataset_hash TEXT,
        training_timestamp DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        metadata_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        session_name TEXT NOT NULL,
        user TEXT NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME,
        branch TEXT,
        initial_commit TEXT,
        final_commit TEXT,
        total_duration_seconds INTEGER,
        models_count INTEGER,
        best_model TEXT,
        best_accuracy REAL,
        terminal_log TEXT,
        status TEXT DEFAULT 'inactive',
        session_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS session_annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        text TEXT NOT NULL,
        model_related TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS session_models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        model_id INTEGER NOT NULL,
        position_in_session INTEGER,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id),
        FOREIGN KEY(model_id) REFERENCES models(id)
    );

    CREATE TABLE IF NOT EXISTS model_evolution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    );

    CREATE INDEX IF NOT EXISTS idx_model_name ON models(model_name);
    CREATE INDEX IF NOT EXISTS idx_accuracy ON models(accuracy DESC);
    CREATE INDEX IF NOT EXISTS idx_git_commit ON models(git_commit);
    CREATE INDEX IF NOT EXISTS idx_dataset_hash ON models(dataset_hash);
    CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id);
    CREATE INDEX IF NOT EXISTS idx_session_name ON sessions(session_name);
    CREATE INDEX IF NOT EXISTS idx_evolution_position ON model_evolution(position_in_timeline);
    CREATE INDEX IF NOT EXISTS idx_evolution_session ON model_evolution(session_id);
    """

    def __init__(self, db_path: str = ".vcm/vcm.db") -> None:
        self.db_path = db_path

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a configured SQLite connection with timeout and WAL mode."""
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            yield conn
        finally:
            conn.close()

    def init(self) -> None:
        """Initialize SQLite database schema and indexes."""
        try:
            with self.get_connection() as conn:
                conn.executescript(self.SCHEMA_SQL)
                conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to initialize database: {exc}") from exc

    def insert_model(self, metadata: MetadataModel) -> int:
        """Insert a MetadataModel record into the database."""
        accuracy = float(metadata.metrics.get("accuracy", 0.0)) if "accuracy" in metadata.metrics else None
        f1_score = float(metadata.metrics.get("f1_score", 0.0)) if "f1_score" in metadata.metrics else None

        dataset_hash = None
        if metadata.data.dvc_files:
            dataset_hash = metadata.data.dvc_files[0].dvc_hash

        training_timestamp = metadata.training.timestamp
        metadata_json = metadata.to_json()

        query = """
        INSERT INTO models (
            model_name, model_file, model_hash, accuracy, f1_score,
            git_commit, git_branch, dataset_hash, training_timestamp, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    query,
                    (
                        metadata.model_name,
                        metadata.model_file,
                        metadata.model_hash,
                        accuracy,
                        f1_score,
                        metadata.code.git_commit,
                        metadata.code.git_branch,
                        dataset_hash,
                        training_timestamp,
                        metadata_json,
                    ),
                )
                last_id = cursor.lastrowid
                if last_id is None:
                    raise DatabaseError("Failed to retrieve inserted model ID")
                inserted_model_id = int(last_id)

                # Auto-register in model_evolution if not already present
                try:
                    p_cur = conn.execute(
                        "SELECT COALESCE(MAX(position_in_timeline), 0) + 1 AS next_pos FROM model_evolution"
                    )
                    p_row = p_cur.fetchone()
                    next_pos = int(p_row["next_pos"]) if p_row else 1

                    prev_cur = conn.execute(
                        "SELECT model_id FROM model_evolution WHERE position_in_timeline = ?",
                        (next_pos - 1,),
                    )
                    prev_row = prev_cur.fetchone()
                    prev_id = int(prev_row["model_id"]) if prev_row else None

                    session_id = metadata.session.session_id if metadata.session else None
                    conn.execute(
                        """
                        INSERT INTO model_evolution (
                            model_id, position_in_timeline, previous_model_id, session_id,
                            git_commit, reasoning, reasoning_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(model_id) DO NOTHING
                        """,
                        (
                            inserted_model_id,
                            next_pos,
                            prev_id,
                            session_id,
                            metadata.code.git_commit or "",
                            metadata.reasoning,
                            datetime.now().isoformat() if metadata.reasoning else None,
                        ),
                    )
                    if prev_id is not None:
                        conn.execute(
                            "UPDATE model_evolution SET next_model_id = ? WHERE model_id = ?",
                            (inserted_model_id, prev_id),
                        )
                except Exception:
                    pass

                conn.commit()
                return inserted_model_id
        except sqlite3.IntegrityError as exc:
            raise DatabaseError(f"Model with hash '{metadata.model_hash}' already exists: {exc}") from exc
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to insert model: {exc}") from exc

    def update_model(self, model_id: int, metadata: MetadataModel) -> bool:
        """Update an existing model record by ID."""
        accuracy = float(metadata.metrics.get("accuracy", 0.0)) if "accuracy" in metadata.metrics else None
        f1_score = float(metadata.metrics.get("f1_score", 0.0)) if "f1_score" in metadata.metrics else None

        dataset_hash = None
        if metadata.data.dvc_files:
            dataset_hash = metadata.data.dvc_files[0].dvc_hash

        query = """
        UPDATE models SET
            model_name = ?,
            model_file = ?,
            model_hash = ?,
            accuracy = ?,
            f1_score = ?,
            git_commit = ?,
            git_branch = ?,
            dataset_hash = ?,
            training_timestamp = ?,
            metadata_json = ?
        WHERE id = ?
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    query,
                    (
                        metadata.model_name,
                        metadata.model_file,
                        metadata.model_hash,
                        accuracy,
                        f1_score,
                        metadata.code.git_commit,
                        metadata.code.git_branch,
                        dataset_hash,
                        metadata.training.timestamp,
                        metadata.to_json(),
                        model_id,
                    ),
                )
                conn.commit()
                return bool(cursor.rowcount > 0)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to update model: {exc}") from exc

    def get_all_models(self) -> List[MetadataModel]:
        """Retrieve all tracked models, ordered by created_at DESC."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models ORDER BY id DESC"
                )
                rows = cursor.fetchall()
                return [MetadataModel.from_json(row["metadata_json"]) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch models: {exc}") from exc

    def query_by_accuracy(self, min_acc: float = 0.0) -> List[MetadataModel]:
        """Query models with accuracy >= min_acc, ordered by accuracy DESC."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE accuracy >= ? ORDER BY accuracy DESC",
                    (min_acc,),
                )
                rows = cursor.fetchall()
                return [MetadataModel.from_json(row["metadata_json"]) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to query models by accuracy: {exc}") from exc

    def query_by_accuracy_range(
        self,
        min: Optional[float] = None,
        max: Optional[float] = None,
        min_acc: Optional[float] = None,
        max_acc: Optional[float] = None,
    ) -> List[MetadataModel]:
        """Query models with accuracy within range [min, max]."""
        low = min if min is not None else (min_acc if min_acc is not None else 0.0)
        high = max if max is not None else (max_acc if max_acc is not None else 1.0)
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE accuracy >= ? AND accuracy <= ? ORDER BY accuracy DESC",
                    (low, high),
                )
                rows = cursor.fetchall()
                return [MetadataModel.from_json(row["metadata_json"]) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to query models by accuracy range: {exc}") from exc

    def query_by_dataset(self, dataset_hash: str) -> List[MetadataModel]:
        """Query models matching a specific dataset hash or path."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE dataset_hash = ? OR metadata_json LIKE ? ORDER BY id DESC",
                    (dataset_hash, f"%{dataset_hash}%"),
                )
                rows = cursor.fetchall()
                return [MetadataModel.from_json(row["metadata_json"]) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to query models by dataset: {exc}") from exc

    def query_by_dataset_version(self, dataset_path_or_hash: str) -> List[MetadataModel]:
        """Query models matching a specific dataset version."""
        return self.query_by_dataset(dataset_path_or_hash)

    def get_model_by_id(self, model_id: int) -> Optional[MetadataModel]:
        """Retrieve model metadata by database ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE id = ?",
                    (model_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return MetadataModel.from_json(row["metadata_json"])
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch model by ID: {exc}") from exc

    def get_model_by_name(self, model_name: str) -> Optional[MetadataModel]:
        """Retrieve latest model metadata matching model_name."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE model_name = ? ORDER BY id DESC LIMIT 1",
                    (model_name,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return MetadataModel.from_json(row["metadata_json"])
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch model by name: {exc}") from exc

    def get_model_by_file(self, model_file: str) -> Optional[MetadataModel]:
        """Retrieve latest model metadata matching model_file path."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE model_file = ? ORDER BY id DESC LIMIT 1",
                    (model_file,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return MetadataModel.from_json(row["metadata_json"])
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch model by file: {exc}") from exc

    def get_model_by_hash(self, model_hash: str) -> Optional[MetadataModel]:
        """Retrieve model metadata matching model_hash."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE model_hash = ?",
                    (model_hash,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return MetadataModel.from_json(row["metadata_json"])
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch model by hash: {exc}") from exc

    def get_model_id_by_hash(self, model_hash: str) -> Optional[int]:
        """Retrieve model row ID matching model_hash."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM models WHERE model_hash = ?",
                    (model_hash,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return int(row["id"])
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch model ID by hash: {exc}") from exc

    def get_best_model(self, metric: str = "accuracy") -> Optional[MetadataModel]:
        """Retrieve the top model based on a specified metric (default accuracy)."""
        models = self.get_all_models()
        if not models:
            return None
        valid_models = [m for m in models if metric in m.metrics]
        if not valid_models:
            return models[0]
        return max(reversed(valid_models), key=lambda m: float(m.metrics[metric]))

    def delete_model(self, model_id: int) -> bool:
        """Delete a model record by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("DELETE FROM models WHERE id = ?", (model_id,))
                conn.commit()
                return bool(cursor.rowcount > 0)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to delete model: {exc}") from exc

    def is_corrupted(self) -> bool:
        """Check if SQLite database file is corrupted."""
        if not os.path.exists(self.db_path):
            return False
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("PRAGMA integrity_check;")
                row = cursor.fetchone()
                if not row or row[0] != "ok":
                    return True
                return False
        except Exception:
            return True

    def rebuild_from_metadata(self, metadata_list: List[MetadataModel]) -> int:
        """Recreate database and re-insert all metadata objects with deduplication."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        self.init()

        # Deduplicate by model_hash and model_name (prefer latest created_at)
        unique_models: dict[str, MetadataModel] = {}
        for meta in metadata_list:
            key = meta.model_hash
            if key not in unique_models:
                unique_models[key] = meta
            elif meta.created_at > unique_models[key].created_at:
                unique_models[key] = meta

        count = 0
        for meta in unique_models.values():
            try:
                self.insert_model(meta)
                count += 1
            except Exception:
                pass
        return count

    # ==================== Phase 2 Session Database Methods ====================

    def insert_session(self, session: Session) -> int:
        """Insert a Session record into the database."""
        query = """
        INSERT INTO sessions (
            session_id, session_name, user, start_time, end_time,
            branch, initial_commit, final_commit, total_duration_seconds,
            models_count, best_model, best_accuracy, terminal_log,
            status, session_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    query,
                    (
                        session.session_id,
                        session.session_name,
                        session.user,
                        session.start_time.isoformat()
                        if isinstance(session.start_time, datetime)
                        else str(session.start_time),
                        session.end_time.isoformat()
                        if isinstance(session.end_time, datetime)
                        else (str(session.end_time) if session.end_time else None),
                        session.branch,
                        session.initial_commit,
                        session.final_commit,
                        session.total_duration_seconds,
                        session.models_count,
                        session.best_model,
                        session.best_accuracy,
                        session.terminal_log,
                        session.status,
                        session.to_json(),
                    ),
                )
                conn.commit()
                last_id = cursor.lastrowid
                if last_id is None:
                    raise DatabaseError("Failed to retrieve inserted session ID")

                for a in session.annotations:
                    self.add_session_annotation(session.session_id, a)

                return int(last_id)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to insert session: {exc}") from exc

    def update_session(self, session: Session) -> bool:
        """Update existing session by session_id."""
        query = """
        UPDATE sessions SET
            session_name = ?,
            user = ?,
            start_time = ?,
            end_time = ?,
            branch = ?,
            initial_commit = ?,
            final_commit = ?,
            total_duration_seconds = ?,
            models_count = ?,
            best_model = ?,
            best_accuracy = ?,
            terminal_log = ?,
            status = ?,
            session_json = ?
        WHERE session_id = ?
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    query,
                    (
                        session.session_name,
                        session.user,
                        session.start_time.isoformat()
                        if isinstance(session.start_time, datetime)
                        else str(session.start_time),
                        session.end_time.isoformat()
                        if isinstance(session.end_time, datetime)
                        else (str(session.end_time) if session.end_time else None),
                        session.branch,
                        session.initial_commit,
                        session.final_commit,
                        session.total_duration_seconds,
                        session.models_count,
                        session.best_model,
                        session.best_accuracy,
                        session.terminal_log,
                        session.status,
                        session.to_json(),
                        session.session_id,
                    ),
                )
                conn.commit()
                return bool(cursor.rowcount > 0)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to update session: {exc}") from exc

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by its unique session_id."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT session_json FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                row = cursor.fetchone()
                if not row or not row["session_json"]:
                    return None
                data = json.loads(row["session_json"])
                return Session.from_dict(data)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch session by ID: {exc}") from exc

    def get_session_by_name(self, session_name: str) -> Optional[Session]:
        """Retrieve latest session matching session_name."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT session_json FROM sessions WHERE session_name = ? ORDER BY id DESC LIMIT 1",
                    (session_name,),
                )
                row = cursor.fetchone()
                if not row or not row["session_json"]:
                    return None
                data = json.loads(row["session_json"])
                return Session.from_dict(data)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch session by name: {exc}") from exc

    def get_all_sessions(self) -> List[Session]:
        """Retrieve all recorded sessions."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT session_json FROM sessions ORDER BY id DESC"
                )
                rows = cursor.fetchall()
                sessions: List[Session] = []
                for row in rows:
                    if row["session_json"]:
                        try:
                            sessions.append(Session.from_dict(json.loads(row["session_json"])))
                        except Exception:
                            pass
                return sessions
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch all sessions: {exc}") from exc

    def add_session_annotation(self, session_id: str, annotation: Annotation) -> None:
        """Add an annotation record linked to a session."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO session_annotations (session_id, timestamp, text, model_related) VALUES (?, ?, ?, ?)",
                    (
                        session_id,
                        annotation.timestamp.isoformat()
                        if isinstance(annotation.timestamp, datetime)
                        else str(annotation.timestamp),
                        annotation.text,
                        annotation.model_related,
                    ),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to add session annotation: {exc}") from exc

    def get_session_annotations(self, session_id: str) -> List[Annotation]:
        """Get annotations for a given session."""
        try:
            with self.get_connection() as conn:
                query = (
                    "SELECT timestamp, text, model_related "
                    "FROM session_annotations WHERE session_id = ? ORDER BY id ASC"
                )
                cursor = conn.execute(query, (session_id,))
                rows = cursor.fetchall()
                return [
                    Annotation(
                        timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                        text=row["text"],
                        model_related=row["model_related"],
                    )
                    for row in rows
                ]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to get session annotations: {exc}") from exc

    def link_model_to_session(self, session_id: str, model_id: int, position: int) -> None:
        """Record model link to a session."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO session_models (session_id, model_id, position_in_session) VALUES (?, ?, ?)",
                    (session_id, model_id, position),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to link model to session: {exc}") from exc

    def get_models_for_session(self, session_id: str) -> List[MetadataModel]:
        """Retrieve model metadata records associated with a session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT m.metadata_json FROM models m
                    JOIN session_models sm ON m.id = sm.model_id
                    WHERE sm.session_id = ?
                    ORDER BY sm.position_in_session ASC
                    """,
                    (session_id,),
                )
                rows = cursor.fetchall()
                return [MetadataModel.from_json(row["metadata_json"]) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to get models for session: {exc}") from exc

    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[sqlite3.Row]:
        """Execute a raw SQL query and return fetched rows."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, tuple(params) if params else ())
                return cursor.fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Query execution failed: {exc}") from exc

    def create_evolution_entry(
        self,
        model_id: int,
        position: int,
        previous_model_id: Optional[int] = None,
        next_model_id: Optional[int] = None,
        session_id: Optional[str] = None,
        git_commit: str = "",
        reasoning: Optional[str] = None,
    ) -> int:
        """Create evolution tracking entry for a model."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO model_evolution (
                        model_id, position_in_timeline, previous_model_id, next_model_id,
                        session_id, git_commit, reasoning
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(model_id) DO UPDATE SET
                        position_in_timeline=excluded.position_in_timeline,
                        previous_model_id=excluded.previous_model_id,
                        next_model_id=excluded.next_model_id,
                        session_id=COALESCE(excluded.session_id, model_evolution.session_id),
                        git_commit=COALESCE(excluded.git_commit, model_evolution.git_commit),
                        reasoning=COALESCE(excluded.reasoning, model_evolution.reasoning),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (model_id, position, previous_model_id, next_model_id, session_id, git_commit, reasoning),
                )
                conn.commit()
                return int(cursor.lastrowid or 0)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to create evolution entry: {exc}") from exc

    def add_reasoning(
        self,
        model_id: int,
        reasoning: str,
        user: str = "",
        force: bool = False,
    ) -> bool:
        """Add or update reasoning annotation for a model by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT reasoning FROM model_evolution WHERE model_id = ?",
                    (model_id,),
                )
                row = cursor.fetchone()
                if row and row["reasoning"] and row["reasoning"].strip() and not force:
                    raise ValueError("Reasoning already exists. Use force=True to override.")

                now = datetime.now()
                now_str = now.isoformat()
                if row:
                    conn.execute(
                        """
                        UPDATE model_evolution
                        SET reasoning = ?, reasoning_added_by = ?,
                            reasoning_timestamp = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE model_id = ?
                        """,
                        (reasoning, user, now_str, model_id),
                    )
                else:
                    p_cur = conn.execute(
                        "SELECT COALESCE(MAX(position_in_timeline), 0) + 1 AS next_pos FROM model_evolution"
                    )
                    p_row = p_cur.fetchone()
                    next_pos = int(p_row["next_pos"]) if p_row else 1
                    conn.execute(
                        """
                        INSERT INTO model_evolution (
                            model_id, position_in_timeline, reasoning, reasoning_added_by, reasoning_timestamp
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (model_id, next_pos, reasoning, user, now_str),
                    )

                m_cur = conn.execute("SELECT metadata_json FROM models WHERE id = ?", (model_id,))
                m_row = m_cur.fetchone()
                if m_row and m_row["metadata_json"]:
                    try:
                        m_data: dict[str, Any] = json.loads(m_row["metadata_json"])
                        m_data["reasoning"] = reasoning
                        m_data["reasoning_added_by"] = user
                        m_data["reasoning_timestamp"] = now.isoformat()
                        updated_json_str = json.dumps(m_data, indent=2)
                        conn.execute(
                            "UPDATE models SET metadata_json = ? WHERE id = ?",
                            (updated_json_str, model_id),
                        )
                        # Sync update to disk sidecar if present
                        m_file = str(m_data.get("model_file") or "")
                        if m_file:
                            repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(self.db_path)))
                            candidates = [
                                os.path.join(repo_dir, f"{m_file}.vcm.json"),
                                f"{m_file}.vcm.json",
                            ]
                            for c in candidates:
                                if os.path.isfile(c):
                                    try:
                                        with open(c, "w", encoding="utf-8") as mf:
                                            mf.write(updated_json_str)
                                    except Exception:
                                        pass
                    except Exception:
                        pass

                conn.commit()
                return True
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to add reasoning: {exc}") from exc

    def add_model_reasoning(
        self,
        model_name_or_id: Union[str, int],
        reasoning: str,
        user: str = "",
        force: bool = False,
    ) -> bool:
        """Add reasoning for a model identified by name or ID."""
        if isinstance(model_name_or_id, int):
            model_id = model_name_or_id
        else:
            with self.get_connection() as conn:
                cur = conn.execute(
                    "SELECT id FROM models WHERE model_name = ? ORDER BY id DESC LIMIT 1",
                    (str(model_name_or_id),),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Model not found: {model_name_or_id}")
                model_id = int(row["id"])

        return self.add_reasoning(model_id, reasoning, user=user, force=force)

    def get_evolution_entry(self, model_name_or_id: Union[str, int]) -> Optional[EvolutionRecord]:
        """Get evolution tracking entry for a model by ID or model name."""
        try:
            with self.get_connection() as conn:
                if isinstance(model_name_or_id, int):
                    cursor = conn.execute("SELECT * FROM model_evolution WHERE model_id = ?", (model_name_or_id,))
                else:
                    cursor = conn.execute(
                        """
                        SELECT me.* FROM model_evolution me
                        JOIN models m ON me.model_id = m.id
                        WHERE m.model_name = ?
                        ORDER BY me.id DESC LIMIT 1
                        """,
                        (str(model_name_or_id),),
                    )
                row = cursor.fetchone()
                if not row:
                    return None
                return EvolutionRecord(dict(row))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to fetch evolution entry: {exc}") from exc

    def get_model_timeline(
        self,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        accuracy_range: Optional[Tuple[float, float]] = None,
    ) -> ModelTimeline:
        """Get complete model evolution timeline."""
        from vcm.models.timeline import TimelineStore

        store = TimelineStore(self)
        return store.get_model_timeline(
            session_id=session_id,
            since=since,
            until=until,
            accuracy_range=accuracy_range,
        )

    def auto_detect_timeline(self, session_id: Optional[str] = None) -> ModelTimeline:
        """Auto-detect timeline progression and return ModelTimeline."""
        from vcm.models.timeline import TimelineStore

        store = TimelineStore(self)
        store.auto_detect_and_link_timeline(session_id=session_id)
        return store.get_model_timeline(session_id=session_id)
