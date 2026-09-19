# VCM Model Evolution Timeline - Agent Implementation Prompt

**Copy and paste this prompt to your agent to begin implementation.**

---

## PROMPT FOR AGENT: Model Evolution Timeline Feature Implementation

```
You are implementing a new feature for VCM: "Model Evolution Timeline"

PROBLEM STATEMENT:
==================
Developers train multiple models but lose track of:
- Which model was trained first
- Why they moved to the next model
- What changed between consecutive attempts

SOLUTION:
=========
Implement complete model progression tracking with optional reasoning annotations.

NEW COMMANDS:
- vcm timeline (Show model progression)
- vcm timeline-reason <model> (Add why model was trained)
- vcm timeline analyze (Analyze progression patterns)

REFERENCE DOCUMENTS:
====================
Read these in order:
1. vcm_model_evolution_timeline_spec.md (Complete specification)
2. vcm_evolution_timeline_agent_guide.md (Day-by-day implementation)

SPECIFICATIONS TO FOLLOW:
=========================
Data Models (Section 2.3 of spec):
- EvolutionEntry: Position, model info, reasoning, changes
- ModelTimeline: List of entries with statistics
- ModelDifference: What changed between models

Database (Section 3 of spec):
- New table: model_evolution
- Tracks: position, reasoning, previous/next models
- Enables: chronological queries

CLI (Section 4 of spec):
- vcm timeline --session <name> --show-reasoning --format html
- vcm timeline-reason <model> "<reason>"
- vcm timeline analyze

IMPLEMENTATION PLAN:
====================
Follow vcm_evolution_timeline_agent_guide.md exactly:

DAY 1: Data Model & Database (4 hours)
 Create vcm/models/evolution.py with dataclasses
 Update vcm/db/database.py with model_evolution table
 Implement CRUD methods
 Run unit tests

DAY 2: Timeline Logic (4 hours)
 Create vcm/models/timeline.py with TimelineStore
 Implement get_model_timeline() query
 Implement regression detection
 Run unit tests

DAY 3: CLI & Formatters (4 hours)
 Create vcm/cli/timeline_commands.py
 Create vcm/utils/timeline_formatters.py
 Implement table, HTML, JSON, CSV formatters
 Run CLI tests

DAY 4: Testing & Validation (4 hours)
 Unit tests: test_evolution_timeline.py
 Integration tests: test_timeline_integration.py
 Advanced scenario: test_scenario_9_model_evolution.py
 Final validation

QUALITY REQUIREMENTS:
====================
 100% type hints (no Any)
 >90% test coverage
 0 linting violations
 0 type errors (mypy --strict)
 Clear error messages
 Comprehensive docstrings

KEY FEATURES TO IMPLEMENT:
==========================
1. Timeline Detection:
 - Auto-detect models by training timestamp
 - Assign sequential positions
 - Link previous/next models

2. Reasoning Tracking:
 - Store why each model was trained
 - Optional annotations (user can add later)
 - Timestamp and user tracking

3. Timeline Queries:
 - Get progression for session/date range
 - Filter by accuracy range
 - Detect regressions automatically

4. Visualization:
 - ASCII table with accuracy changes
 - HTML report with charts
 - JSON export for automation
 - CSV for spreadsheet analysis

TESTING STRATEGY:
=================
1. Write tests FIRST (TDD)
2. Implement code to pass tests
3. Run full test suite after each day
4. Validate performance (<100ms queries)
5. Test real iris scenario end-to-end

VALIDATION COMMANDS:
====================
After each day:
 pytest vcm/tests/unit/test_evolution*.py -v --cov

End of Day 4:
 pytest vcm/tests/*/test_*timeline*.py -v --cov=vcm
 mypy vcm/models/evolution.py vcm/models/timeline.py --strict
 flake8 vcm/cli/timeline_commands.py --max-line-length=120
 pytest vcm/tests/advanced/test_scenario_9*.py -v

DELIVERABLES:
==============
 vcm/models/evolution.py (dataclasses)
 vcm/models/timeline.py (timeline store & queries)
 vcm/cli/timeline_commands.py (CLI commands)
 vcm/utils/timeline_formatters.py (output formatting)
 Updated vcm/db/database.py (schema + methods)
 vcm/tests/unit/test_evolution_timeline.py (15+ unit tests)
 vcm/tests/integration/test_timeline_integration.py (5+ integration tests)
 vcm/tests/advanced/test_scenario_9_model_evolution.py (real workflow test)

EXPECTED OUTCOME:
=================
Users can now:
1. See model progression: vcm timeline
2. Understand why models were created: vcm timeline --show-reasoning
3. Analyze patterns: vcm timeline analyze
4. Export reports: vcm timeline --format html --output timeline.html
5. Add reasoning retroactively: vcm timeline-reason v2 "Testing approach"

SUCCESS CRITERIA:
=================
[x] All 25+ tests passing
[x] Coverage >90% for timeline module
[x] Type checking: 0 errors
[x] Linting: 0 violations
[x] CLI commands working with real data
[x] Advanced scenario (iris) passing
[x] Performance: timeline queries <100ms
[x] No TODOs in code

DO:
===
 Follow vcm_evolution_timeline_agent_guide.md step by step
 Write tests FIRST before implementation
 Read spec sections at beginning of each day
 Report progress after each component
 Validate with pytest after each day
 Reference spec for any ambiguity

DON'T:
======
 Skip testing (TDD first)
 Add features beyond spec
 Leave TODOs in code
 Skip type hints
 Ignore error cases
 Rush - follow the guide carefully

STARTING NOW:
=============
1. Read vcm_model_evolution_timeline_spec.md (sections 2, 3, 4)
2. Read vcm_evolution_timeline_agent_guide.md (full guide)
3. Start with DAY 1: Data Model & Database
4. First task: Create vcm/models/evolution.py
5. Write all dataclasses (frozen, immutable)
6. Then update database schema
7. Run unit tests to validate

Reference the spec constantly - it has all details you need.
Questions? Check the spec first - answer is probably there.

Ready? Start now with Day 1! 
```

---

## OPTIONAL: Shortened Prompt (If context is tight)

If you need a minimal prompt:

```
Feature: Model Evolution Timeline (Phase 2.1)
Objective: Track model progression with optional reasoning

Reference:
- vcm_model_evolution_timeline_spec.md (complete spec)
- vcm_evolution_timeline_agent_guide.md (day-by-day guide)

Do this:
1. Read both documents
2. Follow the guide day by day (4 days)
3. TDD: Write tests first, then code
4. Validate: Run tests after each day

Expected output:
- 8 new Python files
- 25+ tests
- >90% coverage
- vcm timeline command working

Ready? Start with Day 1 in the guide.
```

---

## CHECKLIST: BEFORE GIVING TO AGENT

Before pasting the prompt, verify:

- [ ] vcm_model_evolution_timeline_spec.md uploaded
- [ ] vcm_evolution_timeline_agent_guide.md uploaded
- [ ] Agent can read both documents
- [ ] Agent understands TDD approach
- [ ] Agent knows to follow guide exactly

---

## COPY & PASTE THIS PROMPT TO AGENT

The prompt above is ready to copy directly. Just paste the "PROMPT FOR AGENT" section (starting from "You are implementing...") into your agent's context.

**Expected Duration:** 3-4 days of implementation
**Result:** Complete model evolution tracking feature ready for production

---

**Ready to implement? Give this prompt to your agent!** 
