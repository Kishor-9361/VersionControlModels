"""Timeline store, query methods, regression analysis, and evolution detection."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from vcm.models.evolution import (
    Annotation,
    EvolutionEntry,
    ModelDifference,
    ModelTimeline,
)

if TYPE_CHECKING:
    from vcm.db.database import Database


class TimelineStore:
    """Query and manage model evolution timelines."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_model_timeline(
        self,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        accuracy_range: Optional[Tuple[float, float]] = None,
    ) -> ModelTimeline:
        """Get chronologically ordered model progression."""
        # Ensure database is initialized
        self.db.init()

        # Check if model_evolution table has records; if not, attempt auto-detect
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM model_evolution")
            row = cursor.fetchone()
            count = row["cnt"] if row else 0

            # If models exist but model_evolution is empty, auto-link
            if count == 0:
                m_cur = conn.execute("SELECT COUNT(*) AS cnt FROM models")
                m_row = m_cur.fetchone()
                if m_row and m_row["cnt"] > 0:
                    self.auto_detect_and_link_timeline(session_id=None)

        query = """
        SELECT
            me.position_in_timeline,
            m.id AS model_id,
            m.model_name,
            m.training_timestamp,
            m.accuracy,
            m.metadata_json,
            me.reasoning,
            me.reasoning_added_by,
            me.reasoning_timestamp,
            me.previous_model_id,
            me.next_model_id,
            me.session_id,
            m.git_commit
        FROM model_evolution me
        JOIN models m ON me.model_id = m.id
        WHERE 1=1
        """
        params: List[Any] = []

        if session_id:
            query += " AND (me.session_id = ? OR m.metadata_json LIKE ?)"
            params.append(session_id)
            params.append(f'%"session_id": "{session_id}"%')

        if since:
            query += " AND COALESCE(m.training_timestamp, m.created_at) >= ?"
            params.append(since.isoformat() if isinstance(since, datetime) else str(since))

        if until:
            query += " AND COALESCE(m.training_timestamp, m.created_at) <= ?"
            params.append(until.isoformat() if isinstance(until, datetime) else str(until))

        if accuracy_range:
            query += " AND m.accuracy BETWEEN ? AND ?"
            params.extend([float(accuracy_range[0]), float(accuracy_range[1])])

        query += " ORDER BY me.position_in_timeline ASC, m.training_timestamp ASC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, tuple(params))
            rows = cursor.fetchall()

        entries: List[EvolutionEntry] = []
        prev_meta_data: Optional[Dict[str, Any]] = None
        for row in rows:
            pos = int(row["position_in_timeline"])
            model_id = int(row["model_id"])
            model_name = str(row["model_name"])
            ts_val = row["training_timestamp"]
            if isinstance(ts_val, datetime):
                ts = ts_val
            elif isinstance(ts_val, str):
                try:
                    ts = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                except ValueError:
                    ts = datetime.now()
            else:
                ts = datetime.now()

            acc = float(row["accuracy"]) if row["accuracy"] is not None else 0.0

            meta_data: Dict[str, Any] = {}
            if row["metadata_json"]:
                try:
                    meta_data = json.loads(row["metadata_json"])
                except Exception:
                    meta_data = {}

            metrics = meta_data.get("metrics", {})
            parsed_metrics = {str(k): float(v) for k, v in metrics.items() if isinstance(v, (int, float))}

            r_ts_val = row["reasoning_timestamp"]
            r_ts: Optional[datetime] = None
            if isinstance(r_ts_val, datetime):
                r_ts = r_ts_val
            elif isinstance(r_ts_val, str) and r_ts_val:
                try:
                    r_ts = datetime.fromisoformat(r_ts_val.replace("Z", "+00:00"))
                except ValueError:
                    r_ts = None

            reasoning = row["reasoning"] or meta_data.get("reasoning")
            reasoning_by = row["reasoning_added_by"] or meta_data.get("reasoning_added_by")

            prev_entry = entries[-1] if entries else None
            prev_model = prev_entry.model_name if prev_entry else None
            prev_acc = prev_entry.accuracy if prev_entry else None
            delta = (acc - prev_acc) if prev_acc is not None else None

            # Calculate changes difference if previous model exists
            diff: Optional[ModelDifference] = None
            if prev_entry and meta_data:
                code_dict = meta_data.get("code", {})
                hyper_dict = meta_data.get("hyperparameters", {})
                prev_hyper = prev_meta_data.get("hyperparameters", {}) if prev_meta_data else {}
                changes_dict = meta_data.get("changes_from_previous") or {}

                code_changed = bool(code_dict.get("git_commit") != prev_entry.git_commit)
                git_commits = [code_dict.get("git_commit", "")] if code_changed else []

                if changes_dict and "hyperparameters" in changes_dict:
                    hyper_changes = {
                        k: (None, v) if not isinstance(v, (list, tuple)) else (v[0], v[1])
                        for k, v in changes_dict["hyperparameters"].items()
                    }
                else:
                    hyper_changes = {}
                    all_h_keys = set(hyper_dict.keys()) | set(prev_hyper.keys())
                    for k in all_h_keys:
                        old_v = prev_hyper.get(k)
                        new_v = hyper_dict.get(k)
                        if old_v != new_v:
                            hyper_changes[k] = (old_v, new_v)

                diff = ModelDifference(
                    code_changed=code_changed,
                    git_commits=git_commits,
                    hyperparams_changed=hyper_changes,
                )

            prev_meta_data = meta_data

            entry = EvolutionEntry(
                position=pos,
                model_name=model_name,
                model_id=model_id,
                timestamp=ts,
                accuracy=acc,
                metrics=parsed_metrics,
                reasoning=reasoning,
                reasoning_added_by=reasoning_by,
                reasoning_timestamp=r_ts,
                previous_model=prev_model,
                previous_model_accuracy=prev_acc,
                accuracy_improvement=delta,
                changes=diff,
                session_id=row["session_id"],
                git_commit=str(row["git_commit"] or ""),
            )
            entries.append(entry)

        # Build ModelTimeline statistics
        if not entries:
            return ModelTimeline(
                entries=[],
                total_models=0,
                best_model=None,
                worst_model=None,
                best_accuracy=0.0,
                worst_accuracy=0.0,
                accuracy_improvement=0.0,
                date_range=(None, None),
                session_ids=set(),
            )

        accuracies = [e.accuracy for e in entries]
        max_acc = max(accuracies)
        min_acc = min(accuracies)
        best_entry = max(entries, key=lambda e: e.accuracy)
        worst_entry = min(entries, key=lambda e: e.accuracy)

        # Improvement from first model to last model (or best vs first)
        improvement = entries[-1].accuracy - entries[0].accuracy if len(entries) > 1 else 0.0

        date_range = (entries[0].timestamp, entries[-1].timestamp)
        session_ids: Set[str] = {e.session_id for e in entries if e.session_id}

        return ModelTimeline(
            entries=entries,
            total_models=len(entries),
            best_model=best_entry.model_name,
            worst_model=worst_entry.model_name,
            best_accuracy=max_acc,
            worst_accuracy=min_acc,
            accuracy_improvement=round(improvement, 6),
            date_range=date_range,
            session_ids=session_ids,
        )

    def detect_regressions(self, timeline: ModelTimeline) -> List[Dict[str, Any]]:
        """Identify accuracy regressions in chronological progression."""
        regressions: List[Dict[str, Any]] = []

        for i, entry in enumerate(timeline.entries):
            if i > 0:
                prev_entry = timeline.entries[i - 1]
                if entry.accuracy < prev_entry.accuracy:
                    delta = entry.accuracy - prev_entry.accuracy
                    regressions.append(
                        {
                            "model": entry.model_name,
                            "position": entry.position,
                            "accuracy": entry.accuracy,
                            "previous_model": prev_entry.model_name,
                            "previous_accuracy": prev_entry.accuracy,
                            "delta": delta,
                            "severity": "high" if abs(delta) > 0.02 else "low",
                        }
                    )

        return regressions

    def detect_timeline_gaps(self, timeline: ModelTimeline) -> List[str]:
        """Find timeline anomalies: missing reasoning, regressions, position jumps."""
        issues: List[str] = []

        for entry in timeline.entries:
            if not entry.reasoning or not entry.reasoning.strip():
                issues.append(f"Missing reasoning for {entry.model_name}")

        regressions = self.detect_regressions(timeline)
        for reg in regressions:
            issues.append(
                f"Accuracy regression at {reg['model']}: {reg['delta']:+.2%} "
                f"(from {reg['previous_accuracy']:.2%} to {reg['accuracy']:.2%})"
            )

        return issues

    def auto_detect_and_link_timeline(self, session_id: Optional[str] = None) -> None:
        """Automatically detect model progression from timestamps and link as evolution chain."""
        self.db.init()
        query = "SELECT id, model_name, training_timestamp, accuracy FROM models WHERE 1=1"
        params: List[Any] = []

        if session_id:
            query += " AND (metadata_json LIKE ?)"
            params.append(f'%"session_id": "{session_id}"%')

        query += " ORDER BY training_timestamp ASC, id ASC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, tuple(params))
            models = cursor.fetchall()

            for pos, model_row in enumerate(models, 1):
                model_id = int(model_row["id"])
                prev_id = int(models[pos - 2]["id"]) if pos > 1 else None
                next_id = int(models[pos]["id"]) if pos < len(models) else None

                conn.execute(
                    """
                    INSERT INTO model_evolution (
                        model_id, position_in_timeline, previous_model_id, next_model_id, session_id
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(model_id) DO UPDATE SET
                        position_in_timeline=excluded.position_in_timeline,
                        previous_model_id=excluded.previous_model_id,
                        next_model_id=excluded.next_model_id
                    """,
                    (model_id, pos, prev_id, next_id, session_id),
                )
            conn.commit()


def detect_timeline_issues(
    timeline: Optional[ModelTimeline] = None,
    db: Optional[Database] = None,
) -> List[str]:
    """Top-level helper to detect timeline issues (regressions, missing reasoning)."""
    if timeline is not None:
        store = TimelineStore(db if db is not None else timeline_store_db_factory())
        return store.detect_timeline_gaps(timeline)

    # If timeline is not provided, fetch from database
    real_db = db if db is not None else timeline_store_db_factory()
    store = TimelineStore(real_db)
    current_timeline = store.get_model_timeline()
    return store.detect_timeline_gaps(current_timeline)


def timeline_store_db_factory() -> Database:
    """Helper factory to instantiate Database from active configuration."""
    from vcm.config import VCMConfig
    from vcm.db.database import Database

    config = VCMConfig.load()
    return Database(db_path=config.database_path)


__all__ = [
    "ModelDifference",
    "Annotation",
    "EvolutionEntry",
    "ModelTimeline",
    "TimelineStore",
    "detect_timeline_issues",
]
