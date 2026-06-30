# OSW-AUTO-045 Self-Check

## Step ID

OSW-AUTO-045_V0_1_RC2_TAG_GATE

## Branch / Worktree

- Branch: `feature/osw-p13-5-v0-1-rc2-tag-gate`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p13-5-v0-1-rc2-tag-gate`
- Base branch: `develop`

## Previous RC1 Tag Evidence

- Tag name: `v0.1.0-rc1`
- Object type: `tag`
- Peeled target commit: `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- Status: unchanged before review; not moved, recreated, overwritten, deleted,
  or pushed.

## Target RC2 Metadata

- Target package version: `0.1.0rc2`
- Target local tag name: `v0.1.0-rc2`
- Source license metadata: `GPL-3.0-or-later`
- Final tag `v0.1.0`: absent before review.

## Scope Summary

This step updates package and release metadata from rc1 to rc2, generalizes the
release metadata checker for explicit expected version/source license and prior
RC evidence, and records rc1 as local-only historical evidence. It does not
implement product features, alter license text, create release artifacts, push,
or create any tag before review.

## Files Changed

- `pyproject.toml`
- `src/osw/__init__.py`
- `CHANGELOG.md`
- `README.md`
- `docs/10_release_checklist.md`
- `docs/09_risk_register.md`
- `docs/07_decision_log.md`
- `docs/13_license_and_version_plan.md`
- `tools/qa/check_release_metadata.py`
- `tests/unit/test_release_metadata.py`
- `tests/unit/test_package_smoke.py`
- `.codex/reports/self_check/OSW-AUTO-045_V0_1_RC2_TAG_GATE.md`

`README.md` and `tests/unit/test_package_smoke.py` received minimal version
metadata consistency updates needed to avoid rc1/rc2 contradictions and keep
required unit tests passing.

## Commands Run And Results

- `git status --short`: clean before work; dirty only with intentional changes
  after implementation.
- `git branch --show-current`: `develop` during root preflight.
- `git worktree list`: verified existing worktrees and new feature worktree.
- `git show-ref --verify --quiet refs/heads/develop`: passed.
- `git rev-parse HEAD` on `develop`: `84651ef17ea74f30706bc13b7593bf94662ada9e`.
- `git tag --list "v0.1*"`: `v0.1.0-rc1`.
- `git cat-file -t refs/tags/v0.1.0-rc1`: `tag`.
- `git rev-parse "v0.1.0-rc1^{commit}"`:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`.
- `git tag --list "v0.1.0-rc2"`: empty.
- `git tag --list "v0.1.0"`: empty.
- `python -m osw.cli --version`: returned `osw 0.1.0rc1` on the feature branch
  because the local Python environment imports the editable main worktree until
  the squash merge lands.
- `$env:PYTHONPATH='src'; python -m osw.cli --version`: `osw 0.1.0rc2`.
- `python -m osw.cli doctor`: returned version `0.1.0rc1` for the same editable
  main-worktree reason.
- `$env:PYTHONPATH='src'; python -m osw.cli doctor`: returned version
  `0.1.0rc2` and optional dependency diagnostics.
- `python tools/qa/check_release_metadata.py`: passed for `0.1.0rc2`.
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e`:
  passed.
- `python tools/qa/check_release_metadata.py --forbid-release-tags`: failed for
  the expected strict pre-tag reason because local rc1 exists.
- `pytest tests/unit/test_release_metadata.py -q`: `10 passed`.
- `pytest tests/unit -q`: `226 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `ruff check tools/qa/check_release_metadata.py tests/unit/test_release_metadata.py src/osw/__init__.py`:
  passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/run_fast_qa.py`: passed; CLI output showed rc1 because of
  the editable main-worktree import path noted above.
- `python tools/qa/run_pre_merge_qa.py`: passed with the same feature-branch
  editable import note.
- `pytest tests/integration -q -m "not external_solver"`:
  `4 passed, 3 skipped, 3 deselected`.
- `pytest tests/golden -q`: `10 passed`.
- `pytest tests/validation -q`: `4 passed`.
- `pytest -q --import-mode=importlib`: `244 passed, 19 skipped`.
- `git diff --check`: passed.
- `tools/qa/check_docs_links.py`: skipped because the tool is absent.
- `pytest -q`: failed only with the documented duplicate
  `test_plugin_manager_dialog.py` basename import mismatch.

## Known P2 Exceptions

- Default `pytest -q`: non-blocking P2 exception because the failure is exactly
  the documented duplicate module basename mismatch and all targeted suites
  passed.
- Docs link checker: `tools/qa/check_docs_links.py` is absent and remains the
  documented P2 placeholder; it was not implemented in this step.

## Tag Safety

- No tag was created before review.
- Existing `v0.1.0-rc1` was not modified.
- `v0.1.0-rc2` was absent before review.
- Final `v0.1.0` was absent before review.
- No push occurred.

## Remaining Risks

- Raw feature-branch CLI commands resolve the currently installed editable main
  worktree until the squash merge updates `develop`; post-merge checks must
  confirm raw CLI reports `0.1.0rc2` before any rc2 tag is created.
- `v0.1.0-rc2` must be created only after squash merge and post-merge pre-tag
  checks pass on clean `develop`.
- Public push and final `v0.1.0` tag creation remain separate gates.

## Merge / Tag Recommendation

Proceed to review. If review score is at least 90 and no hard blockers remain,
squash merge to `develop`, run post-merge pre-tag checks, and create local
annotated `v0.1.0-rc2` only if those checks pass.
