"""Session data models, SessionTracker lifecycle, and comparative analysis."""

from __future__ import annotations

import getpass
import html
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from vcm.integrations.git_client import GitClient
from vcm.utils.terminal_logger import TerminalLogger


class SessionModelItem(dict[str, Any]):
    """Dictionary representing a model trained in a session with attribute-style access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


@dataclass
class Annotation:
    """User annotation or event note during a training session."""
    timestamp: datetime
    text: str
    model_related: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        ts_str = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
        d: Dict[str, Any] = {
            "timestamp": ts_str,
            "text": self.text,
            "model_related": self.model_related,
        }
        if self.tags:
            d["tags"] = list(self.tags)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Annotation:
        ts_raw = data.get("timestamp")
        if isinstance(ts_raw, datetime):
            ts = ts_raw
        elif isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return cls(
            timestamp=ts,
            text=str(data.get("text", "")),
            model_related=data.get("model_related"),
            tags=list(data.get("tags", [])),
        )


@dataclass(frozen=True)
class SessionInfo:
    """Contextual session information attached to model metadata."""
    session_id: str
    session_name: str
    session_start: Optional[str] = None
    session_end: Optional[str] = None
    position_in_session: Optional[int] = None
    previous_model: Optional[str] = None
    previous_model_in_session: Optional[str] = None
    next_model: Optional[str] = None
    next_model_in_session: Optional[str] = None
    session_best_model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        prev_m = self.previous_model or self.previous_model_in_session
        next_m = self.next_model or self.next_model_in_session
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "session_start": self.session_start,
            "session_end": self.session_end,
            "position_in_session": self.position_in_session,
            "previous_model": prev_m,
            "previous_model_in_session": prev_m,
            "next_model": next_m,
            "next_model_in_session": next_m,
            "session_best_model": self.session_best_model,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[SessionInfo]:
        if not data:
            return None
        prev_m = data.get("previous_model") or data.get("previous_model_in_session")
        next_m = data.get("next_model") or data.get("next_model_in_session")
        return cls(
            session_id=str(data.get("session_id", "")),
            session_name=str(data.get("session_name", "")),
            session_start=data.get("session_start"),
            session_end=data.get("session_end"),
            position_in_session=data.get("position_in_session"),
            previous_model=prev_m,
            previous_model_in_session=prev_m,
            next_model=next_m,
            next_model_in_session=next_m,
            session_best_model=data.get("session_best_model"),
        )


@dataclass
class Session:
    """State and recorded history of a training session."""
    session_id: str
    session_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    user: str = ""
    branch: Optional[str] = None
    initial_commit: Optional[str] = None
    final_commit: Optional[str] = None
    terminal_log: str = ""
    models_trained: List[SessionModelItem] = field(default_factory=list)
    commits_made: List[str] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    total_duration_seconds: Optional[int] = None
    models_count: int = 0
    best_model: Optional[str] = None
    best_accuracy: Optional[float] = None
    status: str = "inactive"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "start_time": (
                self.start_time.isoformat()
                if isinstance(self.start_time, datetime)
                else str(self.start_time)
            ),
            "end_time": (
                self.end_time.isoformat()
                if isinstance(self.end_time, datetime)
                else (str(self.end_time) if self.end_time else None)
            ),
            "user": self.user,
            "branch": self.branch,
            "initial_commit": self.initial_commit,
            "final_commit": self.final_commit,
            "terminal_log": self.terminal_log,
            "models_trained": [dict(m) for m in self.models_trained],
            "commits_made": list(self.commits_made),
            "annotations": [a.to_dict() for a in self.annotations],
            "total_duration_seconds": self.total_duration_seconds,
            "models_count": self.models_count,
            "best_model": self.best_model,
            "best_accuracy": self.best_accuracy,
            "status": self.status,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Session:
        st_raw = data.get("start_time")
        if isinstance(st_raw, datetime):
            start_time = st_raw
        elif isinstance(st_raw, str):
            try:
                start_time = datetime.fromisoformat(st_raw.replace("Z", "+00:00"))
            except ValueError:
                start_time = datetime.now(timezone.utc)
        else:
            start_time = datetime.now(timezone.utc)

        et_raw = data.get("end_time")
        end_time: Optional[datetime] = None
        if isinstance(et_raw, datetime):
            end_time = et_raw
        elif isinstance(et_raw, str):
            try:
                end_time = datetime.fromisoformat(et_raw.replace("Z", "+00:00"))
            except ValueError:
                end_time = None

        models_list = [SessionModelItem(m) for m in data.get("models_trained", [])]
        annotations_list = [Annotation.from_dict(a) if isinstance(a, dict) else a for a in data.get("annotations", [])]

        return cls(
            session_id=str(data.get("session_id", "")),
            session_name=str(data.get("session_name", "")),
            start_time=start_time,
            end_time=end_time,
            user=str(data.get("user", "")),
            branch=data.get("branch"),
            initial_commit=data.get("initial_commit"),
            final_commit=data.get("final_commit"),
            terminal_log=str(data.get("terminal_log", "")),
            models_trained=models_list,
            commits_made=list(data.get("commits_made", [])),
            annotations=annotations_list,
            total_duration_seconds=data.get("total_duration_seconds"),
            models_count=int(data.get("models_count", len(models_list))),
            best_model=data.get("best_model"),
            best_accuracy=(float(data["best_accuracy"]) if data.get("best_accuracy") is not None else None),
            status=str(data.get("status", "inactive")),
        )


class SessionTracker:
    """Manages active session lifecycle, output capture, model linkage, and reporting."""

    ACTIVE_SESSION_FILE = ".vcm/active_session.json"

    def __init__(
        self,
        session_name: str = "default_session",
        repo_path: str = ".",
        db_path: Optional[str] = None,
        session_id: Optional[str] = None,
        user: Optional[str] = None,
    ) -> None:
        self.repo_path = os.path.abspath(repo_path)
        self.session_name = session_name
        self.session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        self.db_path = db_path or os.path.join(self.repo_path, ".vcm", "vcm.db")
        self.git_client = GitClient(repo_path=self.repo_path)
        self.terminal_logger = TerminalLogger()

        self.session = Session(
            session_id=self.session_id,
            session_name=self.session_name,
            user=user or getpass.getuser(),
            start_time=datetime.now(timezone.utc),
            status="inactive",
        )

    @property
    def status(self) -> str:
        return self.session.status

    @status.setter
    def status(self, value: str) -> None:
        self.session.status = value

    @property
    def start_time(self) -> datetime:
        return self.session.start_time

    @start_time.setter
    def start_time(self, val: datetime) -> None:
        self.session.start_time = val

    @property
    def end_time(self) -> Optional[datetime]:
        return self.session.end_time

    @end_time.setter
    def end_time(self, val: Optional[datetime]) -> None:
        self.session.end_time = val

    @property
    def last_model_name(self) -> Optional[str]:
        if self.session.models_trained:
            val = self.session.models_trained[-1].get("name")
            return str(val) if val else None
        return None

    def _get_active_file_path(self) -> str:
        return os.path.join(self.repo_path, self.ACTIVE_SESSION_FILE)

    def _get_database(self) -> Any:
        from vcm.db.database import Database
        db = Database(db_path=self.db_path)
        db.init()
        return db

    def start(self, auto_capture_terminal: bool = True) -> str:
        """Start session tracking and terminal logging."""
        self.session.status = "active"
        self.session.start_time = datetime.now(timezone.utc)
        if not self.session.user:
            self.session.user = getpass.getuser()

        # Check git info
        git_info = self.git_client.get_safe_code_info()
        self.session.branch = git_info.git_branch or "main"
        self.session.initial_commit = git_info.git_commit
        if self.session.initial_commit:
            self.session.commits_made = [self.session.initial_commit]

        # Start capturing terminal output if requested
        if auto_capture_terminal:
            self.terminal_logger.start_capture()

        # Save active session marker file
        active_path = self._get_active_file_path()
        os.makedirs(os.path.dirname(active_path), exist_ok=True)
        with open(active_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "session_id": self.session_id,
                    "session_name": self.session_name,
                    "start_time": self.session.start_time.isoformat(),
                    "user": self.session.user,
                    "branch": self.session.branch,
                    "initial_commit": self.session.initial_commit,
                },
                f,
                indent=2,
            )

        # Persist session to database
        try:
            db = self._get_database()
            existing = db.get_session(self.session_id)
            if existing:
                db.update_session(self.session)
            else:
                db.insert_session(self.session)
        except Exception:
            pass

        return self.session_id

    def end(self) -> Session:
        """End session tracking, stop terminal capture, and persist final summary."""
        self.session.status = "completed"
        self.session.end_time = datetime.now(timezone.utc)

        # Sync from DB in case models were logged by CLI/subprocess
        try:
            db = self._get_database()
            saved = db.get_session(self.session_id)
            if saved and saved.models_trained:
                existing_names = {m.name for m in self.session.models_trained}
                for m in saved.models_trained:
                    if m.name not in existing_names:
                        self.session.models_trained.append(m)
                self.session.models_count = len(self.session.models_trained)
                self.session.best_model = saved.best_model
                self.session.best_accuracy = saved.best_accuracy
        except Exception:
            pass

        # Stop terminal capture
        captured = self.terminal_logger.stop_capture()
        if captured:
            self.session.terminal_log = captured

        # Update git commits
        git_info = self.git_client.get_safe_code_info()
        self.session.final_commit = git_info.git_commit
        if self.session.final_commit and self.session.final_commit not in self.session.commits_made:
            self.session.commits_made.append(self.session.final_commit)

        # Duration
        dur = self.get_duration()
        self.session.total_duration_seconds = max(1, int(dur.total_seconds()))

        # Remove active session marker
        active_path = self._get_active_file_path()
        if os.path.exists(active_path):
            try:
                os.remove(active_path)
            except Exception:
                pass

        # Update database
        try:
            db = self._get_database()
            db.update_session(self.session)
        except Exception:
            pass

        return self.session

    def log_model(
        self,
        model_meta: Any,
        model_name: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record model training event in the current session and maintain model chain."""
        extracted_name = model_name
        extracted_acc: Optional[float] = None
        extracted_metrics: Dict[str, Any] = dict(metrics or {})

        if isinstance(model_meta, dict):
            extracted_name = extracted_name or model_meta.get("name") or model_meta.get("model_name")
            if "accuracy" in model_meta:
                try:
                    extracted_acc = float(model_meta["accuracy"])
                except (ValueError, TypeError):
                    pass
            if "metrics" in model_meta and isinstance(model_meta["metrics"], dict):
                extracted_metrics.update(model_meta["metrics"])
                if extracted_acc is None and "accuracy" in extracted_metrics:
                    try:
                        extracted_acc = float(extracted_metrics["accuracy"])
                    except (ValueError, TypeError):
                        pass
        elif hasattr(model_meta, "model_name"):
            extracted_name = extracted_name or getattr(model_meta, "model_name")
            if hasattr(model_meta, "metrics") and isinstance(model_meta.metrics, dict):
                extracted_metrics.update(model_meta.metrics)
                if "accuracy" in extracted_metrics:
                    try:
                        extracted_acc = float(extracted_metrics["accuracy"])
                    except (ValueError, TypeError):
                        pass

        extracted_name = extracted_name or f"model_v{len(self.session.models_trained) + 1}"

        # Position in session
        position = len(self.session.models_trained) + 1

        # Link with previous model
        previous_item = self.session.models_trained[-1] if self.session.models_trained else None
        prev_model_name = previous_item.name if previous_item else None

        item = SessionModelItem(
            name=extracted_name,
            model_name=extracted_name,
            accuracy=extracted_acc,
            metrics=extracted_metrics,
            position=position,
            timestamp=datetime.now(timezone.utc).isoformat(),
            previous_model=prev_model_name,
            next_model=None,
        )

        if previous_item is not None:
            previous_item.next_model = item.name

        self.session.models_trained.append(item)
        self.session.models_count = len(self.session.models_trained)

        # Update best model
        candidates = [m for m in self.session.models_trained if m.accuracy is not None]
        if candidates:
            best_item = max(candidates, key=lambda m: float(m.accuracy or 0.0))
            self.session.best_model = best_item.name
            self.session.best_accuracy = float(best_item.accuracy or 0.0)
        else:
            self.session.best_model = item.name

        # Persist to database if initialized
        try:
            db = self._get_database()
            db.update_session(self.session)
        except Exception:
            pass

    def annotate(self, text: str, model_related: Optional[str] = None, tags: Optional[List[str]] = None) -> Annotation:
        """Add developer note/annotation to the active session."""
        annotation = Annotation(
            timestamp=datetime.now(timezone.utc),
            text=text,
            model_related=model_related,
            tags=list(tags) if tags else [],
        )
        self.session.annotations.append(annotation)

        try:
            db = self._get_database()
            db.add_session_annotation(self.session_id, annotation)
        except Exception:
            pass

        return annotation

    def get_terminal_log(self) -> str:
        """Retrieve full terminal log."""
        if self.terminal_logger._buffer:
            return self.terminal_logger.get_log()
        return self.session.terminal_log

    def get_models(self) -> List[SessionModelItem]:
        """Retrieve models trained in this session."""
        try:
            db = self._get_database()
            saved = db.get_session(self.session_id)
            if saved and saved.models_trained:
                existing_names = {m.name for m in self.session.models_trained}
                for m in saved.models_trained:
                    if m.name not in existing_names:
                        self.session.models_trained.append(m)
                self.session.models_count = len(self.session.models_trained)
                self.session.best_model = saved.best_model
                self.session.best_accuracy = saved.best_accuracy
        except Exception:
            pass
        return self.session.models_trained

    def get_annotations(self) -> List[Annotation]:
        """Retrieve annotations in this session."""
        return self.session.annotations

    def get_commits(self) -> List[str]:
        """Retrieve commits captured in this session."""
        return self.session.commits_made

    def get_duration(self) -> timedelta:
        """Compute duration of the session."""
        end_t = self.session.end_time or datetime.now(timezone.utc)
        start_t = self.session.start_time
        if start_t > end_t:
            return timedelta(seconds=0)
        return end_t - start_t

    def export_json(self) -> str:
        """Export complete session data as a formatted JSON string."""
        summary = self.session.to_dict()
        summary["models"] = [dict(m) for m in self.session.models_trained]
        if self.session.best_model:
            summary["best_model"] = {
                "name": self.session.best_model,
                "accuracy": self.session.best_accuracy,
            }
        return json.dumps(summary, indent=2)

    def export_html(self) -> str:
        """Export session report as standalone HTML document."""
        data = self.session.to_dict()
        dur = self.get_duration()
        models_html = ""
        for m in self.session.models_trained:
            acc_str = f"{m.accuracy:.2%}" if isinstance(m.accuracy, (int, float)) else "N/A"
            models_html += f"<li><strong>{html.escape(m.name)}</strong> - Accuracy: {acc_str}</li>"

        annotations_html = ""
        for a in self.session.annotations:
            ts_local = a.timestamp.astimezone() if a.timestamp.tzinfo else a.timestamp
            annotations_html += f"<li><em>{ts_local.strftime('%H:%M:%S')}</em>: {html.escape(a.text)}</li>"

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>VCM Session Report - {html.escape(data['session_name'])}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 40px; background: #0f172a; color: #f8fafc;
        }}
        .card {{
            background: #1e293b; border-radius: 8px; padding: 24px;
            margin-bottom: 24px; border: 1px solid #334155;
        }}
        h1 {{ color: #38bdf8; }}
        h2 {{ color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        .badge {{ background: #0284c7; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.9em; }}
        pre {{ background: #020617; padding: 16px; border-radius: 6px; overflow-x: auto; color: #a5f3fc; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Session: {html.escape(data['session_name'])} <span class="badge">{data['session_id']}</span></h1>
        <p><strong>User:</strong> {html.escape(data['user'])} |
           <strong>Duration:</strong> {dur} |
           <strong>Status:</strong> {data['status']}</p>
        <p><strong>Best Model:</strong> {html.escape(str(data['best_model']))} ({data['best_accuracy']})</p>
    </div>

    <div class="card">
        <h2>Models Trained ({len(data['models_trained'])})</h2>
        <ul>{models_html or '<li>No models recorded</li>'}</ul>
    </div>

    <div class="card">
        <h2>Annotations ({len(data['annotations'])})</h2>
        <ul>{annotations_html or '<li>No annotations recorded</li>'}</ul>
    </div>

    <div class="card">
        <h2>Terminal Log</h2>
        <pre>{html.escape(self.get_terminal_log() or 'No terminal logs captured.')}</pre>
    </div>
</body>
</html>"""

    def __enter__(self) -> SessionTracker:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end()

    @classmethod
    def get_active_session(cls, repo_path: str = ".") -> Optional[SessionTracker]:
        """Detect and load currently active session if one exists."""
        active_path = os.path.join(os.path.abspath(repo_path), cls.ACTIVE_SESSION_FILE)
        if not os.path.exists(active_path):
            return None

        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracker = cls(
                session_name=data.get("session_name", "active_session"),
                repo_path=repo_path,
                session_id=data.get("session_id"),
            )
            # Rehydrate from DB if available
            db = tracker._get_database()
            saved_session = db.get_session(data.get("session_id"))
            if saved_session:
                tracker.session = saved_session
            else:
                tracker.session.status = "active"
                if "start_time" in data:
                    tracker.session.start_time = datetime.fromisoformat(data["start_time"])
            return tracker
        except Exception:
            return None

    @classmethod
    def create_retrospective(
        cls,
        name: str,
        start: datetime,
        end: datetime,
        repo_path: str = ".",
    ) -> SessionTracker:
        """Reconstruct a session retrospectively from Git commits and Model database records."""
        tracker = cls(session_name=name, repo_path=repo_path)
        tracker.session.start_time = start
        tracker.session.end_time = end
        tracker.session.status = "completed"
        dur = end - start
        tracker.session.total_duration_seconds = max(1, int(dur.total_seconds()))

        # Query models from DB falling within [start, end]
        try:
            db = tracker._get_database()
            all_models = db.get_all_models()
            for m in reversed(all_models):
                t_str = m.training.timestamp
                if t_str:
                    try:
                        m_time = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                        # timezone naive vs aware check
                        if m_time.tzinfo is None and start.tzinfo is not None:
                            m_time = m_time.replace(tzinfo=timezone.utc)
                        elif m_time.tzinfo is not None and start.tzinfo is None:
                            start = start.replace(tzinfo=timezone.utc)
                            end = end.replace(tzinfo=timezone.utc)

                        if start <= m_time <= end:
                            tracker.log_model(m)
                    except Exception:
                        pass
        except Exception:
            pass

        # Save to DB
        try:
            db = tracker._get_database()
            db.insert_session(tracker.session)
        except Exception:
            pass

        return tracker


class ComparisonResult(dict[str, Any]):
    """Dictionary subclass supporting attribute-style field access."""

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"'ComparisonResult' object has no attribute '{item}'")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class SessionComparator:
    """Compares metrics, models count, and efficiency between two training sessions."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path

    def compare_sessions(
        self,
        session1: Union[str, Session, SessionTracker],
        session2: Union[str, Session, SessionTracker],
    ) -> ComparisonResult:
        """Compare two sessions by ID, name, or Session objects."""
        s1: Any = session1
        s2: Any = session2
        if isinstance(s1, str):
            loaded1 = SessionStore.get_session(s1, db_path=self.db_path)
            if loaded1:
                s1 = loaded1
        if isinstance(s2, str):
            loaded2 = SessionStore.get_session(s2, db_path=self.db_path)
            if loaded2:
                s2 = loaded2
        return self.compare(s1, s2)

    @classmethod
    def compare(
        cls,
        session1: Union[str, Session, SessionTracker],
        session2: Union[str, Session, SessionTracker],
    ) -> ComparisonResult:
        s1_obj: Any = session1
        s2_obj: Any = session2
        if isinstance(s1_obj, str):
            loaded1 = SessionStore.get_session(s1_obj)
            if loaded1:
                s1_obj = loaded1
        if isinstance(s2_obj, str):
            loaded2 = SessionStore.get_session(s2_obj)
            if loaded2:
                s2_obj = loaded2

        s1 = s1_obj.session if isinstance(s1_obj, SessionTracker) else s1_obj
        s2 = s2_obj.session if isinstance(s2_obj, SessionTracker) else s2_obj

        s1_count = len(s1.models_trained) if hasattr(s1, "models_trained") else 0
        s2_count = len(s2.models_trained) if hasattr(s2, "models_trained") else 0

        s1_acc = float(s1.best_accuracy or 0.0) if hasattr(s1, "best_accuracy") else 0.0
        s2_acc = float(s2.best_accuracy or 0.0) if hasattr(s2, "best_accuracy") else 0.0

        diff = s1_acc - s2_acc
        s1_name = getattr(s1, "session_name", "session1")
        s2_name = getattr(s2, "session_name", "session2")
        winner = s1_name if diff >= 0 else s2_name

        if s1_count == 0 and s2_count == 0:
            rec = "Neither session contains trained models to compare."
            winner = "none"
        elif s1_count == 0:
            rec = f"Session '{s2_name}' contains evaluated models ({s2_acc:.2%}), while '{s1_name}' has 0 models."
            winner = s2_name
        elif s2_count == 0:
            rec = f"Session '{s1_name}' contains evaluated models ({s1_acc:.2%}), while '{s2_name}' has 0 models."
            winner = s1_name
        elif diff == 0:
            rec = f"Both sessions achieved parity at {s1_acc:.2%} accuracy."
            winner = "tie"
        else:
            rec = f"Session '{winner}' produced higher accuracy ({max(s1_acc, s2_acc):.2%})."

        return ComparisonResult({
            "models_count": {"s1": s1_count, "s2": s2_count},
            "s1_models_count": s1_count,
            "s2_models_count": s2_count,
            "best_accuracy": {"s1": s1_acc, "s2": s2_acc},
            "s1_best_accuracy": s1_acc,
            "s2_best_accuracy": s2_acc,
            "accuracy_delta": diff,
            "better_session": winner,
            "recommendation": rec,
        })


class SessionStore:
    """Convenience persistence and lookup utility for sessions."""

    @classmethod
    def _find_db_path(cls, repo_path: str, db_path: Optional[str] = None) -> str:
        if db_path:
            return db_path
        abs_repo = os.path.abspath(repo_path)
        candidates = [
            os.path.join(abs_repo, ".vcm", "vcm.db"),
            os.path.join(abs_repo, "vcm.db"),
            os.path.join(abs_repo, "test.db"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return candidates[0]

    @classmethod
    def get_session(
        cls,
        session_id_or_name: str,
        repo_path: str = ".",
        db_path: Optional[str] = None,
    ) -> Optional[SessionTracker]:
        from vcm.db.database import Database
        target_db = cls._find_db_path(repo_path, db_path)
        db = Database(db_path=target_db)
        db.init()

        session = db.get_session(session_id_or_name)
        if not session:
            session = db.get_session_by_name(session_id_or_name)
        if not session:
            return None

        tracker = SessionTracker(
            session_name=session.session_name,
            repo_path=repo_path,
            db_path=target_db,
            session_id=session.session_id,
        )
        tracker.session = session
        return tracker

    @classmethod
    def list_sessions(cls, repo_path: str = ".", db_path: Optional[str] = None) -> List[Session]:
        from vcm.db.database import Database
        target_db = cls._find_db_path(repo_path, db_path)
        db = Database(db_path=target_db)
        db.init()
        return db.get_all_sessions()
