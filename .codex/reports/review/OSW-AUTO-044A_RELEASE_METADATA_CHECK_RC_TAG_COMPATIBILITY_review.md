# OSW-AUTO-044A Review

## Review Score

95 / 100

## Decision

Approve.

## Scope Review

The diff is limited to release metadata QA tooling, focused release metadata
tests, release checklist/risk/decision docs, and required Codex evidence
reports. No product source, package version metadata, license text, external
solver behavior, docs link checker implementation, or default pytest collection
fix is included.

## QA Tooling Review

`tools/qa/check_release_metadata.py` now separates tag policy from metadata
checks:

- strict pre-tag mode rejects any local `v0.1*` tags through
  `--forbid-release-tags`;
- default mode accepts only the expected local annotated `v0.1.0-rc1` tag when
  present, still rejecting final `v0.1.0` and unexpected `v0.1*` tags;
- RC-aware mode validates expected tag name, peeled target commit, annotated tag
  status, final tag absence, and unexpected tag absence.

The checker does not create, delete, move, or push tags.

## Test Coverage Review

`tests/unit/test_release_metadata.py` covers:

- aligned metadata without tag checks;
- placeholder license rejection;
- valid expected annotated rc1 in default mode;
- strict pre-tag rejection with local rc1;
- RC-aware success for annotated rc1 at the expected target;
- wrong target failure;
- lightweight tag failure when annotation is required;
- final tag failure;
- unexpected release tag failure.

The tests monkeypatch Git command output and do not mutate real repository tags
or require network access.

## Documentation Review

`docs/10_release_checklist.md`, `docs/09_risk_register.md`, and
`docs/07_decision_log.md` now state that local rc1 remains OSW-AUTO-043
evidence, must not be pushed after this merge, and should be superseded by an
RC2 tag gate for the next current `develop` release candidate. Public push and
final `v0.1.0` remain blocked behind separate maintainer-controlled gates.

## Wording And Safety Review

The docs avoid public release claims, industrial certification language, and
external solver bundling claims. They preserve GPL-3.0-or-later metadata as
already decided and do not make new legal assertions.

## QA Evidence Review

Passing checks:

- `python tools/qa/check_release_metadata.py`
- `python tools/qa/check_release_metadata.py --expected-rc-tag v0.1.0-rc1 --expected-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --require-annotated-rc-tag`
- `pytest tests/unit/test_release_metadata.py -q`
- `pytest tests/unit -q`
- `ruff check src tests`
- `ruff check tools/qa/check_release_metadata.py tests/unit/test_release_metadata.py`
- `python tools/qa/check_no_solver_artifacts_committed.py`
- `python tools/qa/check_scope_drift.py`
- `python tools/qa/check_architecture_boundaries.py`
- `python tools/qa/run_fast_qa.py`
- `python tools/qa/run_pre_merge_qa.py`
- `pytest -q --import-mode=importlib`
- `git diff --check`

Expected/non-blocking:

- `python tools/qa/check_release_metadata.py --forbid-release-tags` fails for
  the intended strict pre-tag reason because local rc1 exists.
- `pytest -q` fails only with the documented duplicate
  `test_plugin_manager_dialog.py` basename collection mismatch.
- `tools/qa/check_docs_links.py` is absent and remains a P2 follow-up.

## Required Amend Items

None.

## Final Merge Recommendation

Squash merge to `develop` if pre-merge QA remains green and tag state is
unchanged. After merge, do not push `v0.1.0-rc1`; use
`OSW-AUTO-045_V0_1_RC2_TAG_GATE` for the next current RC candidate.
