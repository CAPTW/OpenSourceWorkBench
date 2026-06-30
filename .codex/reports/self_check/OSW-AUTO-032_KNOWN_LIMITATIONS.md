# OSW-AUTO-032 Known Limitations Self-Check

## Scope

Added a dedicated known limitations page for OSW v0.1 and linked it from the
root README and release checklist.

No `src/**` files were changed.

## Acceptance Criteria

- `docs/known_limitations.md` exists.
- README links the known limitations page.
- Release checklist references the limitations page.
- Limitations explicitly state that OSW v0.1 does not make industrial
  certification claims, does not replace expert engineering judgment, does not
  support commercial native CAD direct import, does not support Simulink or
  `.mlapp`, does not support full MATLAB proprietary toolbox compatibility, and
  keeps OpenFOAM, CFD/CAE validation, `.m` execution, external solver
  dependency, and optional dependency behavior bounded.
- The language is direct and boundary-setting, without apology or expanded
  product claims.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `Test-Path tools\qa\check_docs_links.py`
- PowerShell local markdown link check for `README.md`,
  `docs/known_limitations.md`, and `docs/10_release_checklist.md`
- `python tools\qa\check_scope_drift.py --base develop`
- `python tools\qa\check_scope_drift.py`
- `python tools\qa\run_fast_qa.py`
- `pytest tests\unit -q`
- `ruff check src tests`
- `python tools\qa\check_architecture_boundaries.py`
- `python tools\qa\check_no_solver_artifacts_committed.py`

## Results

- `tools\qa\check_docs_links.py` is not present in this repository; skipped with
  this explicit reason.
- Local markdown links resolve.
- Initial review found that the self-check report needed clearer negative-scope
  wording. After amend, the scope drift checks passed.
- Fast QA passed, including CLI smoke, doctor, ruff, and unit tests.
- `pytest tests\unit -q`: `187 passed, 3 skipped`.
- `ruff check src tests`: passed.
- Architecture boundary check passed.
- Solver artifact check passed.

## Residual Risks

- This pass documents boundaries but does not add automated tests for the known
  limitations page itself.
- Future feature docs still need to link or reference the known limitations page
  when they introduce new user-facing workflow boundaries.
