# Self-Check: OSW-AUTO-039_PACKAGING_INSTALL_DOCS

## Step ID

OSW-AUTO-039_PACKAGING_INSTALL_DOCS

## Branch / Worktree

- Branch: `feature/osw-p12-2-install-docs`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p12-2-install-docs`
- Base branch: `develop`

## Files Changed

- `README.md`
- `docs/install.md`
- `docs/10_release_checklist.md`
- `.codex/reports/self_check/OSW-AUTO-039_PACKAGING_INSTALL_DOCS.md`

## Scope Summary

Added source-first packaging and installation documentation for OSW v0.1. The
guide documents conda, pip, uv, Windows, Linux, optional Python extras, optional
external tool notes, Docker as optional only, and troubleshooting. It keeps
external solvers and heavy optional stacks separate from the base install path.

No packaging overhaul, mandatory external solver installation, feature
implementation, or binary/runtime artifact was added.

## Install Coverage Summary

- Conda: `environment.yml` based editable development install.
- Pip: Windows and Linux virtual environment editable install.
- uv: Windows and Linux editable install.
- Optional Python extras: `gui`, `mesh`, `viz`, `thermo` / `chm`, `mscript`,
  and `all`.
- Optional external tools: CalculiX `ccx`, OpenFOAM, GNU Octave, Cantera, and
  CoolProp.
- Docker: documented as optional and not the v0.1 release path.
- Troubleshooting: Python version, quoted extras, missing `osw`, optional
  dependencies, external executables, Windows activation policy, OpenFOAM
  environment setup, and generated artifacts.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `python tools/qa/check_docs_links.py` if present
- Local ASCII docs check for touched docs
- Local markdown link check for touched docs
- `pytest tests/unit -q`
- `ruff check src tests`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_plugin_manifests.py`
- `git diff --check`
- `rg` content check for install guide coverage terms

## Command Results

- Preflight: base worktree clean on `develop`; `develop` exists.
- Feature worktree created on `feature/osw-p12-2-install-docs`.
- `tools/qa/check_docs_links.py`: skipped because the tool is not present.
- Local ASCII docs check: passed.
- Local markdown link check over touched docs: passed.
- `pytest tests/unit -q`: `216 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/qa/check_plugin_manifests.py`: passed.
- `git diff --check`: passed.
- Content check confirmed coverage of conda, pip, uv, Windows, Linux, Docker,
  CalculiX, OpenFOAM, GNU Octave, Cantera, CoolProp, troubleshooting,
  PyInstaller/source-install fallback, and known limitations.

## Skipped Checks

- `tools/qa/check_docs_links.py`: not present in this repository.
- Project markdown link/content command: no dedicated project command exists in
  `tools/qa`; a local targeted link check was run instead.

## Remaining Risks

- Docker is documented as optional only; no Dockerfile was added.
- External solver installation notes intentionally point users to separate local
  installation and PATH setup rather than bundling or requiring solver runtimes.
- PyInstaller/standalone packaging remains deferred; source and conda installs
  are the v0.1 readiness path.

## Merge Recommendation

Recommend review and merge if the review score is at least 90 with no hard
blockers. The change is documentation-only and keeps optional dependencies
separate from base install readiness.
