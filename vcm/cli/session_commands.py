"""CLI commands for Session Tracking and Activity Logging."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import datetime
from typing import Optional

import click
from tabulate import tabulate

from vcm.models.session import SessionComparator, SessionStore, SessionTracker
from vcm.utils.formatters import format_local_timestamp


@click.group(name="session")
def session_group() -> None:
    """Manage development and training sessions."""
    pass


@session_group.command(name="start")
@click.argument("session_name", required=False, default=None)
def session_start(session_name: Optional[str]) -> None:
    """Start tracking a development session."""
    name = session_name or f"sess_{datetime.now().strftime('%Y_%m_%d_%H_%M')}"
    existing_active = SessionTracker.get_active_session()
    if existing_active:
        msg = (
            f"Warning: Active session '{existing_active.session_name}' "
            f"({existing_active.session_id}) is already in progress."
        )
        click.echo(msg)
        click.echo("Use 'vcm session end' before starting a new one.")
        return

    tracker = SessionTracker(session_name=name)
    session_id = tracker.start()

    click.echo(f"Session started: {session_id}")
    click.echo(f"   Name: {name}")
    click.echo(f"   Start: {format_local_timestamp(tracker.session.start_time, '%Y-%m-%d %H:%M:%S', include_tz=True)}")
    click.echo(f"   User: {tracker.session.user}")
    click.echo("   Terminal logging: enabled")
    click.echo("Use 'vcm session end' when finished")


@session_group.command(name="end")
def session_end() -> None:
    """End the active session and save tracking data."""
    tracker = SessionTracker.get_active_session()
    if not tracker:
        click.echo("Error: No active session found to end.")
        sys.exit(1)

    tracker.end()

    dur = tracker.get_duration()
    hrs, remainder = divmod(int(dur.total_seconds()), 3600)
    mins, _ = divmod(remainder, 60)
    dur_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins} minutes"

    click.echo("Session ended.")
    click.echo(f"   Duration: {dur_str}")
    click.echo(f"   Models trained: {tracker.session.models_count}")
    click.echo(f"   Commits: {len(tracker.session.commits_made)}")
    if tracker.session.best_model:
        acc_str = f"{tracker.session.best_accuracy:.1%}" if tracker.session.best_accuracy is not None else "N/A"
        click.echo(f"   Best model: {tracker.session.best_model} (acc: {acc_str})")
    log_lines = len(tracker.session.terminal_log.splitlines()) if tracker.session.terminal_log else 0
    click.echo(f"   Terminal log: {log_lines:,} lines")
    click.echo(f"   Session saved: {tracker.session_id}")


@session_group.command(name="list")
def session_list() -> None:
    """List all recorded development sessions."""
    sessions = SessionStore.list_sessions()
    if not sessions:
        click.echo("No sessions found.")
        return

    rows = []
    for s in sessions:
        acc_str = f"{s.best_accuracy:.1%}" if s.best_accuracy is not None else "N/A"
        rows.append([
            s.session_id,
            s.session_name,
            s.user,
            s.status,
            s.models_count,
            s.best_model or "None",
            acc_str,
            format_local_timestamp(s.start_time, "%Y-%m-%d %H:%M"),
        ])

    headers = ["Session ID", "Name", "User", "Status", "Models", "Best Model", "Accuracy", "Started"]
    click.echo(tabulate(rows, headers=headers, tablefmt="rounded_grid"))


@session_group.command(name="info")
@click.argument("session_name")
def session_info(session_name: str) -> None:
    """Show detailed session information."""
    tracker = SessionStore.get_session(session_name)
    if not tracker:
        click.echo(f"Error: Session '{session_name}' not found.")
        sys.exit(1)

    s = tracker.session
    dur = tracker.get_duration()
    hrs, remainder = divmod(int(dur.total_seconds()), 3600)
    mins, _ = divmod(remainder, 60)
    dur_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins} minutes"

    click.echo(f"\nSession: {s.session_name}")
    click.echo("═" * 45)
    click.echo(f"ID: {s.session_id}")
    click.echo(f"User: {s.user}")
    click.echo(f"Duration: {dur_str}")
    click.echo(f"Status: {s.status}")

    click.echo(f"\nModels Trained ({len(s.models_trained)}):")
    for i, m in enumerate(s.models_trained, 1):
        best_marker = " [BEST]" if m.name == s.best_model else ""
        acc = f"{m.accuracy:.1%}" if m.accuracy is not None else "N/A"
        click.echo(f"  {i}. {m.name} (Acc: {acc}){best_marker}")

    click.echo(f"\nAnnotations ({len(s.annotations)}):")
    for a in s.annotations:
        click.echo(f"  • {format_local_timestamp(a.timestamp, '%H:%M:%S')}: \"{a.text}\"")

    click.echo(f"\nGit Commits ({len(s.commits_made)}):")
    for c in s.commits_made:
        click.echo(f"  • {c}")

    log_count = len(s.terminal_log.splitlines()) if s.terminal_log else 0
    click.echo(f"\nTerminal Log: {log_count:,} lines captured\n")


@session_group.command(name="logs")
@click.argument("session_name")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", help="Output format")
def session_logs(session_name: str, fmt: str) -> None:
    """View terminal logs recorded during a session."""
    tracker = SessionStore.get_session(session_name)
    if not tracker:
        click.echo(f"Error: Session '{session_name}' not found.")
        sys.exit(1)

    s = tracker.session
    logs = tracker.get_terminal_log()

    if fmt == "json":
        click.echo(json.dumps({"session_id": s.session_id, "terminal_log": logs}, indent=2))
    else:
        click.echo("═" * 60)
        click.echo(f"Session: {s.session_name}")
        click.echo(f"User: {s.user} | Branch: {s.branch or 'main'}")
        click.echo("─" * 60)
        click.echo(logs or "[No terminal logs recorded]")
        click.echo("─" * 60)
        click.echo(f"Total models: {len(s.models_trained)} | Best: {s.best_model or 'None'}")


@session_group.command(name="models")
@click.argument("session_name")
def session_models(session_name: str) -> None:
    """List all models trained in a specific session."""
    tracker = SessionStore.get_session(session_name)
    if not tracker:
        click.echo(f"Error: Session '{session_name}' not found.")
        sys.exit(1)

    s = tracker.session
    if not s.models_trained:
        click.echo(f"No models trained in session '{session_name}'.")
        return

    rows = []
    for i, m in enumerate(s.models_trained, 1):
        acc = f"{m.accuracy:.1%}" if m.accuracy is not None else "N/A"
        time_str = format_local_timestamp(m.timestamp, "%Y-%m-%d %H:%M:%S")
        pos_str = ""
        if i == 1:
            pos_str = "first"
        elif i == len(s.models_trained):
            pos_str = "last"
        if m.name == s.best_model:
            pos_str = f"{pos_str} [BEST]".strip()

        rows.append([i, m.name, acc, time_str, pos_str])

    headers = ["#", "Model Name", "Accuracy", "Time", "Position"]
    click.echo(f"\nModels trained in: {s.session_name}")
    click.echo(tabulate(rows, headers=headers, tablefmt="rounded_grid"))


@session_group.command(name="annotate")
@click.argument("text")
@click.option("--model", "model_related", default=None, help="Related model name")
def session_annotate(text: str, model_related: Optional[str]) -> None:
    """Add a developer note to the active session."""
    tracker = SessionTracker.get_active_session()
    if not tracker:
        click.echo("Error: No active session to annotate. Start one with 'vcm session start'.")
        sys.exit(1)

    anno = tracker.annotate(text=text, model_related=model_related)
    click.echo(f"Annotation recorded at {format_local_timestamp(anno.timestamp, '%H:%M:%S')}")


@session_group.command(name="compare")
@click.argument("session1")
@click.argument("session2")
def session_compare(session1: str, session2: str) -> None:
    """Compare two development sessions."""
    s1 = SessionStore.get_session(session1)
    s2 = SessionStore.get_session(session2)

    if not s1:
        click.echo(f"Error: Session '{session1}' not found.")
        sys.exit(1)
    if not s2:
        click.echo(f"Error: Session '{session2}' not found.")
        sys.exit(1)

    comp = SessionComparator.compare(s1, s2)

    click.echo(f"\nSession Comparison: {session1} vs {session2}")
    click.echo("═" * 45)
    click.echo("Metrics:")
    click.echo(f"  {session1}: {comp['s1_models_count']} models, best={comp['s1_best_accuracy']:.1%}")
    click.echo("\nResult:")
    click.echo(f"  Accuracy delta: {comp['accuracy_delta']:+.2%}")
    click.echo("\nRecommendation:")
    click.echo(f"  {comp['recommendation']}\n")


@session_group.command(name="explain-improvement")
@click.argument("session_name")
@click.argument("model1")
@click.argument("model2")
def session_explain_improvement(session_name: str, model1: str, model2: str) -> None:
    """Explain differences and improvements between two models in a session."""
    tracker = SessionStore.get_session(session_name)
    if not tracker:
        click.echo(f"Error: Session '{session_name}' not found.")
        sys.exit(1)

    m1_item = next((m for m in tracker.session.models_trained if m.name == model1), None)
    m2_item = next((m for m in tracker.session.models_trained if m.name == model2), None)

    if not m1_item or not m2_item:
        click.echo(f"Error: Could not find both {model1} and {model2} in session.")
        sys.exit(1)

    m1_acc = float(m1_item.accuracy or 0.0)
    m2_acc = float(m2_item.accuracy or 0.0)
    delta = m2_acc - m1_acc

    click.echo(f"\nComparing {model1} vs {model2} in session '{session_name}'")
    click.echo("─" * 50)
    click.echo(f"Accuracy: {m1_acc:.2%} -> {m2_acc:.2%} (delta: {delta:+.2%})")

    # Show annotations in between
    click.echo("\nSession Annotations:")
    for a in tracker.session.annotations:
        click.echo(f"  • {format_local_timestamp(a.timestamp, '%H:%M:%S')}: {a.text}")

    if delta > 0:
        conclusion_msg = f"Performance improved by {delta:+.2%}"
    elif delta < 0:
        conclusion_msg = f"Performance regressed by {delta:+.2%}"
    else:
        conclusion_msg = f"Performance unchanged ({delta:+.2%})"
    click.echo(f"\nConclusion: {conclusion_msg}\n")


@session_group.command(name="create-retrospective")
@click.option("--name", default="retrospective_session", help="Session name")
@click.option("--start", "start_str", default=None, help="Start ISO timestamp")
@click.option("--end", "end_str", default=None, help="End ISO timestamp")
def session_create_retrospective(name: str, start_str: Optional[str], end_str: Optional[str]) -> None:
    """Reconstruct a session retrospectively from past model records."""
    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else datetime(2024, 1, 1, 0, 0)
    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else datetime.now()

    tracker = SessionTracker.create_retrospective(
        name=name,
        start=start_dt,
        end=end_dt,
    )
    click.echo(f"Retrospective session '{name}' created with {len(tracker.session.models_trained)} models.")


@session_group.command(name="export")
@click.argument("session_name")
@click.option("--format", "fmt", type=click.Choice(["json", "html", "csv"]), default="json", help="Export format")
@click.option("--output", default=None, help="Output destination file")
def session_export(session_name: str, fmt: str, output: Optional[str]) -> None:
    """Export session report as JSON, HTML, or CSV."""
    tracker = SessionStore.get_session(session_name)
    if not tracker:
        click.echo(f"Error: Session '{session_name}' not found.")
        sys.exit(1)

    if fmt == "json":
        content = tracker.export_json()
    elif fmt == "html":
        content = tracker.export_html()
    else:
        # CSV
        out_buf = io.StringIO()
        writer = csv.writer(out_buf)
        writer.writerow(["model_name", "accuracy", "position", "timestamp"])
        for m in tracker.session.models_trained:
            writer.writerow([m.name, m.accuracy, m.position, m.timestamp])
        content = out_buf.getvalue()

    if output:
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"Exported to: {output}")
    else:
        # Default destination file or stdout
        dest = f"sessions/{session_name.replace(' ', '_')}.{fmt}"
        os.makedirs("sessions", exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"Exported to: {dest}")
