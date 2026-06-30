# OSW-AUTO-042 Self-Check

## Step ID

OSW-AUTO-042_FINAL_LICENSE_METADATA_AND_RELEASE_NOTES

## Branch / Worktree

- Branch: `feature/osw-p13-2-final-license-release-notes`
- Worktree: `C:\Users\USER\source\repos\_worktrees\osw-p13-2-final-license-release-notes`
- Base branch: `develop`

## Maintainer License Decision

- Input value: `GPL-3.0-or-later`
- Decision note recorded in docs: repository source is GPL-3.0-or-later;
  external solver binaries are optional and not bundled by default; this is a
  maintainer project decision, not legal advice.

## Files Changed

- `LICENSE`
- `README.md`
- `CHANGELOG.md`
- `docs/07_decision_log.md`
- `docs/09_risk_register.md`
- `docs/10_release_checklist.md`
- `docs/13_license_and_version_plan.md`
- `docs/14_third_party_notices.md`
- `pyproject.toml`
- `src/osw/__init__.py`
- `tests/unit/test_package_smoke.py`
- `tests/unit/test_release_metadata.py`
- `tools/qa/check_release_metadata.py`
- `.codex/reports/self_check/OSW-AUTO-042_FINAL_LICENSE_METADATA_AND_RELEASE_NOTES.md`
- `.codex/reports/review/OSW-AUTO-042_FINAL_LICENSE_METADATA_AND_RELEASE_NOTES_review.md`

## Scope Summary

- Replaced the placeholder `LICENSE` with canonical GNU GPL version 3 text from
  the trusted local source
  `D:\Program Files\Git\mingw64\share\licenses\xz\COPYING.GPLv3`.
- Recorded the GPL-3.0-or-later maintainer decision in README,
  `pyproject.toml`, `docs/13_license_and_version_plan.md`,
  `docs/07_decision_log.md`, and `docs/10_release_checklist.md`.
- Updated package and CLI version metadata to `0.1.0rc1`.
- Added draft `CHANGELOG.md` release notes and `docs/14_third_party_notices.md`.
- Added a local-only release metadata QA helper and focused unit tests.
- Kept public tag creation and public announcement blocked for a dedicated
  release/tag gate.

## Commands Run

- `git status --short` from the base repo: clean before worktree creation.
- `git branch --show-current`: `develop`.
- `git worktree list`: no existing OSW-AUTO-042 worktree.
- `git tag --list "v0.1*"`: no local v0.1 tags.
- `git worktree add -b feature/osw-p13-2-final-license-release-notes ../_worktrees/osw-p13-2-final-license-release-notes develop`: passed.
- `Get-Content` on required docs, README, LICENSE, pyproject, and AGENTS files:
  passed.
- Local GPL text verification:
  `Get-Content 'D:\Program Files\Git\mingw64\share\licenses\xz\COPYING.GPLv3'`
  and `Get-FileHash ... -Algorithm SHA256`: passed; SHA-256
  `3972DC9744F6499F0F9B2DBF76696F2AE7AD8AF9B23DDE66D6AF86C9DFB36986`.
- `Copy-Item` from that local GPLv3 text into `LICENSE`: passed.
- `python -m osw.cli --version`: initially reported old installed
  `osw 0.1.0a0`; after editable refresh, passed with `osw 0.1.0rc1`.
- `python -m osw.cli doctor`: initially reported old installed version; after
  editable refresh, passed with `version: 0.1.0rc1`.
- `python -m pip install -e . --no-deps`: passed; refreshed local editable
  install to this worktree version.
- Removed generated `src/open_solver_workbench.egg-info` after verifying it was
  inside the worktree; no generated package metadata remains in Git status.
- `python tools/qa/check_release_metadata.py`: passed.
- `pytest tests/unit/test_release_metadata.py -q`: `2 passed`.
- `ruff check src tests`: passed.
- `python tools/qa/check_scope_drift.py`: passed.
- `python tools/qa/check_architecture_boundaries.py`: passed.
- `python tools/qa/check_no_solver_artifacts_committed.py`: passed.
- `pytest tests/unit -q`: first failed only because existing package smoke
  tests expected `0.1.0a0`; after updating version expectations, passed with
  `218 passed, 3 skipped`.
- `python tools/qa/run_fast_qa.py`: first failed for the same version test;
  after the test update, passed.
- `python tools/qa/run_pre_merge_qa.py`: first failed through fast QA for the
  same version test; after the test update, passed.
- `git diff --check`: passed with a line-ending warning for `LICENSE` only.
- `tools/qa/check_docs_links.py`: skipped because the tool is not present.

## Skipped Checks

- `python tools/qa/check_docs_links.py`: skipped; file is not present. This
  remains the existing P2 docs-link checker placeholder and was not implemented
  in this step.

## Remaining Risks

- Public tag creation and public announcement remain blocked until a dedicated
  release/tag gate completes.
- Third-party notices are a v0.1 source-distribution draft, not legal advice or
  final redistribution approval.
- External solver binaries remain optional local dependencies and are not
  bundled by default.
- The historical default broad `pytest -q` duplicate basename issue remains a
  separate P2 follow-up if still present in environments that do not use the
  current split/importlib path.

## Merge Recommendation

Merge recommended after review: the maintainer license decision is explicit,
metadata and docs are aligned, no tag was created, no release artifacts or
external solver binaries are staged, and required QA passes.
