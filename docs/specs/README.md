# VCM Specification & Historical Documentation Archive

This directory organizes all architectural specifications, test strategies, agent guides, and execution prompts across the evolution of the VCM platform.

---

## Directory Index

```
docs/specs/
├── phase1/ # Phase 1: Core MVP Architecture & Model DNA Capture
├── phase2/ # Phase 2: Session Tracking, Terminal Capture & Advanced Scenarios
└── phase3/ # Phase 3: Model Evolution Timeline, Reasoning & Regression Detection
```

---

## Phase 1: Core MVP Specifications (`phase1/`)

Foundational specifications for single-run tracking, Model DNA capture, and the dual-layer storage architecture (SQLite + JSON sidecars).

- [vcm_mvp_specification_doc1.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase1/vcm_mvp_specification_doc1.md) — Scope, technology stack, database schemas, and data flow diagrams.
- [vcm_test_cases.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase1/vcm_test_cases.md) — Initial 60+ unit, integration, and CLI test cases.
- [vcm_agent_procedure.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase1/vcm_agent_procedure.md) — Build procedure and implementation checkpoints.

---

## Phase 2: Session Tracking & Advanced Scenarios (`phase2/`)

Specifications introducing development sessions, terminal stdout/stderr interception with secret masking, side-by-side session comparisons, and real-world ML workflows.

- [vcm_session_tracking_spec2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/vcm_session_tracking_spec2.md) — Complete session lifecycle, schema, models, and comparisons.
- [vcm_phase2_agent_guide2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/vcm_phase2_agent_guide2.md) — Implementation guide and instructions for engineering agents.
- [vcm_advanced_testing2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/vcm_advanced_testing2.md) — Scenarios 1–8: Single training, multiple models, data versions, code diffs, lineage, troubleshooting, reproducibility, audit trails.
- [vcm_cli_documentation2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/vcm_cli_documentation2.md) — CLI commands for sessions, analysis, reproduction, deployment, and auditing.
- [vcm_testing_strategy2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/vcm_testing_strategy2.md) — Test pyramid, coverage goals, and performance benchmarks.
- [EXECUTIVE_SUMMARY2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/EXECUTIVE_SUMMARY2.md) — Phase 2 executive overview and architecture comparison.
- [DOCUMENTATION_INDEX2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/DOCUMENTATION_INDEX2.md) — Index of all Phase 2 documents.
- [QUICK_REFERENCE2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/QUICK_REFERENCE2.md) — CLI cheat sheet and Python API snippets.
- [AGENT_PROMPTS2.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase2/AGENT_PROMPTS2.md) — Operational prompts and task prompts for Phase 2.

---

## Phase 3: Model Evolution Timeline & Reasoning (`phase3/`)

Specifications introducing progression tracking across model iterations, developer rationale annotations, automated regression detection, gap analysis, and visual timeline generators.

- [vcm_model_evolution_timeline_spec3.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase3/vcm_model_evolution_timeline_spec3.md) — Technical specification for model progression, `model_evolution` schema, regression detection, and visual formatters.
- [vcm_evolution_timeline_agent_guide3.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase3/vcm_evolution_timeline_agent_guide3.md) — Engineering guide, quality gates, and implementation phases.
- [AGENT_PROMPT_EVOLUTION_TIMELINE3.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase3/AGENT_PROMPT_EVOLUTION_TIMELINE3.md) — Prompts and execution workflows for Phase 3.
- [MODEL_EVOLUTION_TIMELINE_SUMMARY3.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase3/MODEL_EVOLUTION_TIMELINE_SUMMARY3.md) — Executive summary of timeline capabilities.
- [FINAL_DELIVERY_SUMMARY3.md](file:///home/kishorveeraragavan/Desktop/VersionControl/docs/specs/phase3/FINAL_DELIVERY_SUMMARY3.md) — Final delivery verification, metrics scorecard, and sign-off criteria.
