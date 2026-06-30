# OSW-AUTO-045 Review

## Review Score

94 / 100

## Decision

Approve.

## Scope Review

The diff is a release-operation metadata update. It updates package version
metadata, release notes, release docs, release metadata QA, focused release
metadata tests, the package version smoke expectation, and required evidence
reports. It does not implement product features, change license text, vendor
external solver binaries, create release artifacts, fix the default pytest
collection P2, or implement the docs link checker.

`README.md` and `tests/unit/test_package_smoke.py` changes are minimal version
metadata consistency edits needed to avoid rc1/rc2 contradictions and keep the
required unit suite passing.

## Release Metadata Review

- `pyproject.toml` version is `0.1.0rc2`.
- `src/osw/__init__.py` version is `0.1.0rc2`.
- README release candidate status says `0.1.0rc2` and keeps rc1 local-only.
- `CHANGELOG.md` has `0.1.0rc2` and `v0.1.0-rc2` notes.
- License metadata remains `GPL-3.0-or-later`.
- `docs/14_third_party_notices.md` remains present and external solver binaries
  remain unbundled by default.

## Checker Review

`tools/qa/check_release_metadata.py` now supports:

- `--expected-version`;
- `--expected-source-license`;
- strict pre-tag mode with `--forbid-release-tags`;
- prior RC allowance with `--allowed-prior-rc-tag` and
  `--allowed-prior-rc-target`;
- current RC validation with `--expected-rc-tag`, `--expected-rc-target`, and
  `--require-annotated-rc-tag`;
- final `v0.1.0` rejection;
- unexpected `v0.1*` rejection;
- `HEAD` resolution for expected tag target.

The checker does not mutate tags, push, use the network, or blindly allow all
release tags.

## Tag Safety Review

- Existing `v0.1.0-rc1` is still an annotated tag object.
- Existing rc1 still peels to
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`.
- `v0.1.0-rc2` was not created before review.
- Final `v0.1.0` was not created.
- No push occurred.

## QA Evidence Review

Passing checks:

- `python tools/qa/check_release_metadata.py`
- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `pytest tests/unit/test_release_metadata.py -q`
- `pytest tests/unit -q`
- `ruff check src tests`
- `ruff check tools/qa/check_release_metadata.py tests/unit/test_release_metadata.py src/osw/__init__.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `pytest tests/integration -q -m "not external_solver"`
- `pytest tests/golden -q`
- `pytest tests/validation -q`
- `pytest -q --import-mode=importlib`
- `git diff --check`

Expected/non-blocking:

- `python tools/qa/check_release_metadata.py --forbid-release-tags` fails for
  the intended strict pre-tag reason because local rc1 exists.
- Feature-branch raw `python -m osw.cli --version` reports rc1 because the
  local Python environment imports the editable main worktree before the merge;
  source-tree execution with `PYTHONPATH=src` reports rc2. Post-merge checks
  must confirm raw CLI reports rc2 before tag creation.
- Default `pytest -q` fails only with the documented duplicate
  `test_plugin_manager_dialog.py` basename collection mismatch.
- `tools/qa/check_docs_links.py` is absent and remains a P2 follow-up.

## Required Amend Items

None.

## Final Merge Recommendation

Squash merge to `develop` if pre-merge QA remains green and tag state remains
unchanged. After merge, run the full post-merge pre-tag checks on `develop` and
create local annotated `v0.1.0-rc2` only if raw CLI reports `0.1.0rc2`, rc1 is
unchanged, rc2/final tags are absent, and all required checks pass.
