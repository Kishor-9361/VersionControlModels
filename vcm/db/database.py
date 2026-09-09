"""SQLite Database layer for VCM model metadata indexing and querying."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, List, Optional

from vcm.models.metadata import MetadataModel


class DatabaseError(Exception):
    """Raised when database operations encounter an error."""
    pass


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

    CREATE INDEX IF NOT EXISTS idx_model_name ON models(model_name);
    CREATE INDEX IF NOT EXISTS idx_accuracy ON models(accuracy DESC);
    CREATE INDEX IF NOT EXISTS idx_git_commit ON models(git_commit);
    CREATE INDEX IF NOT EXISTS idx_dataset_hash ON models(dataset_hash);
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
                conn.commit()
                last_id = cursor.lastrowid
                if last_id is None:
                    raise DatabaseError("Failed to retrieve inserted model ID")
                return int(last_id)
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

    def query_by_dataset(self, dataset_hash: str) -> List[MetadataModel]:
        """Query models matching a specific dataset hash."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT metadata_json FROM models WHERE dataset_hash = ? ORDER BY id DESC",
                    (dataset_hash,),
                )
                rows = cursor.fetchall()
                return [MetadataModel.from_json(row["metadata_json"]) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to query models by dataset: {exc}") from exc

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
        return max(valid_models, key=lambda m: float(m.metrics[metric]))

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
        """Recreate database and re-insert all metadata objects."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        self.init()
        count = 0
        for meta in metadata_list:
            self.insert_model(meta)
            count += 1
        return count
