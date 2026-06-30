# OSW-AUTO-044A Self-Check

## Step ID

OSW-AUTO-044A_RELEASE_METADATA_CHECK_RC_TAG_COMPATIBILITY

## Branch / Worktree

- Branch: `feature/osw-p13-4-release-metadata-rc-tag-compat`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p13-4-release-metadata-rc-tag-compat`
- Base branch: `develop`

## Scope Summary

This step fixes a release QA policy mismatch after OSW-AUTO-043 created the
local annotated `v0.1.0-rc1` tag. The release metadata checker now supports:

- strict pre-tag mode through `--forbid-release-tags`;
- RC-aware expected-tag mode through `--expected-rc-tag`,
  `--expected-rc-target`, and `--require-annotated-rc-tag`;
- safe default behavior that accepts the expected local annotated rc1 tag while
  still rejecting final or unexpected `v0.1*` tags.

No product features, package versions, license metadata, license text, tags, or
release artifacts were changed.

## Files Changed

- `tools/qa/check_release_metadata.py`
- `tests/unit/test_release_metadata.py`
- `docs/10_release_checklist.md`
- `docs/09_risk_register.md`
- `docs/07_decision_log.md`
- `.codex/reports/self_check/OSW-AUTO-044A_RELEASE_METADATA_CHECK_RC_TAG_COMPATIBILITY.md`

## Release Tag Evidence

- `git tag --list "v0.1*"`: `v0.1.0-rc1`
- `git cat-file -t refs/tags/v0.1.0-rc1`: `tag`
- `git rev-parse "v0.1.0-rc1^{commit}"`:
  `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `git tag --list "v0.1.0"`: empty

The existing local rc1 tag was not modified. No new RC tag or final tag was
created.

## Commands Run

- `git status --short`: clean before work; dirty only with intentional changes
  after implementation.
- `git branch --show-current`: `develop` during root preflight.
- `git worktree list`: confirmed existing worktrees and then the new feature
  worktree.
- `git show-ref --verify --quiet refs/heads/develop`: passed.
- `git tag --list "v0.1*"`: `v0.1.0-rc1`.
- `git cat-file -t refs/tags/v0.1.0-rc1`: `tag`.
- `git rev-parse "v0.1.0-rc1^{commit}"`: expected OSW-AUTO-043 commit.
- `git tag --list "v0.1.0"`: empty.
- `python tools/qa/check_release_metadata.py`: initially reproduced the
  blocker; after the fix, passed.
- `python tools/qa/check_release_metadata.py --expected-rc-tag v0.1.0-rc1 --expected-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --require-annotated-rc-tag`:
  passed.
- `python tools/qa/check_release_metadata.py --forbid-release-tags`: failed for
  the expected strict pre-tag reason.
- `pytest tests/unit/test_release_metadata.py -q`: `9 passed`.
- `pytest tests/unit -q`: `225 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `ruff check tools/qa/check_release_metadata.py tests/unit/test_release_metadata.py`:
  passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/run_fast_qa.py`: passed.
- `python tools/qa/run_pre_merge_qa.py`: passed.
- `git diff --check`: passed.
- `pytest -q --import-mode=importlib`: `243 passed, 19 skipped`.
- `pytest -q`: failed only with the documented duplicate
  `test_plugin_manager_dialog.py` basename import mismatch.
- `python tools/qa/check_docs_links.py`: skipped because the tool is not
  present.

## Skipped Or Non-Blocking Checks

- `tools/qa/check_docs_links.py` is absent and remains the documented P2
  follow-up.
- Default `pytest -q` remains the documented P2 duplicate basename collection
  issue. Targeted suites and `pytest -q --import-mode=importlib` passed.
- Extra exploratory `ruff check tools tests` found unrelated pre-existing style
  issues in tool files outside this task. The touched checker and tests pass
  scoped ruff.

## Remaining Risks

- After this merge, `v0.1.0-rc1` remains local-only and still points to the
  original OSW-AUTO-043 commit, not the new `develop` HEAD.
- The next current release candidate should be produced by
  `OSW-AUTO-045_V0_1_RC2_TAG_GATE`.
- Public push and final `v0.1.0` tag creation remain blocked until separate
  maintainer-controlled gates.

## Merge Recommendation

Merge after review if score is at least 90 and tag state remains unchanged.
