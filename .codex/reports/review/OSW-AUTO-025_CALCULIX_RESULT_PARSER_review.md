# OSW-AUTO-025 CalculiX Result Parser Review

Decision: Merge possible
Score: 94/100
Checkpoint: acbe0ed

## Scope And Files

- `src/osw/core/result_dataset.py`
- `src/osw/solvers/calculix/result_parser.py`
- `src/osw/solvers/calculix/validation.py`
- `src/osw/solvers/calculix/__init__.py`
- `src/osw/post/report_generator.py`
- `src/osw/post/pyvista_scene.py`
- `tests/unit/test_calculix_result_parser.py`
- `tests/validation/test_calculix_cantilever.py`
- `docs/04_validation_matrix.md`

The change adds a lightweight result dataset contract, a minimal table-oriented
CalculiX `.dat` parser, cantilever tip-displacement validation, report table
handoff, and a PyVista contour placeholder. It does not parse full `.frd`
content and does not claim production-grade validation.

## Review Score

| Category | Score | Evidence |
| --- | ---: | --- |
| Architecture Compliance | 18/18 | Parser stays under `osw.solvers.calculix`; core result dataset has no top-level GUI or heavy optional dependency. |
| Test Coverage / Regression Safety | 18/18 | Tests cover valid `.dat`, corrupt/partial rows, dataset serialization, report handoff, FRD stub behavior, contour placeholder, and cantilever tolerance checks. |
| User Workflow Quality | 11/12 | Warnings are preserved in the dataset and report-table bridge; FRD-only path is explicit. |
| Numerical / Validation Safety | 11/12 | Cantilever validation uses `F L^3 / (3 E I)` with tolerance and avoids broader accuracy claims. |
| Error Handling / Robustness | 10/10 | Missing rows, corrupt numeric values, no `.dat` path, and FRD-only usage are handled explicitly. |
| Security / Script Safety | 10/10 | No process execution, script execution, network access, or GUI subprocess coupling. |
| Documentation | 4/5 | Validation matrix now includes the cantilever formula and evidence. |
| Scope Discipline | 5/5 | No advanced nonlinear results, no full FRD parser, no unrelated solver domains. |
| Git / Local Environment Safety | 7/10 | Feature worktree is clean and checkpointed; no destructive Git operations. |

## Issues

Critical issues: none
High issues: none
Medium issues: none
Low issues:
- The `.dat` parser intentionally supports a small table-oriented subset and
  may need adapters for additional CalculiX output variants.
- FRD contour data is represented as a stub until result-to-mesh mapping is
  designed and tested.

## Commands Run

- `pytest tests\unit -q` -> passed, 138 passed, 1 skipped at baseline.
- `pytest tests\unit\test_calculix_result_parser.py tests\validation\test_calculix_cantilever.py -q` -> failed before implementation with missing parser/dataset modules.
- `pytest tests\unit\test_calculix_result_parser.py tests\validation\test_calculix_cantilever.py -q` -> passed, 8 passed.
- `ruff check src tests` -> passed.
- `python tools\qa\run_fast_qa.py` -> passed, 144 passed, 1 skipped.
- `python tools\qa\check_scope_drift.py` -> passed.
- `python tools\qa\check_architecture_boundaries.py` -> passed.
- `python tools\qa\check_no_solver_artifacts_committed.py` -> passed.
- `python tools\qa\check_plugin_manifests.py` -> passed.

## Required Fixes

None.

## Required Rerun Commands

- `python tools\qa\run_pre_merge_qa.py`
- `pytest tests\unit\test_calculix_result_parser.py tests\validation\test_calculix_cantilever.py -q`

## Generated/Runtime Artifact Check

No solver runtime artifacts are staged. Sample `.dat` contents are created only
inside pytest temporary directories.

## Residual Risks

- Full FRD parsing and result-to-mesh contour mapping remain later reviewed
  work.
- Additional real CalculiX `.dat` layouts should be added as fixtures as the
  demo path matures.
