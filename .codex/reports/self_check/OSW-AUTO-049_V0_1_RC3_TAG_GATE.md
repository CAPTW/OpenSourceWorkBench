# OSW-AUTO-049 v0.1 RC3 Tag Gate Self-Check

## Scope

This step prepares v0.1.0rc3 release metadata and the local annotated rc3 tag
gate after OSW-AUTO-047 fixed default pytest collection and OSW-AUTO-048 added
local-only docs link checking. It does not implement product features, change
solver adapters, change GUI behavior, build release artifacts, bundle external
solver binaries, create a final tag, implement remote push logic, or push.

## Prior RC Tag Evidence

- `v0.1.0-rc1` object type: `tag`
- `v0.1.0-rc1` peeled target:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc1` status: unchanged and preserved as historical local-only
  evidence.
- `v0.1.0-rc2` object type: `tag`
- `v0.1.0-rc2` peeled target:
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0-rc2` status: unchanged and preserved as historical local-only
  evidence.
- `v0.1.0-rc3`: absent before this feature-branch review.
- `v0.1.0`: absent before this feature-branch review.

## Target Metadata

- Target package version: `0.1.0rc3`
- Target local RC tag: `v0.1.0-rc3`
- Source license metadata: `GPL-3.0-or-later`
- Final package version/tag remain blocked: `0.1.0` / `v0.1.0`

## Implementation Summary

- Updated package metadata in `pyproject.toml` and `src/osw/__init__.py` from
  `0.1.0rc2` to `0.1.0rc3`.
- Updated package smoke tests for the rc3 CLI-visible version.
- Updated `tools/qa/check_release_metadata.py` for rc3 defaults and multiple
  prior RC allowances while preserving strict pre-tag mode and final-tag
  rejection.
- Expanded isolated release metadata tests for prior rc1/rc2 history, rc3
  annotated-tag validation, wrong-target failures, lightweight-tag rejection,
  final-tag rejection, unexpected release-tag rejection, strict pre-tag failure,
  repeatable CLI prior-RC options, and unpaired prior-RC CLI argument rejection.
- Updated release notes, README current-RC wording, release checklist, risk
  register, decision log, and license/version plan for rc3 while keeping rc1 and
  rc2 historical.

## Feature-Branch Command Results

Passed:

- `git status --short`: intentional rc3 metadata/docs/test/tool changes only.
- `git tag --list "v0.1*"`: `v0.1.0-rc1`, `v0.1.0-rc2`
- `git cat-file -t refs/tags/v0.1.0-rc1`: `tag`
- `git rev-parse "v0.1.0-rc1^{commit}"`:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `git cat-file -t refs/tags/v0.1.0-rc2`: `tag`
- `git rev-parse "v0.1.0-rc2^{commit}"`:
  `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `git tag --list "v0.1.0-rc3"`: absent
- `git tag --list "v0.1.0"`: absent
- `python tools/qa/check_docs_links.py`: 30 Markdown files, 58 local links,
  0 skipped external links, 0 failures
- `python tools/qa/check_duplicate_test_basenames.py`
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc3 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --allowed-prior-rc-tag v0.1.0-rc2 --allowed-prior-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `pytest tests/unit/test_release_metadata.py -q`: 14 passed
- `pytest tests/unit/test_package_smoke.py -q`: 6 passed
- `pytest tests/unit -q`: 252 passed, 3 skipped
- `pytest tests/gui -q`: 10 skipped
- `pytest -q --import-mode=importlib`: 269 passed, 19 skipped
- `pytest tests/integration -q -m "not external_solver"`:
  4 passed, 3 skipped, 3 deselected
- `pytest tests/golden -q`: 10 passed
- `pytest tests/validation -q`: 4 passed
- `pytest -q`: 270 passed, 19 skipped
- `ruff check src tests`
- `ruff check tools/qa/check_release_metadata.py tests/unit/test_release_metadata.py tests/unit/test_package_smoke.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `git diff --check`

Expected strict-mode failure:

- `python tools/qa/check_release_metadata.py --forbid-release-tags` failed for
  the expected reason: local `v0.1*` tags exist and strict pre-tag mode forbids
  release tags.

Feature-branch editable install note:

- Raw `python -m osw.cli --version` and `python -m osw.cli doctor` reported
  `0.1.0rc2` in this worktree because the local editable install still points
  at the main `develop` worktree until the squash merge lands.
- `$env:PYTHONPATH='src'; python -m osw.cli --version` reported
  `osw 0.1.0rc3`.
- `$env:PYTHONPATH='src'; python -m osw.cli doctor` reported version
  `0.1.0rc3`.
- Post-merge raw CLI checks on `develop` remain mandatory before local rc3 tag
  creation.

## Tag And Push Safety

- No tag was created on the feature branch.
- No prior tag was moved, recreated, overwritten, retargeted, deleted, or
  pushed.
- No final `v0.1.0` tag was created.
- No push occurred.
- Target commit for local rc3 tag creation: pending until post-merge pre-tag QA
  passes on `develop`; the final response records the actual target if created.

## Remaining Risks

- External URL freshness remains intentionally out of scope for the local-only
  docs link checker.
- Public push, final tag creation, release artifacts, and public announcement
  remain separate maintainer-controlled gates.
