# OSW-AUTO-033 v0.1 Demo Smoke And Release Checklist Self-Check

## Step ID

`OSW-AUTO-033_V0_1_DEMO_SMOKE_AND_RELEASE_CHECKLIST`

## Branch And Worktree

- Branch: `feature/osw-p9-4-demo-smoke-release-checklist`
- Worktree:
  `C:\Users\USER\source\repos\_worktrees\osw-p9-4-demo-smoke-release-checklist`

## Files Changed

- `README.md`
- `docs/10_release_checklist.md`
- `docs/demo_smoke_checklist.md`
- `.codex/reports/self_check/OSW-AUTO-033_V0_1_DEMO_SMOKE_AND_RELEASE_CHECKLIST.md`
- `.codex/reports/review/OSW-AUTO-033_V0_1_DEMO_SMOKE_AND_RELEASE_CHECKLIST_review.md`

## Scope Summary

This step adds documentation-only release readiness material. It does not change
`src/`, `tests/`, `tools/`, dependency metadata, solver adapters, executable
example assets, generated solver outputs, or binary files.

The wording keeps OSW v0.1 as an educational/research prototype. It does not
claim industrial certification, does not guarantee external solver availability,
does not support native commercial CAD direct import, and keeps `.m` execution
preview-first and user-triggered.

## Demo Smoke Coverage Summary

`docs/demo_smoke_checklist.md` covers all eight v0.1 examples:

- `01_step_import`
- `02_mesh_import`
- `03_gmsh_meshing`
- `04_calculix_cantilever`
- `05_openfoam_cavity`
- `06_cantera_reactor`
- `07_coolprop_property`
- `08_mscript_figure`

Each demo entry includes purpose, expected user-facing workflow,
required/optional dependencies, smoke check steps, expected evidence, pass
criteria, skip criteria, and known limitations or safety notes.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `pytest tests\unit -q`
- `ruff check src tests`
- `python tools\qa\run_fast_qa.py`
- `python tools\qa\check_scope_drift.py`
- `python tools\qa\check_scope_drift.py --base develop`
- `python tools\qa\check_architecture_boundaries.py`
- `python tools\qa\check_no_solver_artifacts_committed.py`
- `python tools\qa\check_changed_files_scope.py --base develop ...`
- PowerShell local markdown link check for `README.md`,
  `docs/demo_smoke_checklist.md`, and `docs/10_release_checklist.md`
- `Test-Path tools\qa\check_docs_links.py`

## Command Results

- `pytest tests\unit -q`: `187 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `python tools\qa\run_fast_qa.py`: passed.
- Scope drift checks: passed.
- Architecture boundary check: passed.
- Solver artifact check: passed.
- Changed-file scope check: passed.
- Local markdown link check: passed.

## Skipped Checks

- `tools\qa\check_docs_links.py` is not present in this repository, so it was
  reported as skipped rather than treated as a hidden success.
- No project-specific markdown link/content command exists beyond the local
  PowerShell link check used in this step.

## Remaining Risks

- The demo smoke checklist is documentation-based. It does not prove optional
  local dependencies are installed in every reviewer environment.
- Optional executable smoke for Gmsh, CalculiX, OpenFOAM, Cantera, CoolProp, and
  GNU Octave remains local-environment dependent.
- The checklist records release readiness evidence; it does not claim
  production-grade validation.

## Merge Recommendation

Merge is recommended after review if the worktree remains clean and pre-merge QA
continues to pass.
