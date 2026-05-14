# OSW-AUTO-031 Tutorial Examples Self-Check

## Scope

Implemented documentation-only tutorials for `examples/01_step_import` through
`examples/08_mscript_figure`, added `docs/tutorials.md`, and linked the tutorial
index from `README.md`.

No `src/**` files were changed.

## Acceptance Criteria

- Each requested tutorial has `Goal`, `Prerequisites`, `Steps`, `Expected
  Output`, and `Troubleshooting` sections.
- Optional external dependencies are marked explicitly for meshio, Gmsh,
  CalculiX/ccx, OpenFOAM, Cantera, CoolProp, GNU Octave, and visualization.
- The `.m` tutorial includes a preview-first security warning and says import
  must never execute code.
- README links the tutorial index and all example tutorials.
- Documentation avoids broad solver/product claims and keeps examples bounded to
  OSW v0.1 educational/research workflows.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `Test-Path tools\qa\check_docs_links.py`
- PowerShell required-section check for all eight example READMEs
- PowerShell local markdown link check for `README.md` and `docs/tutorials.md`
- `pytest tests/unit -q`
- `ruff check src tests`
- `python tools\qa\check_scope_drift.py`
- `python tools\qa\check_architecture_boundaries.py`
- `python tools\qa\check_no_solver_artifacts_committed.py`
- `python tools\qa\run_fast_qa.py`

## Results

- `tools\qa\check_docs_links.py` is not present in this repository; skipped with
  this explicit reason.
- Initial `pytest tests/unit -q` failed because two existing docs tests expected
  exact Cantera and CoolProp non-goal wording. The README wording was restored.
- Review found one STEP expected-output bullet that tripped
  `check_scope_drift.py` at checkpoint `8ec9c92`. The amend reworded that bullet
  to keep the unsupported-format guidance without the unsafe phrase.
- Final `pytest tests/unit -q`: `187 passed, 3 skipped`.
- Final `python tools\qa\run_fast_qa.py`: passed, including CLI smoke, doctor,
  ruff, and unit tests.
- Final `ruff check src tests`: passed.
- Final scope drift check: passed.
- Final architecture boundary check: passed.
- Final solver artifact check: passed.
- Local markdown links from the root README and tutorial index resolve.

## Residual Risks

- This pass documents tutorial workflows but does not add executable tutorial
  fixtures or generated example artifacts.
- Optional dependency examples remain dependent on local installations when the
  user chooses to run them.
