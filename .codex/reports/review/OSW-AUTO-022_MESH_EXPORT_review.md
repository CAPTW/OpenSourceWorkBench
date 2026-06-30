# OSW-AUTO-022 Mesh Export Review

Decision: Merge possible
Score: 94/100
Checkpoint: 0b1477a

## Scope And Files

- `src/osw/mesh/conversion.py`
- `src/osw/mesh/__init__.py`
- `tests/unit/test_mesh_export.py`
- `tests/golden/mesh/test_mesh_export_contract.py`

The change stays inside the mesh package and test fixtures. It adds a generic
mesh export artifact pipeline for `.vtu`, `.msh`, `.xdmf`/`.xmf`, and `.inp`
through meshio, while preserving existing `convert_mesh` and
`convert_mesh_to_vtu` path-return behavior.

## Review Score

| Category | Score | Evidence |
| --- | ---: | --- |
| Architecture Compliance | 18/18 | Mesh export stays in `osw.mesh`, uses guarded meshio loading, and only references `ResultRef` for artifact tracking. |
| Test Coverage / Regression Safety | 18/18 | Unit and golden tests cover formats, artifacts, ResultRef bridge, unsupported extensions, unsupported cell types, and legacy conversion behavior. |
| User Workflow Quality | 11/12 | Export errors list supported formats/cell types and artifacts are report/project friendly. |
| Numerical / Validation Safety | 11/12 | No solver validation or accuracy claims; `.inp` support is export-only and bounded to common meshio/CalculiX-like cell types. |
| Error Handling / Robustness | 10/10 | Unsupported format and cell type failures are clear and non-crashing. |
| Security / Script Safety | 10/10 | No subprocess, solver execution, script execution, or GUI coupling. |
| Documentation | 4/5 | Golden contract stabilizes exported format/artifact schema; no broad docs needed. |
| Scope Discipline | 5/5 | No CalculiX adapter implementation or OpenFOAM case generation added. |
| Git / Local Environment Safety | 7/10 | Feature worktree is clean and checkpointed; no destructive Git actions. |

## Issues

Critical issues: none
High issues: none
Medium issues: none
Low issues:
- Real meshio export is not run locally because the base environment does not
  install optional `meshio`; fake meshio tests cover writer integration.

## Commands Run

- `pytest tests\unit -q` -> passed, 118 passed, 1 skipped at baseline.
- `pytest tests\unit\test_mesh_export.py tests\golden\mesh -q` -> failed before implementation with missing export API.
- `pytest tests\unit\test_mesh_export.py tests\golden\mesh -q` -> passed, 8 passed.
- `ruff check src tests` -> passed.
- `python tools\qa\run_fast_qa.py` -> passed, 124 passed, 1 skipped.
- `python tools\qa\check_scope_drift.py` -> passed.
- `python tools\qa\check_architecture_boundaries.py` -> passed.
- `python tools\qa\check_no_solver_artifacts_committed.py` -> passed.

## Required Fixes

None.

## Required Rerun Commands

- `python tools\qa\run_pre_merge_qa.py`
- `pytest tests\unit\test_mesh_export.py tests\golden\mesh -q`

## Generated/Runtime Artifact Check

No generated mesh exports, solver runtime artifacts, or report outputs are
staged. Test exports are created under pytest `tmp_path` only.

## Residual Risks

- `.inp` export is a generic meshio/Abaqus-format bridge for later CalculiX
  handoff, not a CalculiX adapter.
- Real optional meshio export should be exercised in an environment with the
  `mesh` extra installed.
