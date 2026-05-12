# OSW-AUTO-023 CalculiX Input Deck Review

Decision: Merge possible
Score: 94/100
Checkpoint: 46d9996

## Scope And Files

- `src/osw/solvers/calculix/__init__.py`
- `src/osw/solvers/calculix/adapter.py`
- `src/osw/solvers/calculix/input_deck.py`
- `src/osw/solvers/calculix/validation.py`
- `src/osw/solvers/calculix/osw-plugin.json`
- `tests/unit/test_calculix_adapter.py`
- `tests/unit/test_calculix_input_deck.py`
- `tests/unit/test_calculix_validation.py`
- `tests/golden/calculix/cantilever_linear_static.inp`
- `tests/golden/calculix/test_calculix_cantilever_golden.py`
- `examples/04_calculix_cantilever/README.md`

The change stays inside the CalculiX solver adapter package, tests, golden
fixtures, and bounded example documentation. It prepares linear static input
decks only and does not execute CalculiX.

## Review Score

| Category | Score | Evidence |
| --- | ---: | --- |
| Architecture Compliance | 18/18 | Solver adapter implements `SolverAdapterPlugin`; no GUI imports or subprocess calls. |
| Test Coverage / Regression Safety | 18/18 | Focused tests cover deck sections, validation errors/warnings, adapter contract, pressure loads, unsupported cell types, and golden output. |
| User Workflow Quality | 11/12 | Validation messages are friendly and prepare output includes a command preview; no full GUI wiring in this scope. |
| Numerical / Validation Safety | 11/12 | Explicitly limited to linear static, isotropic elastic, fixed support, force, and pressure. Unit warnings are surfaced when non-SI values are provided. |
| Error Handling / Robustness | 10/10 | Missing material, missing fixed support, bad node sets, empty mesh, unsupported cells, and invalid loads are handled before deck generation. |
| Security / Script Safety | 10/10 | No script execution, external solver execution, network access, or GUI direct subprocess path. |
| Documentation | 4/5 | Example README states bounded workflow and exclusions; broader CalculiX docs can come later. |
| Scope Discipline | 5/5 | No nonlinear contact/plasticity implementation, OpenFOAM/SU2 files, or GUI `.inp` editing. |
| Git / Local Environment Safety | 7/10 | Feature worktree used, checkpoint committed, no destructive Git operations; pre-merge still required. |

## Issues

Critical issues: none
High issues: none
Medium issues: none
Low issues:
- The adapter prepares `.inp` text only; real CalculiX execution and result
  parsing remain future reviewed work.
- Element support is intentionally limited to common mesh cell types and does
  not perform advanced element quality or physical group mapping.

## Commands Run

- `pytest tests\unit -q` -> passed, 124 passed, 1 skipped at baseline.
- `pytest tests\unit\test_calculix_input_deck.py tests\unit\test_calculix_validation.py tests\unit\test_calculix_adapter.py tests\golden\calculix -q` -> failed before implementation with missing `osw.solvers.calculix`.
- `pytest tests\unit\test_calculix_input_deck.py tests\unit\test_calculix_validation.py tests\unit\test_calculix_adapter.py tests\golden\calculix -q` -> passed, 11 passed.
- `ruff check src tests` -> passed.
- `python tools\qa\run_fast_qa.py` -> passed, 134 passed, 1 skipped.
- `python tools\qa\check_scope_drift.py` -> passed.
- `python tools\qa\check_architecture_boundaries.py` -> passed.
- `python tools\qa\check_no_solver_artifacts_committed.py` -> passed.
- `python tools\qa\check_plugin_manifests.py` -> passed.

## Required Fixes

None.

## Required Rerun Commands

- `python tools\qa\run_pre_merge_qa.py`
- `pytest (Get-ChildItem tests\unit -Filter test_calculix_*.py | ForEach-Object { $_.FullName }) tests\golden\calculix -q`

## Generated/Runtime Artifact Check

No runtime solver output is staged. The committed `.inp` file is a curated
golden fixture under `tests/golden/calculix`.

## Residual Risks

- CalculiX binary availability, execution, and result import are outside this
  phase-step.
- Advanced section/material mapping, inelastic material behavior, contact-type
  analyses, and industrial validation claims remain excluded from this phase.
