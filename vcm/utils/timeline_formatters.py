"""Formatters for Model Evolution Timeline: Table, HTML, JSON, CSV, and ASCII plots."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from vcm.models.evolution import ModelTimeline


def format_local_timestamp(dt_val: Any, fmt: str = "%Y-%m-%d %H:%M:%S", include_tz: bool = False) -> str:
    """Convert UTC or ISO timestamp to user's local timezone (e.g. IST) and format string."""
    if not dt_val:
        return "N/A"

    parsed_dt: Optional[datetime] = None
    if isinstance(dt_val, datetime):
        parsed_dt = dt_val
    elif isinstance(dt_val, str):
        try:
            parsed_dt = datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
        except Exception:
            try:
                parsed_dt = datetime.strptime(dt_val[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                return str(dt_val)[:19]

    if parsed_dt is not None:
        if parsed_dt.tzinfo is not None:
            local_dt = parsed_dt.astimezone()
        else:
            local_dt = parsed_dt.replace(tzinfo=timezone.utc).astimezone()

        formatted = local_dt.strftime(fmt)
        if include_tz:
            tz_str = local_dt.strftime("%Z")
            if tz_str:
                formatted += f" ({tz_str})"
        return formatted

    return str(dt_val)


def format_timeline_table(
    timeline: ModelTimeline,
    show_reasoning: bool = True,
    show_changes: bool = True,
    highlight_best: bool = True,
) -> str:
    """Format timeline progression as a formatted text / ASCII table."""
    output: List[str] = []
    output.append("Model Evolution Timeline")
    output.append("═" * 70)
    output.append("")

    if not timeline.entries:
        output.append("No models recorded in evolution timeline.")
        output.append("═" * 70)
        return "\n".join(output)

    for entry in timeline.entries:
        badge = ""
        if highlight_best and entry.model_name == timeline.best_model:
            badge = " [BEST]"

        change_str = ""
        if entry.accuracy_improvement is not None:
            if entry.accuracy_improvement > 0:
                change_str = f" (+{entry.accuracy_improvement:.1%})"
            elif entry.accuracy_improvement < 0:
                change_str = f" ({entry.accuracy_improvement:.1%}) [REGRESSION]"
            else:
                change_str = " (no change)"
        else:
            change_str = " (baseline)"

        date_str = format_local_timestamp(entry.timestamp, "%Y-%m-%d %H:%M:%S")

        output.append(f"Position {entry.position} │ {entry.model_name}{badge}")
        output.append(f"Accuracy   │ {entry.accuracy:.1%}{change_str}")
        output.append(f"Date       │ {date_str}")

        if show_reasoning and entry.reasoning:
            output.append(f"Why this?  │ {entry.reasoning}")

        if entry.session_id:
            output.append(f"Session    │ {entry.session_id}")

        if show_changes and entry.changes:
            ch_list: List[str] = []
            if entry.changes.code_changed:
                ch_list.append("Code modified")
            if entry.changes.data_changed:
                ch_list.append("Data updated")
            if entry.changes.hyperparams_changed:
                params_str = ", ".join(entry.changes.hyperparams_changed.keys())
                ch_list.append(f"Hyperparams ({params_str})")
            if ch_list:
                output.append(f"Changes    │ {'; '.join(ch_list)}")

        output.append("")

    # Summary section
    output.append("═" * 70)
    output.append("Summary")
    output.append("═" * 70)
    output.append(f"Total models:        {timeline.total_models}")
    output.append(f"Best model:          {timeline.best_model or 'N/A'} ({timeline.best_accuracy:.1%})")
    if timeline.best_accuracy == timeline.worst_accuracy and timeline.total_models > 1:
        output.append(f"Worst model:         None (all models tied at {timeline.best_accuracy:.1%})")
    else:
        output.append(f"Worst model:         {timeline.worst_model or 'N/A'} ({timeline.worst_accuracy:.1%})")
    output.append(f"Overall improvement: {timeline.accuracy_improvement:+.1%}")

    regressions = [e for e in timeline.entries if e.accuracy_improvement is not None and e.accuracy_improvement < 0]
    if regressions:
        reg_names = ", ".join(e.model_name for e in regressions)
        output.append(f"Regressions:         {len(regressions)} ({reg_names})")

    if timeline.session_ids:
        output.append(f"Sessions involved:   {len(timeline.session_ids)}")

    return "\n".join(output)


def format_timeline_html(timeline: ModelTimeline, show_reasoning: bool = True) -> str:
    """Format timeline as interactive, responsive HTML report with charts and model cards."""
    # Generate SVG points for chart
    svg_points = ""
    svg_markers = ""
    if timeline.entries:
        width = 750
        height = 200
        padding = 40
        n = len(timeline.entries)
        min_acc = max(0.0, timeline.worst_accuracy - 0.05)
        max_acc = min(1.0, timeline.best_accuracy + 0.05)
        span = (max_acc - min_acc) if max_acc > min_acc else 1.0

        coords = []
        for i, entry in enumerate(timeline.entries):
            x = padding + (i * (width - 2 * padding) / (n - 1 if n > 1 else 1))
            normalized_y = (entry.accuracy - min_acc) / span
            y = height - padding - (normalized_y * (height - 2 * padding))
            coords.append((x, y, entry))

        svg_points = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in coords)
        for x, y, entry in coords:
            color = "#4caf50" if entry.model_name == timeline.best_model else "#2196f3"
            if entry.accuracy_improvement and entry.accuracy_improvement < 0:
                color = "#f44336"
            svg_markers += (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}"/>'
                f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" font-size="11" '
                f'fill="#333">{entry.model_name} ({entry.accuracy:.1%})</text>'
            )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Evolution Timeline</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 24px;
            background: #f8fafc;
            color: #1e293b;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 26px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #64748b;
            margin-bottom: 24px;
            font-size: 14px;
        }}
        .chart-box {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .model-cards {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #94a3b8;
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            transition: transform 0.15s ease;
        }}
        .card:hover {{
            transform: translateX(2px);
        }}
        .card.best {{
            border-left-color: #10b981;
            background: #f0fdf4;
        }}
        .card.regression {{
            border-left-color: #ef4444;
            background: #fef2f2;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .model-title {{
            font-size: 17px;
            font-weight: 600;
            color: #0f172a;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            font-size: 12px;
            font-weight: 600;
            border-radius: 9999px;
            background: #e2e8f0;
            color: #334155;
        }}
        .badge.best {{
            background: #d1fae5;
            color: #065f46;
        }}
        .badge.regression {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .badge.improvement {{
            background: #dcfce7;
            color: #166534;
        }}
        .metrics-row {{
            display: flex;
            gap: 20px;
            font-size: 14px;
            color: #475569;
            margin-bottom: 8px;
        }}
        .accuracy-val {{
            font-size: 18px;
            font-weight: 700;
            color: #0284c7;
        }}
        .reasoning-box {{
            margin-top: 8px;
            padding: 8px 12px;
            background: rgba(0,0,0,0.03);
            border-radius: 4px;
            font-size: 13px;
            color: #334155;
            font-style: italic;
        }}
        .summary-box {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .summary-box h2 {{
            font-size: 18px;
            margin-top: 0;
            color: #0f172a;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-top: 12px;
        }}
        .stat-item {{
            display: flex;
            flex-direction: column;
        }}
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Model Evolution Timeline</h1>
        <div class="subtitle">Progression and Decision Tracking across {timeline.total_models} Model Experiments</div>

        <div class="chart-box">
            <svg viewBox="0 0 750 200" width="100%" height="200">
                <polyline fill="none" stroke="#0284c7" stroke-width="2" points="{svg_points}" />
                {svg_markers}
            </svg>
        </div>

        <div class="model-cards">
"""

    for entry in timeline.entries:
        is_best = entry.model_name == timeline.best_model
        is_reg = entry.accuracy_improvement is not None and entry.accuracy_improvement < 0
        card_cls = "card"
        badge_html = ""

        if is_best:
            card_cls += " best"
            badge_html = '<span class="badge best">[BEST]</span>'
        elif is_reg:
            card_cls += " regression"
            badge_html = f'<span class="badge regression">{entry.accuracy_improvement:+.1%} REGRESSION</span>'
        elif entry.accuracy_improvement and entry.accuracy_improvement > 0:
            badge_html = f'<span class="badge improvement">+{entry.accuracy_improvement:.1%}</span>'

        date_str = format_local_timestamp(entry.timestamp, "%b %d, %H:%M")

        reasoning_html = ""
        if show_reasoning and entry.reasoning:
            reasoning_html = f'<div class="reasoning-box"><strong>Why:</strong> {entry.reasoning}</div>'

        html += f"""            <div class="{card_cls}">
                <div class="card-header">
                    <span class="model-title">#{entry.position} {entry.model_name}</span>
                    {badge_html}
                </div>
                <div class="metrics-row">
                    <div>Accuracy: <span class="accuracy-val">{entry.accuracy:.1%}</span></div>
                    <div>Trained: {date_str}</div>
                    {f"<div>Session: {entry.session_id}</div>" if entry.session_id else ""}
                </div>
                {reasoning_html}
            </div>
"""

    reg_count = len([e for e in timeline.entries if e.accuracy_improvement is not None and e.accuracy_improvement < 0])

    html += f"""        </div>

        <div class="summary-box">
            <h2>Timeline Summary & Analysis</h2>
            <div class="summary-grid">
                <div class="stat-item">
                    <span class="stat-label">Total Models</span>
                    <span class="stat-value">{timeline.total_models}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Best Model</span>
                    <span class="stat-value">{timeline.best_model or 'N/A'} ({timeline.best_accuracy:.1%})</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Net Improvement</span>
                    <span class="stat-value">{timeline.accuracy_improvement:+.1%}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Regressions</span>
                    <span class="stat-value">{reg_count}</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html


def format_timeline_json(timeline: ModelTimeline) -> str:
    """Format timeline as serialized JSON."""
    return json.dumps(timeline.to_dict(), indent=2, default=str)


def format_timeline_csv(timeline: ModelTimeline) -> str:
    """Format timeline progression as CSV text."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "position",
        "model_name",
        "accuracy",
        "accuracy_improvement",
        "reasoning",
        "timestamp",
        "session_id",
        "git_commit",
    ])

    for entry in timeline.entries:
        ts_str = (
            entry.timestamp.isoformat()
            if isinstance(entry.timestamp, datetime)
            else str(entry.timestamp)
        )
        writer.writerow([
            entry.position,
            entry.model_name,
            entry.accuracy,
            entry.accuracy_improvement if entry.accuracy_improvement is not None else "",
            entry.reasoning or "",
            ts_str,
            entry.session_id or "",
            entry.git_commit,
        ])

    return output.getvalue()


def format_timeline_ascii(timeline: ModelTimeline) -> str:
    """Format timeline as an ASCII visualization plot."""
    if not timeline.entries:
        return "No timeline data available to plot."

    lines: List[str] = [
        "Model Accuracy Over Time",
        "═" * 45,
        "",
    ]

    min_acc = min(e.accuracy for e in timeline.entries)
    max_acc = max(e.accuracy for e in timeline.entries)
    steps = 6

    if max_acc > min_acc:
        y_min = max(0.0, min_acc - 0.05)
        y_max = min(1.0, max_acc + 0.05)
    else:
        # All models have identical accuracy - scale cleanly up to 100.0% (max 1.0)
        y_max = min(1.0, max(0.2, max_acc))
        y_min = 0.0

    span = y_max - y_min if y_max > y_min else 1.0

    for step in range(steps, -1, -1):
        threshold = y_min + (step / steps) * span
        row_str = f"{threshold * 100:5.1f}% │ "
        step_half_range = span / (steps * 2)
        for entry in timeline.entries:
            if abs(entry.accuracy - threshold) <= step_half_range:
                star = "* " if entry.model_name == timeline.best_model else ""
                warn = "! " if (entry.accuracy_improvement and entry.accuracy_improvement < 0) else ""
                row_str += f"{star}{warn}{entry.model_name}  "
            else:
                row_str += "       "
        lines.append(row_str)

    lines.append("       ├" + "─" * (len(timeline.entries) * 9))
    footer_models = "       │ " + "  ".join(f"{e.model_name:>6}" for e in timeline.entries)
    lines.append(footer_models)
    return "\n".join(lines)


def generate_analysis_report(timeline: ModelTimeline, store: Optional[Any] = None) -> str:
    """Generate detailed analytical trajectory & regression report."""
    output: List[str] = [
        "Timeline Analysis Report",
        "═" * 65,
        "",
    ]

    if not timeline.entries:
        output.append("No models available in timeline for analysis.")
        return "\n".join(output)

    # 1. Improvement Trajectory
    output.append("Improvement Trajectory:")
    first_acc = timeline.entries[0].accuracy
    best_acc = timeline.best_accuracy
    output.append(f"   Baseline ({timeline.entries[0].model_name}): {first_acc:.1%}")
    output.append(f"   Peak ({timeline.best_model}): {best_acc:.1%} ({best_acc - first_acc:+.1%} vs baseline)")
    output.append(f"   Final ({timeline.entries[-1].model_name}): {timeline.entries[-1].accuracy:.1%}")
    output.append("")

    regressions = [e for e in timeline.entries if e.accuracy_improvement and e.accuracy_improvement < 0]

    # 2. Root Cause Analysis
    output.append("Root Cause Analysis:")
    best_step = None
    max_gain = -1.0
    for entry in timeline.entries:
        if entry.accuracy_improvement and entry.accuracy_improvement > max_gain:
            max_gain = entry.accuracy_improvement
            best_step = entry

    if best_step:
        reason_note = best_step.reasoning or "Hyperparameter/code refinements"
        output.append(f"   Best improvement ({best_step.previous_model} → {best_step.model_name}): +{max_gain:.1%}")
        output.append(f"   Key factor: {reason_note}")
    elif len(timeline.entries) > 1 and not regressions:
        output.append(
            f"   Steady performance across {len(timeline.entries)} models "
            "- optimal accuracy maintained across architectures."
        )
    else:
        output.append("   Single model baseline or steady performance.")
    output.append("")

    # 3. Anomalies Detected
    output.append("Anomalies Detected:")
    unannotated = [e for e in timeline.entries if not e.reasoning or not e.reasoning.strip()]

    if regressions:
        for reg in regressions:
            output.append(
                f"   • {reg.model_name} regression: {reg.accuracy_improvement:+.1%} drop from {reg.previous_model}"
            )
    else:
        output.append("   • No accuracy regressions detected.")

    if unannotated:
        missing_names = ", ".join(e.model_name for e in unannotated)
        output.append(f"   • Missing reasoning annotations on: {missing_names}")
    output.append("")

    # 4. Recommendations
    recommendations: List[str] = []
    if timeline.best_model:
        recommendations.append(
            f"Candidate for production deployment: {timeline.best_model} ({timeline.best_accuracy:.1%})"
        )
    if regressions:
        failed_names = ", ".join(r.model_name for r in regressions)
        recommendations.append(f"Avoid re-attempting unsuccessful configurations from: {failed_names}")
    recommendations.append("Continue iterative experimentation on top of best verified architecture.")

    output.append("Recommendations:")
    for idx, rec in enumerate(recommendations, 1):
        output.append(f"   {idx}. {rec}")
    output.append("")

    improved_count = len([e for e in timeline.entries if e.accuracy_improvement and e.accuracy_improvement > 0])
    wasted_count = len(regressions)
    total = timeline.total_models
    if total > 1 and not regressions and timeline.best_accuracy >= 0.99:
        efficiency = 100.0
        eff_note = " (Optimal accuracy maintained across all versions)"
    else:
        efficiency = (improved_count / total * 100) if total > 0 else 0.0
        eff_note = ""

    output.append("Experiment Efficiency:")
    output.append(f"   Total models:           {total}")
    raw_pct = (improved_count / total * 100) if total > 0 else 0.0
    output.append(f"   Successful improvements: {improved_count}/{total} ({raw_pct:.0f}%)")
    output.append(f"   Regressed attempts:     {wasted_count}/{total}")
    output.append(f"   Efficiency score:       {efficiency:.0f}%{eff_note}")

    return "\n".join(output)


__all__ = [
    "format_timeline_table",
    "format_timeline_html",
    "format_timeline_json",
    "format_timeline_csv",
    "format_timeline_ascii",
    "generate_analysis_report",
]
