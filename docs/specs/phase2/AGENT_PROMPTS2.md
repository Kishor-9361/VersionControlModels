# VCM Agent Prompts - Ready to Copy & Paste

**Use These Prompts:** Copy exactly, modify only if needed 
**Best Practice:** Use one prompt per context window 
**Quality:** Production-grade specifications in all documents 

---

## MASTER PROMPT (Start Here)

**Use This First:** Gets agent oriented and ready

---

### PROMPT 1: Initial Orientation & Understanding

```
You are building VCM (Version Control for ML Models), a production-quality 
platform for tracking ML model training, versioning, and reproducibility.

CONTEXT:
========
Phase 1 (MVP) has been completed with 60+ unit tests and 92+ total tests passing.
Your task: Implement Phase 2 and advanced testing (Weeks 5-6).

DOCUMENTS PROVIDED:
===================
You have 8 specification documents with complete requirements:

1. EXECUTIVE_SUMMARY.md - Overview of what's been delivered
2. QUICK_REFERENCE.md - One-page summary
3. DOCUMENTATION_INDEX.md - Master index of all documents
4. vcm_session_tracking_spec.md - NEW FEATURE: Session tracking system
5. vcm_advanced_testing.md - Real ML project scenarios (8 workflows)
6. vcm_cli_documentation.md - Complete CLI reference for all commands
7. vcm_testing_strategy.md - Comprehensive test plan (140+ tests)
8. vcm_phase2_agent_guide.md - Day-by-day implementation guide

WHAT YOU'RE BUILDING:
====================
1. Session Tracking System
 - Auto-capture terminal output (with secret masking)
 - Group models by development session
 - Store user annotations
 - Session comparison & analysis
 
2. Advanced Testing
 - 8 real ML project scenarios (iris classification)
 - Performance validation
 - Reproducibility testing
 
3. Complete CLI Enhancement
 - 8 new session commands
 - Full integration with existing commands

YOUR TASK (Priority Order):
===========================
1. Read vcm_phase2_agent_guide.md (understand the 2-week plan)
2. Read vcm_session_tracking_spec.md (understand what to build)
3. Follow vcm_phase2_agent_guide.md EXACTLY - day by day
4. Use vcm_testing_strategy.md for test execution schedule
5. Reference vcm_advanced_testing.md for scenario templates
6. Reference vcm_cli_documentation.md for command specifications

KEY PRINCIPLES:
===============
 TDD First: Write tests BEFORE implementation
 Production Quality: No TODOs, all error cases handled
 Type Safety: Full type hints on all functions
 Complete Testing: Follow test cases exactly
 Clear Communication: Explain what you're implementing and why
 Quality Gates: Meet all validation criteria before moving on

STARTING NOW:
=============
Begin with Phase 2, Week 1, Day 1-2: Session Model & Database

Your first task:
1. Read vcm_session_tracking_spec.md section "Session Structure"
2. Read vcm_phase2_agent_guide.md section "PHASE 2: WEEK 1 (Session Tracking Core)"
3. Read vcm_test_cases.md section "PART 1: UNIT TESTS" (for test patterns)
4. Create files:
 - vcm/models/session.py (with SessionTracker class)
 - vcm/tests/unit/test_session.py (with 12 unit tests)

5. Start by writing all tests FIRST
6. Then implement code to pass tests
7. Run: pytest tests/unit/test_session.py -v --cov
8. Verify: 12/12 tests passing, >95% coverage

QUALITY STANDARDS:
==================
Every module must have:
- 100% type hints
- Comprehensive docstrings
- No commented-out code
- All error cases handled
- >90% test coverage
- Clear variable/function names

COMMUNICATION:
==============
Before each major section:
1. State what you're implementing
2. Reference the relevant spec section
3. List files you're creating
4. Describe your approach
5. Run tests and report results

After each module completion:
1. Report test results
2. Show code coverage
3. List any challenges
4. Confirm ready for next step

VALIDATION CHECKPOINTS:
=======================
After each day:
 pytest tests/unit/test_session.py -v --cov=vcm.models.session

After each week:
 pytest tests/unit/ -v --cov=vcm --cov-report=term-missing

After Phase 2:
 pytest tests/ -v --cov=vcm --cov-report=html
 mypy vcm/ --strict
 flake8 vcm/ --max-line-length=100
 # Expected: All passing, >85% coverage

DO NOT:
=======
 Skip testing (TDD first)
 Add features beyond spec
 Skip error handling
 Ignore type hints
 Leave TODOs in code
 Rush - follow the guide

DO:
===
 Follow vcm_phase2_agent_guide.md exactly
 Write tests first, then code
 Reference specifications
 Report progress clearly
 Validate at checkpoints
 Ask clarifying questions if spec is ambiguous

Ready? Start with: vcm_phase2_agent_guide.md section "PHASE 2: WEEK 1"
```

---

## PHASE-SPECIFIC PROMPTS

### PROMPT 2: Week 1 Session Tracking Implementation

```
PHASE 2, WEEK 1: Session Tracking Core Implementation

OBJECTIVE:
Build SessionTracker class and database layer for session tracking.

REFERENCE DOCUMENTS:
1. vcm_phase2_agent_guide.md - Days 1-7 of this week
2. vcm_session_tracking_spec.md - Complete feature specification
3. vcm_testing_strategy.md - Test execution plan

DAY 1-2 TASK: Session Model & Database
================================
Files to create:
- vcm/models/session.py (Session dataclasses)
- vcm/db/database.py (UPDATE - add session tables)
- vcm/tests/unit/test_session.py (Unit tests)

Implementation checklist:
- SessionTracker class with lifecycle (start, end)
- Nested dataclasses: SessionInfo, Annotation
- Database tables: sessions, session_annotations, session_models
- All methods from spec
- 12 unit tests (UT-1.1 to UT-1.12 from test spec)

Steps:
1. Read vcm_session_tracking_spec.md "Session Structure"
2. Write all 12 tests in test_session.py FIRST
3. Implement SessionTracker class to pass tests
4. Update database.py with session tables
5. Run: pytest tests/unit/test_session.py -v --cov=vcm.models.session
6. Verify: 12/12 passing, >95% coverage

Expected output:
- vcm/models/session.py (200+ lines)
- vcm/tests/unit/test_session.py (300+ lines)
- Updated vcm/db/database.py with session tables

DAY 3 TASK: Terminal Logging with Privacy
====================================
Files to create:
- vcm/utils/terminal_logger.py (Terminal capture & masking)
- vcm/tests/unit/test_terminal.py (Terminal logging tests)

Implementation:
- TerminalLogger class
- Secret masking (API_KEY, password, token, SECRET)
- Encryption at rest
- Test masking effectiveness

Run validation:
pytest tests/unit/test_terminal.py -v --cov=vcm.utils.terminal_logger

DAY 4 TASK: Session-Model Linkage
===========================
Files to modify:
- vcm/models/metadata.py (Add session field)
- vcm/trainer.py (Detect active session)

Implementation:
- Add session context to MetadataModel
- Link models to sessions automatically
- Store session position & previous/next model

DAY 5 TASK: Session CLI Commands
===========================
Files to create:
- vcm/cli/session_commands.py (All session CLI)
- vcm/tests/cli/test_session_cli.py (CLI tests)

Commands to implement:
- vcm session start
- vcm session end
- vcm session list
- vcm session info
- vcm session logs
- vcm session models
- vcm session annotate
- vcm session compare
- vcm session export

Run: pytest tests/cli/test_session_cli.py -v

DAY 6-7 TASK: Integration & E2E
=========================
Files to create/modify:
- vcm/tests/integration/test_session_*.py (Integration tests)

Full workflow test:
1. Start session
2. Train models (auto-join session)
3. Add annotations
4. End session
5. Query session info
6. Export results

Run: pytest tests/integration/test_session*.py -v

WEEKLY VALIDATION:
==================
pytest tests/unit/test_session*.py -v --cov=vcm
pytest tests/integration/test_session*.py -v
# Expected: 18+ tests passing

If any test fails:
1. Read error carefully
2. Check specification
3. Fix implementation
4. Re-run test
5. Report finding

Ready? Start with vcm_session_tracking_spec.md "Session Structure"
```

---

### PROMPT 3: Week 2 Advanced Testing

```
PHASE 2, WEEK 2: Advanced Testing & Real Project Validation

OBJECTIVE:
Implement 8 real ML project scenarios to validate VCM works in production.

REFERENCE DOCUMENTS:
1. vcm_phase2_agent_guide.md - Days 1-7 of this week
2. vcm_advanced_testing.md - Complete scenario specifications
3. vcm_testing_strategy.md - Testing checklist

DAY 1-2 TASK: Iris Project Setup
============================
Files to create:
- tests/fixtures/iris_project/ (Real ML project directory)
 ├── data/
 │ ├── iris_train_v1.0.csv
 │ ├── iris_train_v2.0.csv (scaled)
 │ └── iris_test_v1.0.csv
 ├── training_scripts/
 │ ├── train_model_v1.py
 │ └── train_model_v2.py (improved)
 ├── .gitignore
 ├── .vcmconfig.yaml
 └── conftest.py (pytest fixtures)

Implementation:
1. Create real iris classification datasets
2. Create working training scripts
3. Initialize git repo
4. Initialize DVC (optional but recommended)
5. Create pytest fixtures for project setup

Result: Reproducible test project that can be run multiple times

DAY 3-5 TASK: Implement All 8 Scenarios
==================================
Files to create:
- tests/advanced/test_scenario_1_single_training.py
- tests/advanced/test_scenario_2_multiple_models.py
- tests/advanced/test_scenario_3_data_version_impact.py
- tests/advanced/test_scenario_4_code_changes.py
- tests/advanced/test_scenario_5_lineage_analysis.py
- tests/advanced/test_scenario_6_troubleshooting.py
- tests/advanced/test_scenario_7_reproducibility.py
- tests/advanced/test_scenario_8_audit_trail.py

For each scenario:
1. Read specification in vcm_advanced_testing.md
2. Create test file with all assertions
3. Run real ML workflow
4. Verify all metadata captured correctly
5. Validate insights are accurate

Run: pytest tests/advanced/ -v -s

Expected: 8/8 scenarios passing with real models trained

DAY 6 TASK: Performance & Reproducibility
====================================
Files to create:
- tests/performance/test_query_performance.py
- tests/performance/test_metadata_overhead.py
- tests/performance/test_reproducibility.py

Performance targets:
- Query <200ms for 100 models
- Metadata capture <2.5s overhead
- Reproducibility: byte-for-byte identical models

DAY 7 TASK: Full Validation
=======================
Commands to run:
pytest tests/ -v --cov=vcm --cov-report=html --cov-report=term-missing --tb=short
mypy vcm/ --strict
flake8 vcm/ --max-line-length=100
black vcm/ --check
bandit -r vcm/

Expected results:
[x] 140+ tests passing
[x] Coverage >85%
[x] 0 type errors
[x] 0 linting violations
[x] No HIGH security issues

Generate report showing all metrics passing.

WEEKLY VALIDATION:
==================
After each scenario:
pytest tests/advanced/test_scenario_X.py -v -s

Full suite validation:
pytest tests/ -v --cov=vcm --cov-report=term-missing
# Expected: All passing, >85% coverage

Ready? Start with tests/fixtures/iris_project/ setup
```

---

## QUALITY VALIDATION PROMPTS

### PROMPT 4: After Each Component (Daily Check)

```
QUALITY CHECK: After Implementing Each Component

After you finish implementing any module, run this:

STEP 1: Run Tests
pytest tests/unit/test_[module].py -v --cov=vcm.[module]

Verify:
 All tests passing (100%)
 Coverage >90%
 No warnings

STEP 2: Check Code Quality
mypy vcm/[module]/ --strict

Verify:
 0 type errors
 All functions have type hints
 No "Any" types

STEP 3: Check Linting
flake8 vcm/[module]/ --max-line-length=100

Verify:
 0 violations
 No commented-out code
 Consistent formatting

STEP 4: Check for TODOs
grep -r "TODO\|FIXME\|XXX" vcm/[module]/

Verify:
 No TODOs found
 All functions complete

STEP 5: Verify Documentation
- Docstrings on all classes
- Docstrings on all public methods
- Type hints on all functions
- README or inline comments for complex logic

If any check fails:
1. Fix the issue
2. Re-run the check
3. Continue only when passing

Report Format:
"[x] [Module] Quality Check Passed
 - Tests: X/X passing, Y% coverage
 - Types: 0 errors
 - Linting: 0 violations
 - Ready for next component"
```

---

### PROMPT 5: Weekly Full Validation

```
FULL QUALITY VALIDATION: End of Each Week

Run this at the end of Week 1 and Week 2:

COMMAND 1: Full Test Suite
pytest tests/ -v \
 --cov=vcm \
 --cov-report=html \
 --cov-report=term-missing \
 --tb=short

Check:
 All tests passing
 Coverage >85%
 No test failures
 HTML report generated

COMMAND 2: Type Checking
mypy vcm/ --strict

Check:
 0 errors
 No warnings
 All type hints complete

COMMAND 3: Code Quality
flake8 vcm/ --max-line-length=100

Check:
 0 violations
 Code style consistent

COMMAND 4: Security
bandit -r vcm/

Check:
 No HIGH severity issues
 No credential leaks

COMMAND 5: Code Formatting
black vcm/ --check

Check:
 Formatting consistent
 No format issues

FINAL REPORT FORMAT:
====================
Week [X] Quality Report
═══════════════════════════

Test Results:
[x] Tests passing: X/X
[x] Coverage: Y%
[x] No failures

Code Quality:
[x] Type checking: 0 errors
[x] Linting: 0 violations
[x] Formatting: OK
[x] Security: No HIGH issues

Deliverables:
[x] [Module 1]: Complete, tested
[x] [Module 2]: Complete, tested
...

Status: READY FOR NEXT PHASE / READY FOR PRODUCTION

Any failures? Identify and fix before continuing.
```

---

## CONTEXT-SPECIFIC PROMPTS

### PROMPT 6: If Tests Fail

```
TEST DEBUGGING: When Tests Fail

If any test fails:

STEP 1: Understand the Failure
- Read test name carefully
- Read error message completely
- Note expected vs actual values

STEP 2: Find Root Cause
1. Check specification: Is my implementation right?
 Reference: vcm_session_tracking_spec.md or vcm_testing_strategy.md
 
2. Check test case: Is test expectation clear?
 Reference: vcm_test_cases.md (for Phase 1) or test file itself
 
3. Check implementation: Does code match spec?
 Compare code to specification document

STEP 3: Fix the Issue
Don't debug in the dark:
1. Make a clear hypothesis
2. Test the hypothesis
3. Verify fix with test run
4. Run full test suite to catch regressions

STEP 4: Report
"Test Failure [Test Name]:
Cause: [Root cause]
Fix: [What was changed]
Verification: [Test now passes]"

DO NOT:
 Modify tests to match code
 Skip failing tests
 Ignore error messages
 Make random changes

DO:
 Understand the test
 Fix the implementation
 Verify with full test run
 Report what you learned
```

---

### PROMPT 7: Final Production Validation

```
FINAL PRODUCTION VALIDATION: End of Phase 2

Before declaring "complete", run this comprehensive validation:

STEP 1: Full Test Suite
pytest tests/ -v \
 --cov=vcm \
 --cov-report=html \
 --cov-report=term-missing \
 --tb=short

Requirements:
[x] 140+ tests passing (100%)
[x] Coverage >85%
[x] No warnings
[x] No skipped tests

STEP 2: Code Quality
mypy vcm/ --strict # 0 errors
flake8 vcm/ --max-line-length=100 # 0 violations
black vcm/ --check # Formatting OK
bandit -r vcm/ # No HIGH issues

STEP 3: Advanced Scenarios
pytest tests/advanced/ -v -s

Requirements:
[x] 8/8 scenarios passing
[x] Real iris project working
[x] All metadata captured correctly

STEP 4: Real Project End-to-End
Run this workflow manually:
1. vcm init
2. vcm session start "final test"
3. vcm train --model-name test_v1 --script train.py --metrics metrics.json
4. vcm models --best
5. vcm lineage models/test_v1.pkl
6. vcm session end
7. vcm session info "final test"

Requirements:
[x] All commands work
[x] All outputs correct
[x] Session tracking accurate

STEP 5: Documentation Check
Verify:
[x] README.md exists
[x] CLI commands match documentation
[x] All examples work
[x] No broken links

FINAL REPORT: Production Readiness Checklist
═════════════════════════════════════════════

Tests:
[x] 140+ tests passing
[x] Coverage: X%
[x] 0 failures

Code Quality:
[x] Type checking: 0 errors
[x] Linting: 0 violations
[x] Formatting: OK
[x] Security: OK

Real-World:
[x] 8 scenarios working
[x] Iris project validated
[x] E2E workflow complete

Documentation:
[x] CLI documented
[x] Examples provided
[x] Workflows explained

Status: [x] PRODUCTION READY

If any item fails: Do not declare complete. Fix and re-validate.
```

---

## SUMMARY: HOW TO USE THESE PROMPTS

### Usage Pattern

```
Session 1: Initial Orientation
├─ Use: PROMPT 1 (Master Prompt)
├─ Agent: Understands task and context
└─ Output: Ready to start

Session 2-9: Implementation (Week 1)
├─ Use: PROMPT 2 (Week 1 Session Tracking)
├─ Daily: PROMPT 4 (Quality Check after each day)
├─ Agent: Implements session tracking system
└─ Output: 12 unit tests + integration tests passing

Session 10-17: Implementation (Week 2)
├─ Use: PROMPT 3 (Week 2 Advanced Testing)
├─ Daily: PROMPT 4 (Quality Check)
├─ Agent: Runs 8 real ML scenarios
└─ Output: 8 scenarios passing, advanced tests complete

Session 18: Validation
├─ Use: PROMPT 7 (Final Validation)
├─ Agent: Runs full validation suite
└─ Output: Production ready or issues identified

Weekly Checkpoint:
├─ Use: PROMPT 5 (Weekly Full Validation)
├─ Agent: Generates weekly report
└─ Output: Quality metrics and status
```

---

## COPY-PASTE READY PROMPTS

Pick your starting point and copy the prompt exactly:

**First Context Window:** Use PROMPT 1 
**Week 1 Dev:** Use PROMPT 2 
**Week 2 Dev:** Use PROMPT 3 
**Daily Check:** Use PROMPT 4 
**Weekly Report:** Use PROMPT 5 
**When Tests Fail:** Use PROMPT 6 
**Final Validation:** Use PROMPT 7 

---

## [x] FINAL INSTRUCTIONS

1. **Upload all 8 documents** to your agent (or context)
2. **Use PROMPT 1** for orientation
3. **Follow PROMPT 2** for Week 1 implementation
4. **Follow PROMPT 3** for Week 2 implementation
5. **Use PROMPT 4** daily to validate quality
6. **Use PROMPT 5** at end of each week
7. **Use PROMPT 7** for final validation

**Total timeline:** 2 weeks following this plan

**Expected outcome:** Production-ready Phase 2 with 140+ tests passing

---

**Ready to give to agent? Copy PROMPT 1 and paste to start!** 
