# Contributing to VCM

## Development Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd VersionControl
   ```

2. Create and activate a Python 3.9+ virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```

---

## Testing & Quality Gates

Run the test suite before submitting code:

```bash
# Run pytest with coverage
pytest vcm/tests/ -v --cov=vcm --cov-report=term-missing

# Run static type checker
mypy vcm/

# Run flake8 linter
flake8 vcm/ --max-line-length=140
```

### Quality Standards
- All public classes and functions must include docstrings and type annotations.
- Code coverage must remain >= 80%.
- No TODO or FIXME placeholders in production code.
