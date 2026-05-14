# Self-Check: OSW-AUTO-035_VALIDATION_MATRIX

## Step ID

OSW-AUTO-035_VALIDATION_MATRIX

## Branch / Worktree

- Branch: `feature/osw-p11-1-validation-matrix`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p11-1-validation-matrix`
- Base branch: `develop`

## Files Changed

- `docs/04_validation_matrix.md`
- `tests/validation/test_validation_matrix_documentation.py`
- `.codex/reports/self_check/OSW-AUTO-035_VALIDATION_MATRIX.md`

## Scope Summary

Strengthened the v0.1 validation matrix as documentation-backed validation
evidence. The matrix now defines the requested fields and five required cases:

- `VAL-CAE-001` CalculiX cantilever beam.
- `VAL-MESH-001` mesh import/export.
- `VAL-MSCRIPT-001` simple plot FigureDataset.
- `VAL-CHM-001` CoolProp known property.
- `VAL-REPORT-001` HTML report sections.

Each case maps to a v0.1 demo or report step, states expected output, gives a
tolerance or pass criterion, lists source/formula evidence, and records status
and last-run evidence. Limitations explicitly state that this is not industrial
certification, external solvers remain optional, `.m` workflows are
preview-first, and native commercial CAD direct import is not supported.

## Coverage Summary

Added `tests/validation/test_validation_matrix_documentation.py` to assert that
the required case IDs, required fields, pass criteria, and key limitation
language remain present in the validation matrix.

## Review Amend Summary

Initial review scored 86/100 because `VAL-CHM-001` named a CoolProp property
check without a fixed state point, expected value, or numeric tolerance. The
amend branch tightens the row to Water at `pressure_pa=101325.0` and
`temperature_k=300.0`, expected density approximately `996.6 kg/m^3`, and a
numeric pass bound of `990.0 < D < 1000.0 kg/m^3`. The validation documentation
test now checks those concrete terms.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git worktree list`
- `git show-ref --verify --quiet refs/heads/develop`
- `pytest tests/validation -q`
- `python tools/qa/check_docs_links.py` if present
- `ruff check src tests`
- `python tools/qa/run_fast_qa.py`
- `pytest tests/unit -q`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `git diff --check`
- Amend rerun: `pytest tests/validation -q`
- Amend rerun: `ruff check src tests`
- Amend rerun: `python tools/qa/run_fast_qa.py`
- Amend rerun: `python tools/qa/check_scope_drift.py`
- Amend rerun: `python tools/qa/check_architecture_boundaries.py`
- Amend rerun: `python tools/qa/check_no_solver_artifacts_committed.py`
- Amend rerun: `python tools/qa/check_docs_links.py` if present

## Command Results

- Preflight: base worktree clean, current branch `develop`, `develop` exists.
- Feature worktree created on `feature/osw-p11-1-validation-matrix`.
- `pytest tests/validation -q` passed: `4 passed`.
- `python tools/qa/check_docs_links.py` skipped: tool not present.
- `ruff check src tests` passed.
- `python tools/qa/run_fast_qa.py` passed, including CLI version, doctor, Ruff,
  and unit tests.
- `pytest tests/unit -q` passed: `202 passed, 3 skipped`.
- `python tools/qa/check_scope_drift.py` passed.
- `python tools/qa/check_architecture_boundaries.py` passed.
- `python tools/qa/check_no_solver_artifacts_committed.py` passed.
- `git diff --check` passed.
- Amend `pytest tests/validation -q` passed: `4 passed`.
- Amend `ruff check src tests` passed.
- Amend `python tools/qa/run_fast_qa.py` passed, including unit tests:
  `202 passed, 3 skipped`.
- Amend scope drift, architecture boundary, and solver artifact checks passed.
- Amend docs link check skipped: tool not present.

## Skipped Checks

- `tools/qa/check_docs_links.py` is not present in this repository state.

## Remaining Risks

- Validation matrix rows summarize current v0.1 evidence; they do not prove
  industrial accuracy or production suitability.
- Optional dependency rows remain dependent on local availability of CoolProp,
  Octave, and solver tooling and must skip or report missing dependencies
  cleanly.
- Some evidence is unit-test backed rather than external solver execution backed
  by design.

## Merge Recommendation

Recommend review and merge if the review score is at least 90 with no hard
blockers. The change is documentation/test-only, stays within validation scope,
and has focused regression coverage.
