# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-03 (Production Release)

### Added
- **Core Model DNA Engine (Phase 1)**
  - Automated tracking of Git commit SHA, git diff, author, and branch.
  - Integration with DVC for dataset version tracking and SHA-256 data file hashing.
  - Hyperparameter tracking and evaluation metrics loading (JSON/YAML).
  - JSON sidecar metadata generation and indexed SQLite database (`vcm.db`).
  - Core CLI commands: `init`, `train`, `models`, `info`, `compare`, `lineage`, `export`, and `status`.

- **Session Tracking & Developer Reasoning (Phase 2)**
  - Iterative model development sessions grouping multiple training runs.
  - Interactive and programmatic developer annotations (`vcm session annotate`).
  - Multi-process annotation persistence and relational SQLite rehydration (`session_annotations`).
  - Live activity logging across independent CLI commands (`vcm session logs`, `vcm session info`).
  - Terminal output logging with automated secret and credential masking (API keys, tokens).
  - Multi-session comparison and analysis (`vcm session compare`).
  - Session lifecycle CLI commands: `start`, `end`, `list`, `info`, `logs`, `annotate`, `models`, `compare`, `explain-improvement`, `create-retrospective`, `export`.

- **Model Evolution Timeline & Progression (Phase 3)**
  - Ordered chronological progression tracking across model iterations.
  - Automated regression detection for degradation in key evaluation metrics.
  - Multi-format timeline visualization: Rich ANSI terminal tables, standalone interactive HTML, machine-readable JSON, and CSV export.
  - Timeline CLI commands: `timeline show`, `timeline reason`, `timeline-reason`, `timeline analyze`.

- **MLflow & MLOps Integrations**
  - Dual-mode MLflow client supporting native Python SDK and REST HTTP API fallback.
  - Parameter, metric, and Model DNA sidecar tag synchronization (`vcm mlflow sync`, `vcm mlflow sync --all`).
  - Workspace MLflow tracking configuration toggling (`vcm mlflow enable`, `vcm mlflow disable`, `vcm mlflow status`).
  - Deterministic model reproducibility validation utilities (`vcm reproduce`).
  - Production deployment status tracking and comprehensive audit trails (`vcm deploy`, `vcm audit`).
  - Self-healing SQLite database integrity check and automatic repair command (`vcm repair`).

- **Automated Validation & Tooling**
  - Exhaustive 66-command automated runner (`run_all_commands.py`) with 100% pass rate.
  - 40 test files with 168 passing tests (100% pass rate).
  - Over 91% test coverage across core and CLI modules.
  - Strict type checking compliance (`mypy vcm/` with zero errors across 76 files).
  - Flake8 clean codebase (zero PEP8 violations).
  - 8 end-to-end real ML scenarios validating Iris model lifecycle.
