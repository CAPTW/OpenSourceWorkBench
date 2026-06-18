# v0.1.4rc1 package metadata editable alignment

## Context

Local verification showed:

- `osw` source and CLI reported `0.1.4rc1`.
- Installed package metadata reported `0.1.3rc1`.
- `v0.1.4-rc1` release and `v0.1.4-rc1` target commit remained unchanged.

## Diagnosis

### Before repair

- `osw.__file__`: `D:\dev\repos\Workbench\src\osw\__init__.py`
- Installed distribution version (`importlib.metadata.version("open-solver-workbench")`): `0.1.3rc1`
- Tracked source metadata:
  - `pyproject.toml`: `version = "0.1.4rc1"`
  - `src/osw/__init__.py`: `__version__ = "0.1.4rc1"`

## Repair

Commands run:

- `gh auth status`
- `gh auth setup-git`
- `.venv\Scripts\python.exe -m pip install --no-deps --force-reinstall -e .`
- (if needed) `.venv\Scripts\python.exe -m pip uninstall -y open-solver-workbench`
- `.venv\Scripts\python.exe -m pip install --no-deps -e .`

No dependency install or upgrade was performed.

### After repair

- `osw.__file__`: `D:\dev\repos\Workbench\src\osw\__init__.py`
- Installed distribution version: `0.1.4rc1`
- `pip show open-solver-workbench`: `Version: 0.1.4rc1`
- `osw.cli --version`: `osw 0.1.4rc1`

## QA guard

`tools/qa/check_release_metadata.py` was updated to validate installed distribution metadata:

- It now checks `importlib.metadata.version("open-solver-workbench")`.
- It reports failure when installed metadata version is not expected.
- It ignores (passes) the check when the distribution is not installed.
- New unit tests in `tests/unit/test_release_metadata.py` cover mismatch, exact-match, and missing-distribution behavior.

## Non-goals

- No version bump.
- No release edits, tags, or tag pushes.
- No asset upload/download mutations.
- No issue comment/create/close operations.

## Future note

Prefer running QA and CLI checks via `.venv\Scripts\python.exe` once editable metadata is repaired, without process-local `PYTHONPATH` workarounds.
