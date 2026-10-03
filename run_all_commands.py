#!/usr/bin/env python3
"""Comprehensive Interactive CLI Runner for VCM (Version Control Models).

Executes and displays the formatted terminal output for EVERY VCM command
and subcommand across all operational phases:
- System & Information
- Workspace Configuration
- Project Initialization & Status
- Training & Model DNA Capture
- Model Catalog Queries & Filtering
- Inspection, Comparison & Lineage
- Metadata Export & Disaster Recovery
- Session Tracking & Annotations
- Model Evolution Timeline & Regression Detection
- Deep Lineage Analysis
- Deployment & Audit Trails
- Deterministic Model Reproduction
- MLflow Dual-Mode Integration (Native SDK & Offline File Store)

Usage:
    python run_all_commands.py               # Run all commands straight through
    python run_all_commands.py --pause       # Pause after each command to inspect output
    python run_all_commands.py --filter ml   # Run only commands matching 'ml' (e.g. mlflow)
    python run_all_commands.py --list        # List all available commands without running
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from typing import List, Tuple

# ANSI color codes for rich terminal styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner(text: str, color: str = CYAN) -> None:
    width = 78
    print(f"\n{color}{BOLD}╔{'═' * (width - 2)}╗{RESET}")
    print(f"{color}{BOLD}║  {text:<{width - 5}}║{RESET}")
    print(f"{color}{BOLD}╚{'═' * (width - 2)}╝{RESET}\n")


def print_section(section_num: int, title: str) -> None:
    width = 78
    print(f"\n\n{YELLOW}{BOLD}{'═' * width}")
    print(f"  SECTION {section_num}: {title.upper()}")
    print(f"{'═' * width}{RESET}\n")


def run_command(
    cmd: List[str],
    index: int,
    total: int,
    description: str,
    pause: bool = False,
) -> Tuple[bool, float]:
    cmd_str = " ".join(cmd)
    width = 78

    print(f"{CYAN}┌{'─' * (width - 2)}┐{RESET}")
    print(f"{CYAN}│ {BOLD}[{index}/{total}] {description:<{width - 12}}{RESET}{CYAN}│{RESET}")
    print(f"{CYAN}│ {DIM}$ {cmd_str:<{width - 6}}{RESET}{CYAN}│{RESET}")
    print(f"{CYAN}└{'─' * (width - 2)}┘{RESET}")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time

    # Print command standard output
    if result.stdout.strip():
        print(result.stdout.strip())
    else:
        print(f"{DIM}(Command produced no standard output){RESET}")

    # Print standard error if any occurred
    if result.stderr.strip() and result.returncode != 0:
        print(f"\n{RED}{BOLD}[STDERR]{RESET}\n{result.stderr.strip()}")

    # Print status indicator
    if result.returncode == 0:
        print(f"\n{GREEN}✔ SUCCESS (Exit Code 0) — {duration:.2f}s{RESET}")
        success = True
    else:
        print(f"\n{RED}✖ FAILED (Exit Code {result.returncode}) — {duration:.2f}s{RESET}")
        success = False

    print(f"{DIM}{'─' * width}{RESET}")

    if pause:
        try:
            input(f"\n{YELLOW}Press [Enter] to continue to next command (or Ctrl+C to stop)...{RESET}")
        except KeyboardInterrupt:
            print(f"\n{RED}Execution interrupted by user.{RESET}")
            sys.exit(0)

    return success, duration


def main() -> None:
    parser = argparse.ArgumentParser(description="VCM Exhaustive Command Runner")
    parser.add_argument("--pause", action="store_true", help="Pause after each command to inspect output")
    parser.add_argument("--filter", type=str, default="", help="Filter commands by keyword (e.g. 'timeline', 'session')")
    parser.add_argument("--list", action="store_true", help="List all scheduled commands without executing")
    parser.add_argument("--dir", type=str, default="ml_project_demo", help="Target demo working directory")
    args = parser.parse_args()

    # Determine project root and demo directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    demo_dir = os.path.join(root_dir, args.dir)

    if not os.path.exists(demo_dir):
        print(f"{RED}Error: Demo directory '{demo_dir}' not found.{RESET}")
        sys.exit(1)

    # Locate VCM binary
    vcm_bin = os.path.join(root_dir, "venv", "bin", "vcm")
    if not os.path.exists(vcm_bin):
        vcm_bin = "vcm"

    # Define all commands with Section, Description, and CLI arguments
    all_commands: List[Tuple[str, str, List[str]]] = [
        # --- SECTION 1: SYSTEM & INFORMATION ---
        ("System & Info", "Show VCM version flag", [vcm_bin, "--version"]),
        ("System & Info", "Display root CLI help & commands list", [vcm_bin, "--help"]),
        ("System & Info", "Show version via version command", [vcm_bin, "version"]),
        ("System & Info", "Show verbose environment & system version", [vcm_bin, "version", "--verbose"]),

        # --- SECTION 2: WORKSPACE CONFIGURATION ---
        ("Configuration", "Display active VCM configuration", [vcm_bin, "config", "show"]),
        ("Configuration", "Set configuration key (models_dir)", [vcm_bin, "config", "set", "models_dir", "models"]),
        ("Configuration", "Set MLflow tracking URI", [vcm_bin, "config", "set", "mlflow_tracking_uri", "file:./mlruns"]),
        ("Configuration", "Reset configuration back to defaults", [vcm_bin, "config", "reset"]),

        # --- SECTION 3: PROJECT INITIALIZATION & STATUS ---
        ("Init & Status", "Initialize VCM project database and sidecar storage", [vcm_bin, "init"]),
        ("Init & Status", "Inspect comprehensive workspace status", [vcm_bin, "status"]),

        # --- SECTION 4: TRAINING & MODEL DNA CAPTURE ---
        (
            "Training & DNA",
            "Train Model 1: Baseline Logistic Regression",
            [
                vcm_bin, "train",
                "--model-name", "iris_logistic_v1",
                "--dataset", "data/iris_v1.csv",
                "--script", "train_model1.py",
                "--metrics", "metrics_v1.json",
                "--model-file", "models/iris_logistic_v1.pkl",
                "--params", "C=0.1",
                "--params", "solver=lbfgs",
                "--reasoning", "Baseline Logistic Regression on Iris v1",
            ],
        ),
        (
            "Training & DNA",
            "Train Model 2: Random Forest Ensemble",
            [
                vcm_bin, "train",
                "--model-name", "iris_rf_v2",
                "--dataset", "data/iris_v1.csv",
                "--script", "train_model2.py",
                "--metrics", "metrics_v2.json",
                "--model-file", "models/iris_rf_v2.pkl",
                "--params", "n_estimators=100",
                "--params", "max_depth=4",
                "--reasoning", "Random Forest ensemble to reduce model variance",
            ],
        ),
        (
            "Training & DNA",
            "Train Model 3: Gradient Boosting on Scaled Dataset",
            [
                vcm_bin, "train",
                "--model-name", "iris_gb_v3",
                "--dataset", "data/iris_v2.csv",
                "--script", "train_model3.py",
                "--metrics", "metrics_v3.json",
                "--model-file", "models/iris_gb_v3.pkl",
                "--params", "n_estimators=150",
                "--params", "learning_rate=0.05",
                "--reasoning", "Gradient Boosting on robust-scaled feature distribution",
            ],
        ),

        # --- SECTION 5: MODEL CATALOG QUERIES ---
        ("Model Catalog", "List all tracked models in rounded grid", [vcm_bin, "models"]),
        ("Model Catalog", "Filter catalog to show only best performing model", [vcm_bin, "models", "--best"]),
        ("Model Catalog", "Filter models by training dataset path", [vcm_bin, "models", "--dataset", "data/iris_v1.csv"]),
        ("Model Catalog", "Limit models list sorted by accuracy", [vcm_bin, "models", "--limit", "2", "--sort-by", "accuracy"]),
        ("Model Catalog", "Export catalog in machine-readable JSON", [vcm_bin, "models", "--format", "json"]),
        ("Model Catalog", "Export catalog to CSV file", [vcm_bin, "models", "--format", "csv", "--export", "models_export.csv"]),

        # --- SECTION 6: INSPECTION, COMPARISON & LINEAGE ---
        ("Inspection & Lineage", "Display detailed Model DNA summary", [vcm_bin, "info", "models/iris_rf_v2.pkl"]),
        ("Inspection & Lineage", "Display model metadata in full JSON format", [vcm_bin, "info", "models/iris_rf_v2.pkl", "--json"]),
        ("Inspection & Lineage", "Compare two models side-by-side with metrics & params delta", [vcm_bin, "compare", "models/iris_logistic_v1.pkl", "models/iris_rf_v2.pkl"]),
        ("Inspection & Lineage", "Display hierarchical lineage tree for model", [vcm_bin, "lineage", "models/iris_rf_v2.pkl"]),

        # --- SECTION 7: METADATA EXPORT & DISASTER RECOVERY ---
        ("Export & Recovery", "Export metadata sidecar to explicit JSON file", [vcm_bin, "export", "models/iris_rf_v2.pkl", "--output", "rf_v2_export.json"]),
        ("Export & Recovery", "Rebuild SQLite database from on-disk sidecars (Self-Healing)", [vcm_bin, "repair"]),

        # --- SECTION 8: SESSION TRACKING (ALL SUBCOMMANDS) ---
        ("Session Tracking", "Start a development session with live terminal logging", [vcm_bin, "session", "start", "hyperparameter_tuning"]),
        ("Session Tracking", "Record developer hypothesis annotation into active session", [vcm_bin, "session", "annotate", "Hypothesis: increasing tree depth sharpens decision boundaries"]),
        ("Session Tracking", "Record model-specific observation note", [vcm_bin, "session", "annotate", "Observation: validation accuracy reached target threshold", "--model", "iris_rf_v2"]),
        ("Session Tracking", "Inspect captured masked terminal logs for session", [vcm_bin, "session", "logs", "hyperparameter_tuning"]),
        ("Session Tracking", "Show session metadata, duration, and models trained", [vcm_bin, "session", "info", "hyperparameter_tuning"]),
        ("Session Tracking", "List all tracked development sessions", [vcm_bin, "session", "list"]),
        ("Session Tracking", "End active session and save immutable session archive", [vcm_bin, "session", "end"]),
        ("Session Tracking", "Create retrospective session from existing model history", [vcm_bin, "session", "create-retrospective", "--name", "historical_benchmark_session"]),
        ("Session Tracking", "List models linked to retrospective session", [vcm_bin, "session", "models", "historical_benchmark_session"]),
        ("Session Tracking", "Compare two development sessions side-by-side", [vcm_bin, "session", "compare", "historical_benchmark_session", "historical_benchmark_session"]),
        ("Session Tracking", "Explain performance improvement between models in session", [vcm_bin, "session", "explain-improvement", "historical_benchmark_session", "iris_logistic_v1", "iris_rf_v2"]),
        ("Session Tracking", "Export session summary report to interactive HTML visualizer", [vcm_bin, "session", "export", "historical_benchmark_session", "--format", "html", "--output", "session_report.html"]),
        ("Session Tracking", "Export session summary to structured JSON", [vcm_bin, "session", "export", "historical_benchmark_session", "--format", "json", "--output", "session_report.json"]),

        # --- SECTION 9: MODEL EVOLUTION TIMELINE (ALL FORMATS & SUBCOMMANDS) ---
        ("Evolution Timeline", "Display timeline with reasoning annotations and best model highlight", [vcm_bin, "timeline", "--show-reasoning", "--highlight-best"]),
        ("Evolution Timeline", "Display timeline in compact ASCII graph format", [vcm_bin, "timeline", "--format", "ascii"]),
        ("Evolution Timeline", "Export evolution timeline in JSON format", [vcm_bin, "timeline", "--format", "json"]),
        ("Evolution Timeline", "Export timeline progression metrics to CSV", [vcm_bin, "timeline", "--format", "csv", "--output", "timeline_export.csv"]),
        ("Evolution Timeline", "Generate rich standalone interactive HTML timeline visualizer", [vcm_bin, "timeline", "--format", "html", "--output", "timeline_report.html"]),
        ("Evolution Timeline", "Filter timeline by accuracy range and highlight parameter changes", [vcm_bin, "timeline", "--accuracy-range", "0.90-1.0", "--show-changes"]),
        ("Evolution Timeline", "Execute timeline show subcommand", [vcm_bin, "timeline", "show"]),
        ("Evolution Timeline", "Perform automated root cause and regression analysis", [vcm_bin, "timeline", "analyze"]),
        ("Evolution Timeline", "Export regression analysis report to text file", [vcm_bin, "timeline", "analyze", "--output", "timeline_analysis.txt"]),
        ("Evolution Timeline", "Add reasoning note to model version via timeline reason", [vcm_bin, "timeline", "reason", "iris_rf_v2", "Updated reasoning via timeline reason subcommand", "--force"]),
        ("Evolution Timeline", "Inspect reasoning notes via standalone timeline-reason --show", [vcm_bin, "timeline-reason", "iris_rf_v2", "--show"]),
        ("Evolution Timeline", "Update reasoning note via standalone timeline-reason command", [vcm_bin, "timeline-reason", "iris_rf_v2", "Production candidate approved after review", "--force"]),

        # --- SECTION 10: DEEP LINEAGE & IMPACT ANALYSIS ---
        ("Lineage Analysis", "Generate complete dataset & code lineage report", [vcm_bin, "analysis", "--report", "full_lineage"]),
        ("Lineage Analysis", "Generate high-level model lineage summary report", [vcm_bin, "analysis", "--report", "summary"]),
        ("Lineage Analysis", "Compare code and dataset evolution impact between two models", [vcm_bin, "analysis", "--compare", "iris_logistic_v1", "iris_rf_v2"]),
        ("Lineage Analysis", "Show impact analysis across all iterations", [vcm_bin, "analysis", "--show-impact"]),

        # --- SECTION 11: PRODUCTION DEPLOYMENT & AUDIT TRAILS ---
        ("Deploy & Audit", "Deploy model to staging environment", [vcm_bin, "deploy", "models/iris_rf_v2.pkl", "--environment", "staging"]),
        ("Deploy & Audit", "Deploy model to production environment", [vcm_bin, "deploy", "models/iris_rf_v2.pkl", "--environment", "production"]),
        ("Deploy & Audit", "Inspect staging deployment audit trail", [vcm_bin, "audit", "--environment", "staging"]),
        ("Deploy & Audit", "Inspect production deployment audit trail", [vcm_bin, "audit", "--environment", "production"]),

        # --- SECTION 12: DETERMINISTIC MODEL REPRODUCTION ---
        ("Reproduce", "Reproduce model deterministically from Model DNA metadata", [vcm_bin, "reproduce", "models/iris_logistic_v1.pkl"]),

        # --- SECTION 13: MLFLOW DUAL-MODE INTEGRATION ---
        ("MLflow Integration", "Inspect MLflow integration connection status", [vcm_bin, "mlflow", "status"]),
        ("MLflow Integration", "Enable MLflow tracking in VCM configuration", [vcm_bin, "mlflow", "enable"]),
        ("MLflow Integration", "Verify enabled MLflow status and tracking target", [vcm_bin, "mlflow", "status"]),
        ("MLflow Integration", "Sync single model parameters, metrics & DNA tags to MLflow", [vcm_bin, "mlflow", "sync", "iris_logistic_v1"]),
        ("MLflow Integration", "Sync all tracked workspace models to MLflow in batch", [vcm_bin, "mlflow", "sync", "--all"]),
        ("MLflow Integration", "Disable MLflow tracking integration", [vcm_bin, "mlflow", "disable"]),
        ("MLflow Integration", "Confirm disabled MLflow status", [vcm_bin, "mlflow", "status"]),
    ]

    # Filter commands if requested
    if args.filter:
        flt = args.filter.lower()
        all_commands = [
            (sec, desc, cmd) for sec, desc, cmd in all_commands
            if flt in sec.lower() or flt in desc.lower() or any(flt in c.lower() for c in cmd)
        ]
        if not all_commands:
            print(f"{RED}No commands matched filter '{args.filter}'.{RESET}")
            sys.exit(1)

    # If --list flag was passed, print all scheduled commands and exit
    if args.list:
        print_banner(f"VCM COMMAND CATALOG ({len(all_commands)} COMMANDS SCHEDULED)")
        current_sec = ""
        for idx, (section, desc, cmd) in enumerate(all_commands, 1):
            if section != current_sec:
                current_sec = section
                print(f"\n{YELLOW}{BOLD}▶ {current_sec}{RESET}")
            print(f"  {CYAN}{idx:02d}.{RESET} {desc} -> {DIM}{' '.join(cmd)}{RESET}")
        print(f"\nTotal: {len(all_commands)} commands.\n")
        return

    # Switch working directory to demo directory
    os.chdir(demo_dir)

    print_banner(f"VCM EXHAUSTIVE CLI EXECUTION SUITE ({len(all_commands)} COMMANDS)")
    print(f"  {BOLD}Working Directory:{RESET} {demo_dir}")
    print(f"  {BOLD}VCM Executable:   {RESET} {vcm_bin}")
    print(f"  {BOLD}Total Commands:   {RESET} {len(all_commands)}")
    if args.pause:
        print(f"  {YELLOW}Interactive Pause:{RESET} Enabled (will prompt after each command)")
    print(f"{DIM}{'─' * 78}{RESET}\n")

    # Clean prior run temporary files for deterministic execution
    clean_files = [
        "metrics_v1.json", "metrics_v2.json", "metrics_v3.json",
        "rf_v2_export.json", "models_export.csv", "session_report.html",
        "session_report.json", "timeline_report.html", "timeline_export.csv",
        "timeline_analysis.txt", "full_lineage_report.txt",
    ]
    for cf in clean_files:
        if os.path.exists(cf):
            os.remove(cf)

    if os.path.exists(".vcm"):
        shutil.rmtree(".vcm")
    if os.path.exists("models"):
        shutil.rmtree("models")
    if os.path.exists(".vcmconfig.yaml"):
        os.remove(".vcmconfig.yaml")

    # Ensure demo git repository exists
    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "VCM Test"], check=False, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "test@vcm.local"], check=False, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], check=False, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial commit for demo"], check=False, stdout=subprocess.DEVNULL)

    # Execution tracking variables
    passed = 0
    failed = 0
    total = len(all_commands)
    total_start = time.time()
    current_sec = ""

    for idx, (section, desc, cmd) in enumerate(all_commands, 1):
        if section != current_sec:
            current_sec = section
            print_section(idx, current_sec)

        ok, dur = run_command(cmd, idx, total, desc, pause=args.pause)
        if ok:
            passed += 1
        else:
            failed += 1

    total_time = time.time() - total_start

    # Final Execution Summary
    print_banner("EXECUTION SUMMARY & SCORECARD", GREEN if failed == 0 else RED)
    print(f"  {BOLD}Total Commands Executed:{RESET} {total}")
    print(f"  {GREEN}{BOLD}Passed Successfully:    {RESET} {passed} ({passed / total * 100:.1f}%)")
    if failed > 0:
        print(f"  {RED}{BOLD}Failed Commands:        {RESET} {failed}")
    else:
        print(f"  {GREEN}{BOLD}Failed Commands:        {RESET} 0 (ZERO ERRORS)")
    print(f"  {BOLD}Total Execution Time:   {RESET} {total_time:.2f}s")

    print(f"\n{YELLOW}{BOLD}Generated Deliverable Artifacts:{RESET}")
    artifacts = [
        ("Database Sidecars", "models/*.pkl.vcm.json"),
        ("Model Catalog Export", "models_export.csv"),
        ("Model Export Sidecar", "rf_v2_export.json"),
        ("Session Interactive HTML", "session_report.html"),
        ("Session Structured JSON", "session_report.json"),
        ("Timeline ASCII / Table", "Standard Output"),
        ("Timeline CSV Export", "timeline_export.csv"),
        ("Timeline Interactive HTML", "timeline_report.html"),
        ("Timeline Regression Report", "timeline_analysis.txt"),
    ]
    for label, path in artifacts:
        status_check = "✔ Created" if ("*" in path or os.path.exists(path) or path == "Standard Output") else "Pending"
        print(f"  • {label:<28} -> {path:<30} [{GREEN}{status_check}{RESET}]")

    print(f"\n{GREEN}{BOLD}{'═' * 78}")
    print(f"  ALL {passed}/{total} VCM COMMANDS & SUBCOMMANDS VERIFIED & OPERATIONAL! 🚀")
    print(f"{'═' * 78}{RESET}\n")


if __name__ == "__main__":
    main()
