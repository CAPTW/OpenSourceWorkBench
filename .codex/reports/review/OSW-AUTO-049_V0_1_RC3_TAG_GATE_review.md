# OSW-AUTO-049 v0.1 RC3 Tag Gate Review

Decision: Merge possible, then tag only after post-merge pre-tag QA passes.

Score: 97/100

Checkpoint: `17f3ef1e831658ed00b09a0ae50d744e0ffe3f2e`

## Scope Reviewed

Reviewed the rc3 metadata/tag-gate branch for forbidden product changes,
release metadata consistency, prior RC preservation, local-only tag safety,
test isolation, docs honesty, and required QA evidence. A reviewer subagent also
inspected the branch and reported no hard blockers.

## Score

| Category | Score | Notes |
| --- | ---: | --- |
| Architecture Compliance | 8/8 | Changes are limited to version metadata, release docs, release QA tooling, release tests, and evidence reports. No product behavior, GUI workflow, or solver adapter changed. |
| Test Coverage / Regression Safety | 18/18 | Release metadata tests cover rc3 metadata, prior rc1/rc2 allowance, wrong prior targets, expected rc3 target checks, lightweight-tag rejection, final-tag rejection, unexpected tags, strict pre-tag mode, repeatable CLI prior-RC args, and unpaired CLI arg rejection. |
| User Workflow Quality | 6/6 | CLI release metadata diagnostics remain explicit and local-only; docs state rc1/rc2 historical and rc3 current local candidate. |
| Numerical / Validation Safety | 8/8 | No numerical behavior or validation math changed. |
| Error Handling / Robustness | 8/8 | Checker rejects final/unexpected tags, wrong targets, lightweight tags when annotated tags are required, and unpaired prior-RC CLI options. |
| Security / Script Safety | 8/8 | No network access, tag mutation, push, release artifact build, external solver execution, or script execution added. |
| Documentation / Release Notes | 12/12 | README, CHANGELOG, release checklist, risk register, decision log, and license/version plan are aligned around rc3 while preserving rc1/rc2 history and final/push blocks. |
| Scope Discipline | 8/8 | No Simulink, `.mlapp`, commercial native CAD, full solver UI, industrial claims, product features, solver adapter changes, or GUI behavior changes. |
| Git / Local Environment Safety | 9/12 | Worktree is isolated and clean after checkpoint. Deducted for the known feature-worktree editable-install caveat where bare CLI reports rc2 until the squash merge updates `develop`; post-merge raw CLI checks are mandatory before tagging. |
| Release Tag Safety | 12/12 | rc1 and rc2 are annotated and unchanged, rc3 is absent before merge, final `v0.1.0` is absent, and no push occurred. |

## Findings

Critical issues: none.

High issues: none.

Medium issues: none.

Low issues:

- Feature-worktree bare `python -m osw.cli` reports `0.1.0rc2` because the
  local editable install points at the main worktree. Source-isolated package
  smoke validates rc3 with `PYTHONPATH=src`, and the post-merge raw CLI check on
  `develop` is required before any local rc3 tag is created.

## Required Fixes

None.

## Evidence

Feature-branch checks passed:

- `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc3 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --allowed-prior-rc-tag v0.1.0-rc2 --allowed-prior-rc-target 684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `python tools/qa/check_release_metadata.py --forbid-release-tags`: expected failure because local rc1/rc2 tags exist
- `$env:PYTHONPATH='src'; python -m osw.cli --version`: `osw 0.1.0rc3`
- `$env:PYTHONPATH='src'; python -m osw.cli doctor`: version `0.1.0rc3`
- `python tools/qa/check_docs_links.py`: 30 Markdown files, 58 local links, 0 external skipped, 0 failures
- `python tools/qa/check_duplicate_test_basenames.py`
- `pytest tests/unit/test_release_metadata.py -q`: 14 passed
- `pytest tests/unit/test_package_smoke.py -q`: 6 passed
- `pytest tests/unit -q`: 252 passed, 3 skipped
- `pytest tests/gui -q`: 10 skipped
- `pytest -q --import-mode=importlib`: 269 passed, 19 skipped
- `pytest tests/integration -q -m "not external_solver"`: 4 passed, 3 skipped, 3 deselected
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

Tag evidence before merge:

- `v0.1.0-rc1` object type: `tag`
- `v0.1.0-rc1` peeled target: `29c5c8bec8df30c7f7be72fc9be5e5409794968e`
- `v0.1.0-rc2` object type: `tag`
- `v0.1.0-rc2` peeled target: `684dc6138d4257564bbcdd176a9d5ed311a7316d`
- `v0.1.0-rc3`: absent
- `v0.1.0`: absent

## Merge Recommendation

Proceed with squash merge to `develop` using:

`chore(release): prepare v0.1.0rc3 local candidate`

After merge, run all post-merge pre-tag checks on `develop`. Create local
annotated `v0.1.0-rc3` only if those checks pass and raw CLI reports
`0.1.0rc3`.

## Residual Risks

- External URL freshness remains intentionally outside the local-only docs link
  checker.
- Public tag push, final tag creation, release artifacts, and public
  announcement remain separate maintainer-controlled gates.
