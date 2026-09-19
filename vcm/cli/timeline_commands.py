"""CLI commands for Model Evolution Timeline (timeline, timeline-reason, timeline analyze)."""

from __future__ import annotations

import getpass
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

import click

from vcm.config import VCMConfig
from vcm.db.database import Database
from vcm.models.timeline import TimelineStore
from vcm.utils.timeline_formatters import (
    format_timeline_ascii,
    format_timeline_csv,
    format_timeline_html,
    format_timeline_json,
    format_timeline_table,
    generate_analysis_report,
    format_local_timestamp,
)


def parse_accuracy_range(val: Optional[str]) -> Optional[Tuple[float, float]]:
    """Parse range string like '0.9-0.95' or '0.9,0.95' into tuple of floats."""
    if not val:
        return None
    cleaned = val.replace(",", "-")
    parts = [p.strip() for p in cleaned.split("-") if p.strip()]
    if len(parts) == 2:
        try:
            return (float(parts[0]), float(parts[1]))
        except ValueError:
            return None
    return None


def parse_date_filter(val: Optional[str]) -> Optional[datetime]:
    """Parse ISO or flexible date filter string."""
    if not val:
        return None
    val = val.strip()
    try:
        return datetime.fromisoformat(val)
    except ValueError:
        pass
    try:
        from dateutil import parser  # type: ignore

        parsed = parser.parse(val)
        if isinstance(parsed, datetime):
            return parsed
        return None
    except Exception:
        return None


def _show_timeline_impl(
    session: Optional[str],
    since: Optional[str],
    until: Optional[str],
    output_format: str,
    output: Optional[str],
    show_reasoning: bool,
    show_changes: bool,
    highlight_best: bool,
    accuracy_range: Optional[str],
) -> None:
    """Core execution logic for showing model evolution timeline."""
    try:
        config = VCMConfig.load()
        db = Database(config.database_path)
        db.init()
        store = TimelineStore(db)

        since_dt = parse_date_filter(since)
        until_dt = parse_date_filter(until)
        acc_range = parse_accuracy_range(accuracy_range)

        timeline = store.get_model_timeline(
            session_id=session,
            since=since_dt,
            until=until_dt,
            accuracy_range=acc_range,
        )

        if output_format == "table":
            rendered = format_timeline_table(
                timeline,
                show_reasoning=show_reasoning,
                show_changes=show_changes,
                highlight_best=highlight_best,
            )
        elif output_format == "html":
            rendered = format_timeline_html(timeline, show_reasoning=show_reasoning)
        elif output_format == "json":
            rendered = format_timeline_json(timeline)
        elif output_format == "csv":
            rendered = format_timeline_csv(timeline)
        elif output_format == "ascii":
            rendered = format_timeline_ascii(timeline)
        else:
            rendered = format_timeline_table(timeline, show_reasoning=show_reasoning)

        if output:
            out_dir = os.path.dirname(output)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(rendered)
            click.echo(f"Timeline exported to {output}")
        else:
            click.echo(rendered)
    except Exception as exc:
        click.echo(f"Error: Failed to display timeline: {exc}", err=True)
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option("--session", default=None, help="Filter timeline by session ID or name.")
@click.option("--since", default=None, help="Include models trained since date (e.g. 2026-01-15).")
@click.option("--until", default=None, help="Include models trained until date.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "html", "csv", "ascii"]),
    default="table",
    help="Output formatting format.",
)
@click.option("--output", default=None, help="Export timeline report to destination file.")
@click.option("--show-reasoning", is_flag=True, default=False, help="Display reasoning annotations for each model.")
@click.option("--show-changes", is_flag=True, default=False, help="Display code and parameter changes from previous.")
@click.option("--highlight-best", is_flag=True, default=True, help="Visually highlight best model in timeline.")
@click.option("--accuracy-range", default=None, help="Filter by accuracy range, e.g. 0.9-0.95.")
@click.pass_context
def timeline_group(
    ctx: click.Context,
    session: Optional[str],
    since: Optional[str],
    until: Optional[str],
    output_format: str,
    output: Optional[str],
    show_reasoning: bool,
    show_changes: bool,
    highlight_best: bool,
    accuracy_range: Optional[str],
) -> None:
    """Display model evolution timeline and progression tracking."""
    if ctx.invoked_subcommand is None:
        _show_timeline_impl(
            session=session,
            since=since,
            until=until,
            output_format=output_format,
            output=output,
            show_reasoning=show_reasoning,
            show_changes=show_changes,
            highlight_best=highlight_best,
            accuracy_range=accuracy_range,
        )


@timeline_group.command("show")
@click.option("--session", default=None, help="Filter timeline by session ID or name.")
@click.option("--since", default=None, help="Include models trained since date.")
@click.option("--until", default=None, help="Include models trained until date.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "html", "csv", "ascii"]),
    default="table",
    help="Output formatting format.",
)
@click.option("--output", default=None, help="Export timeline report to destination file.")
@click.option("--show-reasoning", is_flag=True, default=False, help="Display reasoning annotations for each model.")
@click.option("--show-changes", is_flag=True, default=False, help="Display code and parameter changes from previous.")
@click.option("--highlight-best", is_flag=True, default=True, help="Visually highlight best model in timeline.")
@click.option("--accuracy-range", default=None, help="Filter by accuracy range, e.g. 0.9-0.95.")
def timeline_show_cmd(
    session: Optional[str],
    since: Optional[str],
    until: Optional[str],
    output_format: str,
    output: Optional[str],
    show_reasoning: bool,
    show_changes: bool,
    highlight_best: bool,
    accuracy_range: Optional[str],
) -> None:
    """Explicit subcommand to display timeline."""
    _show_timeline_impl(
        session=session,
        since=since,
        until=until,
        output_format=output_format,
        output=output,
        show_reasoning=show_reasoning,
        show_changes=show_changes,
        highlight_best=highlight_best,
        accuracy_range=accuracy_range,
    )


@timeline_group.command("analyze")
@click.option("--session", default=None, help="Analyze models for a specific session.")
@click.option("--output", default=None, help="Export analysis report to file.")
def timeline_analyze_cmd(session: Optional[str], output: Optional[str]) -> None:
    """Analyze model evolution trajectory, regressions, and experimentation efficiency."""
    try:
        config = VCMConfig.load()
        db = Database(config.database_path)
        db.init()
        store = TimelineStore(db)

        timeline = store.get_model_timeline(session_id=session)
        report = generate_analysis_report(timeline, store)

        if output:
            out_dir = os.path.dirname(output)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            click.echo(f"Analysis exported to {output}")
        else:
            click.echo(report)
    except Exception as exc:
        click.echo(f"Error: Timeline analysis failed: {exc}", err=True)
        sys.exit(1)


def _reason_impl(model_name: str, reasoning: Optional[str], force: bool, show: bool) -> None:
    """Implementation for recording or viewing reasoning on a model."""
    try:
        config = VCMConfig.load()
        db = Database(config.database_path)
        db.init()

        if show:
            entry = db.get_evolution_entry(model_name)
            if entry and entry.get("reasoning"):
                click.echo(f"Reasoning for {model_name}: {entry['reasoning']}")
                if entry.get("reasoning_added_by"):
                    click.echo(f"  Added by:  {entry['reasoning_added_by']}")
                if entry.get("reasoning_timestamp"):
                    r_ts = format_local_timestamp(entry["reasoning_timestamp"], "%Y-%m-%d %H:%M:%S", include_tz=True)
                    click.echo(f"  Timestamp: {r_ts}")
            else:
                click.echo(f"No reasoning recorded for {model_name}")
            return

        if not reasoning or not reasoning.strip():
            click.echo("Error: REASONING text is required when not using --show", err=True)
            sys.exit(1)

        user = getpass.getuser()
        db.add_model_reasoning(
            model_name_or_id=model_name,
            reasoning=reasoning,
            user=user,
            force=force,
        )
        click.echo(f"Added reasoning to {model_name}")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Error: Failed to record reasoning: {exc}", err=True)
        sys.exit(1)


@timeline_group.command("reason")
@click.argument("model_name")
@click.argument("reasoning", required=False)
@click.option("--force", is_flag=True, default=False, help="Override existing reasoning annotation.")
@click.option("--show", is_flag=True, default=False, help="Show existing reasoning for model.")
def timeline_reason_subcmd(
    model_name: str,
    reasoning: Optional[str],
    force: bool,
    show: bool,
) -> None:
    """Add or update reasoning annotation for a model within timeline."""
    _reason_impl(model_name=model_name, reasoning=reasoning, force=force, show=show)


@click.command("timeline-reason")
@click.argument("model_name")
@click.argument("reasoning", required=False)
@click.option("--force", is_flag=True, default=False, help="Override existing reasoning annotation.")
@click.option("--show", is_flag=True, default=False, help="Show existing reasoning for model.")
def timeline_reason_standalone_cmd(
    model_name: str,
    reasoning: Optional[str],
    force: bool,
    show: bool,
) -> None:
    """Add or view reasoning for why a model version was trained."""
    _reason_impl(model_name=model_name, reasoning=reasoning, force=force, show=show)


__all__ = [
    "timeline_group",
    "timeline_reason_standalone_cmd",
    "timeline_analyze_cmd",
]
