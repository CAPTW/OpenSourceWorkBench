# OSW-AUTO-070 Patch v0.1.2 RC1 Prep Review

## Review Decision

- Score: 94/100.
- Decision: APPROVE for squash merge after final pre-merge QA remains green.

## Scope Review

- The change is release-prep scoped: package version metadata, release metadata tests, release docs, and required reports.
- No product feature code, GUI behavior, solver adapter behavior, package dependency version expansion, release artifact build, or public announcement was added.
- Source license metadata remains `GPL-3.0-or-later`.

## Version And Tag Review

- Package metadata is consistently `0.1.2rc1` in `pyproject.toml`, `src/osw/__init__.py`, and package smoke expectations.
- Release docs state that `v0.1.1` is historical local-only evidence and must not be published as current after the GUI workflow fix.
- Final `v0.1.2` is documented as blocked until a later final gate.
- Existing historical tags are preserved by policy; no tag operation is part of this feature-branch review.

## Release Metadata Checker Review

- Existing checker support for repeatable historical final tags, prior RC allowances, expected current RC tags, annotated-tag requirements, `HEAD` target resolution, and forbidden final tags is exercised with new `0.1.2rc1` tests.
- New tests cover multiple historical finals (`v0.1.0`, `v0.1.1`), prior `v0.1.1-rc1`, forbidden `v0.1.2`, expected annotated `v0.1.2-rc1`, wrong-target failures, lightweight-tag failure, and unexpected `v0.1.2*` tag rejection.
- Tests use mocked Git output and do not mutate real repository tags, require network access, or push.

## QA Evidence

Passed:

- Release metadata command for `0.1.2rc1` before `v0.1.2-rc1`.
- `ruff check src tests`.
- `pytest tests/unit/test_release_metadata.py -q`.
- `pytest tests/unit/test_package_smoke.py -q`.
- `pytest tests/unit -q`.
- `pytest tests/gui -q` in the base environment skipped because PySide6 was missing.
- `pytest tests/integration -q -m "not external_solver"`.
- `pytest tests/golden -q`.
- `pytest tests/validation -q`.
- `pytest -q`.
- `pytest -q --import-mode=importlib`.
- `python tools/qa/run_fast_qa.py`.
- `python tools/qa/run_pre_merge_qa.py`.
- Source-install validation in `C:/Users/USER/source/repos/_venvs/osw-v012rc1-source-run-070`.
- Full-extras GUI workflow smoke, with 14 GUI tests passing.

## Remaining Risks

- Optional external executable live solver runs remain environment-specific P2 evidence.
- Manual desktop Computer Use depth remains P2; the RC1 gate relies on QTest/focused GUI tests.
- Cantera deprecation warning remains a P2 follow-up.
- Packaging artifact smoke remains a later gate.

## Required Amendments

None.
